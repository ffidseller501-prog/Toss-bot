import os
import secrets
import hmac
import hashlib
import json
import telebot
from datetime import datetime, date

# ─────────────────────────────────────────
#  CONFIGURATION & STORAGE
# ─────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID  = int(os.environ.get("ADMIN_ID", 123456789))

bot = telebot.TeleBot(BOT_TOKEN)
STATS_FILE = "stats.json"
STREAK_FILE = "streaks.json"

_rng = secrets.SystemRandom()

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
    "messages": []
})

streaks = load_json(STREAK_FILE, {})

# ─────────────────────────────────────────
#  CRYPTO-SECURE RANDOM ENGINE (COIN UNCHANGED)
# ─────────────────────────────────────────
def generate_secure_random(user_id, max_val):
    secret_key = secrets.token_bytes(32)
    salt = f"{user_id}".encode('utf-8')
    secure_hash = hmac.new(secret_key, salt, hashlib.sha256).hexdigest()
    hash_int = int(secure_hash[-8:], 16)
    return hash_int % max_val

# ─────────────────────────────────────────
#  TRUE RANDOM ENGINE (DICE, SPIN, LUCKY, LIST, RPS)
# ─────────────────────────────────────────
def true_random(max_val):
    return _rng.randint(0, max_val - 1)

# ─────────────────────────────────────────
#  STREAK SYSTEM
# ─────────────────────────────────────────
def update_streak(user_id, command):
    uid = str(user_id)
    today = str(date.today())

    if uid not in streaks:
        streaks[uid] = {}

    user_streaks = streaks[uid]

    if command not in user_streaks:
        user_streaks[command] = {
            "current": 1,
            "best": 1,
            "last_date": today
        }
    else:
        last = user_streaks[command].get("last_date", "")
        current = user_streaks[command].get("current", 0)
        best = user_streaks[command].get("best", 0)

        last_date_obj = datetime.strptime(last, "%Y-%m-%d").date() if last else None
        today_obj = date.today()

        if last_date_obj == today_obj:
            # Already played today, no streak change
            save_json(STREAK_FILE, streaks)
            return user_streaks[command]["current"], user_streaks[command]["best"]

        diff = (today_obj - last_date_obj).days if last_date_obj else 999

        if diff == 1:
            current += 1
        else:
            current = 1

        best = max(best, current)
        user_streaks[command] = {
            "current": current,
            "best": best,
            "last_date": today
        }

    save_json(STREAK_FILE, streaks)
    return user_streaks[command]["current"], user_streaks[command]["best"]

def streak_text(user_id, command):
    current, best = update_streak(user_id, command)
    fire = "🔥" * min(current, 5)
    return f"\n{fire} Streak: *{current} day(s)* | Best: *{best}*"

# ─────────────────────────────────────────
#  USER RECORDING
# ─────────────────────────────────────────
def record_user(user_id, username, first_name):
    uid = str(user_id)
    if uid not in stats["total_users"]:
        stats["total_users"].append(uid)
    stats["activity"][uid] = {
        "username": username or "",
        "name": first_name or ""
    }
    save_json(STATS_FILE, stats)

# ─────────────────────────────────────────
#  COMMANDS
# ─────────────────────────────────────────

@bot.message_handler(commands=["start", "menu"])
def cmd_start(message):
    record_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    welcome_text = (
        "Welcome to *@flipxobot*! 🎮\n"
        "I can help you make instant random decisions.\n\n"
        "🪙 Flip Coin — /coin\n"
        "🎲 Roll Dice — /dice\n"
        "🎡 Spin Wheel — /spin\n"
        "🔢 Lucky Number — /lucky\n"
        "📋 Choose from List — /list Item1, Item2, ...\n"
        "🪨 Rock Paper Scissors — /rps"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

# --- COIN FLIP (COMPLETELY UNCHANGED) ---
@bot.message_handler(commands=["flip", "coin"])
def cmd_flip(message):
    record_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    outcome = "Heads" if generate_secure_random(message.from_user.id, 2) == 0 else "Tails"
    stats["total_tosses"] += 1
    save_json(STATS_FILE, stats)
    bot.reply_to(message, f"🪙 Toss Result: *{outcome}*", parse_mode="Markdown")

# --- DICE ROLL ---
@bot.message_handler(commands=["dice"])
def cmd_dice(message):
    record_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    num = true_random(6) + 1
    s = streak_text(message.from_user.id, "dice")
    bot.reply_to(message, f"🎲 Cube rolled: *{num}*{s}", parse_mode="Markdown")

# --- SPIN WHEEL ---
@bot.message_handler(commands=["spin"])
def cmd_spin(message):
    record_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    zones = ["Zone A", "Zone B", "Zone C", "Zone D", "Jackpot 🌟"]
    chosen_zone = zones[true_random(len(zones))]
    s = streak_text(message.from_user.id, "spin")
    bot.reply_to(message, f"🎡 Wheel landed on: *{chosen_zone}*{s}", parse_mode="Markdown")

# --- LUCKY NUMBER ---
@bot.message_handler(commands=["lucky"])
def cmd_lucky(message):
    record_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    lucky_num = true_random(10)
    s = streak_text(message.from_user.id, "lucky")
    bot.reply_to(message, f"🔢 Your lucky digit: *{lucky_num}*{s}", parse_mode="Markdown")

# --- ITEM PICKER FROM LIST ---
@bot.message_handler(commands=["list"])
def cmd_list(message):
    record_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    raw_text = message.text[5:].strip()

    if not raw_text:
        bot.reply_to(message, "⚠️ Invalid Input Format.\nPlease use: /list Item1, Item2, Item3", parse_mode="Markdown")
        return

    items = [item.strip() for item in raw_text.split(",") if item.strip()]
    if not items:
        bot.reply_to(message, "Please use: /list Item1, Item2, ...")
        return

    chosen = items[true_random(len(items))]
    s = streak_text(message.from_user.id, "list")
    bot.reply_to(message, f"📋 Picked from list: *{chosen}*{s}", parse_mode="Markdown")

# --- ROCK PAPER SCISSORS ---
@bot.message_handler(commands=["rps"])
def cmd_rps(message):
    record_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    choices = ["Rock", "Paper", "Scissors"]
    chosen = choices[true_random(3)]
    s = streak_text(message.from_user.id, "rps")
    bot.reply_to(message, f"⚔️ Weapon chosen: *{chosen}*{s}", parse_mode="Markdown")

# ─────────────────────────────────────────
#  ADMIN MODULE (UNCHANGED)
# ─────────────────────────────────────────
@bot.message_handler(commands=["admin"])
def cmd_admin(message):
    if message.from_user.id != ADMIN_ID:
        return
    kb = telebot.types.InlineKeyboardMarkup()
    kb.add(telebot.types.InlineKeyboardButton("📊 Check Stats", callback_data="adm_stats"))
    bot.reply_to(message, "⚙️ *Dashboard*", parse_mode="Markdown", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    if call.from_user.id != ADMIN_ID:
        return
    bot.answer_callback_query(call.id)
    if call.data == "adm_stats":
        total_users = len(stats["total_users"])
        total_tosses = stats["total_tosses"]
        text = f"📊 *Live Logs:*\n\nTotal Users: `{total_users}`\nCoin Plays: `{total_tosses}`"
        bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown")

if __name__ == "__main__":
    bot.infinity_polling()
