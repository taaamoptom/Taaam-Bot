import os
import json
from dotenv import load_dotenv
import telebot
from telebot import types
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ==== Load .env ====
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
TOPIC_ID = int(os.getenv("TOPIC_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(BOT_TOKEN)
user_data = {}
users = set()  # barcha foydalanuvchilar ro‘yxati

# ==== Google Credentials ====
google_creds = {
    "type": os.getenv("GOOGLE_TYPE"),
    "project_id": os.getenv("GOOGLE_PROJECT_ID"),
    "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("GOOGLE_PRIVATE_KEY").replace("\\n", "\n"),
    "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
    "auth_uri": os.getenv("GOOGLE_AUTH_URI"),
    "token_uri": os.getenv("GOOGLE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("GOOGLE_AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": os.getenv("GOOGLE_CLIENT_X509_CERT_URL"),
}

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds, scope)
client = gspread.authorize(creds)

sheet_file = client.open("Lidlar")
sheets = {
    "👩 Manager 1": sheet_file.worksheet("Manager_1"),
    "👨 Manager 2": sheet_file.worksheet("Manager_2")
}

# ==== Viloyatlar va tumanlar ====
regions = {
    "Toshkent": ["Chilonzor", "Yunusobod", "Sergeli", "Bektemir"],
    "Farg‘ona": ["Qo‘qon", "Marg‘ilon", "Beshariq", "Rishton"],
    "Andijon": ["Asaka", "Xo‘jaobod", "Shahrixon", "Marhamat"],
    "Namangan": ["Chust", "Kosonsoy", "To‘raqo‘rg‘on", "Uychi"],
    "Qarshi": ["Koson", "Mirishkor", "Shahrisabz", "Kitob"],
    "Buxoro": ["G‘ijduvon", "Qorako‘l", "Olot", "Vobkent"],
    "Samarqand": ["Urgut", "Kattaqo‘rg‘on", "Bulung‘ur", "Ishtixon"]
}

# ==== Kategoriyalar ====
categories = [
    "Soch taqinchoqlari", "Bijuteriya", "Kosmetika", "Taroq-Oynakcha",
    "Sumka-Hamyon", "Ro‘zg‘or Buyumlari", "O‘yinchoqlar", "Baby shop"
]

# ==== Managerlar ====
managers = {
    "👩 Manager 1": 7680588743,
    "👨 Manager 2": 987654321
}

def get_manager_name(chat_id):
    for k, v in managers.items():
        if v == chat_id:
            return k
    return None

# ==== Start komandasi ====
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id

    # foydalanuvchini ro‘yxatga qo‘shamiz
    if chat_id not in managers.values():
        users.add(chat_id)

    # agar manager bo‘lsa
    if chat_id in managers.values():
        bot.send_message(chat_id, f"👋 Xush kelibsiz! Siz {get_manager_name(chat_id)}. "
                                  f"Endi sizga foydalanuvchilarning ma’lumotlari kelib turadi.")
        return

    # oddiy foydalanuvchi
    user_data[chat_id] = {"categories": []}
    bot.send_message(chat_id, "👋 Salom! Ismingizni kiriting:")
    bot.register_next_step_handler(message, get_name)

# ==== Ism olish ====
def get_name(message):
    chat_id = message.chat.id
    user_data[chat_id]["name"] = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    phone_btn = types.KeyboardButton("📱 Raqamni yuborish", request_contact=True)
    markup.add(phone_btn)
    bot.send_message(chat_id, "📱 Telefon raqamingizni yuboring:", reply_markup=markup)

# ==== Telefon olish ====
@bot.message_handler(content_types=['contact'])
def get_contact(message):
    chat_id = message.chat.id
    phone = message.contact.phone_number.replace("+", "").replace(" ", "")
    user_data[chat_id]["phone"] = phone
    user_data[chat_id]["username"] = message.from_user.username or "-"
    bot.send_message(chat_id, "✅ Raqamingiz qabul qilindi.", reply_markup=types.ReplyKeyboardRemove())
    show_regions(chat_id)

# ==== Viloyat tanlash ====
def show_regions(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for region in regions.keys():
        markup.add(types.KeyboardButton(region))
    bot.send_message(chat_id, "📍 Yashash viloyatingizni tanlang:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in regions.keys())
def get_region(message):
    chat_id = message.chat.id
    user_data[chat_id]["region"] = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for district in regions[message.text]:
        markup.add(types.KeyboardButton(district))
    bot.send_message(chat_id, f"📍 {message.text} viloyati tanlandi.\nEndi tumanni tanlang:", reply_markup=markup)

@bot.message_handler(func=lambda m: any(m.text in d for d in regions.values()))
def get_district(message):
    chat_id = message.chat.id
    user_data[chat_id]["district"] = message.text
    bot.send_message(chat_id, f"✅ Manzil: {user_data[chat_id]['region']}, {message.text}", reply_markup=types.ReplyKeyboardRemove())
    show_categories(chat_id)

# ==== Kategoriya tanlash ====
def show_categories(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(text=cat, callback_data=f"cat:{cat}") for cat in categories]
    markup.add(*buttons)
    markup.add(types.InlineKeyboardButton("✅ Tasdiqlash", callback_data="confirm"))
    bot.send_message(chat_id, "📂 Kategoriyalardan tanlang:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat") or call.data == "confirm")
def callback_handler(call):
    chat_id = call.message.chat.id
    if call.data.startswith("cat:"):
        category = call.data.split(":")[1]
        if category in user_data[chat_id]["categories"]:
            user_data[chat_id]["categories"].remove(category)
        else:
            user_data[chat_id]["categories"].append(category)

        selected = "\n".join([f"- {c}" for c in user_data[chat_id]["categories"]]) or "❌ Hech narsa tanlanmagan"
        bot.edit_message_text(
            f"📂 Tanlangan kategoriyalar:\n{selected}\n\n👇 Tanlashni davom eting yoki tasdiqlang.",
            chat_id, call.message.message_id, reply_markup=call.message.reply_markup
        )
    elif call.data == "confirm":
        if not user_data[chat_id]["categories"]:
            bot.answer_callback_query(call.id, "Hech bo‘lmaganda bitta kategoriya tanlang!")
            return
        show_managers(chat_id)

# ==== Manager tanlash ====
def show_managers(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for m in managers.keys():
        markup.add(types.KeyboardButton(m))
    bot.send_message(chat_id, "👨‍💼 Qaysi manager bilan bog‘lanmoqchisiz?", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in managers.keys())
def get_manager(message):
    chat_id = message.chat.id
    manager_name = message.text
    manager_id = managers[manager_name]
    user_data[chat_id]["manager"] = manager_name

    text = (
        f"🆕 Yangi buyurtma!\n\n"
        f"👤 Ism: {user_data[chat_id].get('name')}\n"
        f"📱 Tel: +{user_data[chat_id].get('phone')}\n"
        f"💬 Username: @{user_data[chat_id].get('username')}\n\n"
        f"📍 Manzil: {user_data[chat_id]['region']}, {user_data[chat_id]['district']}\n\n"
        f"📂 Kategoriyalar:\n" + "\n".join([f"- {c}" for c in user_data[chat_id]['categories']]) +
        f"\n\n👨‍💼 Manager: {manager_name}"
    )

    send_to_group_topic(text)
    bot.send_message(manager_id, text)
    bot.send_message(chat_id, "✅ Ma’lumotlaringiz yuborildi!", reply_markup=types.ReplyKeyboardRemove())

    sheet = sheets[manager_name]
    sheet.append_row([
        user_data[chat_id].get("name"),
        user_data[chat_id].get("phone"),
        user_data[chat_id].get("username"),
        f"{user_data[chat_id]['region']}, {user_data[chat_id]['district']}",
        ", ".join(user_data[chat_id]['categories']),
        manager_name
    ])

# ==== Guruhga yuborish ====
def send_to_group_topic(text):
    if TOPIC_ID:
        bot.send_message(chat_id=GROUP_ID, text=text, message_thread_id=TOPIC_ID)
    else:
        bot.send_message(chat_id=GROUP_ID, text=text)

# ==== ID olish ====
@bot.message_handler(commands=['getid'])
def get_id(message):
    bot.send_message(message.chat.id, f"Bu chat ID: {message.chat.id}\nTopic ID: {message.message_thread_id}")

# ==== Admin uchun broadcast ====
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    chat_id = message.chat.id
    if chat_id != ADMIN_ID:
        bot.send_message(chat_id, "❌ Sizda bu komanda yo‘q.")
        return

    text = message.text.replace("/broadcast", "").strip()
    if not text:
        bot.send_message(chat_id, "ℹ️ Foydalanish: /broadcast <xabar matni>")
        return

    success, fail = 0, 0
    for uid in users:
        try:
            bot.send_message(uid, text)
            success += 1
        except:
            fail += 1

    bot.send_message(chat_id, f"✅ Xabar {success} ta foydalanuvchiga yuborildi.\n❌ {fail} ta yuborilmadi.")

print("✅ Bot ishlayapti...")
bot.infinity_polling()
