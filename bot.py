import os
import time
import secrets
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ─────────────────────────────────────────
#  CONFIGURATION
# ─────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID   = int(os.environ.get("ADMIN_ID", 123456789))  # Apna Telegram Numeric ID daalein

bot = telebot.TeleBot(BOT_TOKEN)

# Live-editable config (admin panel se change hoga)
bot_config = {
    "welcome": (
        "🔥 *PREMIUM COIN TOSS BOT* 🔥\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "👋 *Assalam u Alaikum!* Khush Aamdeed!\n\n"
        "🪙 Yeh bot *100% Cryptographic Random* engine use karta hai "
        "taake har toss bilkul fair aur unbiased ho.\n\n"
        "📌 *Available Commands:*\n"
        "🔹 /start — Bot start karein\n"
        "🔹 /flip  — Seedha coin flip karein\n"
        "🔹 /help  — Help guide dekh\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👨‍💻 *Developer:* @{dev}"
    ),
    "help": (
        "ℹ️ *HELP & GUIDE*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "⚙️ *Kaise Khelen?*\n"
        "Bas neeche wala *FLIP COIN* button dabao.\n"
        "System 5 second mein coin spin karega aur\n"
        "aapko *HEAD* ya *TAIL* result dega.\n\n"
        "🔐 *Randomness kaise kaam karta hai?*\n"
        "Hum Python ka `secrets` module use karte hain\n"
        "jo hardware-level entropy se random result deta hai —\n"
        "koi manipulation possible nahi!\n\n"
        "📌 *Commands:*\n"
        "🔹 /start — Main menu\n"
        "🔹 /flip  — Coin toss\n"
        "🔹 /help  — Yeh guide\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ *Powered by:* @{dev}"
    ),
    "result_title": "🏆 *TOSS RESULT* 🏆",
    "dev_name": "supanz",
}

# ─────────────────────────────────────────
#  HELPER — config text fill karna
# ─────────────────────────────────────────
def cfg(key):
    return bot_config[key].replace("{dev}", bot_config["dev_name"])

# ─────────────────────────────────────────
#  KEYBOARDS
# ─────────────────────────────────────────
def main_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("🪙  ⚡  FLIP COIN NOW  ⚡  🪙", callback_data="flip"),
        InlineKeyboardButton("ℹ️  Help Guide",                callback_data="help"),
    )
    return kb

def back_keyboard():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("⬅️  Back to Menu", callback_data="home"))
    return kb

def after_flip_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("🔄  Flip Again",      callback_data="flip"),
        InlineKeyboardButton("⬅️  Back to Menu",    callback_data="home"),
    )
    return kb

def admin_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("📝  Edit Welcome Message", callback_data="adm_welcome"),
        InlineKeyboardButton("ℹ️  Edit Help Message",    callback_data="adm_help"),
        InlineKeyboardButton("🏆  Edit Result Title",    callback_data="adm_result_title"),
        InlineKeyboardButton("👨‍💻  Edit Developer Name",  callback_data="adm_dev_name"),
        InlineKeyboardButton("❌  Close Panel",          callback_data="adm_close"),
    )
    return kb

# ─────────────────────────────────────────
#  COMMAND HANDLERS
# ─────────────────────────────────────────
@bot.message_handler(commands=["start", "menu"])
def cmd_start(message):
    bot.send_message(
        message.chat.id,
        cfg("welcome"),
        parse_mode="Markdown",
        reply_markup=main_keyboard(),
    )

@bot.message_handler(commands=["flip"])
def cmd_flip(message):
    # Seedha flip shuru — processing msg bhejo phir result
    msg = bot.send_message(
        message.chat.id,
        "⏳ *Toss In Progress... Please wait 5 seconds*",
        parse_mode="Markdown",
    )
    time.sleep(5.0)
    _send_result(message.chat.id, msg.message_id)

@bot.message_handler(commands=["help"])
def cmd_help(message):
    bot.send_message(
        message.chat.id,
        cfg("help"),
        parse_mode="Markdown",
        reply_markup=back_keyboard(),
    )

