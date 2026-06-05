import os
import time
import secrets
import hmac
import hashlib
import json
import threading
from datetime import datetime, timedelta
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ─────────────────────────────────────────
#  CONFIGURATION & STORAGE
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

# Ensure key structural integrity
for k, v in {"head_count": 0, "tail_count": 0, "messages": []}.items():
    if k not in stats:
        stats[k] = v

DEFAULT_CONFIG = {
    "welcome": (
        "✨ *WELCOME TO PREMIUM COIN TOSS* ✨\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "👋 Welcome to the most secure flip arena!\n"
        "Our cryptographic hash engine ensures pure randomness.\n\n"
        "⚡ *Commands:*\n"
        "👉 /flip — Toss the coin instantly\n"
        "👉 /menu — Open interactive panel\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👨‍💻 *Developer:* @{dev}"
    ),
    "help": (
        "ℹ️ *HELP & CRYPTO FAIRNESS*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "⚙️ *How to Play:*\n"
        "• Type /flip to activate the wheel\n"
        "• Wait 3 seconds for physical sync\n"
        "• Get an un-rigged cryptographic outcome\n\n"
        "🔐 *Fairness Metric:*\n"
        "Every toss creates a discrete salt using system hardware entropy running on an HMAC-SHA256 frame.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ *Powered by:* @{dev}"
    ),
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
#  CRYPTO-SECURE RANDOM ENGINE
# ─────────────────────────────────────────
def fair_toss(user_id):
    secret_key = secrets.token_bytes(32)
    salt = f"{time.time_ns()}-{user_id}".encode('utf-8')
    secure_hash = hmac.new(secret_key, salt, hashlib.sha256).hexdigest()
    hash_int = int(secure_hash[-8:], 16)
    return "HEAD" if hash_int % 2 == 0 else "TAIL"

# ─────────────────────────────────────────
#  ANALYTICS ENGINE
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
#  PREMIUM COMPONENT KEYBOARDS
# ─────────────────────────────────────────
def start_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("ℹ️  Explore Help & Systems", callback_data="help"))
    return kb

def help_back_keyboard():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("⬅️  Return to Main Menu", callback_data="home"))
    return kb

def admin_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📊 Analytics Stats",      callback_data="adm_stats"),
        InlineKeyboardButton("💬 Msg Monitor",       callback_data="adm_messages"),
    )
    kb.add(
        InlineKeyboardButton("📝 Change Welcome",       callback_data="adm_welcome"),
        InlineKeyboardButton("ℹ️ Change Help",          callback_data="adm_help"),
    )
    kb.add(
        InlineKeyboardButton("👨‍💻 Set Dev Alias",       callback_data="adm_dev_name"),
    )
    kb.add(
        InlineKeyboardButton("🗑️ Factory Reset",       callback_data="adm_reset_stats"),
        InlineKeyboardButton("❌ Exit Console",         callback_data="adm_close")
    )
    return kb

def confirm_reset_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("⚡ Confirm Destruction", callback_data="adm_reset_confirm"),
        InlineKeyboardButton("❌ Retain Core",          callback_data="adm_back")
    )
    return kb

# ─────────────────────────────────────────
#  FRONTEND CORE COMMANDS
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

def process_flip_async(chat_id, message_id, user_id):
    try:
        time.sleep(1.0)
        bot.edit_message_text("⏳ *Spinning... 2s*", chat_id=chat_id, message_id=message_id, parse_mode="Markdown")
        time.sleep(1.0)
        bot.edit_message_text("⏳ *Spinning... 1s*", chat_id=chat_id, message_id=message_id, parse_mode="Markdown")
        time.sleep(1.0)
        
        outcome = fair_toss(user_id)
        record_toss(outcome)
        _edit_result(chat_id, message_id, outcome)
    except Exception as e:
        print(f"Threading Sync Error: {e}")

@bot.message_handler(commands=["flip"])
def cmd_flip(message):
    record_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    msg = bot.reply_to(
        message,
        "⏳ *Spinning... 3s*",
        parse_mode="Markdown",
    )
    threading.Thread(target=process_flip_async, args=(message.chat.id, msg.message_id, message.from_user.id)).start()

@bot.message_handler(commands=["admin"])
def cmd_admin(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "⚠️ *Security Alert:* Access Denied. Unauthorized terminal execution.", parse_mode="Markdown")
        return
    bot.reply_to(
        message,
        "🛠️ *CONTROL OVERRIDE MODULE*\n━━━━━━━━━━━━━━━━━━━━━━━━━\nSystem telemetry initialized. Manage core buffers below:",
        parse_mode="Markdown",
        reply_markup=admin_keyboard(),
    )

@bot.message_handler(commands=["resetall"])
def cmd_resetall(message):
    if message.from_user.id != ADMIN_ID:
        return
    bot.reply_to(
        message,
        "⚠️ *DESTRUCTIVE DIRECTIVE DETECTED*\n\n"
        "Confirm total database purging:\n"
        "• Drops all system identity structures\n"
        "• Wipes absolute historical calculations\n\n"
        "_This instruction is non-reversible!_",
        parse_mode="Markdown",
        reply_markup=confirm_reset_keyboard(),
    )

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
#  SAME TO SAME REQUESTED RESULT UI
# ─────────────────────────────────────────
def _edit_result(chat_id, message_id, outcome):
    emoji = "🟡" if outcome == "HEAD" else "⚪"
        
    text = (
        f"🪙 *Result:* `{outcome}` {emoji}\n"
        f"👨‍💻 *Developer:* @{bot_config['dev_name']}\n\n"
        f"Play again use /flip"
    )
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=text,
        parse_mode="Markdown",
    )

