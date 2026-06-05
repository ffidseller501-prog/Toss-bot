import os
import time
import secrets  # Cryptographically strong random numbers ke liye
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Environment Variables Configuration
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 123456789)) # Enter your Telegram Numeric ID

bot = telebot.TeleBot(BOT_TOKEN)

# Dynamic Master Storage (Admin can change everything live)
bot_config = {
    "welcome": "🔥 **WELCOME TO THE PREMIUM TOSS SYSTEM** 🔥\n\n👋 **Hello Buddy! Welcome to the most secure coin flipping system.**",
    "help": "ℹ️ **BOT HELP & OFFICIAL GUIDE**\n\n⚙️ **HOW TO PLAY?**\n**Just click the button below. The system will automatically spin the coin for 5 seconds and give you a 100% unbiased random result.**",
    "result_title": "🏆 **TOSS BOT RESULT** 🏆",
    "dev_name": "supanz"
}

# --- KEYBOARDS & LAYOUTS ---
def get_user_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("🪙 ⚡ FLIP COIN NOW ⚡ 🪙", callback_data="user_flip"),
        InlineKeyboardButton("ℹ️ VIEW HELP GUIDE", callback_data="user_help")
    )
    return markup

def get_admin_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("📝 Edit Welcome Message", callback_data="adm_edit_welcome"),
        InlineKeyboardButton("ℹ️ Edit Help Message", callback_data="adm_edit_help"),
        InlineKeyboardButton("🏆 Edit Result Title", callback_data="adm_edit_title"),
        InlineKeyboardButton("👨‍💻 Edit Developer User", callback_data="adm_edit_dev"),
        InlineKeyboardButton("❌ Close Admin Panel", callback_data="adm_close")
    )
    return markup

# --- MAIN COMMAND HANDLERS ---

@bot.message_handler(commands=['start', 'flip', 'menu'])
def send_welcome_menu(message):
    bot.reply_to(
        message, 
        f"{bot_config['welcome']}\n\n🚀 **COMMANDS YOU CAN USE:**\n🔹 **/flip** — **Toss the coin**\n─────────────────────────\n👨‍💻 **Developer:** @{bot_config['dev_name']}",
        parse_mode="Markdown",
        reply_markup=get_user_keyboard()
    )

# --- INLINE CONTROLS & TRUE RANDOM LOGIC ---

@bot.callback_query_handler(func=lambda call: True)
def handle_all_callbacks(call):
    user_id = call.from_user.id
    
    # 1. Main Flip Logic
    if call.data == "user_flip":
        # 1-Line Premium Processing Message as requested
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="⏳ **Toss In Processing... Please Wait 5sec**",
            parse_mode="Markdown"
        )
        
        # Strict 5 seconds hold simulation
        time.sleep(3.5)
        
        # --- TRUE CRYPTO RANDOM GENERATION (FIXED TAIL ISSUE) ---
        # secrets.choice bilkul un-biased secure random selection karta hai hardware level par
        final_outcome = secrets.choice(['HEAD', 'TAIL'])
        result_emoji = "🟡" if final_outcome == "HEAD" else "⚪"
        
        final_card = (
            f"{bot_config['result_title']}\n"
            f"─────────────────────────\n"
            f"{result_emoji} **Toss Result:** `{final_outcome}`\n"
            f"─────────────────────────\n"
            f"👨‍💻 **Developer:** @{bot_config['dev_name']}"
        )
        
        retry_markup = InlineKeyboardMarkup()
        retry_markup.add(InlineKeyboardButton("🔄 FLIP COIN AGAIN", callback_data="user_flip"))
        retry_markup.add(InlineKeyboardButton("⬅️ BACK TO MENU", callback_data="menu_home"))
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=final_card,
            parse_mode="Markdown",
            reply_markup=retry_markup
        )
        
    elif call.data == "user_help":
        back_markup = InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ BACK TO MENU", callback_data="menu_home"))
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"{bot_config['help']}\n─────────────────────────\n⚡ **Powered by:** @{bot_config['dev_name']}",
            parse_mode="Markdown",
            reply_markup=back_markup
        )
        
    elif call.data == "menu_home":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"{bot_config['welcome']}\n\n🚀 **COMMANDS YOU CAN USE:**\n🔹 **/flip** — **Toss the coin**\n─────────────────────────\n👨‍💻 **Developer:** @{bot_config['dev_name']}",
            parse_mode="Markdown",
            reply_markup=get_user_keyboard()
        )

    # --- ADMIN CONTROLS LIVE FIXES ---
    elif call.data.startswith('adm_'):
        if user_id != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Access Denied: You are not @supanz!", show_alert=True)
            return
            
        action = call.data
        if action == "adm_close":
            bot.delete_message(call.message.chat.id, call.message.message_id)
            return
            
        key_mapping = {
            "adm_edit_welcome": "welcome",
            "adm_edit_help": "help",
            "adm_edit_title": "result_title",
            "adm_edit_dev": "dev_name"
        }
        
        target_key = key_mapping.get(action)
        prompt = bot.send_message(call.message.chat.id, f"✍️ **Send me the new text for:** `{target_key.upper()}`", parse_mode="Markdown")
        bot.register_next_step_handler(prompt, save_dynamic_setting, target_key)

def save_dynamic_setting(message, key_to_update):
    if message.from_user.id == ADMIN_ID:
        bot_config[key_to_update] = message.text
        bot.reply_to(message, f"✅ **Successfully updated {key_to_update.upper()} live in the system!**", parse_mode="Markdown")

# --- ADMIN PANEL COMMAND ---
@bot.message_handler(commands=['admin'])
def load_admin_hub(message):
    if message.from_user.id == ADMIN_ID:
        bot.reply_to(
            message, 
            "⚙️ **POWERFUL ADMIN PANEL ACTIVATED**\n─────────────────────────\nAap bot ke saare text messages aur username yaha se live edit kar sakte hain:", 
            parse_mode="Markdown", 
            reply_markup=get_admin_keyboard()
        )
    else:
        bot.reply_to(message, "❌ *Access Denied!* Only @supanz can control this system.", parse_mode="Markdown")

# Run Poll
if __name__ == "__main__":
    print("[POWER LOGS] Ultra-Powerful Random Coin Toss Bot is fully functional...")
    bot.infinity_polling()
        
