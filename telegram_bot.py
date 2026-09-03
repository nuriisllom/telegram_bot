import socket
import time
import sqlite3
import telebot
from telebot import types
from datetime import datetime, timedelta
import random

# ================== MUHIM: IPv4 MUAMMOSINI YECHISH ==================
old_getaddrinfo = socket.getaddrinfo

def new_getaddrinfo(*args):
    responses = old_getaddrinfo(*args)
    return [response for response in responses if response[0] == socket.AF_INET]

socket.getaddrinfo = new_getaddrinfo
# ====================================================================

# ================== SOZLAMALAR ==================
TOKEN = "8868037557:AAFRiE_IyfKpCkhMNjulbWbmoxKLCnY7pSE"          
ADMIN_ID = 8861178123
CARD_NUMBER = "5614681275957417"
CARD_OWNER = "Umarov Ayubxon"

CHANNEL_USERNAME = "@orzufood1"
CHANNEL_LINK = "https://t.me/orzufood1"

CONTACT_PHONE = "+998995130444" # Bog'lanish uchun raqam shu yerda saqlanadi

# BONUS TIZIMI
BONUS_PER_10000 = 1
BONUS_VALUE = 500

# ================== BOTNI YARATISH ==================
bot = telebot.TeleBot(TOKEN, threaded=True)
# ===================================================

# ================== MA'LUMOTLAR BAZASI ==================
def init_db():
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, username TEXT, 
                  first_name TEXT, last_name TEXT, 
                  registration_date TEXT, orders_count INTEGER DEFAULT 0,
                  total_spent INTEGER DEFAULT 0, bonus_points INTEGER DEFAULT 0, 
                  referal_code TEXT, referred_by INTEGER)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS orders
                 (order_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
                  items TEXT, total INTEGER, address TEXT, phone TEXT, 
                  payment_method TEXT, status TEXT DEFAULT 'new', order_date TEXT,
                  FOREIGN KEY(user_id) REFERENCES users(user_id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS reviews
                 (review_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
                  rating INTEGER, comment TEXT, review_date TEXT,
                  FOREIGN KEY(user_id) REFERENCES users(user_id))''')
    
    conn.commit()
    conn.close()

init_db()

# ================== MENYULAR ==================
FAST_CARS = {
    " Tico": 8000,
    "🚗 Matiz": 10000,
    "🚗 Epica": 15000,
    " Kia": 20000,
    "🚗 Damas": 20000,
    "🚗 Spark": 20000,
    "🚗 Labo": 23000,
    "🚗 Nexia1": 28000,
    "🚗 Nexia3": 30000,
    " Euro": 40000,
    "🚗 Lacetti/Gentra": 30000,
    "🚗 Kia K5": 35000,
    "🚗 Cobalt": 33000,
    "🚗 Malibu": 45000,
    " Captiva": 50000,
    "🚗 Gelik": 100000,
    "🚗 Kamaz": 90000,
}

FAST_FOOD = {
    "🍔 Burger": 25000,
    " Dabl burger": 40000,
    "🧀 Dabl cheese": 50000,
    " Lavash (kichik)": 25000,
    "🌯 Lavash (katta)": 40000,
}

COLD_DRINKS = {
    " Pepsi 0.5L": 8000,
    "🧊 Fanta 0.5L": 8000,
    "🧊 Cola 0.5L": 8000,
    "🧊 Lipton 0.5L": 8000,
    "🧊 Pepsi 1L": 12000,
    "🧊 Fanta 1L": 12000,
    "🧊 Cola 1L": 12000,
    "🧊 Pepsi 2L": 20000,
    "🧊 Fanta 2L": 20000,
    "🧊 Cola 2L": 20000,
}

HOT_DRINKS = {
    "☕ Qora kofe": 7000,
    "☕ Sutli kofe": 7000,
    "☕ Qora choy": 4000,
    "☕ Oq choy": 4000,
    "☕ Qora choy limon novotliy": 8000,
    "☕ Malina choy": 8000,
}

user_orders = {}
user_languages = {}
admin_state = {}

# ================== YORDAMCHI FUNKSIYALAR ==================
def generate_referal_code(user_id):
    import string
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{code}{user_id % 1000}"

def save_user(user_id, username, first_name, last_name, referred_by=None):
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
    if not c.fetchone():
        referal_code = generate_referal_code(user_id)
        c.execute('''INSERT INTO users 
                     (user_id, username, first_name, last_name, registration_date, referal_code, referred_by)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (user_id, username, first_name, last_name, 
                   datetime.now().strftime('%Y-%m-%d %H:%M:%S'), referal_code, referred_by))
        
        if referred_by:
            c.execute('UPDATE users SET bonus_points = bonus_points + 3 WHERE user_id = ?', (referred_by,))
            try:
                bot.send_message(referred_by, f"🎁 Tabriklaymiz! Do'stingiz botga kirdi va sizga 3 ball qo'shildi!")
            except:
                pass
    else:
        c.execute('''UPDATE users SET username = ?, first_name = ?, last_name = ? 
                     WHERE user_id = ?''', (username, first_name, last_name, user_id))
    conn.commit()
    conn.close()

def update_user_stats(user_id, amount):
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    points_earned = amount // 10000 * BONUS_PER_10000
    c.execute('''UPDATE users SET orders_count = orders_count + 1, 
                 total_spent = total_spent + ?, bonus_points = bonus_points + ?
                 WHERE user_id = ?''', (amount, points_earned, user_id))
    conn.commit()
    conn.close()

def get_user_bonus(user_id):
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('SELECT bonus_points FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def get_user_info(user_id):
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('SELECT orders_count, total_spent, bonus_points FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result if result else (0, 0, 0)

def use_bonus(user_id, points):
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('UPDATE users SET bonus_points = bonus_points - ? WHERE user_id = ?', (points, user_id))
    conn.commit()
    conn.close()

# ================== OBUNA TEKSHIRUV ==================
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ("member", "administrator", "creator")
    except:
        return False

def send_subscribe_message(chat_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📢 Kanalga o'tish", url=CHANNEL_LINK))
    markup.add(types.InlineKeyboardButton("✅ A'zo bo'ldim", callback_data="check_sub"))
    bot.send_message(
        chat_id,
        "Botdan foydalanish uchun avval kanalimizga a'zo bo'ling 👇\n\n"
        "A'zo bo'lgach, pastdagi \"✅ A'zo bo'ldim\" tugmasini bosing.",
        reply_markup=markup
    )

# ================== ASOSIY MENU ==================
def send_main_menu(chat_id, user_id):
    user_orders[user_id] = {"cart": [], "step": None}
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🚗 Fast mashinalar", callback_data="cat_cars"),
        types.InlineKeyboardButton("🍔 Fast Food", callback_data="cat_fastfood"),
    )
    markup.add(
        types.InlineKeyboardButton("🧊 Sovuq ichimliklar", callback_data="cat_cold"),
        types.InlineKeyboardButton(" Issiq ichimliklar", callback_data="cat_hot"),
    )
    markup.add(
        types.InlineKeyboardButton("🛒 Savatni ko'rish", callback_data="view_cart"),
        types.InlineKeyboardButton("❌ Savatni tozalash", callback_data="clear_cart"),
    )
    
    bot.send_message(
        chat_id, 
        "📋 *Kategoriyani tanlang:*\n\n"
        "🚗 Fast mashinalar\n"
        "🍔 Fast Food (Burger, Lavash)\n"
        "🧊 Sovuq ichimliklar (Pepsi, Fanta, Cola)\n"
        "☕ Issiq ichimliklar (Kofe, Choy)\n\n"
        "🚚 _Alisher Navoiy ko'chasi bo'ylab yetkazib berish BEPUL! Qolgan joylar Yandex xizmati orqali._",
        reply_markup=markup,
        parse_mode="Markdown"
    )

def send_category_items(chat_id, user_id, category):
    user_orders[user_id]["category"] = category
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    if category == "cars":
        items = FAST_CARS
        title = " Fast mashinalar:"
    elif category == "fastfood":
        items = FAST_FOOD
        title = "🍔 Fast Food:"
    elif category == "cold":
        items = COLD_DRINKS
        title = "🧊 Sovuq ichimliklar:"
    elif category == "hot":
        items = HOT_DRINKS
        title = "☕ Issiq ichimliklar:"
    else:
        items = {}
        title = ""
    
    for name, price in items.items():
        markup.add(types.InlineKeyboardButton(f"{name} — {price} so'm", callback_data=f"item|{name}"))
    
    markup.add(types.InlineKeyboardButton("️ Orqaga", callback_data="back_to_menu"))
    
    bot.send_message(chat_id, title, reply_markup=markup)

# ================== SAVAT FUNKSIYALARI ==================
def send_cart_menu(chat_id, user_id):
    order = user_orders.get(user_id)
    
    if not order or not order.get("cart"):
        bot.send_message(chat_id, " Savatingiz bo'sh!\n\nMenyudan mahsulot tanlang.")
        return
    
    cart_text, total = cart_summary_text(order["cart"])
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for i, item in enumerate(order["cart"]):
        markup.add(types.InlineKeyboardButton(
            f"❌ {item['name']} x{item['qty']} — {item['price'] * item['qty']} so'm",
            callback_data=f"remove_item|{i}"
        ))
    
    markup.add(types.InlineKeyboardButton("🗑 Hammasini o'chirish", callback_data="clear_cart"))
    markup.add(types.InlineKeyboardButton("✅ Buyurtma berish", callback_data="checkout"))
    markup.add(types.InlineKeyboardButton("➕ Mahsulot qo'shish", callback_data="back_to_menu"))
    
    bot.send_message(
        chat_id,
        f"🛒 *Sizning savatingiz:*\n\n{cart_text}\n\n💰 *Jami: {total} so'm*",
        reply_markup=markup,
        parse_mode="Markdown"
    )

def remove_item_from_cart(user_id, item_index):
    order = user_orders.get(user_id)
    if not order or not order.get("cart"):
        return False, None
    
    if 0 <= item_index < len(order["cart"]):
        removed_item = order["cart"].pop(item_index)
        return True, removed_item
    return False, None

# ================== MIJOZ FUNKSIYALARI MENYUSI ==================
def send_customer_menu(chat_id, user_id):
    orders_count, total_spent, bonus_points = get_user_info(user_id)
    discount_value = bonus_points * BONUS_VALUE
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📋 Mening buyurtmalarim", callback_data="my_orders"),
        types.InlineKeyboardButton("⭐ Baholash", callback_data="rate_service"),
    )
    markup.add(
        types.InlineKeyboardButton("🎁 Bonuslarim", callback_data="my_bonus"),
        types.InlineKeyboardButton("📊 Mening statistika", callback_data="my_stats"),
    )
    markup.add(
        types.InlineKeyboardButton("📞 Aloqa", callback_data="contact_us"),
    )
    markup.add(
        types.InlineKeyboardButton(" Asosiy menyu", callback_data="back_to_menu"),
    )
    
    bot.send_message(
        chat_id,
        f" *Mijoz kabinetim*\n\n"
        f"📊 Sizning statistika:\n"
        f"• Buyurtmalar: {orders_count} ta\n"
        f"• Jami xarajat: {total_spent} so'm\n"
        f"• Bonuslar: {bonus_points} ball ({discount_value} so'm)\n\n"
        f"💡 Har 10,000 so'mdan 1 ball qozonasiz\n"
        f"💰 1 ball = {BONUS_VALUE} so'm chegirma\n\n"
        f"Quyidagi funksiyalardan foydalanishingiz mumkin:",
        reply_markup=markup,
        parse_mode="Markdown"
    )

# ================== ADMIN FUNKSIYALARI MENYUSI ==================
def send_admin_menu(chat_id):
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM users')
    total_users = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM orders')
    total_orders = c.fetchone()[0]
    c.execute('SELECT SUM(total) FROM orders')
    total_revenue = c.fetchone()[0] or 0
    conn.close()
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Statistika", callback_data="admin_stats"),
        types.InlineKeyboardButton(" Buyurtmalar", callback_data="admin_orders"),
    )
    markup.add(
        types.InlineKeyboardButton("📢 Hammaga xabar", callback_data="admin_broadcast"),
        types.InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="admin_users"),
    )
    markup.add(
        types.InlineKeyboardButton("🔙 Asosiy menyu", callback_data="back_to_menu"),
    )
    
    bot.send_message(
        chat_id,
        f"👨‍💼 *Admin panel*\n\n"
        f"📊 Umumiy statistika:\n"
        f"• Foydalanuvchilar: {total_users}\n"
        f"• Buyurtmalar: {total_orders}\n"
        f"• Daromad: {total_revenue} so'm\n\n"
        f"Admin funksiyalari:",
        reply_markup=markup,
        parse_mode="Markdown"
    )

