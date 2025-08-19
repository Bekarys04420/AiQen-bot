import os
import socket
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# =====================
# Flask keep alive (Render/Replit үшін)
# =====================
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# =====================
# Мәліметтер
# =====================
servers = {}  # {ip: {"name": "Server1", "record": 0}}
user_messages = {}  # {user_id: count}
user_nicks = {}  # {user_id: "Бекарыс"}

# =====================
# Minecraft пинг (қарапайым эмуляция)
# =====================
def ping_server(ip, port=25565):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect((ip, port))
        sock.close()
        import random
        online = random.randint(1, 20)
        max_players = 50
        version = "1.20.x"
        return online, max_players, version
    except:
        return 0, 0, "Белгісіз"

# =====================
# Telegram BOT
# =====================
def start_bot():
    TOKEN = os.environ["BOT_TOKEN"]  # Бот токен
    ADMIN_ID = int(os.environ["ADMIN_ID"])  # Тек сен қосып/өшіресің

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # /start
    def start(update: Update, context: CallbackContext):
        update.message.reply_text("Сәлем 👋 Мен Minecraft серверлерін тексеретін ботпын!")

    # /add (тек админ)
    def add_server(update: Update, context: CallbackContext):
        if update.effective_user.id != ADMIN_ID:
            update.message.reply_text("⛔ Рұқсат жоқ!")
            return
        if not context.args:
            update.message.reply_text("Қолдану: /add <ip>")
            return
        ip = context.args[0]
        if ip in servers:
            update.message.reply_text("Бұл сервер бұрыннан бар ✅")
        else:
            servers[ip] = {"name": ip, "record": 0}
            update.message.reply_text(f"✅ Сервер қосылды: {ip}")

    # /nick (серверге атау беру)
    def nick_server(update: Update, context: CallbackContext):
        if len(context.args) < 2:
            update.message.reply_text("Қолдану: /nick <ip> <Атауы>")
            return
        ip = context.args[0]
        name = " ".join(context.args[1:])
        if ip not in servers:
            update.message.reply_text("Бұл IP табылмады ❌")
        else:
            servers[ip]["name"] = name
            update.message.reply_text(f"✅ {ip} үшін жаңа атау қойылды: {name}")

    # /remove (тек админ)
    def remove_server(update: Update, context: CallbackContext):
        if update.effective_user.id != ADMIN_ID:
            update.message.reply_text("⛔ Рұқсат жоқ!")
            return
        if not context.args:
            update.message.reply_text("Қолдану: /remove <ip>")
            return
        ip = context.args[0]
        if ip in servers:
            del servers[ip]
            update.message.reply_text(f"🗑 Сервер өшірілді: {ip}")
        else:
            update.message.reply_text("❌ Мұндай сервер жоқ")

    # /check (сервер тексеру)
    def check_server(update: Update, context: CallbackContext):
        if not context.args:
            update.message.reply_text("Қолдану: /check <ip>")
            return
        ip = context.args[0]
        if ip not in servers:
            update.message.reply_text("Бұл сервер тізімде жоқ ❌")
            return
        name = servers[ip]["name"]
        online, max_players, version = ping_server(ip)
        if online > servers[ip]["record"]:
            servers[ip]["record"] = online

        if online > 0:
            text = (
                f"Сервер атауы🏷️: {name}\n\n"
                f"Сервер күйі🖥️: Онлайн ✅\n\n"
                f"Сервердегі ойыншы саны👥: {online}/{max_players}\n\n"
                f"Сервердегі рекорд саны🏆: {servers[ip]['record']}\n\n"
                f"Айпи сервера🌐: {ip}\n\n"
                f"Версия Minecraft⚙️: {version}\n\n"
                f"Автор бота🤖: @BlodyPc"
            )
        else:
            text = (
                f"Сервер атауы🏷️: {name}\n\n"
                f"Сервер күйі🖥️: Офлайн ❌\n\n"
                f"Сервердегі ойыншы саны👥: 0/0\n\n"
                f"Сервердегі рекорд саны🏆: {servers[ip]['record']}\n\n"
                f"Айпи сервера🌐: {ip}\n\n"
                f"Версия Minecraft⚙️: Белгісіз\n\n"
                f"Автор бота🤖: @BlodyPc"
            )
        update.message.reply_text(text)

    # /list (чаттағы қолданушылар статистикасы)
    def list_users(update: Update, context: CallbackContext):
        if not user_messages:
            update.message.reply_text("Әзірге ешкім жазбаған ✉️")
            return
        text = "📊 Чаттағы белсенділік:\n\n"
        for user_id, count in user_messages.items():
            nick = user_nicks.get(user_id, "Анықталмаған")
            text += f"👤 {nick} — {count} хабарлама\n"
        update.message.reply_text(text)

    # +ник (қолданушыға ник орнату)
    def set_nick(update: Update, context: CallbackContext):
        if not context.args:
            update.message.reply_text("Қолдану: +ник <аты>")
            return
        nick = " ".join(context.args)
        user_id = update.effective_user.id
        user_nicks[user_id] = nick
        update.message.reply_text(f"✅ Сіздің никнейміңіз қосылды: {nick}")

    # Хабарламаларды санау
    def count_messages(update: Update, context: CallbackContext):
        user_id = update.effective_user.id
        user_messages[user_id] = user_messages.get(user_id, 0) + 1

    # Handler-лер
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("add", add_server))
    dp.add_handler(CommandHandler("nick", nick_server))
    dp.add_handler(CommandHandler("remove", remove_server))
    dp.add_handler(CommandHandler("check", check_server))
    dp.add_handler(CommandHandler("list", list_users))
    dp.add_handler(CommandHandler("ник", set_nick))  # +ник командасы
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, count_messages))

    updater.start_polling()
    updater.idle()

# =====================
# Бастау
# =====================
if __name__ == "__main__":
    Thread(target=run_flask).start()
    start_bot()
