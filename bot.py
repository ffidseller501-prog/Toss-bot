import os
import time
import random
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 123456789))
DEVELOPER_USERNAME = os.environ.get("DEVELOPER_USERNAME", "supanz")

bot = telebot.TeleBot(BOT_TOKEN)

# Dynamic Storage
settings = {
    "welcome": "🔥 **WELCOME TO THE PREMIUM TOSS SYSTEM** 🔥",
    "help": "ℹ️ **BOT HELP & OFFICIAL GUIDE**",
    "result_title": "🏆 **TOSS BOT RESULT** 🏆"
}

# --- KEYBOARD ---
def get_main_menu():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🪙 FLIP COIN", callback_data="flip"))
    markup.add(InlineKeyboardButton("ℹ️ HELP", callback_data="help"))
    return markup

# --- COMMANDS ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = get_main_menu()
    bot.reply_to(message, f"{settings['welcome']}\n\n👉 **Click below to play:**", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "flip":
        # Processing 1-line
        msg = bot.edit_message_text("⏳ **Toss In Processing... Please Wait 5sec**", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        time.sleep(5)
        res = random.choice(['HEAD', 'TAIL'])
        emoji = "🟡" if res == "HEAD" else "⚪"
        
        final = f"{settings['result_title']}\n───────────────────\n{emoji} **Result:** `{res}`\n───────────────────\n👨‍💻 **Dev:** @{DEVELOPER_USERNAME}"
        bot.edit_message_text(final, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔄 FLIP AGAIN", callback_data="flip")))

    elif call.data == "help":
        bot.edit_message_text(f"{settings['help']}\n\n👉 **Use /flip to start.**", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ BACK", callback_data="back")))
    
    elif call.data == "back":
        bot.edit_message_text(f"{settings['welcome']}\n\n👉 **Click below to play:**", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=get_main_menu())

# --- ADMIN PANEL (The "OP" Feature) ---
@bot.message_handler(commands=['admin'])
def admin(message):
    if message.from_user.id == ADMIN_ID:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📝 Edit Welcome", callback_data="edit_welcome"),
                   InlineKeyboardButton("🏆 Edit Result Title", callback_data="edit_result"))
        bot.reply_to(message, "⚙️ **ADMIN PANEL**", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('edit_'))
def edit_logic(call):
    key = call.data.split('_')[1]
    msg = bot.send_message(call.message.chat.id, f"✍️ **Enter new text for {key}:**")
    bot.register_next_step_handler(msg, lambda m: save_setting(m, key))

def save_setting(message, key):
    settings[key if key == 'welcome' else 'result_title'] = message.text
    bot.reply_to(message, "✅ **Saved!**")

bot.infinity_polling()
