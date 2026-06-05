import os
import time
import secrets
import json
from datetime import datetime, timedelta
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ─────────────────────────────────────────
#  CONFIGURATION
# ─────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID  = int(os.environ.get("ADMIN_ID", 123456789))  # Apna Telegram ID daalein

bot = telebot.TeleBot(BOT_TOKEN)

# ─────────────────────────────────────────
#  DATA FILES (disk pe save hoga)
# ─────────────────────────────────────────
STATS_FILE  = "stats.json"
CONFIG_FILE = "config.json"

def load_json(path, default):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return default

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# Stats structure
# {
#   "total_users": [...user_ids...],
#   "total_tosses": 0,
#   "activity": {"user_id": "last_seen_iso"}
# }
stats = load_json(STATS_FILE, {
    "total_users": [],
    "total_tosses": 0,
    "activity": {}
})

# ─────────────────────────────────────────
#  BOT CONFIG (admin se edit hoga)
# ─────────────────────────────────────────
DEFAULT_CONFIG = {
    "welcome": (
        "🔥 *PREMIUM COIN TOSS BOT* 🔥\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "👋 *Assalam u Alaikum!* Khush Aamdeed!\n\n"
        "🪙 Yeh bot *100% Cryptographic Random* engine use\n"
        "karta hai — har toss bilkul fair aur unbiased!\n\n"
        "📌 *Command:*  /flip — Coin Toss karo\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👨‍💻 *Developer:* @{dev}"
    ),
    "help": (
        "ℹ️ *HELP & GUIDE*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "⚙️ *Kaise Khelen?*\n"
        "• /flip command use karo\n"
        "• System 5 second mein coin spin karega\n"
        "• *HEAD* ya *TAIL* result milega\n\n"
        "🔐 *Fair Randomness:*\n"
        "Hum Python `secrets` module use karte hain\n"
        "jo hardware-level entropy se result deta hai —\n"
        "koi bhi manipulation possible nahi!\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ *Powered by:* @{dev}"
    ),
    "result_title": "🏆 *TOSS RESULT* 🏆",
    "dev_name": "supanz"
}

bot_config = load_json(CONFIG_FILE, DEFAULT_CONFIG)
# Naye keys add karo agar config file purani ho
for k, v in DEFAULT_CONFIG.items():
    if k not in bot_config:
        bot_config[k] = v
save_json(CONFIG_FILE, bot_config)

def cfg(key):
    return bot_config[key].replace("{dev}", bot_config["dev_name"])

# ─────────────────────────────────────────
#  STATS HELPERS
# ─────────────────────────────────────────
def record_user(user_id):
    uid = str(user_id)
    if uid not in stats["total_users"]:
        stats["total_users"].append(uid)
    stats["activity"][uid] = datetime.utcnow().isoformat()
    save_json(STATS_FILE, stats)

def record_toss():
    stats["total_tosses"] += 1
    save_json(STATS_FILE, stats)

def get_active_users_count(hours=24):
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    count = 0
    for uid, ts in stats["activity"].items():
        try:
            if datetime.fromisoformat(ts) >= cutoff:
                count += 1
        except:
            pass
    return count

# ─────────────────────────────────────────
#  KEYBOARDS
# ─────────────────────────────────────────
def start_keyboard():
    """Sirf Help button — no Toss Now button"""
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("ℹ️  Help & Guide", callback_data="help"))
    return kb

def help_back_keyboard():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("⬅️  Back", callback_data="home"))
    return kb

def admin_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("📊  Stats & Users",         callback_data="adm_stats"),
        InlineKeyboardButton("📝  Edit Welcome Message",  callback_data="adm_welcome"),
        InlineKeyboardButton("ℹ️  Edit Help Message",     callback_data="adm_help"),
        InlineKeyboardButton("🏆  Edit Result Title",     callback_data="adm_result_title"),
        InlineKeyboardButton("👨‍💻  Edit Developer Name",   callback_data="adm_dev_name"),
        InlineKeyboardButton("🔄  Reset All Stats",       callback_data="adm_reset_stats"),
        InlineKeyboardButton("❌  Close Panel",           callback_data="adm_close"),
    )
    return kb

def confirm_reset_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ Haan, Reset Karo", callback_data="adm_reset_confirm"),
        InlineKeyboardButton("❌ Cancel",           callback_data="adm_back"),
    )
    return kb

# ─────────────────────────────────────────
#  COMMANDS
# ─────────────────────────────────────────
@bot.message_handler(commands=["start", "menu"])
def cmd_start(message):
    record_user(message.from_user.id)
    bot.send_message(
        message.chat.id,
        cfg("welcome"),
        parse_mode="Markdown",
        reply_markup=start_keyboard(),
    )

@bot.message_handler(commands=["flip"])
def cmd_flip(message):
    record_user(message.from_user.id)
    msg = bot.send_message(
        message.chat.id,
        "⏳ *Toss In Progress...*\n_Please wait 5 seconds_",
        parse_mode="Markdown",
    )
    time.sleep(5.0)
    record_toss()
    _edit_result(message.chat.id, msg.message_id)

