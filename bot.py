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
ADMIN_ID  = int(os.environ.get("ADMIN_ID", 123456789))

bot = telebot.TeleBot(BOT_TOKEN)

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

stats = load_json(STATS_FILE, {
    "total_users": [],
    "total_tosses": 0,
    "activity": {},
    "messages": []   # stores all user messages
})

# ─────────────────────────────────────────
#  BOT CONFIG
# ─────────────────────────────────────────
DEFAULT_CONFIG = {
    "welcome": (
        "🔥 *PREMIUM COIN TOSS BOT* 🔥\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "👋 *Welcome!*\n\n"
        "🪙 This bot uses a *100% Cryptographic Random*\n"
        "engine — every toss is completely fair & unbiased!\n\n"
        "📌 *Command:*  /flip — Toss the coin\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👨‍💻 *Developer:* @{dev}"
    ),
    "help": (
        "ℹ️ *HELP & GUIDE*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "⚙️ *How to Play?*\n"
        "• Use the /flip command\n"
        "• The system will spin the coin for 5 seconds\n"
        "• You will get either *HEAD* or *TAIL*\n\n"
        "🔐 *How is it Fair?*\n"
        "We use Python's `secrets` module which pulls\n"
        "from hardware-level entropy — zero manipulation!\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ *Powered by:* @{dev}"
    ),
    "result_title": "🏆 *TOSS RESULT* 🏆",
    "dev_name": "supanz"
}

bot_config = load_json(CONFIG_FILE, DEFAULT_CONFIG)
for k, v in DEFAULT_CONFIG.items():
    if k not in bot_config:
        bot_config[k] = v
save_json(CONFIG_FILE, bot_config)

def cfg(key):
    return bot_config[key].replace("{dev}", bot_config["dev_name"])

# ─────────────────────────────────────────
#  STATS HELPERS
# ─────────────────────────────────────────
def record_user(user_id, username, first_name):
    uid = str(user_id)
    if uid not in stats["total_users"]:
        stats["total_users"].append(uid)
    stats["activity"][uid] = {
        "last_seen": datetime.utcnow().isoformat(),
        "username": username or "",
        "name": first_name or ""
    }
    save_json(STATS_FILE, stats)

def record_toss(user_id, username):
    stats["total_tosses"] += 1
    save_json(STATS_FILE, stats)

def record_message(user_id, username, first_name, text):
    stats["messages"].append({
        "uid": str(user_id),
        "username": username or "",
        "name": first_name or "",
        "text": text,
        "time": datetime.utcnow().isoformat()
    })
    # Keep only last 200 messages
    if len(stats["messages"]) > 200:
        stats["messages"] = stats["messages"][-200:]
    save_json(STATS_FILE, stats)

def get_active_users(hours=24):
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    count = 0
    for uid, data in stats["activity"].items():
        try:
            ts = data["last_seen"] if isinstance(data, dict) else data
            if datetime.fromisoformat(ts) >= cutoff:
                count += 1
        except:
            pass
    return count

# ─────────────────────────────────────────
#  KEYBOARDS
# ─────────────────────────────────────────
def start_keyboard():
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
        InlineKeyboardButton("📊  Stats & Users",        callback_data="adm_stats"),
        InlineKeyboardButton("💬  Recent Messages",      callback_data="adm_messages"),
        InlineKeyboardButton("📝  Edit Welcome Message", callback_data="adm_welcome"),
        InlineKeyboardButton("ℹ️  Edit Help Message",    callback_data="adm_help"),
        InlineKeyboardButton("🏆  Edit Result Title",    callback_data="adm_result_title"),
        InlineKeyboardButton("👨‍💻  Edit Developer Name",  callback_data="adm_dev_name"),
        InlineKeyboardButton("🗑️  Reset All Data",       callback_data="adm_reset_stats"),
        InlineKeyboardButton("❌  Close Panel",          callback_data="adm_close"),
    )
    return kb