# ================== CALLBACK HANDLERS ==================
@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub_callback(call):
    user_id = call.from_user.id
    if is_subscribed(user_id):
        bot.answer_callback_query(call.id, "Rahmat! Obuna tasdiqlandi ✅")
        bot.send_message(call.message.chat.id, "Xush kelibsiz! Buyurtma berish uchun /menu buyrug'ini yuboring.")
    else:
        bot.answer_callback_query(call.id, "Siz hali kanalga a'zo bo'lmadingiz ❌", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def category_selected(call):
    user_id = call.from_user.id
    category = call.data.split("_")[1]
    
    if user_id not in user_orders:
        user_orders[user_id] = {"cart": []}
    
    send_category_items(call.message.chat.id, user_id, category)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_menu")
def back_to_menu(call):
    user_id = call.from_user.id
    send_main_menu(call.message.chat.id, user_id)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "view_cart")
def view_cart_callback(call):
    user_id = call.from_user.id
    send_cart_menu(call.message.chat.id, user_id)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("remove_item|"))
def remove_item_callback(call):
    user_id = call.from_user.id
    item_index = int(call.data.split("|")[1])
    
    success, removed_item = remove_item_from_cart(user_id, item_index)
    
    if success:
        bot.answer_callback_query(call.id, f"✅ {removed_item['name']} o'chirildi")
        send_cart_menu(call.message.chat.id, user_id)
    else:
        bot.answer_callback_query(call.id, "❌ Xatolik!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "clear_cart")
def clear_cart(call):
    user_id = call.from_user.id
    if user_id in user_orders:
        user_orders[user_id] = {"cart": [], "step": None}
    bot.answer_callback_query(call.id, "🗑 Savat tozalandi")
    bot.send_message(call.message.chat.id, "🗑 Savat tozalandi! /menu orqali qaytadan boshlashingiz mumkin.")

@bot.callback_query_handler(func=lambda call: call.data == "checkout")
def checkout_callback(call):
    user_id = call.from_user.id
    order = user_orders.get(user_id)
    
    if not order or not order.get("cart"):
        bot.answer_callback_query(call.id, "Savat bo'sh!", show_alert=True)
        return
    
    ask_address(call.message.chat.id, user_id)
    bot.answer_callback_query(call.id)

# MIJOZ FUNKSIYALARI
@bot.callback_query_handler(func=lambda call: call.data == "my_orders")
def my_orders(call):
    user_id = call.from_user.id
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('''SELECT order_id, status, total, order_date FROM orders 
                 WHERE user_id = ? ORDER BY order_id DESC LIMIT 5''', (user_id,))
    orders = c.fetchall()
    conn.close()
    
    if not orders:
        bot.send_message(call.message.chat.id, "📋 Sizda hali buyurtmalar yo'q.")
    else:
        text = "📋 *Mening buyurtmalarim:*\n\n"
        for order_id, status, total, date in orders:
            status_names = {
                "new": "⏳ Kutilmoqda",
                "accepted": "✅ Buyurtmangiz qabul qilindi",
                "cancelled": "❌ Buyurtma bekor qilindi",
                "preparing": "✅ Buyurtmangiz qabul qilindi",
                "delivering": "✅ Buyurtmangiz qabul qilindi",
                "delivered": "✅ Buyurtmangiz qabul qilindi",
            }
            text += f"📦 Buyurtma #{order_id} — {status_names.get(status, status)}\n💰 {total} so'm | 📅 {date}\n\n"
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "rate_service")
def rate_service(call):
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("⭐ 1", callback_data="rate_1"),
        types.InlineKeyboardButton("⭐⭐ 2", callback_data="rate_2"),
        types.InlineKeyboardButton("⭐⭐⭐ 3", callback_data="rate_3"),
    )
    markup.row(
        types.InlineKeyboardButton("⭐⭐⭐⭐ 4", callback_data="rate_4"),
        types.InlineKeyboardButton("⭐⭐⭐⭐⭐ 5", callback_data="rate_5"),
    )
    bot.send_message(call.message.chat.id, "Xizmatimizni baholang:", reply_markup=markup)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("rate_"))
