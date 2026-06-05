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
    "head_count": 0,
    "tail_count": 0,
    "activity": {},
    "messages": []
})
# Make sure new keys exist
for k, v in {"head_count": 0, "tail_count": 0, "messages": []}.items():
    if k not in stats:
        stats[k] = v

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
        "📌 *Command:*\n"
        "🔹 /flip — Toss the coin\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👨‍💻 *Developer:* @{dev}"
    ),
    "help": (
        "ℹ️ *HELP & GUIDE*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "⚙️ *How to Play?*\n"
        "• Type /flip command\n"
        "• Wait 5 seconds while coin spins\n"
        "• Get *HEAD* 🟡 or *TAIL* ⚪\n\n"
        "🔐 *Why is it 100% Fair?*\n"
        "• Uses Python `secrets` module\n"
        "• Hardware-level OS entropy source\n"
        "• Cryptographically secure — zero bias\n\n"
        "📌 *Commands:*\n"
        "🔹 /start — Main menu\n"
        "🔹 /flip  — Toss coin\n\n"
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
#  PURE RANDOM TOSS
# ─────────────────────────────────────────
def fair_toss(user_id=None):
    # secrets.token_bytes pulls directly from OS hardware entropy (/dev/urandom)
    # Take 4 random bytes → integer → modulo 2
    # No pattern, no streak tracking, no prediction possible
    rand_int = int.from_bytes(secrets.token_bytes(4), "big")
    return "HEAD" if rand_int % 2 == 0 else "TAIL"

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

def record_toss(outcome):
    stats["total_tosses"] += 1
    if outcome == "HEAD":
        stats["head_count"] += 1
    else:
        stats["tail_count"] += 1
    save_json(STATS_FILE, stats)

def record_message(user_id, username, first_name, text):
    stats["messages"].append({
        "uid": str(user_id),
        "username": username or "",
        "name": first_name or "",
        "text": text,
        "time": datetime.utcnow().isoformat()
    })
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
    kb.add(InlineKeyboardButton("⬅️  Back to Menu", callback_data="home"))
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
    outcome = fair_toss(message.from_user.id)
    record_toss(outcome)
    _edit_result(message.chat.id, msg.message_id, outcome)

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
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅  Yes, Delete All", callback_data="adm_reset_confirm"),
        InlineKeyboardButton("❌  Cancel",          callback_data="adm_cancel_msg"),
    )
    bot.reply_to(
        message,
        "⚠️ *Are you sure?*\n\n"
        "This will permanently delete:\n"
        "• All user records\n"
        "• All toss stats\n"
        "• All message logs\n\n"
        "_This action cannot be undone!_",
        parse_mode="Markdown",
        reply_markup=kb,
    )

# Log all non-command user messages
@bot.message_handler(func=lambda m: not m.text.startswith("/"), content_types=["text"])
def catch_messages(message):
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
def _edit_result(chat_id, message_id, outcome):
    emoji = "🟡" if outcome == "HEAD" else "⚪"
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
#  EDIT EXAMPLES — shown to admin
# ─────────────────────────────────────────
EDIT_EXAMPLES = {
    "welcome": (
        "🔥 *MY TOSS BOT* 🔥\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "👋 *Welcome!*\n\n"
        "🪙 Fair random coin toss!\n\n"
        "📌 /flip — Toss the coin\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👨‍💻 *Developer:* @{dev}"
    ),
    "help": (
        "ℹ️ *HELP*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "• /flip — Toss coin\n"
        "• Wait 5 sec → get result\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ *Powered by:* @{dev}"
    ),
    "result_title": "🏆 *COIN RESULT* 🏆",
    "dev_name":     "yournamehere"
}