def confirm_reset_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅  Yes, Delete All", callback_data="adm_reset_confirm"),
        InlineKeyboardButton("❌  Cancel",          callback_data="adm_back"),
    )
    return kb

# ─────────────────────────────────────────
#  COMMANDS
# ─────────────────────────────────────────
@bot.message_handler(commands=["start", "menu"])
def cmd_start(message):
    record_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    bot.reply_to(
        message,
        cfg("welcome"),
        parse_mode="Markdown",
        reply_markup=start_keyboard(),
    )

@bot.message_handler(commands=["flip"])
def cmd_flip(message):
    record_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    msg = bot.reply_to(
        message,
        "⏳ *Toss In Progress...*\n_Please wait 5 seconds_",
        parse_mode="Markdown",
    )
    time.sleep(5.0)
    record_toss(message.from_user.id, message.from_user.username)
    _edit_result(message.chat.id, msg.message_id)

@bot.message_handler(commands=["admin"])
def cmd_admin(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ *Access Denied!*", parse_mode="Markdown")
        return
    bot.reply_to(
        message,
        "⚙️ *ADMIN PANEL*\n━━━━━━━━━━━━━━━━━━━━━━━━━\nSelect an option below:",
        parse_mode="Markdown",
        reply_markup=admin_keyboard(),
    )

@bot.message_handler(commands=["resetall"])
def cmd_resetall(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ *Access Denied!*", parse_mode="Markdown")
        return
    # Confirm with inline buttons
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅  Yes, Delete All", callback_data="adm_reset_confirm"),
        InlineKeyboardButton("❌  Cancel",          callback_data="adm_cancel_msg"),
    )
    bot.reply_to(
        message,
        "⚠️ *Are you sure?*\n\nThis will permanently delete:\n"
        "• All user data\n• All stats\n• All message logs\n\n"
        "_This action cannot be undone!_",
        parse_mode="Markdown",
        reply_markup=kb,
    )

# Catch all user messages for logging
@bot.message_handler(func=lambda m: True, content_types=["text"])
def catch_all(message):
    if message.from_user.id == ADMIN_ID:
        return
    record_message(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
        message.text
    )

# ─────────────────────────────────────────
#  RESULT — clean, no buttons
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
        f"_Use /flip to toss again_"
    )
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
    elif call.data.startswith("adm_") or call.data == "adm_cancel_msg":
        if uid != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Access Denied!", show_alert=True)
            return

        bot.answer_callback_query(call.id)

        if call.data == "adm_close":
            bot.delete_message(cid, mid)

        elif call.data in ("adm_back", "adm_cancel_msg"):
            bot.edit_message_text(
                chat_id=cid, message_id=mid,
                text="⚙️ *ADMIN PANEL*\n━━━━━━━━━━━━━━━━━━━━━━━━━\nSelect an option below:",
                parse_mode="Markdown",
                reply_markup=admin_keyboard(),
            )

        elif call.data == "adm_stats":
            total  = len(stats["total_users"])
            active = get_active_users(24)
            tosses = stats["total_tosses"]
            msgs   = len(stats.get("messages", []))
            # Build recent users list
            recent = []
            for uid_str, data in list(stats["activity"].items())[-5:]:
                if isinstance(data, dict):
                    uname = data.get("username", "")
                    name  = data.get("name", "")
                    recent.append(f"  • {name} (@{uname})" if uname else f"  • {name}")
            recent_str = "\n".join(recent) if recent else "  _None yet_"
            text = (
                "📊 *BOT STATISTICS*\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"👥  *Total Users:*        `{total}`\n"
                f"🟢  *Active (Last 24h):*  `{active}`\n"
                f"🪙  *Total Tosses:*       `{tosses}`\n"
                f"💬  *Messages Logged:*    `{msgs}`\n\n"
                f"👤 *Recent Users:*\n{recent_str}\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━"
            )
            back_kb = InlineKeyboardMarkup()
            back_kb.add(InlineKeyboardButton("⬅️  Back", callback_data="adm_back"))
            bot.edit_message_text(
                chat_id=cid, message_id=mid,
                text=text, parse_mode="Markdown",
                reply_markup=back_kb,
            )

        elif call.data == "adm_messages":
            messages = stats.get("messages", [])
            if not messages:
                text = "💬 *Recent Messages*\n━━━━━━━━━━━━━━━━━━━━━━━━━\n\n_No messages yet._"
            else:
                lines = []
                for m in messages[-10:]:  # last 10
                    uname = f"@{m['username']}" if m.get("username") else m.get("name", "Unknown")
                    txt   = m["text"][:60] + ("..." if len(m["text"]) > 60 else "")
                    lines.append(f"👤 *{uname}:* {txt}")
                text = (
                    "💬 *Recent Messages (Last 10)*\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    + "\n\n".join(lines)
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
                text=(
                    "⚠️ *Are you sure?*\n\n"
                    "This will permanently delete:\n"
                    "• All user data\n• All stats\n• All message logs\n\n"
                    "_This action cannot be undone!_"
                ),
                parse_mode="Markdown",
                reply_markup=confirm_reset_keyboard(),
            )

        elif call.data == "adm_reset_confirm":
            stats["total_users"]  = []
            stats["total_tosses"] = 0
            stats["activity"]     = {}
            stats["messages"]     = []
            save_json(STATS_FILE, stats)
            bot.edit_message_text(
                chat_id=cid, message_id=mid,
                text="✅ *All data has been reset successfully!*",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("⬅️  Back", callback_data="adm_back")
                ),
            )

        else:
            key_map = {
                "adm_welcome":      ("welcome",      "Welcome Message"),
                "adm_help":         ("help",         "Help Message"),
                "adm_result_title": ("result_title", "Result Title"),
                "adm_dev_name":     ("dev_name",     "Developer Name"),
            }
            entry = key_map.get(call.data)
            if not entry:
                return
            target, label = entry

            # Show current value + example
            examples = {
                "welcome":      (
                    "🔥 *MY BOT* 🔥\n\n"
                    "👋 Welcome! Use /flip to toss.\n\n"
                    "👨‍💻 *Dev:* @{dev}"
                ),
                "help":         (
                    "ℹ️ *HELP*\n\n"
                    "• /flip — Toss coin\n\n"
                    "⚡ *Powered by:* @{dev}"
                ),
                "result_title": "🏆 *COIN RESULT* 🏆",
                "dev_name":     "yourname"
            }
            current = bot_config.get(target, "")[:200]
            example = examples.get(target, "")

            prompt = bot.send_message(
                cid,
                f"✍️ *Editing:* `{label}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📋 *Current value:*\n{current}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💡 *Example you can copy:*\n`{example}`\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"_Now send your new text as a reply to this message:_",
                parse_mode="Markdown",
            )
            bot.register_next_step_handler(prompt, _save_setting, target, label)

# ─────────────────────────────────────────
#  ADMIN SAVE
# ─────────────────────────────────────────
def _save_setting(message, key, label):
    if message.from_user.id != ADMIN_ID:
        return
    bot_config[key] = message.text
    save_json(CONFIG_FILE, bot_config)
    preview = message.text[:300] + ("..." if len(message.text) > 300 else "")
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("⚙️  Open Admin Panel", callback_data="adm_reopen"))
    bot.reply_to(
        message,
        f"✅ *{label} updated successfully!*\n\n📋 *New value:*\n{preview}",
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
        "⚙️ *ADMIN PANEL*\n━━━━━━━━━━━━━━━━━━━━━━━━━\nSelect an option below:",
        parse_mode="Markdown",
        reply_markup=admin_keyboard(),
    )

# ─────────────────────────────────────────
#  RUN
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("✅ Secure Coin Toss Bot is running...")
    bot.infinity_polling()
    