def rate_callback(call):
    rating = int(call.data.split("_")[1])
    user_id = call.from_user.id
    
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('''INSERT INTO reviews (user_id, rating, review_date)
                 VALUES (?, ?, ?)''', (user_id, rating, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()
    
    bot.answer_callback_query(call.id, f"Rahmat! Siz {rating} yulduz qo'ydingiz ⭐")
    bot.send_message(call.message.chat.id, "Izoh qoldirish uchun /review buyrug'ini yuboring.")

@bot.callback_query_handler(func=lambda call: call.data == "my_bonus")
def my_bonus(call):
    user_id = call.from_user.id
    bonus_points = get_user_bonus(user_id)
    discount = bonus_points * BONUS_VALUE
    
    orders_count, total_spent, _ = get_user_info(user_id)
    
    bot.send_message(
        call.message.chat.id,
        f"🎁 *Sizning bonuslaringiz:*\n\n"
        f"⭐ Ballar: {bonus_points}\n"
        f"💰 Chegirma: {discount} so'm\n\n"
        f"📊 Statistika:\n"
        f"🛒 Buyurtmalar: {orders_count}\n"
        f"💵 Jami xarajat: {total_spent} so'm\n\n"
        f"💡 Har 10,000 so'mdan 1 ball qozonasiz!\n"
        f"💰 1 ball = {BONUS_VALUE} so'm chegirma",
        parse_mode="Markdown"
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "my_stats")
def my_stats(call):
    user_id = call.from_user.id
    orders_count, total_spent, bonus_points = get_user_info(user_id)
    discount_value = bonus_points * BONUS_VALUE
    
    bot.send_message(
        call.message.chat.id,
        f"📊 *Mening statistika:*\n\n"
        f"🛒 Buyurtmalar: {orders_count} ta\n"
        f"💵 Jami xarajat: {total_spent} so'm\n"
        f"🎁 Bonuslar: {bonus_points} ball ({discount_value} so'm)\n\n"
        f"📅 Ro'yxatdan o'tgan: {datetime.now().strftime('%Y-%m-%d')}",
        parse_mode="Markdown"
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "contact_us")
def contact_us(call):
    bot.send_message(
        call.message.chat.id,
        f"📞 *Biz bilan bog'lanish:*\n\n"
        f"📱 Telefon: {CONTACT_PHONE}\n"
        f"📢 Kanal: {CHANNEL_LINK}\n\n"
        f"⏰ Ish vaqti: 24/7\n"
        f"🚚 Alisher Navoiy ko'chasi bo'ylab yetkazib berish BEPUL!\n"
        f"📍 Qolgan manzillar: Yandex taksi xizmati orqali",
        parse_mode="Markdown"
    )
    bot.answer_callback_query(call.id)

# ADMIN FUNKSIYALARI
@bot.callback_query_handler(func=lambda call: call.data == "admin_stats")
def admin_stats(call):
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM users')
    total_users = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM orders')
    total_orders = c.fetchone()[0]
    c.execute('SELECT SUM(total) FROM orders')
    total_revenue = c.fetchone()[0] or 0
    c.execute('SELECT COUNT(*) FROM orders WHERE order_date LIKE ?', 
              (datetime.now().strftime('%Y-%m-%d') + '%',))
    today_orders = c.fetchone()[0]
    c.execute('SELECT SUM(total) FROM orders WHERE order_date LIKE ?', 
              (datetime.now().strftime('%Y-%m-%d') + '%',))
    today_revenue = c.fetchone()[0] or 0
    conn.close()
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📅 Haftalik/Oylik", callback_data="stats_period"),
        types.InlineKeyboardButton("🏆 Top mahsulotlar", callback_data="stats_top_products"),
    )
    markup.add(
        types.InlineKeyboardButton("👑 Top mijozlar", callback_data="stats_top_customers"),
        types.InlineKeyboardButton("⭐ Reytinglar", callback_data="stats_ratings"),
    )
    markup.add(types.InlineKeyboardButton("🔙 Admin panel", callback_data="admin_panel"))

    bot.send_message(
        call.message.chat.id,
        f"📊 *Umumiy statistika:*\n\n"
        f"👥 Jami foydalanuvchilar: {total_users}\n"
        f"📦 Jami buyurtmalar: {total_orders}\n"
        f"💰 Jami daromad: {total_revenue} so'm\n\n"
        f"📅 Bugungi buyurtmalar: {today_orders}\n"
        f"💵 Bugungi daromad: {today_revenue} so'm\n\n"
        f"Batafsil hisobot uchun tugmalardan foydalaning:",
        reply_markup=markup,
        parse_mode="Markdown"
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "stats_period")
def stats_period(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Siz admin emassiz!", show_alert=True)
        return

    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()

    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    c.execute('SELECT COUNT(*), COALESCE(SUM(total),0) FROM orders WHERE order_date >= ?', (week_ago,))
    week_orders, week_revenue = c.fetchone()

    month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    c.execute('SELECT COUNT(*), COALESCE(SUM(total),0) FROM orders WHERE order_date >= ?', (month_ago,))
    month_orders, month_revenue = c.fetchone()

    conn.close()

    avg_week = week_revenue // week_orders if week_orders else 0
    avg_month = month_revenue // month_orders if month_orders else 0

    bot.send_message(
        call.message.chat.id,
        f"📅 *Davr bo'yicha statistika:*\n\n"
        f"🗓 So'nggi 7 kun:\n"
        f"• Buyurtmalar: {week_orders} ta\n"
        f"• Daromad: {week_revenue} so'm\n"
        f"• O'rtacha chek: {avg_week} so'm\n\n"
        f"🗓 So'nggi 30 kun:\n"
        f"• Buyurtmalar: {month_orders} ta\n"
        f"• Daromad: {month_revenue} so'm\n"
        f"• O'rtacha chek: {avg_month} so'm",
        parse_mode="Markdown"
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "stats_top_products")
def stats_top_products(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Siz admin emassiz!", show_alert=True)
        return

    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('SELECT items FROM orders')
    rows = c.fetchall()
    conn.close()

    product_counts = {}
    for (items_text,) in rows:
        if not items_text:
            continue
        for line in items_text.split("\n"):
            line = line.strip()
            if not line.startswith("🔹"):
                continue
            try:
                name_part, rest = line[1:].strip().rsplit(" x", 1)
                qty_str = rest.split(" — ")[0]
                qty = int(qty_str)
                name = name_part.strip()
                product_counts[name] = product_counts.get(name, 0) + qty
            except Exception:
                continue

    if not product_counts:
        bot.send_message(call.message.chat.id, "🏆 Hali yetarli ma'lumot yo'q.")
        bot.answer_callback_query(call.id)
        return

    top = sorted(product_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    text = "🏆 *Eng ko'p buyurtma qilingan mahsulotlar:*\n\n"
    for i, (name, qty) in enumerate(top, 1):
        text += f"{i}. {name} — {qty} ta\n"

    bot.send_message(call.message.chat.id, text, parse_mode="Markdown")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "stats_top_customers")
def stats_top_customers(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Siz admin emassiz!", show_alert=True)
        return

    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('''SELECT first_name, username, user_id, orders_count, total_spent
                 FROM users ORDER BY total_spent DESC LIMIT 10''')
    top = c.fetchall()
    conn.close()

    if not top:
        bot.send_message(call.message.chat.id, "👑 Hali mijozlar yo'q.")
        bot.answer_callback_query(call.id)
        return

    text = " *Top 10 mijoz (xarajat bo'yicha):*\n\n"
    for i, (first_name, username, uid, orders_count, total_spent) in enumerate(top, 1):
        uname = f"@{username}" if username else f"ID:{uid}"
        text += f"{i}. {first_name} ({uname}) — {total_spent} so'm ({orders_count} ta buyurtma)\n"

    bot.send_message(call.message.chat.id, text, parse_mode="Markdown")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "stats_ratings")
def stats_ratings(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Siz admin emassiz!", show_alert=True)
        return

    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*), COALESCE(AVG(rating),0) FROM reviews WHERE rating IS NOT NULL')
    count, avg_rating = c.fetchone()
    c.execute('''SELECT rating, COUNT(*) FROM reviews WHERE rating IS NOT NULL
                 GROUP BY rating ORDER BY rating DESC''')
    breakdown = c.fetchall()
    c.execute('''SELECT comment FROM reviews WHERE comment IS NOT NULL AND comment != ""
                 ORDER BY review_id DESC LIMIT 5''')
    comments = [row[0] for row in c.fetchall()]
    conn.close()

    if count == 0:
        bot.send_message(call.message.chat.id, "⭐ Hali baholashlar yo'q.")
        bot.answer_callback_query(call.id)
        return

    text = f"⭐ *Xizmat reytingi:*\n\n"
    text += f" O'rtacha baho: {avg_rating:.1f} / 5 ({count} ta baho)\n\n"
    for rating, cnt in breakdown:
        text += f"{'⭐' * rating}: {cnt} ta\n"

    if comments:
        text += "\n💬 *So'nggi izohlar:*\n"
        for c_text in comments:
            text += f"• {c_text}\n"

    bot.send_message(call.message.chat.id, text, parse_mode="Markdown")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "admin_orders")
def admin_orders(call):
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('''SELECT order_id, user_id, total, status, order_date FROM orders 
                 ORDER BY order_id DESC LIMIT 10''')
    orders = c.fetchall()
    conn.close()
    
    if not orders:
        bot.send_message(call.message.chat.id, "📋 Hali buyurtmalar yo'q.")
    else:
        text = "📋 So'nggi 10 ta buyurtma:\n\n"
        for order_id, user_id, total, status, date in orders:
            text += f"#{order_id} | User: {user_id} | {total} so'm | {status} | {date}\n"
        text += "\n📝 Holatni o'zgartirish uchun: /order_<raqam>\nMisol: /order_5"
        bot.send_message(call.message.chat.id, text)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast")
def admin_broadcast_start(call):
    user_id = call.from_user.id
    if user_id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Siz admin emassiz!", show_alert=True)
        return

    admin_state[user_id] = "broadcast"
    markup = types.ForceReply(selective=True)
    bot.send_message(
        call.message.chat.id,
        "📢 Barcha foydalanuvchilarga yuboriladigan xabar matnini yozing.\n\n"
        "Bekor qilish uchun /cancel yozing.",
        reply_markup=markup
    )
    bot.answer_callback_query(call.id)

@bot.message_handler(commands=['cancel'])
def cancel_admin_action(message):
    user_id = message.from_user.id
    if user_id in admin_state:
        admin_state.pop(user_id)
        bot.reply_to(message, "❌ Bekor qilindi.")

@bot.message_handler(func=lambda m: admin_state.get(m.from_user.id) == "broadcast")
def admin_broadcast_send(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        return

    admin_state.pop(user_id, None)
    broadcast_text = message.text

    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('SELECT user_id FROM users')
    all_users = [row[0] for row in c.fetchall()]
    conn.close()

    bot.send_message(message.chat.id, f"⏳ {len(all_users)} ta foydalanuvchiga yuborilmoqda...")

    sent = 0
    failed = 0
    for uid in all_users:
        try:
            bot.send_message(uid, broadcast_text)
            sent += 1
        except Exception:
            failed += 1
        time.sleep(0.05)

    bot.send_message(
        message.chat.id,
        f"✅ Xabar yuborish tugadi!\n\n"
        f"✔️ Yuborildi: {sent} ta\n"
        f" Yuborilmadi: {failed} ta (botni block qilganlar)"
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_users")
def admin_users(call):
    user_id = call.from_user.id
    if user_id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Siz admin emassiz!", show_alert=True)
        return

    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('''SELECT user_id, username, first_name, orders_count, total_spent
                 FROM users ORDER BY registration_date DESC LIMIT 20''')
    users = c.fetchall()
    conn.close()

    if not users:
        bot.send_message(call.message.chat.id, "👥 Hali foydalanuvchilar yo'q.")
    else:
        text = " So'nggi 20 ta foydalanuvchi:\n\n"
        for uid, username, first_name, orders_count, total_spent in users:
            uname = f"@{username}" if username else "username yo'q"
            text += f"• {first_name} ({uname}) | ID: {uid}\n  Buyurtmalar: {orders_count} | Xarajat: {total_spent} so'm\n\n"
        bot.send_message(call.message.chat.id, text)
    bot.answer_callback_query(call.id)

@bot.message_handler(regexp=r'^/order_\d+')
def order_status_command(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        bot.reply_to(message, "Siz admin emassiz!")
        return

    order_id = message.text.split('_', 1)[1].strip()
    if not order_id.isdigit():
        bot.reply_to(message, "Noto'g'ri buyurtma raqami.")
        return
    order_id = int(order_id)

    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('SELECT order_id, user_id, total, status FROM orders WHERE order_id = ?', (order_id,))
    order = c.fetchone()
    conn.close()

    if not order:
        bot.reply_to(message, f"❌ #{order_id} raqamli buyurtma topilmadi.")
        return

    _, order_user_id, total, current_status = order

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(
            "✅ Buyurtmangiz qabul qilindi",
            callback_data=f"setstatus|{order_id}|accepted"
        ),
        types.InlineKeyboardButton(
            "❌ Bekor qilish",
            callback_data=f"admin_cancel|{order_id}"
        )
    )

    bot.send_message(
        message.chat.id,
        f" Buyurtma #{order_id}\n"
        f"💰 Jami: {total} so'm\n"
        f"📊 Hozirgi holat: {current_status}\n\n"
        f"Yangi holatni tanlang:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("setstatus|"))
def set_order_status(call):
    user_id = call.from_user.id
    if user_id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Siz admin emassiz!", show_alert=True)
        return

    _, order_id, new_status = call.data.split("|")
    order_id = int(order_id)

    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('SELECT user_id FROM orders WHERE order_id = ?', (order_id,))
    result = c.fetchone()
    if not result:
        conn.close()
        bot.answer_callback_query(call.id, "Buyurtma topilmadi!", show_alert=True)
        return

    order_user_id = result[0]
    c.execute('UPDATE orders SET status = ? WHERE order_id = ?', (new_status, order_id))
    conn.commit()
    conn.close()

    status_names = {
        "new": "⏳ Kutilmoqda",
        "accepted": "✅ Buyurtmangiz qabul qilindi",
        "cancelled": "❌ Buyurtma bekor qilindi",
        "preparing": "✅ Buyurtmangiz qabul qilindi",
        "delivering": "✅ Buyurtmangiz qabul qilindi",
        "delivered": "✅ Buyurtmangiz qabul qilindi",
    }
    status_text = status_names.get(new_status, new_status)

    bot.answer_callback_query(call.id, f"Holat yangilandi: {status_text}")
    bot.send_message(
        call.message.chat.id,
        f"✅ Buyurtma #{order_id} holati yangilandi: {status_text}"
    )

    try:
        customer_markup = types.InlineKeyboardMarkup(row_width=1)
        customer_markup.add(
            types.InlineKeyboardButton(
                "❌ Bekor qilish",
                callback_data=f"customer_cancel|{order_id}"
            )
        )

        if new_status == "accepted":
            bot.send_message(
                order_user_id,
                f"✅ Buyurtmangiz qabul qilindi!\n\n"
                f"📦 Buyurtma raqami: #{order_id}\n"
                f"Tez orada buyurtmangiz tayyorlanadi.\n\n"
                f"Agar bekor qilmoqchi bo'lsangiz, pastdagi tugmani bosing.",
                reply_markup=customer_markup
            )
        elif new_status == "cancelled":
            # O'ZGARTIRILDI: Admin bekor qilganda telefon raqam chiqadigan qilindi
            bot.send_message(
                order_user_id,
                f"❌ Buyurtmangiz #{order_id} bekor qilindi.\n\n"
                f"Savollaringiz bo'lsa, administrator bilan bog'laning:\n"
                f"📞 Tel: {CONTACT_PHONE}",
                reply_markup=types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton(
                        f"📞 {CONTACT_PHONE}",
                        url=f"tel:{CONTACT_PHONE.replace(' ', '')}"
                    )
                )
            )
        else:
            bot.send_message(
                order_user_id,
                f"📦 Buyurtma #{order_id}: {status_text}",
                reply_markup=customer_markup
            )
    except Exception:
        pass

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_cancel|"))
def admin_cancel_order(call):
    user_id = call.from_user.id

    if user_id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Siz admin emassiz!", show_alert=True)
        return

    _, order_id = call.data.split("|")
    order_id = int(order_id)

    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('SELECT user_id, status FROM orders WHERE order_id = ?', (order_id,))
    result = c.fetchone()

    if not result:
        conn.close()
        bot.answer_callback_query(call.id, "Buyurtma topilmadi!", show_alert=True)
        return

    order_user_id, current_status = result
    if current_status == "cancelled":
        conn.close()
        bot.answer_callback_query(call.id, "Buyurtma allaqachon bekor qilingan.", show_alert=True)
        return

    c.execute('UPDATE orders SET status = ? WHERE order_id = ?', ("cancelled", order_id))
    conn.commit()
    conn.close()

    bot.answer_callback_query(call.id, "Buyurtma bekor qilindi ❌")
    bot.send_message(
        call.message.chat.id,
        f"❌ Buyurtma #{order_id} bekor qilindi."
    )

    try:
        # O'ZGARTIRILDI: Admin bekor qilganda mijozga telefon raqam chiqadigan qilindi
        bot.send_message(
            order_user_id,
            f"❌ Buyurtmangiz #{order_id} bekor qilindi.\n\n"
            f"Agar savol bo'lsa, administrator bilan bog'laning:\n"
            f"📞 Tel: {CONTACT_PHONE}",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton(
                    f"📞 {CONTACT_PHONE}",
                    url=f"tel:{CONTACT_PHONE.replace(' ', '')}"
                )
            )
        )
    except Exception:
        pass


@bot.callback_query_handler(func=lambda call: call.data == "cancel_order")
def cancel_current_order(call):
    user_id = call.from_user.id
    user_orders.pop(user_id, None)
    bot.answer_callback_query(call.id, "❌ Buyurtma bekor qilindi")
    bot.send_message(
        call.message.chat.id,
        "❌ Buyurtma bekor qilindi. Qaytadan boshlash uchun /menu ni bosing."
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("customer_cancel|"))
def customer_cancel_request(call):
    user_id = call.from_user.id

    _, order_id = call.data.split("|")
    order_id = int(order_id)

    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute(
        'SELECT status FROM orders WHERE order_id = ? AND user_id = ?',
        (order_id, user_id)
    )
    result = c.fetchone()
    conn.close()

    if not result:
        bot.answer_callback_query(call.id, "Buyurtma topilmadi!", show_alert=True)
        return

    if result[0] == "cancelled":
        bot.answer_callback_query(call.id, "Bu buyurtma allaqachon bekor qilingan.", show_alert=True)
        return

    # O'ZGARTIRILDI: Mijoz bekor qilishni bosganda to'g'ridan-to'g'ri telefon raqamga havola beriladi
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(
            f"📞 {CONTACT_PHONE}",
            url=f"tel:{CONTACT_PHONE.replace(' ', '')}"
        )
    )

    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        f"❌ Buyurtma #{order_id}ni bekor qilmoqchimisiz?\n\n"
        f"Bekor qilish uchun administrator bilan bog'laning:\n"
        f"📞 Tel: {CONTACT_PHONE}",
        reply_markup=markup
    )


def qty_keyboard(prefix):
    markup = types.InlineKeyboardMarkup(row_width=5)
    row = [types.InlineKeyboardButton(f"{i}ta", callback_data=f"{prefix}_{i}") for i in range(1, 6)]
    markup.add(*row)
    markup.add(types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_order"))
    return markup

def send_drinks_menu(chat_id, user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🧊 Sovuq ichimliklar", callback_data="cat_cold"),
        types.InlineKeyboardButton("☕ Issiq ichimliklar", callback_data="cat_hot"),
    )
    markup.add(types.InlineKeyboardButton("➡️ Ichimliksiz davom etish", callback_data="skip_drinks"))
    
    bot.send_message(chat_id, "🥤 Ichimlik tanlang yoki o'tkazib yuboring:", reply_markup=markup)

def cart_summary_text(cart):
    total = 0
    lines = []
    for line in cart:
        subtotal = line["price"] * line["qty"]
        total += subtotal
        lines.append(f"🔹 {line['name']} x{line['qty']} — {subtotal} so'm")
    return "\n".join(lines), total

# ================== ASOSIY BUYRUQLAR ==================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""
    
    referred_by = None
    if len(message.text.split()) > 1:
        ref_code = message.text.split()[1]
        if ref_code != "None":
            conn = sqlite3.connect('bot_database.db')
            c = conn.cursor()
            c.execute('SELECT user_id FROM users WHERE referal_code = ?', (ref_code,))
            result = c.fetchone()
            if result:
                referred_by = result[0]
            conn.close()
    
    save_user(user_id, username, first_name, last_name, referred_by)
    
    if is_subscribed(user_id):
        markup = types.InlineKeyboardMarkup(row_width=3)
        markup.add(
            types.InlineKeyboardButton("📋 Menyuni ko'rish", callback_data="show_menu_btn"),
            types.InlineKeyboardButton("🛒 Savatim", callback_data="view_cart"),
            types.InlineKeyboardButton("👤 Kabinetim", callback_data="customer_menu"),
        )
        
        if user_id == ADMIN_ID:
            markup.add(types.InlineKeyboardButton("👨‍💼 Admin panel", callback_data="admin_panel"))
        
        markup.add(
            types.InlineKeyboardButton("🎁 Bonuslarim", callback_data="my_bonus"),
            types.InlineKeyboardButton("📞 Aloqa", callback_data="contact_us"),
        )
        markup.add(
            types.InlineKeyboardButton("❓ Yordam", callback_data="show_help_btn"),
        )
        
        bot.send_message(
            message.chat.id,
            f"Salom, {first_name}! Xush kelibsiz 🍔\n\n"
            f"🚚 *Yetkazib berish:*\n"
            f"• Alisher Navoiy ko'chasi bo'ylab: BEPUL\n"
            f"• Qolgan manzillar: Yandex xizmati orqali\n\n"
            f"🎁 *Bonus tizimi:*\n"
            f"• Har 10,000 so'mdan 1 ball\n"
            f"• 1 ball = {BONUS_VALUE} so'm chegirma\n\n"
            f"*Quyidagi tugmalardan birini tanlang:*\n",
            reply_markup=markup,
            parse_mode="Markdown"
        )
    else:
        send_subscribe_message(message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == "show_menu_btn")
def show_menu_btn(call):
    user_id = call.from_user.id
    send_main_menu(call.message.chat.id, user_id)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "customer_menu")
def customer_menu_btn(call):
    user_id = call.from_user.id
    send_customer_menu(call.message.chat.id, user_id)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "admin_panel")
