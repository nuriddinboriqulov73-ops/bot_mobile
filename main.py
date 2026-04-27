import telebot
from telebot import types
import sqlite3
import time

TOKEN = "8793822580:AAF40RYW-gBZJp25IE4FTMIBEVLbouk7RJU"
ADMIN_ID = 6911800755

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

cursor.execute("""
CREATE TABLE IF NOT EXISTS tariffs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operator TEXT,
    name TEXT,
    price TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    number TEXT,
    tarif TEXT,
    price TEXT,
    status TEXT
)
""")

conn.commit()

# ===== TARIFLAR =====
tariffs = [
    ("Beeline","Status 20","30000"),
    ("Beeline","Status 40","40000"),
    ("Ucell","Ucell 25","25000"),
    ("Ucell","Ucell 40","40000"),
    ("Uzmobile","Uz 20","20000"),
    ("Uzmobile","Uz 50","50000"),
    ("Mobiuz","Mobi 20","20000"),
    ("Mobiuz","Mobi 50","50000"),
]

for op, name, price in tariffs:
    cursor.execute("SELECT * FROM tariffs WHERE name=?", (name,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO tariffs (operator,name,price) VALUES (?,?,?)",(op,name,price))

conn.commit()

# ===== STATE =====
user_data = {}
admin_state = {}

# ===== MENUS =====
def start_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🟡 Beeline","🔴 Ucell")
    markup.add("🔵 Uzmobile","🟣 Mobiuz")
    return markup

# ===== START =====
@bot.message_handler(commands=['start'])
def start(m):
    user_data[m.chat.id] = {}
    bot.send_message(m.chat.id, "📱 Operator tanlang:", reply_markup=start_menu())

# ===== ORQAGA =====
@bot.message_handler(func=lambda m: m.text == "⬅️ Orqaga")
def back(m):
    bot.send_message(m.chat.id, "📱 Operator tanlang:", reply_markup=start_menu())

# ===== BEELINE MENU (COUNT) =====
@bot.message_handler(func=lambda m: m.text == "🟡 Beeline")
def beeline(m):
    user_data[m.chat.id] = {"operator": "Beeline"}

    cursor.execute("SELECT COUNT(*) FROM numbers WHERE operator='Beeline' AND category='GOLD'")
    gold = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM numbers WHERE operator='Beeline' AND category='SILVER'")
    silver = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM numbers WHERE operator='Beeline' AND category='SIMPLE'")
    simple = cursor.fetchone()[0]

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(f"✨ GOLD ({gold})", f"🥈 SILVER ({silver})", f"📱 SIMPLE ({simple})")
    markup.add("⬅️ Orqaga")

    bot.send_message(m.chat.id, "Kategoriya tanlang:", reply_markup=markup)

# ===== CATEGORY =====
@bot.message_handler(func=lambda m: "GOLD" in m.text or "SILVER" in m.text or "SIMPLE" in m.text)
def category(m):
    cat = m.text.split(" ")[1]

    op = user_data[m.chat.id]["operator"]

    cursor.execute("SELECT number FROM numbers WHERE operator=? AND category=?", (op, cat))
    res = cursor.fetchall()

    markup = types.InlineKeyboardMarkup()
    for r in res:
        markup.add(types.InlineKeyboardButton(r[0], callback_data=f"num_{r[0]}"))

    bot.send_message(m.chat.id, f"{cat} raqamlar:", reply_markup=markup)

# ===== OTHER OPERATORS =====
@bot.message_handler(func=lambda m: m.text in ["🔴 Ucell","🔵 Uzmobile","🟣 Mobiuz"])
def others(m):
    op = m.text.replace("🔴 ","").replace("🔵 ","").replace("🟣 ","")
    user_data[m.chat.id] = {"operator": op}

    cursor.execute("SELECT number FROM numbers WHERE operator=?", (op,))
    res = cursor.fetchall()

    markup = types.InlineKeyboardMarkup()
    for r in res:
        markup.add(types.InlineKeyboardButton(r[0], callback_data=f"num_{r[0]}"))

    bot.send_message(m.chat.id, f"{op} raqamlar:", reply_markup=markup)

# ===== NUMBER =====
@bot.callback_query_handler(func=lambda c: c.data.startswith("num_"))
def number(c):
    num = c.data.split("_")[1]

    data = user_data.get(c.from_user.id,{})
    data["number"] = num
    user_data[c.from_user.id] = data

    op = data.get("operator")

    cursor.execute("SELECT name,price FROM tariffs WHERE operator=?", (op,))
    tariffs = cursor.fetchall()

    markup = types.InlineKeyboardMarkup()
    for t in tariffs:
        markup.add(types.InlineKeyboardButton(f"{t[0]} - {t[1]} so‘m", callback_data=f"tarif_{t[0]}_{t[1]}"))

    bot.send_message(c.message.chat.id, "📶 Tarif tanlang:", reply_markup=markup)

# ===== TARIF =====
@bot.callback_query_handler(func=lambda c: c.data.startswith("tarif_"))
def tarif(c):
    _, name, price = c.data.split("_")

    data = user_data.get(c.from_user.id,{})
    data["tarif"] = name
    data["price"] = price
    user_data[c.from_user.id] = data

    bot.send_message(
        c.message.chat.id,
        f"📞 {data.get('number')}\n📶 {name}\n💰 {price} so‘m\n\n💳 Karta: 9860196600376491\n📸 Screenshot yuboring"
    )

# ===== SCREENSHOT =====
@bot.message_handler(content_types=['photo'])
def photo(m):
    data = user_data.get(m.chat.id,{})

    cursor.execute(
        "INSERT INTO orders (user_id,number,tarif,price,status) VALUES (?,?,?,?,?)",
        (m.chat.id,data.get("number"),data.get("tarif"),data.get("price"),"kutilyapti")
    )
    conn.commit()

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅",callback_data=f"ok_{m.chat.id}"),
        types.InlineKeyboardButton("❌",callback_data=f"no_{m.chat.id}")
    )

    bot.send_photo(ADMIN_ID, m.photo[-1].file_id, caption=str(data), reply_markup=markup)
    bot.send_message(m.chat.id,"⏳ Tekshirilmoqda...")

# ===== ADMIN =====
@bot.callback_query_handler(func=lambda c: c.data.startswith("ok_") or c.data.startswith("no_"))
def admin(c):
    user_id = c.data.split("_")[1]

    if c.data.startswith("ok_"):
        bot.send_message(user_id,"✅ Tasdiqlandi")
    else:
        bot.send_message(user_id,"❌ Rad etildi")

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

# ===== DELETE =====
@bot.message_handler(commands=['delete'])
def delete(m):
    if m.chat.id != ADMIN_ID:
        return

    cursor.execute("SELECT number FROM numbers")
    res = cursor.fetchall()

    markup = types.InlineKeyboardMarkup()
    for r in res:
        markup.add(types.InlineKeyboardButton(r[0], callback_data=f"del_{r[0]}"))

    bot.send_message(m.chat.id,"O‘chirish:",reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("del_"))
def del_num(c):
    if c.from_user.id != ADMIN_ID:
        return

    num = c.data.split("_")[1]
    cursor.execute("DELETE FROM numbers WHERE number=?", (num,))
    conn.commit()

    bot.send_message(c.message.chat.id,f"❌ O‘chirildi: {num}")

# ===== RUN =====
print("Bot ishlayapti...")

while True:
    try:
        bot.infinity_polling()
    except Exception as e:
        print("Xato:", e)
        time.sleep(5)