# ─────────────────────────────────────────
#  CALLBACKS
# ─────────────────────────────────────────
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    cid = call.message.chat.id
    mid = call.message.message_id
    uid = call.from_user.id

    # ── USER ──────────────────────────────
    if call.data == "home":
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            chat_id=cid, message_id=mid,
            text=cfg("welcome"),
            parse_mode="Markdown",
            reply_markup=start_keyboard(),
        )
        return

    if call.data == "help":
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            chat_id=cid, message_id=mid,
            text=cfg("help"),
            parse_mode="Markdown",
            reply_markup=help_back_keyboard(),
        )
        return

    # ── ADMIN ─────────────────────────────
    if not (call.data.startswith("adm_") or call.data == "adm_cancel_msg"):
        return

    if uid != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Access Denied!", show_alert=True)
        return

    bot.answer_callback_query(call.id)

    # Close panel
    if call.data == "adm_close":
        bot.delete_message(cid, mid)

    # Back to panel
    elif call.data in ("adm_back", "adm_cancel_msg"):
        bot.edit_message_text(
            chat_id=cid, message_id=mid,
            text="⚙️ *ADMIN PANEL*\n━━━━━━━━━━━━━━━━━━━━━━━━━\nSelect an option below:",
            parse_mode="Markdown",
            reply_markup=admin_keyboard(),
        )

    # Stats
    elif call.data == "adm_stats":
        total   = len(stats["total_users"])
        active  = get_active_users(24)
        tosses  = stats["total_tosses"]
        heads   = stats.get("head_count", 0)
        tails   = stats.get("tail_count", 0)
        msgs    = len(stats.get("messages", []))

        h_pct = round((heads / tosses * 100), 1) if tosses > 0 else 0
        t_pct = round((tails / tosses * 100), 1) if tosses > 0 else 0

        recent_lines = []
        items = list(stats["activity"].items())[-5:]
        for _, data in items:
            if isinstance(data, dict):
                uname = data.get("username", "")
                name  = data.get("name", "Unknown")
                recent_lines.append(f"  • {name}" + (f" (@{uname})" if uname else ""))
        recent_str = "\n".join(recent_lines) if recent_lines else "  _None yet_"

        text = (
            "📊 *BOT STATISTICS*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👥  *Total Users:*        `{total}`\n"
            f"🟢  *Active (Last 24h):*  `{active}`\n"
            f"🪙  *Total Tosses:*       `{tosses}`\n"
            f"🟡  *HEAD Results:*       `{heads}` ({h_pct}%)\n"
            f"⚪  *TAIL Results:*       `{tails}` ({t_pct}%)\n"
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

    # Recent messages
    elif call.data == "adm_messages":
        messages = stats.get("messages", [])
        if not messages:
            text = "💬 *Recent Messages*\n━━━━━━━━━━━━━━━━━━━━━━━━━\n\n_No messages yet._"
        else:
            lines = []
            for m in messages[-10:]:
                uname = f"@{m['username']}" if m.get("username") else m.get("name", "Unknown")
                txt   = m["text"][:60] + ("..." if len(m["text"]) > 60 else "")
                lines.append(f"👤 *{uname}:*\n_{txt}_")
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

    # Reset confirm dialog
    elif call.data == "adm_reset_stats":
        bot.edit_message_text(
            chat_id=cid, message_id=mid,
            text=(
                "⚠️ *Are you sure?*\n\n"
                "This will permanently delete:\n"
                "• All user records\n"
                "• All toss stats\n"
                "• All message logs\n\n"
                "_This action cannot be undone!_"
            ),
            parse_mode="Markdown",
            reply_markup=confirm_reset_keyboard(),
        )

    # Do the reset
    elif call.data == "adm_reset_confirm":
        stats["total_users"]  = []
        stats["total_tosses"] = 0
        stats["head_count"]   = 0
        stats["tail_count"]   = 0
        stats["activity"]     = {}
        stats["messages"]     = []
        save_json(STATS_FILE, stats)
        bot.edit_message_text(
            chat_id=cid, message_id=mid,
            text="✅ *All data has been reset successfully!*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("⬅️  Back to Panel", callback_data="adm_back")
            ),
        )

    # Edit fields
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
        current = bot_config.get(target, "")
        example = EDIT_EXAMPLES.get(target, "")

        prompt = bot.send_message(
            cid,
            f"✍️ *Editing:* `{label}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📋 *Current value:*\n{current[:200]}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 *Example to copy:*\n`{example}`\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⬇️ *Send your new text now:*",
            parse_mode="Markdown",
        )
        bot.register_next_step_handler(prompt, _save_setting, target, label)

# ─────────────────────────────────────────
#  ADMIN SAVE SETTING
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
        f"✅ *{label} updated successfully!*\n\n"
        f"📋 *Saved value:*\n{preview}",
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
    
