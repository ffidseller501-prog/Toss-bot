import os
import secrets
import hmac
import hashlib
import json
import telebot

# ─────────────────────────────────────────
#  CONFIGURATION & STORAGE
# ─────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID  = int(os.environ.get("ADMIN_ID", 123456789))

bot = telebot.TeleBot(BOT_TOKEN)

STATS_FILE = "stats.json"

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

# ─────────────────────────────────────────
#  CRYPTO-SECURE RANDOM ENGINE
# ─────────────────────────────────────────
def generate_secure_random(user_id, max_val):
    secret_key = secrets.token_bytes(32)
    salt = f"{user_id}".encode('utf-8')
    secure_hash = hmac.new(secret_key, salt, hashlib.sha256).hexdigest()
    hash_int = int(secure_hash[-8:], 16)
    return hash_int % max_val

# ─────────────────────────────────────────
#  ANALYTICS HELPER
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

def record_message(user_id, username, first_name, text):
    if user_id == ADMIN_ID:
        return
    stats["messages"].append({
        "uid": str(user_id),
        "username": username or "",
        "name": first_name or "",
        "text": text
    })
    if len(stats["messages"]) > 200:
        stats["messages"] = stats["messages"][-200:]
    save_json(STATS_FILE, stats)

# ─────────────────────────────────────────
#  FRONTEND CORE COMMANDS (IMAGE 31307.jpg STYLE)
# ─────────────────────────────────────────

@bot.message_handler(commands=["start", "menu"])
def cmd_start(message):
    record_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    welcome_text = (
        "I can help you make decisions with the following commands:\n\n"
        "Flip a coin – /coin\n"
        "Roll a dice – /dice [Sides of the dice]\n"
        "Item from list – /list Item1, Item2, ...\n"
        "Rock, paper, scissors – /rps\n\n"
        "You can also use me inline. Just type @randomTossBot in any conversation!"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

# --- COIN FLIP ---
@bot.message_handler(commands=["flip", "coin"])
def cmd_flip(message):
    record_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    outcome = "Heads" if generate_secure_random(message.from_user.id, 2) == 0 else "Tails"
    stats["total_tosses"] += 1
    save_json(STATS_FILE, stats)
    bot.reply_to(message, f"Coin flipped: *{outcome}*", parse_mode="Markdown")

# --- DICE ROLL ---
@bot.message_handler(commands=["dice"])
def cmd_dice(message):
    record_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    # Default sides is 6 if not provided
    args = message.text.split()
    sides = 6
    if len(args) > 1 and args[1].isdigit():
        sides = int(args[1])
        if sides < 1: sides = 6

    num = generate_secure_random(message.from_user.id, sides) + 1
    bot.reply_to(message, f"Dice rolled: *{num}*", parse_mode="Markdown")

# --- RANDOM ITEM PICKER FROM LIST ---
@bot.message_handler(commands=["list"])
def cmd_list(message):
    record_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    raw_text = message.text[5:].strip()
    
    if not raw_text:
        error_msg = (
            "The parameter you supplied is invalid.\n\n"
            "Example usage: /list Item1, Item2, ..."
        )
        bot.reply_to(message, error_msg, parse_mode="Markdown")
        return

    # Split by comma
    items = [item.strip() for item in raw_text.split(",") if item.strip()]
    if not items:
        bot.reply_to(message, "Example usage: /list Item1, Item2, ...")
        return

    chosen_index = generate_secure_random(message.from_user.id, len(items))
    chosen_item = items[chosen_index]
    bot.reply_to(message, f"Result: *{chosen_item}*", parse_mode="Markdown")

# --- ROCK PAPER SCISSORS ---
@bot.message_handler(commands=["rps"])
def cmd_rps(message):
    record_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    choices = ["Rock", "Paper", "Scissors"]
    chosen = choices[generate_secure_random(message.from_user.id, 3)]
    bot.reply_to(message, f"*{chosen}*", parse_mode="Markdown")

# ─────────────────────────────────────────
#  ADMIN CONTROL FUNCTIONS
# ─────────────────────────────────────────
@bot.message_handler(commands=["admin"])
def cmd_admin(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    # Inline keyboard logic for admin panel
    kb = telebot.types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        telebot.types.InlineKeyboardButton("📊 Simple Stats", callback_data="adm_stats"),
        telebot.types.InlineKeyboardButton("🗑️ Clear Logs", callback_data="adm_clear")
    )
    bot.reply_to(message, "⚙️ *Admin Control Terminal*", parse_mode="Markdown", reply_markup=kb)

@bot.message_handler(func=lambda m: not m.text.startswith("/"), content_types=["text"])
def catch_messages(message):
    record_message(message.from_user.id, message.from_user.username, message.from_user.first_name, message.text)

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    if call.from_user.id != ADMIN_ID:
        return
    bot.answer_callback_query(call.id)
    
    if call.data == "adm_stats":
        total_users = len(stats["total_users"])
        total_tosses = stats["total_tosses"]
        text = f"📊 *Live Counters:*\n\nUsers: `{total_users}`\nTotal Executions: `{total_tosses}`"
        bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown")
        
    elif call.data == "adm_clear":
        stats.update({"total_users": [], "total_tosses": 0, "activity": {}, "messages": []})
        save_json(STATS_FILE, stats)
        bot.edit_message_text("✅ *Data wiped successfully!*", chat_id=call.message.chat.id, message_id=call.message.message_id)

if __name__ == "__main__":
    bot.infinity_polling()
    