def admin_panel_btn(call):
    user_id = call.from_user.id
    if user_id == ADMIN_ID:
        send_admin_menu(call.message.chat.id)
    else:
        bot.answer_callback_query(call.id, "Siz admin emassiz!", show_alert=True)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "show_help_btn")
def show_help_btn(call):
    help_text = (
        " *Bot buyruqlari:*\n\n"
        "/start - Botni boshlash\n"
        "/menu - Menyuni ko'rish\n"
        "/savat - Savatni ko'rish\n"
        "/status - Buyurtma holati\n"
        "/rate - Xizmatni baholash\n"
        "/review - Izoh qoldirish\n"
        "/bonus - Bonuslaringiz\n"
        "/help - Yordam"
    )
    bot.send_message(call.message.chat.id, help_text, parse_mode="Markdown")
    bot.answer_callback_query(call.id)

@bot.message_handler(commands=['menu'])
def show_menu(message):
    user_id = message.from_user.id
    
    if not is_subscribed(user_id):
        send_subscribe_message(message.chat.id)
        return
    send_main_menu(message.chat.id, user_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("item|"))
def item_selected(call):
    user_id = call.from_user.id
    if not is_subscribed(user_id):
        bot.answer_callback_query(call.id, "Avval kanalga a'zo bo'ling.", show_alert=True)
        send_subscribe_message(call.message.chat.id)
        return

    name = call.data.split("|", 1)[1]
    if user_id not in user_orders:
        user_orders[user_id] = {"cart": []}
    
    price = FAST_CARS.get(name) or FAST_FOOD.get(name) or COLD_DRINKS.get(name) or HOT_DRINKS.get(name)
    
    if price is None:
        bot.answer_callback_query(call.id, "Mahsulot topilmadi!", show_alert=True)
        return
    
    user_orders[user_id]["pending_item"] = name
    user_orders[user_id]["pending_price"] = price
    bot.send_message(call.message.chat.id, f"{name} — nechta olasiz?", reply_markup=qty_keyboard("mqty"))
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("mqty_"))
def main_qty_selected(call):
    user_id = call.from_user.id
    qty = int(call.data.split("_")[1])
    order = user_orders.get(user_id)

    if not order or "pending_item" not in order:
        bot.answer_callback_query(call.id, "Bu tugma eskirgan. Iltimos, /menu dan qaytadan boshlang.", show_alert=True)
        return

    order["cart"].append({
        "name": order["pending_item"],
        "qty": qty,
        "price": order["pending_price"],
    })
    bot.send_message(call.message.chat.id, f"✅ {order['pending_item']} x{qty} savatga qo'shildi.")
    send_drinks_menu(call.message.chat.id, user_id)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "skip_drinks")
