import os
import time
import telebot
import yt_dlp

# ================== SOZLAMALAR ==================
TOKEN = "8968746212:AAFvAXU-DwNWWpwIFI03NfC6cd3bh2t3YyE"  # @BotFather'dan Copy qilgan tokeningizni shu yerga qo'ying

bot = telebot.TeleBot(TOKEN)

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)


@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(
        message,
        "Salom! 👋\n"
        "Menga Instagram post, Reels yoki rasm linkini yuboring — "
        "men uni sizga video yoki rasm shaklida jo'natib beraman.\n\n"
        "Eslatma: faqat ochiq (public) sahifalardan yuklab olish mumkin."
    )


@bot.message_handler(func=lambda m: m.text and "instagram.com" in m.text)
def download_instagram(message):
    url = message.text.strip()
    chat_id = message.chat.id

    status_msg = bot.reply_to(message, "⏳ Yuklab olinmoqda, biroz kuting...")

    # Har bir yuklama uchun alohida fayl nomi (bir-birini bosib qolmasligi uchun)
    output_template = os.path.join(DOWNLOAD_DIR, f"{chat_id}_{int(time.time())}.%(ext)s")

    ydl_opts = {
        "outtmpl": output_template,
        "format": "best",
        "quiet": True,
        "noplaylist": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        if not os.path.exists(filename):
            bot.edit_message_text("❌ Fayl topilmadi. Link noto'g'ri yoki sahifa yopiq bo'lishi mumkin.",
                                   chat_id, status_msg.message_id)
            return

        ext = os.path.splitext(filename)[1].lower()

        with open(filename, "rb") as f:
            if ext in [".mp4", ".mov", ".mkv"]:
                bot.send_video(chat_id, f)
            elif ext in [".jpg", ".jpeg", ".png", ".webp"]:
                bot.send_photo(chat_id, f)
            else:
                bot.send_document(chat_id, f)

        bot.delete_message(chat_id, status_msg.message_id)

        # Vaqtinchalik faylni tozalash
        os.remove(filename)

    except Exception as e:
        print(f"Xato: {e}")
        bot.edit_message_text(
            "❌ Yuklab bo'lmadi. Sabablari:\n"
            "- Link noto'g'ri\n"
            "- Sahifa yopiq (private)\n"
            "- Instagram vaqtincha bloklagan\n\n"
            "Boshqa link bilan urinib ko'ring.",
            chat_id, status_msg.message_id
        )


@bot.message_handler(func=lambda m: True)
def echo(message):
    bot.reply_to(message, "Menga Instagram post/Reels linkini yuboring 📎")


if __name__ == "__main__":
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"Xato chiqdi: {e}")
            time.sleep(5)