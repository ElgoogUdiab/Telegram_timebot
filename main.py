from telegram.ext import Updater
import json
from telegram.ext import CommandHandler
from telegram import ReplyKeyboardMarkup, KeyboardButton
import logging
import pytz

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_TIMEZONE = 'UTC'

tz_keyboard = [
    [KeyboardButton(tzname)] for tzname in pytz.all_timezones
]

try:
    with open("token") as f:
        token = f.readline().strip()
except:
    print("No token! Create file named \"token\" under the same directory with main.py!")
    exit(1)
try:
    with open("timezone.json") as f:
        timezones = json.load(f)
except:
    timezones={}

updater = Updater(token=token, use_context=True)
dispatcher = updater.dispatcher

def update_timezone(chat_id, timezone):
    global timezones
    timezones.update({str(chat_id): timezone})
    with open("timezone.json", "w") as f:
        json.dump(timezones, f)

def start(update, context):
    if update.message.chat.type == "private":
        update_timezone(str(update.effective_user.id), DEFAULT_TIMEZONE)
        context.bot.send_message(chat_id=update.effective_user.id, text=f"The default timezone is {DEFAULT_TIMEZONE}.\nPlease set your own timezone with /settz")
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

def set_tz(update, context):
    if update.message.chat.type != "private":
        update.message.reply("Only use this command in private message!")
    else:
        reply_markup = ReplyKeyboardMarkup(tz_keyboard)
        context.bot.send_message(chat_id=update.effective_user.id, text=f"Please select the timezone below.", reply_markup=reply_markup)

language_handler = CommandHandler('settz', set_tz)
dispatcher.add_handler(language_handler)


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)
dispatcher.add_error_handler(error)

updater.start_polling()