# ─────────────────────────────────────────
#  INTERACTIVE CONTROLLER (CALLBACKS)
# ─────────────────────────────────────────
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    cid = call.message.chat.id
    mid = call.message.message_id
    uid = call.from_user.id

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

    # Protect Admin Functions
    if not (call.data.startswith("adm_") or call.data == "adm_reopen"):
        return

    if uid != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Critical: Identity Mismatch!", show_alert=True)
        return

    bot.answer_callback_query(call.id)

    if call.data == "adm_close":
        bot.delete_message(cid, mid)

    elif call.data in ("adm_back", "adm_reopen"):
        text = "🛠️ *CONTROL OVERRIDE MODULE*\n━━━━━━━━━━━━━━━━━━━━━━━━━\nSystem telemetry initialized. Manage core buffers below:"
        if call.data == "adm_reopen":
            bot.send_message(cid, text, parse_mode="Markdown", reply_markup=admin_keyboard())
        else:
            bot.edit_message_text(chat_id=cid, message_id=mid, text=text, parse_mode="Markdown", reply_markup=admin_keyboard())

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
        recent_str = "\n".join(recent_lines) if recent_lines else "  _Matrix Clean_"

        text = (
            "⚙️ *CORE TELEMETRY LOGS*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📈 *Core Registrations:* `{total}` metrics\n"
            f"🟢 *Active Pings (24h):* `{active}` nodes\n"
            f"🪙 *Absolute Runs:* `{tosses}` generations\n"
            f" ├ 🟡 *Heads:* `{heads}` ({h_pct}%)\n"
            f" └ ⚪ *Tails:* `{tails}` ({t_pct}%)\n"
            f"💬 *Buffer Capture:* `{msgs}` strings\n\n"
            f"📡 *Latest Connection Intercepts:*\n{recent_str}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        back_kb = InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ Return to Console", callback_data="adm_back"))
        bot.edit_message_text(chat_id=cid, message_id=mid, text=text, parse_mode="Markdown", reply_markup=back_kb)

    elif call.data == "adm_messages":
        messages = stats.get("messages", [])
        if not messages:
            text = "💬 *BUFFER MONITORING*\n━━━━━━━━━━━━━━━━━━━━━━━━━\n\n_System queue empty._"
        else:
            lines = []
            for m in messages[-10:]:
                uname = f"@{m['username']}" if m.get("username") else m.get("name", "Unknown")
                txt   = m["text"][:50] + ("..." if len(m["text"]) > 50 else "")
                lines.append(f"📡 *{uname}* ➜ ` {txt} `")
            text = (
                "💬 *STREAM BUFFER CAPTURE (Last 10)*\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n" + "\n".join(lines)
            )
        back_kb = InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ Return to Console", callback_data="adm_back"))
        bot.edit_message_text(chat_id=cid, message_id=mid, text=text, parse_mode="Markdown", reply_markup=back_kb)

    elif call.data == "adm_reset_stats":
        bot.edit_message_text(
            chat_id=cid, message_id=mid,
            text=(
                "⚠️ *DESTRUCTIVE DIRECTIVE DETECTED*\n\n"
                "Confirm total database purging:\n"
                "• Drops all system identity structures\n"
                "• Wipes absolute historical calculations\n\n"
                "_This instruction is non-reversible!_"
            ),
            parse_mode="Markdown",
            reply_markup=confirm_reset_keyboard(),
        )

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
            text="✅ *Database drop executed successfully. System state: Clean.*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("⚙️ Open Console", callback_data="adm_back")),
        )

    else:
        key_map = {
            "adm_welcome":  ("welcome", "Welcome Message Block"),
            "adm_help":     ("help", "Help Matrix Layout"),
            "adm_dev_name": ("dev_name", "Developer Identity Alias"),
        }
        target, label = key_map[call.data]
        current = bot_config.get(target, "")

        prompt = bot.send_message(
            cid,
            f"📝 *OVERWRITE MODULE:* `{label}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📥 *Current Buffer State:*\n`{current[:150]}`\n\n"
            f"💬 Send the completely raw text asset to override this configuration packet:",
            parse_mode="Markdown",
        )
        bot.register_next_step_handler(prompt, _save_setting, target, label)

# ─────────────────────────────────────────
#  ADMIN CONTROL FLOW MUTATOR
# ─────────────────────────────────────────
def _save_setting(message, key, label):
    if message.from_user.id != ADMIN_ID:
        return
    bot_config[key] = message.text
    save_json(CONFIG_FILE, bot_config)
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("⚙️ Re-open Master Console", callback_data="adm_reopen"))
    bot.reply_to(
        message,
        f"✅ *State Saved!* Config sector `{label}` synchronized successfully.",
        parse_mode="Markdown",
        reply_markup=kb,
    )

# ─────────────────────────────────────────
#  POLLING BOOT LOADER
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("🚀 System Online. Bot execution thread started.")
    bot.infinity_polling()
                     
