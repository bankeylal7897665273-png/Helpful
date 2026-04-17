import telebot
import re
import time

# Tumhara Bot Token
TOKEN = "8476815426:AAGKsAXYTosiDfVpj1CAoyY6mhswtjgF9Yo"
bot = telebot.TeleBot(TOKEN)

# Warnings database
user_warnings = {}
MAX_WARNINGS = 3
BAN_DURATION = 3600  # 1 Ghanta

# 1. PEHLE SE BHI ZAYADA SPAM WORDS (Regex based)
# Isme DM, SMS, MGS, BOT ke saath Earning, Crypto, Casino, aur Abusive words added hain
SPAM_WORDS_PATTERN = re.compile(
    r'(?i)d[\s\.]*m|s[\s\.]*m[\s\.]*s|m[\s\.]*g[\s\.]*s|b[\s\.]*o[\s\.]*t|'  # Jo tumne bataye
    r'p[\s\.]*a[\s\.]*i[\s\.]*s[\s\.]*a|e[\s\.]*a[\s\.]*r[\s\.]*n|'        # Earning/Paisa
    r'c[\s\.]*r[\s\.]*y[\s\.]*p[\s\.]*t[\s\.]*o|i[\s\.]*n[\s\.]*v[\s\.]*e[\s\.]*s[\s\.]*t|' # Crypto/Invest
    r'l[\s\.]*o[\s\.]*t[\s\.]*t[\s\.]*e[\s\.]*r[\s\.]*y|p[\s\.]*r[\s\.]*o[\s\.]*f[\s\.]*i[\s\.]*t|' # Lottery
    r's[\s\.]*u[\s\.]*b[\s\.]*s[\s\.]*c[\s\.]*r[\s\.]*i[\s\.]*b[\s\.]*e|f[\s\.]*o[\s\.]*l[\s\.]*l[\s\.]*o[\s\.]*w|' # Promo
    r'c[\s\.]*a[\s\.]*s[\s\.]*i[\s\.]*n[\s\.]*o|b[\s\.]*e[\s\.]*t[\s\.]*t[\s\.]*i[\s\.]*n[\s\.]*g|' # Betting
    r'f[\s\.]*r[\s\.]*e[\s\.]*e[\s\.]*d[\s\.]*i[\s\.]*a[\s\.]*m[\s\.]*o[\s\.]*n[\s\.]*d' # Free Diamonds
)

# 2. Telegram Links aur baaki links
LINK_PATTERN = re.compile(r'(?i)(?:https?://|www\.|t\.me/|bit\.ly/|cutt\.ly/)[^\s]+')

def warn_and_punish(message, reason):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    chat_id = message.chat.id
    
    # Ignore Admins (Admin ko block nahi karega)
    member = bot.get_chat_member(chat_id, user_id)
    if member.status in ['administrator', 'creator']:
        return

    # Delete Spam Message
    try:
        bot.delete_message(chat_id, message.message_id)
    except:
        pass

    # Process Warning
    user_warnings[user_id] = user_warnings.get(user_id, 0) + 1
    count = user_warnings[user_id]

    if count >= MAX_WARNINGS:
        until_date = int(time.time()) + BAN_DURATION
        bot.ban_chat_member(chat_id, user_id, until_date=until_date)
        bot.send_message(chat_id, f"🚫 @{username} ko bar-bar spamming ke liye 1 ghante ke liye block kiya gaya.")
        user_warnings[user_id] = 0
    else:
        bot.send_message(chat_id, f"⚠️ @{username}, Do not try again! No spamming allowed.\nReason: {reason}\nWarning: {count}/{MAX_WARNINGS}")

# Auto-delete other bots if added by non-admin
@bot.message_handler(content_types=['new_chat_members'])
def handle_bots(message):
    for member in message.new_chat_members:
        if member.is_bot and member.id != bot.get_me().id:
            bot.ban_chat_member(message.chat.id, member.id)
            bot.send_message(message.chat.id, f"🤖 Unauthorized bot removed.")

# Delete Photos/Videos
@bot.message_handler(content_types=['photo', 'video', 'sticker', 'document'])
def handle_media(message):
    warn_and_punish(message, "Images/Media allowed nahi hai.")

# Handle Text and Links
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    text = message.text
    
    # Check for Links
    if LINK_PATTERN.search(text):
        warn_and_punish(message, "Links/Promotion prohibited.")
        return

    # Check for Spam Words
    if SPAM_WORDS_PATTERN.search(text):
        warn_and_punish(message, "Spam words detected.")
        return

    # Anti-Flood (Jitna bada message, utna spam risk)
    if len(text) > 600:
        warn_and_punish(message, "Too long message (Spam).")

print("Bot is running...")
bot.infinity_polling()
