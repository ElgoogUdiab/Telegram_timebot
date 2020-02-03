from telegram.ext import Updater
import json
from telegram.ext import CommandHandler, MessageHandler, ConversationHandler, Filters
from telegram import ReplyKeyboardMarkup, KeyboardButton
import logging
import pytz

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_TIMEZONE = 'UTC'

# Timezone tree generation
tz_dict = {}
depth = 0
for tzname in pytz.common_timezones:
    tzname = tzname.replace("_", " ")
    tz_split = tzname.split("/")
    depth = max(depth, len(tz_split))
    curr_dict = tz_dict
    for name in tz_split:
        if not name in curr_dict:
            curr_dict[name] = {}
        curr_dict = curr_dict[name]

PREVIOUS_TEXT = "<< Go Back"
CUSTOM_TEXT = "Custom timezone"
def gen_markup(prefix=[]):
    curr_dict = tz_dict
    for name in prefix:
        curr_dict = curr_dict[name]
    keyboard = [
        [KeyboardButton(name)] for name in curr_dict.keys()
    ]
    if len(prefix) == 0:
        last_line = [
            KeyboardButton(CUSTOM_TEXT)
        ]
    else:
        last_line = [
            KeyboardButton(PREVIOUS_TEXT),
            KeyboardButton(CUSTOM_TEXT)
        ]
    keyboard.append(last_line)
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

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
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"The default timezone is {DEFAULT_TIMEZONE}.\nPlease set your own timezone with /settz")
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

SELECT, CUSTOM = range(2)
def set_tz(update, context):
    if update.message.chat.type != "private":
        update.message.reply("Only use this command in private message!")
        return ConversationHandler.END
    else:
        message = context.bot.send_message(chat_id=update.effective_chat.id, text=f"Please select the timezone below.\nType /cancel anytime to cancel.", reply_markup=gen_markup())
        context.user_data["tz"] = []
        context.user_data["message"] = message
        return SELECT
def select(update, context):
    region = update.message.text
    if region == CUSTOM_TEXT:
        context.bot.delete_message(
            chat_id = context.user_data["message"].chat_id,
            message_id = context.user_data["message"].message_id,
        )
        message = context.bot.send_message(
            chat_id = context.user_data["message"].chat_id,
            text = "Type the timezone name below."
        )
        context.user_data["message"]=message
        return CUSTOM
    elif region == PREVIOUS_TEXT:
        context.user_data["tz"].pop()
        context.bot.delete_message(
            chat_id = context.user_data["message"].chat_id,
            message_id = context.user_data["message"].message_id,
        )
        message = context.bot.send_message(
            chat_id = context.user_data["message"].chat_id,
            text="Please select the timezone below.\nType /cancel anytime to cancel.",
            reply_markup = gen_markup(context.user_data["tz"])
        )
        context.user_data["message"]=message
        return SELECT
    curr_dict = tz_dict
    for name in context.user_data["tz"]:
        curr_dict = curr_dict[name]
    if not region in curr_dict:
        context.bot.send_message(chat_id=update.effective_chat.id, text="No such zone! Please select the zone again.")
        return SELECT
    curr_dict = curr_dict[region]
    context.user_data["tz"].append(region)
    if curr_dict == {}:
        tzname = "/".join(context.user_data["tz"])
        context.bot.delete_message(
            chat_id = context.user_data["message"].chat_id,
            message_id = context.user_data["message"].message_id
        )
        context.bot.send_message(
            chat_id = context.user_data["message"].chat_id,
            text = f"Timezone set as {tzname}.",
            reply_markup = None
        )
        update_timezone(str(update.effective_user.id), tzname)
        context.user_data.clear()
        return ConversationHandler.END
    else:
        context.bot.delete_message(
            chat_id = context.user_data["message"].chat_id,
            message_id = context.user_data["message"].message_id,
        )
        message = context.bot.send_message(
            chat_id = context.user_data["message"].chat_id,
            text="Please select the timezone below.\nType /cancel anytime to cancel.",
            reply_markup = gen_markup(context.user_data["tz"])
        )
        context.user_data["message"]=message
        return SELECT
def custom(update, context):
    pass
    return ConversationHandler.END
def cancel(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"OK! Canceled")
    data = context.user_data
    data.clear()
    return ConversationHandler.END
select_tz_handler = ConversationHandler(
    entry_points = [CommandHandler("settz", set_tz)],
    states = {
        SELECT: [MessageHandler(Filters.text, select)],
        CUSTOM: [MessageHandler(Filters.text, custom)]
    },
    fallbacks = [CommandHandler('cancel', cancel)]
)
dispatcher.add_handler(select_tz_handler)

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)
dispatcher.add_error_handler(error)

updater.start_polling()