def skip_drinks(call):
    ask_address(call.message.chat.id, call.from_user.id)
    bot.answer_callback_query(call.id)

# ================== MANZIL SO'RASH ==================
def ask_address(chat_id, user_id):
    user_orders[user_id]["step"] = "address"
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton(" Manzilni yozish"))
    
    bot.send_message(
        chat_id, 
        " *Manzilingizni yozing*\n\n"
        "🚚 *Yetkazib berish shartlari:*\n"
        "• Alisher Navoiy ko'chasi bo'ylab: BEPUL\n"
        "• Qolgan manzillar: Yandex taksi xizmati orqali\n\n"
        "Misol:\n"
        "• Alisher Navoiy ko'chasi, 15-uy\n"
        "• Amir Temur ko'chasi, 8-uy\n\n"
        "Manzilingizni to'liq yozing:",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.from_user.id in user_orders and user_orders[m.from_user.id].get("step") == "address")
def get_address(message):
    user_id = message.from_user.id
    
    try:
        if message.text == "🏠 Manzilni yozish":
            markup = types.ReplyKeyboardRemove()
            bot.send_message(
                message.chat.id,
                "📝 Manzilingizni yozing\n\n"
                "🚚 Alisher Navoiy ko'chasi bo'ylab BEPUL\n"
                "📍 Qolgan joylar: Yandex xizmati orqali"
            , reply_markup=markup)
            user_orders[user_id]["step"] = "address_manual"
            return
        
        user_orders[user_id]["address"] = message.text
        
        bot.send_message(
            message.chat.id, 
            f"✅ *Manzil qabul qilindi:*\n{message.text}\n\n"
            f"📍 *Yetkazib berish:*\n"
            f"• Alisher Navoiy ko'chasi bo'ylab: BEPUL\n"
            f"• Qolgan manzillar: Yandex xizmati orqali",
            parse_mode="Markdown"
        )
        
        user_orders[user_id]["step"] = "phone"
        ask_phone(message.chat.id, user_id)
        
    except Exception as e:
        print(f"Manzilni qabul qilishda xato: {e}")
        bot.send_message(message.chat.id, " Xatolik. Qaytadan yozing:")

