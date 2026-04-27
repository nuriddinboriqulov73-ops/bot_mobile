import telebot
from telebot import types
import sqlite3
import time
import os
from flask import Flask
import threading

# ===== ENV =====
TOKEN = os.getenv("8793822580:AAF40RYW-gBZJp25IE4FTMIBEVLbouk7RJU")
ADMIN_ID = int(os.getenv("6911800755"))

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

# ===== ADD =====
@bot.message_handler(commands=['add'])
def add_number(m):
    if m.chat.id != ADMIN_ID:
        return bot.send_message(m.chat.id, "❌ Siz admin emassiz")

    bot.send_message(m.chat.id, "Format:\noperator raqam\n\nMisol:\nbeeline 901234567")
    bot.register_next_step_handler(m, save_number)

def save_number(m):
    try:
        op, num = m.text.split()

        cursor.execute(
            "INSERT INTO numbers (operator, number) VALUES (?, ?)",
            (op.lower(), num)
        )
        conn.commit()

        bot.send_message(m.chat.id, "✅ Raqam qo‘shildi")
    except:
        bot.send_message(m.chat.id, "❌ Xato format")

# ===== DELETE =====
@bot.message_handler(commands=['del'])
def delete_number(m):
    if m.chat.id != ADMIN_ID:
        return bot.send_message(m.chat.id, "❌ Siz admin emassiz")

    bot.send_message(m.chat.id, "O‘chiriladigan raqamni kiriting:")
    bot.register_next_step_handler(m, remove_number)

def remove_number(m):
    cursor.execute("DELETE FROM numbers WHERE number=?", (m.text,))
    conn.commit()
    bot.send_message(m.chat.id, "🗑 O‘chirildi")

# ===== OPERATOR =====
@bot.message_handler(func=lambda m: m.text in ["🟡 Beeline","🔴 Ucell","🔵 Uzmobile","🟣 Mobiuz"])
def operator(m):
    op = m.text.split()[1].lower()
    user_data[m.chat.id] = {"operator": op}

    bot.send_message(m.chat.id, "🔢 Oxirgi 4 raqam kiriting:")

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

# ===== TANLASH (TO‘LOVSIZ) =====
@bot.callback_query_handler(func=lambda c: c.data.startswith("num_"))
def select_number(c):
    number = c.data.split("_")[1]

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📩 Admin bilan bog‘lanish", url="https://t.me/beeline_Offise_Admin")
    )

    bot.send_message(
        c.message.chat.id,
        f"📞 {number}\n\n✅ Bu raqam bazada mavjud!\n\n📩 Admin bilan bog‘laning.",
        reply_markup=markup
    )

# ===== FLASK =====
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot ishlayapti"

# ===== RUN BOT =====
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
