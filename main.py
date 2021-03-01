from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler, PollAnswerHandler
from telegram import InlineQueryResultArticle, InputTextMessageContent, Poll, ParseMode, ReplyKeyboardMarkup, \
    KeyboardButton, KeyboardButtonPollType
from bs4 import BeautifulSoup
import requests
import re
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

updater = Updater('1469783440:AAHvWSYkHeJAUu_xRrO3h5G6i7-jcHzuSzI')

'''
update:{
    'update_id': 225373416,
    'message': {
        'message_id': 39,
        'date': 1605201782,
        'chat': {
            'id': 239752095,
            'type': 'private',
            'username': 'Lalu1908',
            'first_name': 'Luca',
            'last_name': 'Nicosia'
        }, 
        'text': '/caps',
        'entities': [{'type': 'bot_command', 'offset': 0, 'length': 5}],
        'caption_entities': [],
        'photo': [],
        'new_chat_members': [],
        'new_chat_photo': [],
        'delete_chat_photo': False,
        'group_chat_created': False,
        'supergroup_chat_created': False,
        'channel_chat_created': False,
        'from': {
            'id': 239752095,
            'first_name': 'Luca',
            'is_bot': False,
            'last_name': 'Nicosia',
            'username': 'Lalu1908',
            'language_code': 'it'}
        }
    }
'''


def inline_caps(update, context):
    print("in inline")
    query = update.inline_query.query
    if not query:
        return
    results = list()
    results.append(
        InlineQueryResultArticle(
            id=query.upper(),
            title='Caps',
            input_message_content=InputTextMessageContent(query.upper())
        )
    )
    context.bot.answer_inline_query(update.inline_query.id, results)


def get_bop_url():
    contents = requests.get('https://random.dog/woof.json').json()
    url = contents['url']
    return url


def get_prices(prod):
    print(prod)
    content = BeautifulSoup(prod, "html.parser")
    starting_price = ""
    sale_price = ""
    if content.find(id="priceblock_ourprice") is not None:
        starting_price = content.find(id="priceblock_ourprice").get_text()[0:-2]
        starting_price = starting_price.replace(",", ".")
    else:
        starting_price = -1
    if content.find(id="dealprice_savings") is not None:
        sale_price = content.find(id="dealprice_savings").get_text()
        sale_price = sale_price.replace("\n", "").replace("Risparmi:", "").replace(",", ".")
        sale_price = sale_price[0:sale_price.find("€") - 2]
    else:
        sale_price = -1
    print(starting_price)
    print(sale_price)
    return float(starting_price), float(sale_price)


def get_amazon(update, context):
    arg = ''.join(context.args)
    url = "https://www.instant-gaming.com/"
    headers = {
        'dnt': '1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.517 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-user': '?1',
        'sec-fetch-dest': 'document',
        'referer': 'https://www.amazon.it/',
        'accept-language': 'it-IT',
    }
    page = requests.get(url, headers=headers)
    content = BeautifulSoup(page.content, "html.parser")
    print(content)
    for product in content.find_all(string=re.compile(("_dealView_"))):
        get_prices(product)
    print("fine")


def bop(update, context):
    url = get_bop_url()
    chat_id = update.message.chat_id
    context.bot.send_photo(chat_id=chat_id, photo=url)


def start(update, context):
    text = "Hi {}! I'm a bot, please talk to me!".format(update.effective_user.mention_html())
    context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode=ParseMode.HTML)
    help(update, context)


def echo(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)


def error_callback(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def caps(update, context):
    text_caps = ''.join(context.args).upper()
    if text_caps == "":
        context.bot.send_message(chat_id=update.effective_chat.id, text="you need to insert some text")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)


def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")


def help(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="""This is the help command list:\n- /bop: random dog images\n- /caps <text>: text to caps\n- /help: show this text\nEnjoy!""")


def poll(update, context):
    # Sends a predefined poll
    questions = ["Good", "Really good", "Fantastic", "Great"]
    message = context.bot.send_poll(
        update.effective_chat.id,
        "How are you?",
        questions,
        is_anonymous=False,
        allows_multiple_answers=True,
    )
    # Save some info about the poll the bot_data for later use in receive_poll_answer
    payload = {
        message.poll.id: {
            "questions": questions,
            "message_id": message.message_id,
            "chat_id": update.effective_chat.id,
            "answers": 0,
        }
    }
    context.bot_data.update(payload)


def receive_poll_answer(update, context):
    # Summarize a users poll vote
    answer = update.poll_answer
    poll_id = answer.poll_id
    try:
        questions = context.bot_data[poll_id]["questions"]
    # this means this poll answer update is from an old poll, we can't do our answering then
    except KeyError:
        return
    selected_options = answer.option_ids
    answer_string = ""
    for question_id in selected_options:
        if question_id != selected_options[-1]:
            answer_string += questions[question_id] + " and "
        else:
            answer_string += questions[question_id]
    context.bot.send_message(
        context.bot_data[poll_id]["chat_id"],
        "{} feels {}!".format(update.effective_user.mention_html(), answer_string),
        parse_mode=ParseMode.HTML,
    )
    context.bot_data[poll_id]["answers"] += 1
    # Close poll after three participants voted
    if context.bot_data[poll_id]["answers"] == 3:
        context.bot.stop_poll(
            context.bot_data[poll_id]["chat_id"], context.bot_data[poll_id]["message_id"]
        )


def preview(update, context):
    """Ask user to create a poll and display a preview of it"""
    # using this without a type lets the user chooses what he wants (quiz or poll)
    button = [[KeyboardButton("Press me!", request_poll=KeyboardButtonPollType())]]
    message = "Press the button to let the bot generate a preview for your poll"
    # using one_time_keyboard to hide the keyboard
    update.effective_message.reply_text(
        message, reply_markup=ReplyKeyboardMarkup(button, one_time_keyboard=True)
    )


def main():
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('bop', bop))
    dispatcher.add_handler(CommandHandler('start', start))

    echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
    dispatcher.add_handler(echo_handler)

    dispatcher.add_handler(CommandHandler('caps', caps))
    dispatcher.add_handler(CommandHandler('help', help))
    dispatcher.add_handler(CommandHandler('get_amazon', get_amazon))
    dispatcher.add_handler(CommandHandler('preview', preview))
    dispatcher.add_handler(CommandHandler('poll', poll))
    dispatcher.add_handler(PollAnswerHandler(receive_poll_answer))

    dispatcher.add_handler(InlineQueryHandler(inline_caps))

    dispatcher.add_handler(MessageHandler(Filters.command, unknown))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
    pass