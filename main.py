import telebot
from telebot import types
import sqlite3
import time

TOKEN = "8793822580:AAF40RYW-gBZJp25IE4FTMIBEVLbouk7RJU"
ADMIN_ID = 6911800755
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

user_data = {}
admin_state = {}

# ===== START =====
@bot.message_handler(commands=['start'])
def start(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🟡 Beeline","🔴 Ucell")
    markup.add("🔵 Uzmobile","🟣 Mobiuz")
    bot.send_message(m.chat.id, "📱 Operator tanlang:", reply_markup=markup)

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
        f"💳 Karta: 9860196600376491\n💰 {price} so‘m\n\n📸 Screenshot yuboring"
    )

# ===== SCREENSHOT =====
@bot.message_handler(content_types=['photo'])
def photo(m):
    data = user_data.get(m.chat.id, {})

    username = m.from_user.username
    username = f"@{username}" if username else "username yo‘q"

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"ok_{m.chat.id}"),
        types.InlineKeyboardButton("❌ Bekor qilish", callback_data=f"no_{m.chat.id}")
    )

    text = f"""
🆕 BUYURTMA

👤 {username}
🆔 {m.chat.id}

📞 {data.get("number")}
💰 {data.get("price")} so‘m
"""

    bot.send_photo(ADMIN_ID, m.photo[-1].file_id, caption=text, reply_markup=markup)
    bot.send_message(m.chat.id, "⏳ Tekshirilmoqda...")

# ===== ADMIN APPROVE =====
@bot.callback_query_handler(func=lambda c: c.data.startswith("ok_") or c.data.startswith("no_"))
def admin(c):
    user_id = int(c.data.split("_")[1])

    if c.data.startswith("ok_"):
        bot.send_message(user_id, "✅ To‘lov tasdiqlandi")
    else:
        bot.send_message(user_id, "❌ To‘lov bekor qilindi")

# ===== BULK ADD =====
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
    bot.send_message(m.chat.id,"Raqamlarni yuboring (har biri yangi qatorda):")

# 🔥 BULK INSERT
@bot.message_handler(func=lambda m: m.chat.id in admin_state)
def bulk_add(m):
    data = admin_state[m.chat.id]

    numbers = m.text.split("\n")
    count = 0

    for num in numbers:
        num = num.strip()
        if num:
            cursor.execute(
                "INSERT INTO numbers (operator,number,category) VALUES (?,?,?)",
                (data["operator"], num, data["category"])
            )
            count += 1

    conn.commit()
    bot.send_message(m.chat.id, f"✅ {count} ta raqam qo‘shildi")
    del admin_state[m.chat.id]

# ===== RUN =====
print("Bot ishlayapti...")

while True:
    try:
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print("Xato:", e)
        time.sleep(5)