@bot.message_handler(func=lambda m: m.from_user.id in user_orders and user_orders[m.from_user.id].get("step") == "address_manual")
def get_address_manual(message):
    user_id = message.from_user.id
    
    try:
        user_orders[user_id]["address"] = message.text
        
        bot.send_message(
            message.chat.id, 
            f"✅ *Manzil qabul qilindi:*\n{message.text}\n\n"
            f"📍 *Yetkazib berish:*\n"
            f"• Alisher Navoiy ko'chasi bo'ylab: BEPUL\n"
            f"• Qolgan manzillar: Yandex xizmati orqali",
            parse_mode="Markdown"
        )
        
        user_orders[user_id]["step"] = "phone"
        ask_phone(message.chat.id, user_id)
        
    except Exception as e:
        print(f"Qo'lda manzil qabul qilishda xato: {e}")
        bot.send_message(message.chat.id, "❌ Xatolik. Qaytadan yozing:")

def ask_phone(chat_id, user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("📱 Raqamimni yuborish", request_contact=True))
    markup.add(types.KeyboardButton("✍️ Raqamni qo'lda yozish"))
    
    bot.send_message(
        chat_id,
        "📞 Telefon raqamingizni yuboring",
        reply_markup=markup
    )

@bot.message_handler(content_types=['contact', 'text'],
                      func=lambda m: m.from_user.id in user_orders and user_orders[m.from_user.id].get("step") == "phone")