@bot.message_handler(commands=["admin"])
def cmd_admin(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ *Access Denied!*", parse_mode="Markdown")
        return
    bot.send_message(
        message.chat.id,
        "⚙️ *ADMIN PANEL*\n━━━━━━━━━━━━━━━━━━━━━━━━━\nKoi bhi option select karo:",
        parse_mode="Markdown",
        reply_markup=admin_keyboard(),
    )

# ─────────────────────────────────────────
#  RESULT — clean, no extra buttons
# ─────────────────────────────────────────
def _edit_result(chat_id, message_id):
    outcome = secrets.choice(["HEAD", "TAIL"])
    emoji   = "🟡" if outcome == "HEAD" else "⚪"
    text = (
        f"{cfg('result_title')}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{emoji}  *Result:*  `{outcome}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👨‍💻 *Dev:* @{bot_config['dev_name']}\n\n"
        f"_/flip likhkar dobara toss karo_"
    )
    # Koi button nahi — clean result only
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=text,
        parse_mode="Markdown",
    )

# ─────────────────────────────────────────
#  CALLBACKS
# ─────────────────────────────────────────
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    cid = call.message.chat.id
    mid = call.message.message_id
    uid = call.from_user.id

    # ── USER ──
    if call.data == "home":
        bot.edit_message_text(
            chat_id=cid, message_id=mid,
            text=cfg("welcome"),
            parse_mode="Markdown",
            reply_markup=start_keyboard(),
        )

    elif call.data == "help":
        bot.edit_message_text(
            chat_id=cid, message_id=mid,
            text=cfg("help"),
            parse_mode="Markdown",
            reply_markup=help_back_keyboard(),
        )

    # ── ADMIN ──
    elif call.data.startswith("adm_"):
        if uid != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Access Denied!", show_alert=True)
            return

        bot.answer_callback_query(call.id)

        if call.data == "adm_close":
            bot.delete_message(cid, mid)

        elif call.data == "adm_back":
            bot.edit_message_text(
                chat_id=cid, message_id=mid,
                text="⚙️ *ADMIN PANEL*\n━━━━━━━━━━━━━━━━━━━━━━━━━\nKoi bhi option select karo:",
                parse_mode="Markdown",
                reply_markup=admin_keyboard(),
            )

        elif call.data == "adm_stats":
            total  = len(stats["total_users"])
            active = get_active_users_count(24)
            tosses = stats["total_tosses"]
            text = (
                "📊 *BOT STATISTICS*\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"👥  *Total Users:*       `{total}`\n"
                f"🟢  *Active (24h):*      `{active}`\n"
                f"🪙  *Total Tosses:*      `{tosses}`\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━"
            )
            back_kb = InlineKeyboardMarkup()
            back_kb.add(InlineKeyboardButton("⬅️  Back", callback_data="adm_back"))
            bot.edit_message_text(
                chat_id=cid, message_id=mid,
                text=text, parse_mode="Markdown",
                reply_markup=back_kb,
            )

        elif call.data == "adm_reset_stats":
            bot.edit_message_text(
                chat_id=cid, message_id=mid,
                text="⚠️ *Kya aap sure hain?*\nSaare stats delete ho jayenge!",
                parse_mode="Markdown",
                reply_markup=confirm_reset_keyboard(),
            )

        elif call.data == "adm_reset_confirm":
            stats["total_users"]  = []
            stats["total_tosses"] = 0
            stats["activity"]     = {}
            save_json(STATS_FILE, stats)
            bot.edit_message_text(
                chat_id=cid, message_id=mid,
                text="✅ *Stats reset ho gaye!*",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("⬅️  Back", callback_data="adm_back")
                ),
            )

        else:
            key_map = {
                "adm_welcome":      "welcome",
                "adm_help":         "help",
                "adm_result_title": "result_title",
                "adm_dev_name":     "dev_name",
            }
            target = key_map.get(call.data)
            if not target:
                return
            prompt = bot.send_message(
                cid,
                f"✍️ *{target.upper()} ke liye naya text bhejo:*\n\n"
                f"_Tip: Welcome/Help mein `{{dev}}` likho — dev naam auto fill hoga_",
                parse_mode="Markdown",
            )
            bot.register_next_step_handler(prompt, _save_setting, target)

# ─────────────────────────────────────────
#  ADMIN SAVE
# ─────────────────────────────────────────
def _save_setting(message, key):
    if message.from_user.id != ADMIN_ID:
        return
    bot_config[key] = message.text
    save_json(CONFIG_FILE, bot_config)
    preview = message.text[:300] + ("..." if len(message.text) > 300 else "")
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("⚙️  Admin Panel", callback_data="adm_reopen"))
    bot.reply_to(
        message,
        f"✅ *{key.upper()} update ho gaya!*\n\n📋 *Preview:*\n{preview}",
        parse_mode="Markdown",
        reply_markup=kb,
    )

@bot.callback_query_handler(func=lambda c: c.data == "adm_reopen")
def reopen_admin(call):
    if call.from_user.id != ADMIN_ID:
        return
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        "⚙️ *ADMIN PANEL*\n━━━━━━━━━━━━━━━━━━━━━━━━━\nKoi bhi option select karo:",
        parse_mode="Markdown",
        reply_markup=admin_keyboard(),
    )

# ─────────────────────────────────────────
#  RUN
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("✅ Secure Coin Toss Bot is running...")
    bot.infinity_polling()
    