@bot.message_handler(commands=["admin"])
def cmd_admin(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ *Access Denied!*", parse_mode="Markdown")
        return
    bot.send_message(
        message.chat.id,
        (
            "⚙️ *ADMIN PANEL*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Kisi bhi option pe click karo aur\n"
            "naya text message mein bhejo — live update ho jayega!"
        ),
        parse_mode="Markdown",
        reply_markup=admin_keyboard(),
    )

# ─────────────────────────────────────────
#  RESULT HELPER
# ─────────────────────────────────────────
def _send_result(chat_id, message_id):
    outcome = secrets.choice(["HEAD", "TAIL"])
    emoji   = "🟡" if outcome == "HEAD" else "⚪"
    text = (
        f"{cfg('result_title')}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{emoji}  *Result:*  `{outcome}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👨‍💻 *Developer:* @{bot_config['dev_name']}"
    )
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=text,
        parse_mode="Markdown",
        reply_markup=after_flip_keyboard(),
    )

# ─────────────────────────────────────────
#  CALLBACK HANDLER
# ─────────────────────────────────────────
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    cid = call.message.chat.id
    mid = call.message.message_id
    uid = call.from_user.id

    # ── USER CALLBACKS ──────────────────
    if call.data == "home":
        bot.edit_message_text(
            chat_id=cid, message_id=mid,
            text=cfg("welcome"),
            parse_mode="Markdown",
            reply_markup=main_keyboard(),
        )

    elif call.data == "help":
        bot.edit_message_text(
            chat_id=cid, message_id=mid,
            text=cfg("help"),
            parse_mode="Markdown",
            reply_markup=back_keyboard(),
        )

    elif call.data == "flip":
        bot.edit_message_text(
            chat_id=cid, message_id=mid,
            text="⏳ *Toss In Progress... Please wait 5 seconds*",
            parse_mode="Markdown",
        )
        time.sleep(5.0)
        _send_result(cid, mid)

    # ── ADMIN CALLBACKS ─────────────────
    elif call.data.startswith("adm_"):
        if uid != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Access Denied!", show_alert=True)
            return

        if call.data == "adm_close":
            bot.delete_message(cid, mid)
            return

        key_map = {
            "adm_welcome":      "welcome",
            "adm_help":         "help",
            "adm_result_title": "result_title",
            "adm_dev_name":     "dev_name",
        }
        target = key_map.get(call.data)
        if not target:
            return

        bot.answer_callback_query(call.id)
        prompt = bot.send_message(
            cid,
            f"✍️ *{target.upper()} ke liye naya text bhejo:*\n\n"
            f"_(Welcome/Help mein `{{dev}}` likho — developer ka naam auto fill hoga)_",
            parse_mode="Markdown",
        )
        bot.register_next_step_handler(prompt, _save_setting, target, cid)

# ─────────────────────────────────────────
#  ADMIN SAVE SETTING
# ─────────────────────────────────────────
def _save_setting(message, key, admin_chat_id):
    if message.from_user.id != ADMIN_ID:
        return
    bot_config[key] = message.text
    bot.reply_to(
        message,
        f"✅ *{key.upper()} successfully update ho gaya!*\n\n"
        f"📋 *Preview:*\n{message.text[:200]}{'...' if len(message.text) > 200 else ''}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("⚙️ Admin Panel Wapas Kholo", callback_data="adm_reopen")
        ),
    )

# reopen admin panel via callback
@bot.callback_query_handler(func=lambda c: c.data == "adm_reopen")
def reopen_admin(call):
    if call.from_user.id != ADMIN_ID:
        return
    bot.send_message(
        call.message.chat.id,
        (
            "⚙️ *ADMIN PANEL*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Kisi bhi option pe click karo aur naya text bhejo."
        ),
        parse_mode="Markdown",
        reply_markup=admin_keyboard(),
    )

# ─────────────────────────────────────────
#  START BOT
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("✅ Coin Toss Bot is running...")
    bot.infinity_polling()
                                      
