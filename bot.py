import os
import re
import requests
import telebot
import logging
from urllib.parse import quote
import time

# إعدادات البوت - سيتم أخذ التوكن من متغير البيئة
API_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not API_TOKEN:
    print("❌ Error: TELEGRAM_BOT_TOKEN not found in environment variables")
    exit(1)

bot = telebot.TeleBot(API_TOKEN)

# إعداد السجل logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# وظيفة لاستخراج معلومات من قصص سناب شات
def get_snapchat_stories(username):
    try:
        logger.info(f"جلب قصص سناب شات للمستخدم: {username}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
        }
        
        # واجهات برمجة متعددة لسناب شات
        apis = [
            f"https://snapchat-downloader-api.herokuapp.com/stories/{username}",
            f"https://api.snapchat-downloader.com/stories/{username}",
            f"https://snapchat-downloader.com/api/stories/{username}",
        ]
        
        for api_url in apis:
            try:
                logger.info(f"جرب واجهة برمجة التطبيقات: {api_url}")
                response = requests.get(api_url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data and isinstance(data, list) and len(data) > 0:
                        logger.info(f"تم العثور على {len(data)} قصة")
                        return data
                    elif data and data.get('stories'):
                        logger.info(f"تم العثور على {len(data.get('stories'))} قصة")
                        return data.get('stories')
            
            except Exception as e:
                logger.error(f"فشلت واجهة برمجة التطبيقات: {api_url}, الخطأ: {e}")
                continue
        
        return None
        
    except Exception as e:
        logger.error(f"خطأ في جلب قصص سناب شات: {e}")
        return None

# وظيفة لتحميل الوسائط من رابط
def download_media(url, media_type):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, stream=True, timeout=30)
        
        if response.status_code == 200:
            # إنشاء مجلد مؤقت للتحميل
            timestamp = int(time.time())
            filename = f"{media_type}_{timestamp}.{'mp4' if media_type == 'video' else 'jpg'}"
            
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return filename
        else:
            return None
            
    except Exception as e:
        logger.error(f"خطأ في تحميل الوسائط: {e}")
        return None

# أمر البدء /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = """
    📸 مرحباً بك في بوت تحميل قصص سناب شات! 📸

    أرسل لي اسم مستخدم سناب شات (بدون @) وسأحاول جلب جميع قصصه المنشورة.

    📌 مثال: 
    username
    أو
    https://www.snapchat.com/add/username

    ❗ ملاحظة: قد لا تعمل بعض الحسابات بسبب الخصوصية أو القيود.
    
    📊 لفحص حالة البوت: /status
    """
    bot.send_message(message.chat.id, welcome_text)

# أمر المساعدة /help
@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
    📋 قائمة الأوامر المتاحة:
    
    /start - بدء التشغيل
    /help - عرض المساعدة
    /status - فحص حالة البوت
    
    فقط أرسل اسم مستخدم سناب شات لتحميل قصصه.
    """
    bot.send_message(message.chat.id, help_text)

# أمر فحص الحالة /status
@bot.message_handler(commands=['status'])
def check_status(message):
    try:
        bot.send_message(message.chat.id, "✅ البوت يعمل بشكل طبيعي! أرسل اسم مستخدم سناب شات لتحميل قصصه.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ هناك مشكلة في البوت: {str(e)}")

# معالجة أسماء مستخدمين سناب شات
@bot.message_handler(regexp="(^[a-zA-Z0-9._-]{3,}$|snapchat\.com/add/)")
def handle_snapchat_username(message):
    try:
        # استخراج اسم المستخدم من الرسالة
        text = message.text.strip()
        
        # إذا كان رابطًا، استخرج اسم المستخدم
        if "snapchat.com/add/" in text:
            username_match = re.search(r'snapchat\.com/add/([a-zA-Z0-9._-]+)', text)
            if username_match:
                username = username_match.group(1)
            else:
                bot.send_message(message.chat.id, "❌ لم أتمكن العثور على اسم مستخدم صحيح في الرابط.")
                return
        else:
            username = text
        
        logger.info(f"تم استقبال اسم مستخدم: {username}")
        
        # إظهار رسالة الانتظار
        wait_msg = bot.send_message(message.chat.id, f"⏳ جاري البحث عن قصص @{username}...")
        
        # جلب القصص
        stories = get_snapchat_stories(username)
        
        if not stories or len(stories) == 0:
            bot.edit_message_text(f"❌ لم أتمكن من العثور على أي قصص للمستخدم @{username}. قد يكون الحساب خاصاً أو بدون قصص.", 
                                 message.chat.id, wait_msg.message_id)
            return
        
        bot.edit_message_text(f"✅ تم العثور على {len(stories)} قصة! جاري التحميل...", 
                             message.chat.id, wait_msg.message_id)
        
        # تحميل وإرسال كل قصة
        success_count = 0
        for i, story in enumerate(stories, 1):
            try:
                media_url = story.get('url') or story.get('media_url') or story.get('video_url') or story.get('image_url')
                media_type = 'video' if 'video' in media_url.lower() or '.mp4' in media_url.lower() else 'image'
                
                if not media_url:
                    continue
                
                # إرسال حالة التحميل
                progress_msg = bot.send_message(message.chat.id, f"📥 جاري تحميل القصة {i} من {len(stories)}...")
                
                # تحميل الميديا
                filename = download_media(media_url, media_type)
                
                if filename:
                    # إرسال الميديا
                    if media_type == 'video':
                        with open(filename, 'rb') as media_file:
                            bot.send_video(message.chat.id, media_file, 
                                          caption=f"📸 قصة {i} من @{username}")
                    else:
                        with open(filename, 'rb') as media_file:
                            bot.send_photo(message.chat.id, media_file,
                                          caption=f"📸 قصة {i} من @{username}")
                    
                    # حذف الملف المؤقت
                    os.remove(filename)
                    success_count += 1
                
                # حذف رسالة التقدم
                bot.delete_message(message.chat.id, progress_msg.message_id)
                
                # وقت راحة بين القصص
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"خطأ في معالجة القصة {i}: {e}")
                continue
        
        # إرسال ملخص
        bot.edit_message_text(f"✅ تم تحميل {success_count} من أصل {len(stories)} قصة بنجاح لـ@{username}!", 
                             message.chat.id, wait_msg.message_id)
        
    except Exception as e:
        logger.error(f"خطأ في معالجة طلب سناب شات: {e}")
        bot.send_message(message.chat.id, "❌ حدث خطأ أثناء معالجة الطلب. حاول مرة أخرى.")

# معالجة الرسائل الأخرى
@bot.message_handler(func=lambda message: True)
def handle_other_messages(message):
    if message.text.startswith('/'):
        bot.send_message(message.chat.id, "❌ أمر غير معروف. استخدم /start لمعرفة كيفية الاستخدام.")
    else:
        bot.send_message(message.chat.id, "📨 لتحميل قصص سناب شات، أرسل اسم المستخدم فقط (بدون @).")

# وظيفة لإعادة التشغيل التلقائي في حالة الفشل
def start_bot():
    logger.info("✅ بدء تشغيل بوت تحميل قصص سناب شات...")
    print("✅ بدء تشغيل بوت تحميل قصص سناب شات...")
    
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=60)
        except Exception as e:
            logger.error(f"❌ انتهت عملية البوت بالخطأ: {e}")
            logger.info("🔄 إعادة تشغيل البوت خلال 10 ثوان...")
            time.sleep(10)

if __name__ == '__main__':
    start_bot()
