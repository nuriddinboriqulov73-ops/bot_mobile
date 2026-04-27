import telebot
from telebot import types
import sqlite3
import time
import os
from flask import Flask
import threading

# ===== ENV =====
import os

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CARD = os.getenv("CARD", "9860196600376491")

bot = telebot.TeleBot(TOKEN)

# ===== DATABASE =====
conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS numbers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operator TEXT,
    number TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    number TEXT,
    status TEXT
)
""")

conn.commit()

# ===== STATE =====
user_data = {}

# ===== START =====
@bot.message_handler(commands=['start'])
def start(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🟡 Beeline", "🔴 Ucell")
    markup.add("🔵 Uzmobile", "🟣 Mobiuz")
    markup.add("💎 VIP")

    bot.send_message(m.chat.id, "📱 Operator tanlang:", reply_markup=markup)

# ===== OPERATOR =====
@bot.message_handler(func=lambda m: m.text in ["🟡 Beeline","🔴 Ucell","🔵 Uzmobile","🟣 Mobiuz"])
def operator(m):
    op = m.text.split()[1]
    user_data[m.chat.id] = {"operator": op}

    bot.send_message(m.chat.id, "🔢 Oxirgi 4 raqam kiriting:")

# ===== VIP =====
@bot.message_handler(func=lambda m: m.text == "💎 VIP")
def vip(m):
    cursor.execute("SELECT number FROM numbers")
    res = cursor.fetchall()

    if not res:
        bot.send_message(m.chat.id, "❌ Raqam yo‘q")
        return

    markup = types.InlineKeyboardMarkup()
    for r in res:
        markup.add(types.InlineKeyboardButton(r[0], callback_data=f"num_{r[0]}"))

    bot.send_message(m.chat.id, "💎 VIP raqamlar:", reply_markup=markup)

# ===== SEARCH =====
@bot.message_handler(func=lambda m: m.text.isdigit() and len(m.text)==4)
def search(m):
    data = user_data.get(m.chat.id)
    if not data:
        return

    op = data["operator"]

    cursor.execute("SELECT number FROM numbers WHERE operator=? AND number LIKE ?", (op, f"%{m.text}"))
    res = cursor.fetchall()

    if not res:
        bot.send_message(m.chat.id, "❌ Topilmadi")
        return

    markup = types.InlineKeyboardMarkup()
    for r in res:
        markup.add(types.InlineKeyboardButton(r[0], callback_data=f"num_{r[0]}"))

    bot.send_message(m.chat.id, "📞 Tanlang:", reply_markup=markup)

# ===== TANLASH =====
@bot.callback_query_handler(func=lambda c: c.data.startswith("num_"))
def select_number(c):
    number = c.data.split("_")[1]
    user_data[c.from_user.id]["number"] = number

    bot.send_message(
        c.message.chat.id,
        f"📞 {number}\n💳 Karta: {CARD}\n📸 Screenshot yuboring"
    )

# ===== SCREENSHOT =====
@bot.message_handler(content_types=['photo'])
def photo(m):
    data = user_data.get(m.chat.id, {})

    cursor.execute(
        "INSERT INTO orders (user_id, number, status) VALUES (?, ?, ?)",
        (m.chat.id, data.get("number"), "kutilyapti")
    )
    conn.commit()

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅", callback_data=f"ok_{m.chat.id}"),
        types.InlineKeyboardButton("❌", callback_data=f"no_{m.chat.id}")
    )

    bot.send_photo(
        ADMIN_ID,
        m.photo[-1].file_id,
        caption=f"User: {m.chat.id}\nNumber: {data.get('number')}",
        reply_markup=markup
    )

    bot.send_message(m.chat.id, "⏳ Tekshirilmoqda...")

# ===== ADMIN =====
@bot.callback_query_handler(func=lambda c: c.data.startswith("ok_") or c.data.startswith("no_"))
def admin(c):
    user_id = c.data.split("_")[1]

    if c.data.startswith("ok_"):
        bot.send_message(user_id, "✅ Tasdiqlandi")
    else:
        bot.send_message(user_id, "❌ Rad etildi")

# ===== FLASK =====
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot ishlayapti"

# ===== RUN BOT THREAD =====
def run_bot():
    while True:
        try:
            bot.infinity_polling()
        except Exception as e:
            print("Xato:", e)
            time.sleep(5)

threading.Thread(target=run_bot).start()

# ===== RUN SERVER =====
port = int(os.environ.get("PORT", 10000))
app.run(host="0.0.0.0", port=port)
