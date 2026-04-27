import telebot
from telebot import types
import sqlite3
import time

# ===== SETTINGS =====
TOKEN = "8793822580:AAF40RYW-gBZJp25IE4FTMIBEVLbouk7RJU"
ADMIN_ID = 6911800755   # o'zingizning ID
ADMIN_USERNAME = "@bek_0166"

bot = telebot.TeleBot(TOKEN)

# ===== DATABASE =====
conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS numbers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operator TEXT,
    number TEXT,
    category TEXT
)
""")

conn.commit()

# ===== STATE =====
user_data = {}
admin_state = {}

# ===== START MENU =====
def start_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🟡 Beeline","🔴 Ucell")
    markup.add("🔵 Uzmobile","🟣 Mobiuz")
    return markup

# ===== START =====
@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, "📱 Operator tanlang:", reply_markup=start_menu())

# ===== ORQAGA =====
@bot.message_handler(func=lambda m: m.text == "⬅️ Orqaga")
def back(m):
    bot.send_message(m.chat.id, "📱 Operator tanlang:", reply_markup=start_menu())

# ===== OPERATOR =====
@bot.message_handler(func=lambda m: m.text in ["🟡 Beeline","🔴 Ucell","🔵 Uzmobile","🟣 Mobiuz"])
def operator(m):
    op = m.text.replace("🟡 ","").replace("🔴 ","").replace("🔵 ","").replace("🟣 ","")
    user_data[m.chat.id] = {"operator": op}

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("✨ GOLD","🥈 SILVER","📱 SIMPLE")
    markup.add("⬅️ Orqaga")

    bot.send_message(m.chat.id, "Kategoriya tanlang:", reply_markup=markup)

# ===== CATEGORY =====
@bot.message_handler(func=lambda m: m.text in ["✨ GOLD","🥈 SILVER","📱 SIMPLE"])
def category(m):
    cat = m.text.split(" ")[1]
    op = user_data[m.chat.id]["operator"]

    cursor.execute("SELECT number FROM numbers WHERE operator=? AND category=?", (op, cat))
    res = cursor.fetchall()

    if not res:
        bot.send_message(m.chat.id, "❌ Raqam yo‘q")
        return

    markup = types.InlineKeyboardMarkup()
    for r in res:
        markup.add(types.InlineKeyboardButton(r[0], callback_data=f"num_{r[0]}"))

    bot.send_message(m.chat.id, "Raqam tanlang:", reply_markup=markup)

# ===== NUMBER =====
@bot.callback_query_handler(func=lambda c: c.data.startswith("num_"))
def number(c):
    num = c.data.split("_")[1]
    user_data[c.from_user.id]["number"] = num

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("50 000 so'm", callback_data="pay_50000"))

    bot.send_message(c.message.chat.id, f"📞 {num}\n💰 Tarif tanlang:", reply_markup=markup)

# ===== PAYMENT =====
@bot.callback_query_handler(func=lambda c: c.data.startswith("pay_"))
def pay(c):
    price = c.data.split("_")[1]
    user_data[c.from_user.id]["price"] = price

    bot.send_message(
        c.message.chat.id,
        f"""
💳 To‘lov:
Karta: 9860196600376491
Summa: {price} so‘m

📸 Screenshot yuboring
"""
    )

# ===== SCREENSHOT =====
@bot.message_handler(content_types=['photo'])
def photo(m):
    data = user_data.get(m.chat.id, {})

    username = m.from_user.username
    if username:
        username = "@" + username
    else:
        username = "username yo‘q"

    text = f"""
🆕 BUYURTMA

👤 User: {username}
🆔 ID: {m.chat.id}

📞 Raqam: {data.get("number")}
💰 Narx: {data.get("price")} so‘m

📩 Admin: {ADMIN_USERNAME}
"""

    bot.send_photo(ADMIN_ID, m.photo[-1].file_id, caption=text)
    bot.send_message(m.chat.id, f"⏳ Tekshirilmoqda...\n📩 Admin: {ADMIN_USERNAME}")

# ===== ADD =====
@bot.message_handler(commands=['add'])
def add(m):
    if m.chat.id != ADMIN_ID:
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Beeline","Ucell","Uzmobile","Mobiuz")

    admin_state[m.chat.id] = {}
    bot.send_message(m.chat.id,"Operator:",reply_markup=markup)

@bot.message_handler(func=lambda m: m.chat.id in admin_state and "operator" not in admin_state[m.chat.id])
def add_op(m):
    admin_state[m.chat.id]["operator"] = m.text

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("GOLD","SILVER","SIMPLE")

    bot.send_message(m.chat.id,"Kategoriya:",reply_markup=markup)

@bot.message_handler(func=lambda m: m.chat.id in admin_state and "category" not in admin_state[m.chat.id])
def add_cat(m):
    admin_state[m.chat.id]["category"] = m.text
    bot.send_message(m.chat.id,"Raqam:")

@bot.message_handler(func=lambda m: m.chat.id in admin_state and "number" not in admin_state[m.chat.id])
def add_num(m):
    data = admin_state[m.chat.id]

    cursor.execute(
        "INSERT INTO numbers (operator,number,category) VALUES (?,?,?)",
        (data["operator"], m.text, data["category"])
    )
    conn.commit()

    bot.send_message(m.chat.id,"✅ Qo‘shildi")
    del admin_state[m.chat.id]

# ===== RUN =====
print("Bot ishlayapti...")

while True:
    try:
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print("Xato:", e)
        time.sleep(5)
