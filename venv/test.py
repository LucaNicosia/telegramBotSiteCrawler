import json
import threading

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler, PollAnswerHandler
from telegram import InlineQueryResultArticle, InputTextMessageContent, Poll, ParseMode, ReplyKeyboardMarkup, \
    KeyboardButton, KeyboardButtonPollType
from bs4 import BeautifulSoup
import requests
import re
import logging

headers = {
    'dnt': '1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.517 Safari/537.36',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-user': '?1',
    'sec-fetch-dest': 'document',
    'referer': 'https://www.instant-gaming.com/',
    'accept-language': 'it-IT',
}

instant_gaming_url = "https://www.instant-gaming.com/it"
max_results = 10
cur_results = 5

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

updater = Updater('1469783440:AAHvWSYkHeJAUu_xRrO3h5G6i7-jcHzuSzI')


def help_constructor(header, footer, commands, descriptions):
    help_text = header + "\n"
    help_text += "".join([c + ": " + d + "\n" for (c, d) in (zip(commands, descriptions))])
    help_text += footer
    return help_text


def bitly(longurl):
    headers_bit = {
        "content-type": "application/json",
        "Authorization": "c655daa947fb6ba91e0efa610ac898bf7a00c61f"
    }
    body = json.dumps({
        "domain": "bit.ly",
        "long_url": longurl
    })
    URL = "https://api-ssl.bitly.com/v4/shorten"
    res = requests.post(url=URL, data=body, headers=headers_bit)
    return res.json()['link']


def get_daily_promo_data():
    url = instant_gaming_url
    page = requests.get(url, headers=headers)
    content = BeautifulSoup(page.content, "html.parser")
    price_div = content.find("div", {"id": "ig-promo"})
    prices_div = price_div.find_all("span")
    prices = []
    for price in prices_div:
        prices.append(price.getText()[0:-1])
    img_url = content.find("img", {"class": "picture"}).attrs['src']
    link = content.find("a", {"class": "promo mainshadow"}).attrs['href']

    return prices, img_url, link


def get_daily_promo(update, context):
    (prices, img_url, link) = get_daily_promo_data()
    price1 = prices[0]
    price2 = prices[1]
    actual_price = prices[2]
    text = "This is the today discount\nFrom {}€ to {}€ and now only {}€\nLink: {}".format(price1, price2, actual_price,
                                                                                           link)
    chat_id = update.message.chat_id
    context.bot.send_photo(chat_id=chat_id, photo=img_url, caption=text)


def game_data(game_html):
    parameters = ["name", "price", "discount", "is_dlc", "img_url", "link"]
    game_name = game_html.find("div", {"class": "name"}).getText()
    is_dlc = "no"
    if game_html.find("img", {"class": "dlc"}) is not None:
        is_dlc = "yes"
    game_price = game_html.find("div", {"class": "price"}).getText()[1:-2]
    game_discount = game_html.find("div", {"class": "discount"}).getText()
    img_url = game_html.find("img", {"class": "picture mainshadow"}).attrs['src']
    link = bitly(game_html.find("a", {"class": "cover"}).attrs['href'])
    appo = [game_name, game_price, game_discount, is_dlc, img_url, link]
    json_game = json.dumps(dict(zip(parameters, appo)))
    return json_game


def search_promo_data(search):
    url = "{}/ricerca/?q={}".format(instant_gaming_url, search)
    page = requests.get(url, headers=headers)
    content = BeautifulSoup(page.content, "html.parser")
    if content.find("div", {"class": "noresult"}) is not None:
        return None
    best_games = content.findAll("div", {"class": "category-best item mainshadow"})
    games = content.findAll("div", {"class": "item mainshadow"})
    returned_games = []
    i = 0
    for best_game in best_games:
        json_best_game = game_data(best_game)
        returned_games.append(json_best_game)
        i += 1
        if i >= cur_results:
            break
    if i < cur_results:
        for game in games:
            json_game = game_data(game)
            returned_games.append(json_game)
            i += 1
            if i >= cur_results:
                break

    return returned_games


def search_promo(update, context):
    games = search_promo_data(" ".join(context.args))
    chat_id = update.message.chat_id
    if games is None:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Sorry. No results found...")
        return
    text = "{}\nPrice={}\nDiscount={}\nIs DLC={}\nLink: {}"
    for game_1 in games:
        game = json.loads(game_1)
        context.bot.send_photo(chat_id=chat_id, photo=game['img_url'],
                               caption=text.format(game["name"], game["price"], game["discount"], game["is_dlc"],
                                                   game['link']))


def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")


def help(update, context):
    commands = ["/daily", "/searchpromo", "/help"]
    descriptions = ["show daily instant gaming promo", "show top 5 related games", "show this text"]
    text = help_constructor(header="Hi {}!\nThis is the help command list".format(update.message.from_user["username"]), commands=commands, descriptions=descriptions,
                            footer="Enjoy!")
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)


def main():
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('daily', get_daily_promo))
    dispatcher.add_handler(CommandHandler('help', help))
    dispatcher.add_handler(CommandHandler('searchpromo', search_promo))

    dispatcher.add_handler(MessageHandler(Filters.command, unknown))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
    pass
