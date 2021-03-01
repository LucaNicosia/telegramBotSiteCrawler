import json
import time
import html
from datetime import date
from threading import Thread, Event
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

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

updater = Updater('1463652732:AAGeouG2gBI5TOr-_K0fh6SaEVqYK41F2Ug')

jw_link = "https://www.jw.org"


class NewsThread(Thread):
    def __init__(self, threadID, name, index, update, context):
        Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.index = index
        self.update = update
        self.context = context

    def getIndex(self):
        return self.index

    def run(self):
        # this code can be replaced with "run_function"
        run_function(self)
        print("exiting run")


newsThread = [NewsThread(-1, "", -1 , None, None)]
newsThread_status = []
counter = 0


def run_function(thread_elem):
    latest_article = [];
    while True:
        try:
            timeout = 3600;
            while not newsThread_status[thread_elem.index].is_set():
                latest_article = get_last_news(thread_elem.update, thread_elem.context, latest_article)
                time.sleep(timeout)
                print("after sleep of "+thread_elem.update.message.from_user["username"])
            break;
        except:
            print("exception");


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

    # return res.link
    return res.json()['link']


def start(update, context):
    global counter
    print("starting thread")
    if counter > 0 and not newsThread_status[counter - 1].is_set():
        context.bot.send_message(chat_id=update.effective_chat.id, text="bot already running",
                                 parse_mode=ParseMode.HTML)
        return
    #text = "Hi {}!\nI'm a bot, please talk to me!\n".format(update.effective_user.mention_html())
    #context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode=ParseMode.HTML)
    help(update, context)
    newsThread_status.append(Event())  # newsThread_status[counter] = Event()
    newsThread[0] = NewsThread(0, "news_thread" + str(counter), counter, update, context)
    newsThread[0].start()
    newsThread[0].join(0)
    counter += 1
    print("exiting start")


def status(update, context):
    global counter
    if counter == 0:
        text = "none"
    else:
        if newsThread[0].is_alive():
            text = "alive"
            if newsThread_status[newsThread[0].getIndex()].is_set():
                text = "waiting for timer to shutting down"
        else:
            text = "dead"
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)


def stop(update, context):
    global counter
    if counter == 0:
        context.bot.send_message(chat_id=update.effective_chat.id, text="bot not started")
    else:
        if newsThread_status[counter - 1].is_set():
            context.bot.send_message(chat_id=update.effective_chat.id, text="bot already stopped")
        else:
            newsThread_status[counter - 1].set()
    print("exiting stop")


def get_last_news_data(old_dates, n_news):
    # if old_dates is True -> also dates different from today must be considered
    today = date.today().strftime("%Y-%m-%d")
    url = "{}/it/cosa-nuovo".format(jw_link)
    page = requests.get(url, headers=headers)
    content = BeautifulSoup(page.content, "html.parser")
    parameters = ["title", "img_url", "date", "link"]
    last_news = content.findAll("div", {"class": "synopsis"})
    news_json = []
    for news in last_news:
        title_wrap = news.find("div", {"class": "syn-body sqs"})
        n_date = title_wrap.find("p", {"class": "meta pubDate"}).getText()
        if not old_dates and n_date != today:
            break  # this 'break' is called only when we don't want old news and the date of this news is an old one
        title = html.unescape(title_wrap.find("a").getText()).replace("\n", "").replace("\t", "").strip()
        link = jw_link + title_wrap.find("a").attrs['href']
        short_link = bitly(link)
        img_url = news.find("img")  # bad image url (in case there is no image in the img_page)
        if img_url is None:  # in some case neither bad image is present, don't display any image
            img_url = ""
        else:
            img_url = img_url.attrs["src"]
        img_page = requests.get(link, headers=headers)
        img_content = BeautifulSoup(img_page.content, "html.parser")
        img = img_content.find("figure", {"class": "article-top-related-image"})
        if img is not None:  # in some cases the img_page has not a title image
            img_url = img.find("img").attrs['src']
        appo = [title, img_url, n_date, short_link]
        news_json.append(json.dumps(dict(zip(parameters, appo))))
        if len(news_json) >= n_news:
            break
    news_json.reverse()  # in this way, news are order by the latest to the oldest
    return news_json


def get_last_news(update, context, latest_article):
    old_dates = len(latest_article) == 0
    news = get_last_news_data(old_dates, 5)
    if len(latest_article) == 0:  # no latest_articles yet (first round)
        for elem in news:
            printLatestNews(update, context, json.loads(elem))
        return news
    if len(news) == 0:  # no today news and latest_article already set
        return latest_article
    if json.loads(latest_article[0])["title"] == json.loads(news[0])["title"]:  # if first article is the same, all
        # article are the same
        return latest_article
    for this_news in news:
        news_json = json.loads(this_news)
        # find_news return the vector of items in 'latest' that are equal to 'this'
        find_news = lambda this, latest: [el for el in latest if json.loads(el)["title"] == this["title"]]
        is_present = find_news(news_json, latest_article)
        if len(is_present) == 0:  # if is_present has no elements -> this is a news
            printLatestNews(update, context, news_json)
    return news


def printLatestNews(update, context, latest_article):
    print("new article found: " + latest_article["title"])
    #text = "{}\n<b>{}</b>\n> {}".format(latest_article["date"], latest_article["title"], latest_article["link"])
    text = "{}\n<b>{}</b>\n> {}".format("", latest_article["title"], latest_article["link"])
    chat_id = update.message.chat_id
    if latest_article["img_url"] != "":
        context.bot.send_photo(chat_id=chat_id, photo=latest_article["img_url"], caption=text, parse_mode=ParseMode.HTML)
    else:
        context.bot.send_message(chat_id=chat_id, text=text)


def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")


def help(update, context):
    print()
    commands = ["/start", "/stop", "/status", "/help"]
    descriptions = ["start/restart bot", "stop bot", "shows the program status", "shows this text"]
    text = help_constructor(header="This is the help command list:", commands=commands, descriptions=descriptions,
                            footer="Enjoy!")
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)


def main():
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('stop', stop))
    dispatcher.add_handler(CommandHandler('help', help))
    dispatcher.add_handler(CommandHandler('status', status))

    dispatcher.add_handler(MessageHandler(Filters.command, unknown))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
    pass
