import os
import threading
import time
from dotenv import load_dotenv
import telebot
from telebot import types
from flask import Flask
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ==== Load .env ====
load_dotenv()



BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
TOPIC_ID = int(os.getenv("TOPIC_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(BOT_TOKEN)

# ==== Flask app ====
app = Flask(__name__)
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
    "👩 Mohigul": sheet_file.worksheet("Mohigul"),
    "👩 Sadoqatxon": sheet_file.worksheet("Sadoqatxon")
}

# ==== Viloyatlar va tumanlar ====
regions = {
    "Toshkent viloyati": [
        "Nurafshon shahri", "Bekobod tumani", "Boʻka tumani", "Boʻstonliq tumani",
        "Chinoz tumani", "Ohangaron tumani", "Oqqoʻrgʻon tumani", "Parkent tumani",
        "Piskent tumani", "Quyichirchiq tumani", "Oʻrtachirchiq tumani", "Yangiyoʻl tumani",
        "Zangiota tumani", "Toshkent tumani", "Yuqorichirchiq tumani", "Qibray tumani",
    ],
    
    "Toshkent shahri": [
        "Chilonzor tumani", "Mirzo Ulug‘bek tumani", "Mirobod tumani", "Sergeli tumani",
        "Shahrixon tumani", "Shoʻrchiq tumani", "Toshkent shahri", "Uchqoʻrgʻon tumani",
        "Xoʻjaobod tumani", "Yunusobod tumani", "Zafarobod tumani", "Zomin tumani",
    ],

    "Farg‘ona viloyati": [
        "Farg‘ona shahri", "Farg‘ona tumani", "Beshariq tumani", "Bog`dod tumani", "Buvayda tumani", "Dang‘ara tumani", 
        "Furqat tumani", "Qo‘shtepa tumani", "Quva tumani", "Quvasoy tumani", "Oltiariq tumani", 
        "Rishton tumani", "So'x tumani", "Toshloq tumani", "Uchko‘prik tumani", "Yozyovon tumani", "Qo‘qon shahri",
    ],
    
    "Andijon viloyati": [
        "Andijon shahri", "Andijon tumani", "Asaka tumani", "Baliqchi tumani",
        "Boʻston tumani", "Buloqboshi tumani", "Izboskan tumani", "Jalaquduq tumani",
        "Qoʻrgʻontepa tumani", "Marhamat tumani", "Oltinkoʻl tumani", "Paxtaobod tumani", 
        "Shahrixon tumani", "Ulugʻnor tumani", "Xoʻjaobod tumani",
    ],
    
    "Namangan viloyati": [
        "Namangan shahri", "Chortoq tumani", "Chust tumani", "Kosonsoy tumani",
        "Mingbuloq tumani", "Namangan tumani", "Norin tumani", "Pop tumani",
        "Toʻraqoʻrgʻon tumani", "Uchqoʻrgʻon tumani", "Uychi tumani", "Yangiqoʻrgʻon tumani",
    ],

    "Qashqadaryo viloyati": [
        "Qarshi shahri", "Chiroqchi tumani", "Dehqonobod tumani", "Gʻuzor tumani",
        "Kasbi tumani", "Kitob tumani", "Koson tumani", "Mirishkor tumani",
        "Muborak tumani", "Nishon tumani", "Qamashi tumani", "Qarshi tumani",
        "Shahrisabz shahri", "Shahrisabz tumani", "Yakkabogʻ tumani",
    ],
    
    "Surxondaryo viloyati": [
        "Termiz shahri", "Angor tumani", "Bandixon tumani", "Boysun tumani",
        "Denov tumani", "Jarqoʻrgʻon tumani", "Muzrabot tumani", "Oltinsoy tumani",
        "Qiziriq tumani", "Qumqoʻrgʻon tumani", "Sariosiyo tumani",
        "Sherobod tumani", "Shoʻrchi tumani", "Termiz tumani", "Uzun tumani"
    ],

    "Navoiy viloyati": [
        "Navoiy shahri", "Zarafshon shahri", "Karmana tumani", "Konimex tumani",
        "Navbahor tumani", "Nurota tumani", "Qiziltepa tumani", "Xatirchi tumani",
        "Tomdi tumani", "Uchquduq tumani"
    ],
      
    "Xorazm viloyati": [
        "Urganch shahri", "Bogʻot tumani", "Gurlan tumani", "Xonqa tumani",
        "Hazorasp tumani", "Shovot tumani", "Yangiariq tumani",
        "Yangibozor tumani", "Qoʻshkoʻpir tumani", "Tupproqqalʼa tumani"
    ],
      
    "Samarqand viloyati": [
        "Samarqand shahri", "Bulungʻur tumani", "Ishtixon tumani", "Jomboy tumani",           
        "Kattaqoʻrgʻon tumani", "Kattaqoʻrgʻon shahri", "Narpay tumani",
        "Nurobod tumani", "Oqdaryo tumani", "Paxtachi tumani",
        "Pastdargʻom tumani", "Payariq tumani", "Qoʻshrabot tumani",
        "Tayloq tumani", "Urgut tumani"
    ],
      
    "Jizzax viloyati": [
        "Jizzax shahri", "Arnasoy tumani", "Baxmal tumani", "Doʻstlik tumani",
        "Forish tumani", "Gʻallaorol tumani", "Mirzachoʻl tumani",
        "Paxtakor tumani", "Yangiobod tumani", "Zarbdor tumani",
        "Zafarobod tumani", "Zomin tumani", "Sharof Rashidov tumani"
    ],
      
    "Buxoro viloyati": [
        "Buxoro shahri", "Buxoro tumani", "Qorakoʻl tumani", "Gʻijduvon tumani",
        "Jondor tumani", "Kogon tumani", "Olot tumani", "Peshku tumani",
        "Romitan tumani", "Shofirkon tumani", "Vobkent tumani",
        "Peshkun tumani", "Kogon shahri (alohida tuman maqomida)"
    ],
      
    "Sirdaryo viloyati": [
        "Guliston shahri", "Guliston tumani", "Sardoba tumani",
        "Boyovut tumani", "Mirzaobod tumani", "Oqoltin tumani",
        "Sayxunobod tumani", "Xovos tumani"
    ],

    "Qoraqalpog‘iston Respublikasi": [
        "Amudaryo tumani", "Beruniy tumani", "Boʻzattum tumani",
        "Chimboy tumani", "Ellikqal'a tumani", "Kegeyli tumani",
        "Moʻynoq tumani", "Nukus tumani", "Qanlikoʻl tumani",
        "Qoʻngʻirot tumani", "Qoraoʻzak tumani", "Shumanay tumani",
        "Taxtakoʻpir tumani", "Toʻrtkoʻl tumani", "Xoʻjayli tumani",  
    ],
}

# ==== Kategoriyalar ====
categories = [
    "Soch taqinchoqlari", "Bijuteriya", "Kosmetika", "Taroq-Oynakcha",
    "Sumka-Hamyon", "Ro‘zg‘or Buyumlari", "O‘yinchoqlar", "Baby shop"
]

# ==== Managerlar ====
managers = {
    "👩 Mohigul": 1926487266,
    "👩 Sadoqatxon": 7566604257
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

    if chat_id not in managers.values():
        users.add(chat_id)

    if chat_id in managers.values():
        bot.send_message(chat_id, f"👋 Xush kelibsiz! Siz {get_manager_name(chat_id)}.")
        return

    user_data[chat_id] = {"categories": []}
    bot.send_message(chat_id, "👋 Salom! Ism va familiyangizni yozing:")
    bot.register_next_step_handler(message, get_name)

def get_name(message):
    chat_id = message.chat.id
    user_data[chat_id]["name"] = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    phone_btn = types.KeyboardButton("📱 Raqamni yuborish", request_contact=True)
    markup.add(phone_btn)
    bot.send_message(chat_id, "📱 Telefon raqamingizni yuboring:", reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def get_contact(message):
    chat_id = message.chat.id
    phone = message.contact.phone_number.replace("+", "").replace(" ", "")
    user_data[chat_id]["phone"] = phone
    user_data[chat_id]["username"] = message.from_user.username or "-"
    bot.send_message(chat_id, "✅ Raqam qabul qilindi.", reply_markup=types.ReplyKeyboardRemove())
    show_regions(chat_id)

def show_regions(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for region in regions.keys():
        markup.add(types.KeyboardButton(region))
    bot.send_message(chat_id, "📍 Viloyatingizni tanlang:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in regions.keys())
def get_region(message):
    chat_id = message.chat.id
    user_data[chat_id]["region"] = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for district in regions[message.text]:
        markup.add(types.KeyboardButton(district))
    bot.send_message(chat_id, f"📍 {message.text} tanlandi. Endi tumanni tanlang:", reply_markup=markup)

@bot.message_handler(func=lambda m: any(m.text in d for d in regions.values()))
def get_district(message):
    chat_id = message.chat.id
    user_data[chat_id]["district"] = message.text
    bot.send_message(chat_id, f"✅ Manzil: {user_data[chat_id]['region']}, {message.text}", reply_markup=types.ReplyKeyboardRemove())
    show_categories(chat_id)

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

        selected = "\n".join([f"- {c}" for c in user_data[chat_id]["categories"]]) or "❌ Tanlanmagan"
        bot.edit_message_text(
            f"📂 Tanlangan kategoriyalar:\n{selected}\n\n👇 Tanlashni davom eting yoki tasdiqlang.",
            chat_id, call.message.message_id, reply_markup=call.message.reply_markup
        )
    elif call.data == "confirm":
        if not user_data[chat_id]["categories"]:
            bot.answer_callback_query(call.id, "Hech bo‘lmaganda bitta kategoriya tanlang!")
            return
        show_managers(chat_id)

def show_managers(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for m in managers.keys():
        markup.add(types.KeyboardButton(m))
    bot.send_message(chat_id, "🤵🏻‍♀️ Manager tanlang:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in managers.keys())
def get_manager(message):
    chat_id = message.chat.id
    manager_name = message.text
    manager_id = managers[manager_name]
    user_data[chat_id]["manager"] = manager_name

    text = (
        f"🆕 Yangi Lid!\n\n"
        f"👤 Ism: {user_data[chat_id].get('name')}\n"
        f"📱 Tel: +{user_data[chat_id].get('phone')}\n"
        f"💬 Username: @{user_data[chat_id].get('username')}\n\n"
        f"📍 Manzil: {user_data[chat_id]['region']}, {user_data[chat_id]['district']}\n\n"
        f"📂 Kategoriyalar:\n" + "\n".join([f"- {c}" for c in user_data[chat_id]['categories']]) +
        f"\n\n🤵🏻‍♀️ Manager: {manager_name}"
    )

    send_to_group_topic(text)
    bot.send_message(manager_id, text)
    bot.send_message(chat_id, "✅ Ma’lumot yuborildi!", reply_markup=types.ReplyKeyboardRemove())

    sheet = sheets[manager_name]
    sheet.append_row([
        user_data[chat_id].get("name"),
        user_data[chat_id].get("phone"),
        user_data[chat_id].get("username"),
        f"{user_data[chat_id]['region']}, {user_data[chat_id]['district']}",
        ", ".join(user_data[chat_id]['categories']),
        manager_name
    ])

def send_to_group_topic(text):
    if TOPIC_ID:
        bot.send_message(chat_id=GROUP_ID, text=text, message_thread_id=TOPIC_ID)
    else:
        bot.send_message(chat_id=GROUP_ID, text=text)

@bot.message_handler(commands=['getid'])
def get_id(message):
    bot.send_message(message.chat.id, f"Chat ID: {message.chat.id}\nTopic ID: {message.message_thread_id}")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    chat_id = message.chat.id
    if chat_id != ADMIN_ID:
        bot.send_message(chat_id, "❌ Sizda ruxsat yo‘q.")
        return

    text = message.text.replace("/broadcast", "").strip()
    if not text:
        bot.send_message(chat_id, "ℹ️ Foydalanish: /broadcast <xabar>")
        return

    success, fail = 0, 0
    for uid in users:
        try:
            bot.send_message(uid, text)
            success += 1
        except:
            fail += 1

    bot.send_message(chat_id, f"✅ {success} ta foydalanuvchiga yuborildi.\n❌ {fail} ta yuborilmadi.")

@app.route('/')
def index():
    return "✅ Bot ishlayapti!"

# ==== Polling with Auto-Restart ====
def run_bot():
    print("✅ Bot ishga tushdi...")
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"❌ Xatolik: {e}")
            time.sleep(5)

if __name__ == "__main__":
    # Botni parallel thread’da ishga tushirish
    threading.Thread(target=run_bot).start()

    # Render PORT o‘zgaruvchisini ishlatadi
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