def get_phone(message):
    user_id = message.from_user.id
    
    try:
        if message.contact:
            phone = message.contact.phone_number
            user_orders[user_id]["phone"] = phone
            bot.send_message(message.chat.id, f"✅ Telefon raqam qabul qilindi:\n{phone}")
        elif message.text == "✍️ Raqamni qo'lda yozish":
            user_orders[user_id]["step"] = "phone_manual"
            bot.send_message(message.chat.id, "📱 Telefon raqamingizni yozing:")
            return
        else:
            user_orders[user_id]["phone"] = message.text
            bot.send_message(message.chat.id, f"✅ Telefon raqam qabul qilindi:\n{message.text}")
        
        if user_orders[user_id].get("step") != "phone_manual":
            user_orders[user_id]["step"] = "payment"
            ask_payment(message.chat.id, user_id)
            
    except Exception as e:
        print(f"Telefon raqamni qabul qilishda xato: {e}")
        bot.send_message(message.chat.id, "❌ Xatolik. Qaytadan yuboring:")

@bot.message_handler(func=lambda m: m.from_user.id in user_orders and user_orders[m.from_user.id].get("step") == "phone_manual")
def get_phone_manual(message):
    user_id = message.from_user.id
    
    try:
        user_orders[user_id]["phone"] = message.text
        bot.send_message(message.chat.id, f"✅ Telefon raqam qabul qilindi:\n{message.text}")
        
        user_orders[user_id]["step"] = "payment"
        ask_payment(message.chat.id, user_id)
        
    except Exception as e:
        print(f"Qo'lda telefon qabul qilishda xato: {e}")
        bot.send_message(message.chat.id, "❌ Xatolik. Qaytadan yozing:")

def ask_payment(chat_id, user_id):
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton(" Click / Payme", callback_data="pay|click"),
        types.InlineKeyboardButton("💵 Naqd pul", callback_data="pay|cash"),
    )
    markup.add(types.InlineKeyboardButton(" Bonusdan foydalanish", callback_data="use_bonus"))
    
    bot.send_message(chat_id, "💳 To'lov turini tanlang:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "use_bonus")
def use_bonus_callback(call):
    user_id = call.from_user.id
    bonus_points = get_user_bonus(user_id)
    
    if bonus_points <= 0:
        bot.answer_callback_query(call.id, "Sizda bonus yo'q", show_alert=True)
        return
    
    discount = bonus_points * BONUS_VALUE
    bot.answer_callback_query(call.id, f"Chegirma: {discount} so'm ✅")
    user_orders[user_id]["bonus_used"] = bonus_points
    user_orders[user_id]["discount"] = discount
    finalize_order(call.message.chat.id, user_id, "Naqd pul (bonus bilan)")

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay|"))
def payment_selected(call):
    user_id = call.from_user.id
    method = call.data.split("|", 1)[1]
    order = user_orders.get(user_id)

    if not order:
        bot.answer_callback_query(call.id, "Bu tugma eskirgan.", show_alert=True)
        return

    if method == "cash":
        finalize_order(call.message.chat.id, user_id, "Naqd pul")
    else:
        order["step"] = "receipt"
        bot.send_message(
            call.message.chat.id,
            f"💳 To'lov uchun link:\n\n"
            f"https://click.uz/pay?amount={order.get('total', 0)}\n\n"
            f"Yoki quyidagi kartaga to'lov qiling:\n"
            f"💳 Karta raqami: {CARD_NUMBER}\n"
            f"👤 Karta egasi: {CARD_OWNER}\n\n"
            f"To'lov qilgach, chekning (skrinshot) shu yerga yuboring."
        )
        order["step"] = "receipt"
    bot.answer_callback_query(call.id)

@bot.message_handler(content_types=['photo', 'document', 'text'],
                      func=lambda m: m.from_user.id in user_orders and user_orders[m.from_user.id].get("step") == "receipt")
def get_receipt(message):
    user_id = message.from_user.id
    
    if user_id not in user_orders:
        return

    if message.content_type == 'photo':
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"🧾 To'lov cheki (User ID: {user_id})")
    elif message.content_type == 'document':
        bot.send_document(ADMIN_ID, message.document.file_id, caption=f"🧾 To'lov cheki (User ID: {user_id})")
    else:
        bot.send_message(ADMIN_ID, f"🧾 To'lov cheki (matn): {message.text}\nUser ID: {user_id}")

    finalize_order(message.chat.id, user_id, "Click / Karta orqali")

