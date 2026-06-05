import os
import time
import random
import telebot

# Environment Variables for Railway (No token leak in code)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
# Agar testing ke liye local run karna ho toh ADMIN_ID direct numeric daal sakte hain
ADMIN_ID = int(os.environ.get("ADMIN_ID", 123456789))  
DEVELOPER_USERNAME = os.environ.get("DEVELOPER_USERNAME", "supanz")

bot = telebot.TeleBot(BOT_TOKEN)

# Live Customizable Messages
bot_messages = {
    "start": "👋 *Welcome to Coin Toss Bot!*\n\nUse `/flip` command to toss the coin instantly.\n\n👨‍💻 *Developer:* @{dev}",
    "help": "ℹ️ *Bot Help Menu*\n\n📌 `/start` - Start the bot\n📌 `/flip` - Toss the coin (5 seconds processing)\n📌 `/help` - Show this help menu\n\n⚡ Powered by @{dev}",
    "result_title": "⚡ *COIN TOSS RESULT* ⚡"
}

# --- BASIC COMMANDS ---

@bot.message_handler(commands=['start'])
def command_start(message):
    text = bot_messages["start"].format(dev=DEVELOPER_USERNAME)
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['help'])
def command_help(message):
    text = bot_messages["help"].format(dev=DEVELOPER_USERNAME)
    bot.reply_to(message, text, parse_mode="Markdown")

# --- THE MAIN FLIP PROCESS WITH DIRECT REPLY ---

@bot.message_handler(commands=['flip'])
def command_flip(message):
    processing_text = (
        "⚙️ *Toss In Processing... Please Wait 5sec*\n"
        "🔄 _System is flipping the coin randomly_ `[ 💿 ]`"
    )
    
    # 1. Sends processing text as a direct reply to user's message
    msg = bot.reply_to(message, processing_text, parse_mode="Markdown")
    
    # 2. Strict 5 seconds wait
    time.sleep(5.0)
    
    # 3. Generate random result
    result = random.choice(['HEAD', 'TAIL'])
    
    final_text = (
        f"{bot_messages['result_title']}\n"
        f"───────────────────\n"
        f"🎯 *Result:* `{result}`\n"
        f"───────────────────\n"
        f"👨‍💻 *Developer:* @{DEVELOPER_USERNAME}"
    )
    
    # 4. Edits that specific reply message into final result
    bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=msg.message_id,
        text=final_text,
        parse_mode="Markdown"
    )

# --- ADMIN PANEL ---

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id == ADMIN_ID:
        msg = bot.reply_to(message, "⚙️ *Admin Mode:* Send me the new *Result Title* text:", parse_mode="Markdown")
        bot.register_next_step_handler(msg, save_admin_title)
    else:
        bot.reply_to(message, "❌ Access Denied.", parse_mode="Markdown")

def save_admin_title(message):
    if message.from_user.id == ADMIN_ID:
        bot_messages["result_title"] = message.text
        bot.reply_to(message, "✅ *Result title updated successfully!*", parse_mode="Markdown")

# Run Connection
if __name__ == "__main__":
    print("[SYSTEM] Super Simple Coin Toss Bot is active on Production...")
    bot.infinity_polling()
  
