import telebot
import re
import time
import os
from flask import Flask
from threading import Thread

# Tumhara Bot Token
TOKEN = "8476815426:AAGKsAXYTosiDfVpj1CAoyY6mhswtjgF9Yo"
bot = telebot.TeleBot(TOKEN)

# Render Port Binding ke liye Dummy Flask Server
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is Alive and Running!"

def run_server():
    # Render automatically PORT assign karta hai
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# Warnings database
user_warnings = {}
MAX_WARNINGS = 3
BAN_DURATION = 3600  # 1 Ghanta

# SPAM WORDS PATTERN
SPAM_WORDS_PATTERN = re.compile(
    r'(?i)d[\s\.]*m|s[\s\.]*m[\s\.]*s|m[\s\.]*g[\s\.]*s|b[\s\.]*o[\s\.]*t|'
    r'p[\s\.]*a[\s\.]*i[\s\.]*s[\s\.]*a|e[\s\.]*a[\s\.]*r[\s\.]*n|'
    r'c[\s\.]*r[\s\.]*y[\s\.]*p[\s\.]*t[\s\.]*o|i[\s\.]*n[\s\.]*v[\s\.]*e[\s\.]*s[\s\.]*t|'
    r'l[\s\.]*o[\s\.]*t[\s\.]*t[\s\.]*e[\s\.]*r[\s\.]*y|p[\s\.]*r[\s\.]*o[\s\.]*f[\s\.]*i[\s\.]*t|'
    r's[\s\.]*u[\s\.]*b[\s\.]*s[\s\.]*c[\s\.]*r[\s\.]*i[\s\.]*b[\s\.]*e|f[\s\.]*o[\s\.]*l[\s\.]*l[\s\.]*o[\s\.]*w|'
    r'c[\s\.]*a[\s\.]*s[\s\.]*i[\s\.]*n[\s\.]*o|b[\s\.]*e[\s\.]*t[\s\.]*t[\s\.]*i[\s\.]*n[\s\.]*g|'
    r'f[\s\.]*r[\s\.]*e[\s\.]*e[\s\.]*d[\s\.]*i[\s\.]*a[\s\.]*m[\s\.]*o[\s\.]*n[\s\.]*d'
)

LINK_PATTERN = re.compile(r'(?i)(?:https?://|www\.|t\.me/|bit\.ly/|cutt\.ly/)[^\s]+')

def warn_and_punish(message, reason):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    chat_id = message.chat.id
    
    try:
        # Check if user is Admin
        member = bot.get_chat_member(chat_id, user_id)
        if member.status in ['administrator', 'creator']:
            return
    except Exception as e:
        print(f"Admin check error: {e}")
        return

    # Delete Spam Message
    try:
        bot.delete_message(chat_id, message.message_id)
    except Exception as e:
        print(f"Delete message error: {e}")

    # Process Warning
    user_warnings[user_id] = user_warnings.get(user_id, 0) + 1
    count = user_warnings[user_id]

    if count >= MAX_WARNINGS:
        until_date = int(time.time()) + BAN_DURATION
        try:
            bot.ban_chat_member(chat_id, user_id, until_date=until_date)
            bot.send_message(chat_id, f"🚫 @{username} ko bar-bar spamming ke liye 1 ghante ke liye block kiya gaya.")
            user_warnings[user_id] = 0
        except Exception as e:
            print(f"Ban error: {e}")
    else:
        try:
            bot.send_message(chat_id, f"⚠️ @{username}, Do not try again! No spamming allowed.\nReason: {reason}\nWarning: {count}/{MAX_WARNINGS}")
        except Exception as e:
            print(f"Warning send error: {e}")

@bot.message_handler(content_types=['new_chat_members'])
def handle_bots(message):
    for member in message.new_chat_members:
        if member.is_bot and member.id != bot.get_me().id:
            try:
                bot.ban_chat_member(message.chat.id, member.id)
                bot.send_message(message.chat.id, f"🤖 Unauthorized bot removed.")
            except Exception as e:
                print(f"Bot kick error: {e}")

@bot.message_handler(content_types=['photo', 'video', 'sticker', 'document'])
def handle_media(message):
    warn_and_punish(message, "Images/Media allowed nahi hai.")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    text = message.text
    
    if LINK_PATTERN.search(text):
        warn_and_punish(message, "Links/Promotion prohibited.")
        return

    if SPAM_WORDS_PATTERN.search(text):
        warn_and_punish(message, "Spam words detected.")
        return

    if len(text) > 600:
        warn_and_punish(message, "Too long message (Spam).")

if __name__ == "__main__":
    print("Starting Web Server...")
    Thread(target=run_server).start()
    
    print("Bot is polling...")
    # Polling mein retry logic add kiya gaya hai taaki crash na ho
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)