def finalize_order(chat_id, user_id, payment_method):
    order = user_orders.pop(user_id, None)
    if not order:
        return

    cart_text, total = cart_summary_text(order["cart"])
    address = order.get("address", "Ko'rsatilmagan")
    phone = order.get("phone", "Ko'rsatilmagan")
    discount = order.get("discount", 0)
    bonus_used = order.get("bonus_used", 0)
    
    final_total = total - discount
    
    if bonus_used > 0:
        use_bonus(user_id, bonus_used)

    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('''INSERT INTO orders (user_id, items, total, address, phone, 
                 payment_method, status, order_date)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
              (user_id, cart_text, final_total, address, phone, 
               payment_method, "new", datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    order_id = c.lastrowid
    conn.commit()
    conn.close()

    update_user_stats(user_id, final_total)
    earned_points = final_total // 10000 * BONUS_PER_10000

    # MIJOZGA XABAR
    user_message = (
        f"✅ Rahmat! Buyurtmangiz qabul qilindi!\n\n"
        f"{cart_text}\n\n"
        f"💰 Mahsulotlar: {total} so'm\n"
        f"🎁 Chegirma: -{discount} so'm\n"
        f"💵 Jami: {final_total} so'm\n\n"
        f"📍 Manzil: {address}\n"
        f"📞 Telefon: {phone}\n"
        f"💳 To'lov: {payment_method}\n"
        f"🚚 Yetkazib berish:\n"
        f"   • Alisher Navoiy ko'chasi bo'ylab: BEPUL\n"
        f"   • Qolgan joylar: Yandex xizmati orqali\n\n"
        f"📋 Buyurtma raqami: #{order_id}\n"
        f"🎁 Siz {earned_points} ball qozondingiz!\n\n"
        f"Buyurtmangiz qabul qilindi. Tez orada administrator siz bilan bog'lanadi.\n\n"
        f'Bekor qilmoqchi bo\'lsangiz, pastdagi "❌ Bekor qilish" tugmasini bosing.'
    )
    customer_markup = types.InlineKeyboardMarkup(row_width=1)
    customer_markup.add(
        types.InlineKeyboardButton(
            "❌ Bekor qilish",
            callback_data=f"customer_cancel|{order_id}"
        )
    )

    bot.send_message(
        chat_id,
        user_message,
        reply_markup=customer_markup
    )

    # ADMINGA XABAR
    if ADMIN_ID and ADMIN_ID != 0:
        try:
            admin_message = (
                f" Yangi buyurtma #{order_id}!\n\n"
                f"{cart_text}\n\n"
                f"💰 Mahsulotlar: {total} so'm\n"
                f"🎁 Chegirma: -{discount} so'm\n"
                f"💵 Jami: {final_total} so'm\n\n"
                f"📍 Manzil: {address}\n"
                f"📞 Telefon: {phone}\n"
                f"💳 To'lov: {payment_method}\n"
                f"🚚 Yetkazib berish:\n"
                f"   • Alisher Navoiy bo'ylab: BEPUL\n"
                f"   • Qolgan joylar: Yandex orqali\n\n"
                f"Quyidagi tugmalardan birini tanlang:"
            )
            admin_markup = types.InlineKeyboardMarkup(row_width=2)
            admin_markup.add(
                types.InlineKeyboardButton(
                    "✅ Buyurtmangiz qabul qilindi",
                    callback_data=f"setstatus|{order_id}|accepted"
                ),
                types.InlineKeyboardButton(
                    "❌ Bekor qilish",
                    callback_data=f"admin_cancel|{order_id}"
                )
            )

            bot.send_message(
                ADMIN_ID,
                admin_message,
                reply_markup=admin_markup
            )
            print(f"✅ Buyurtma #{order_id} admin'ga yuborildi!")
            print(f"   Manzil: {address}")
            print(f"   Telefon: {phone}")
            print(f"   Jami: {final_total} so'm")
        except Exception as e:
            print(f"❌ Admin'ga yuborishda xato: {e}")
            print(f"   ADMIN_ID: {ADMIN_ID}")
            print(f"   Iltimos, ADMIN_ID ni tekshiring!")
    else:
        print(f"❌ ADMIN_ID kiritilmagan! Buyurtma #{order_id} admin'ga yuborilmadi.")
        print(f"   Kodda ADMIN_ID ni to'g'ri kiriting (masalan: 123456789)")

# ================== BOSHQA BUYRUQLAR ==================
@bot.message_handler(commands=['status'])
def check_status(message):
    user_id = message.from_user.id
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('''SELECT order_id, status, order_date FROM orders 
                 WHERE user_id = ? ORDER BY order_id DESC LIMIT 5''', (user_id,))
    orders = c.fetchall()
    conn.close()
    
    if not orders:
        bot.reply_to(message, "📋 Sizda hali buyurtmalar yo'q.")
        return
    
    status_text = "📋 So'nggi buyurtmalaringiz:\n\n"
    for order_id, status, date in orders:
        status_names = {
            "new": "⏳ Kutilmoqda",
            "accepted": "✅ Buyurtmangiz qabul qilindi",
            "cancelled": "❌ Buyurtma bekor qilindi",
            "preparing": "✅ Buyurtmangiz qabul qilindi",
            "delivering": "✅ Buyurtmangiz qabul qilindi",
            "delivered": "✅ Buyurtmangiz qabul qilindi",
        }
        status_text += f"📦 Buyurtma #{order_id} — {status_names.get(status, status)}\n📅 {date}\n\n"
    
    bot.send_message(message.chat.id, status_text)

@bot.message_handler(commands=['review'])
def add_review(message):
    user_id = message.from_user.id
    comment = message.text.replace('/review', '').strip()
    
    if not comment:
        bot.reply_to(message, "Izohingizni yozing: /review Zo'r xizmat!")
        return
    
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('''INSERT INTO reviews (user_id, comment, review_date)
                 VALUES (?, ?, ?)''', (user_id, comment, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()
    
    bot.reply_to(message, "✅ Rahmat! Izohingiz qabul qilindi.")

@bot.message_handler(commands=['bonus'])
def show_bonus(message):
    user_id = message.from_user.id
    bonus_points = get_user_bonus(user_id)
    discount = bonus_points * BONUS_VALUE
    
    orders_count, total_spent, _ = get_user_info(user_id)
    
    bot.send_message(
        message.chat.id,
        f"🎁 *Sizning bonuslaringiz:*\n\n"
        f"⭐ Ballar: {bonus_points}\n"
        f"💰 Chegirma: {discount} so'm\n\n"
        f"📊 Statistika:\n"
        f"🛒 Buyurtmalar: {orders_count}\n"
        f"💵 Jami xarajat: {total_spent} so'm\n\n"
        f"💡 Har 10,000 so'mdan 1 ball qozonasiz!\n"
        f"💰 1 ball = {BONUS_VALUE} so'm chegirma",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = (
        "🤖 *Bot buyruqlari:*\n\n"
        "/start - Botni boshlash\n"
        "/menu - Menyuni ko'rish\n"
        "/savat - Savatni ko'rish\n"
        "/status - Buyurtma holati\n"
        "/rate - Xizmatni baholash\n"
        "/review - Izoh qoldirish\n"
        "/bonus - Bonuslaringiz\n"
        "/help - Yordam"
    )
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown")

# ================== BOTNI ISHGA TUSHIRISH ==================
if __name__ == "__main__":
    print("✅ Bot muvaffaqiyatli ishga tushmoqda...")
    print("📊 Ma'lumotlar bazasi tayyor")
    print("🤖 Barcha funksiyalar faol")
    print("🕐 Ish vaqti: 24/7")
    print("🚚 Yetkazib berish:")
    print("   • Alisher Navoiy ko'chasi bo'ylab: BEPUL")
    print("   • Qolgan joylar: Yandex xizmati orqali")
    print(f"☕ Issiq ichimliklar: {len(HOT_DRINKS)} ta")
    print(f"🧊 Sovuq ichimliklar: {len(COLD_DRINKS)} ta")
    print(f"📞 Aloqa: {CONTACT_PHONE}")
    print(f"\n BONUS TIZIMI:")
    print(f"   • Har 10,000 so'mdan {BONUS_PER_10000} ball")
    print(f"   • 1 ball = {BONUS_VALUE} so'm chegirma")
    
    if not ADMIN_ID or ADMIN_ID == 0:
        print("️ DIQQAT: ADMIN_ID kiritilmagan!")
        print("   Buyurtmalar admin'ga yuborilmaydi!")
        print("   Kodda ADMIN_ID ni to'g'ri kiriting (masalan: 123456789)")
    else:
        print(f"✅ ADMIN_ID: {ADMIN_ID}")
        print(f"✅ Buyurtmalar admin'ga yuboriladi")
    
    print("\n🚀 Bot ishga tushdi! Buyurtmalar kelishini kuting...")
    
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=30)
        except Exception as e:
            print(f"⚠️ Xato chiqdi: {e}")
            print("5 soniyadan keyin qayta urinish...")
            time.sleep(5)