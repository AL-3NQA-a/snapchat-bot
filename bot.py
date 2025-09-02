import os
import re
import requests
import telebot
import logging
from urllib.parse import quote
import time
import urllib3
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# تعطيل تحذيرات SSL للاختبار
urllib3.disable_warnings(InsecureRequestWarning)

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

# وظيفة للاتصال الآمن بالواجهات البرمجية
def safe_api_request(api_url, headers, timeout=15):
    try:
        session = requests.Session()
        session.trust_env = False  # مهم لبعض بيئات الاستضافة
        
        response = session.get(
            api_url, 
            headers=headers, 
            timeout=timeout, 
            verify=False,
            allow_redirects=True
        )
        return response
    except Exception as e:
        logger.error(f"فشل الاتصال بـ {api_url}: {e}")
        return None

# وظيفة للتحقق من وجود مستخدم سناب شات
def check_snapchat_user(username):
    try:
        response = safe_api_request(
            f"https://www.snapchat.com/add/{username}", 
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        )
        return response and response.status_code == 200
    except:
        return False

# وظيفة لاستخراج معلومات من قصص سناب شات
def get_snapchat_stories(username):
    try:
        logger.info(f"جلب قصص سناب شات للمستخدم: {username}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
        }
        
        # واجهات برمجة متعددة محدثة (تعمل على Koyeb)
        apis = [
            f"https://snapchat-downloader-api.herokuapp.com/stories/{username}",
            f"https://snapgram-api.herokuapp.com/api/snapchat/stories/{username}",
            f"https://snapchat-api.vercel.app/stories/{username}",
            f"https://api.social-downloader.com/snapchat/stories/{username}",
            f"https://social-downloader.p.rapidapi.com/snapchat/stories/{username}",
        ]
        
        for api_url in apis:
            try:
                logger.info(f"جرب واجهة برمجة التطبيقات: {api_url}")
                
                response = safe_api_request(api_url, headers)
                
                if response and response.status_code == 200:
                    data = response.json()
                    
                    # معالجة ردود مختلفة من واجهات البرمجة
                    if data and isinstance(data, list) and len(data) > 0:
                        logger.info(f"تم العثور على {len(data)} قصة من {api_url}")
                        return data
                    elif data and data.get('stories'):
                        stories = data.get('stories')
                        if stories and len(stories) > 0:
                            logger.info(f"تم العثور على {len(stories)} قصة من {api_url}")
                            return stories
                    elif data and data.get('data'):
                        stories_data = data.get('data')
                        if stories_data and len(stories_data) > 0:
                            logger.info(f"تم العثور على {len(stories_data)} قصة من {api_url}")
                            return stories_data
                    elif data and data.get('status') == 'success' and data.get('result'):
                        stories_result = data.get('result')
                        if stories_result and len(stories_result) > 0:
                            logger.info(f"تم العثور على {len(stories_result)} قصة من {api_url}")
                            return stories_result
                    elif data and data.get('success') and data.get('data'):
                        success_data = data.get('data')
                        if success_data and len(success_data) > 0:
                            logger.info(f"تم العثور على {len(success_data)} قصة من {api_url}")
                            return success_data
            
            except Exception as e:
                logger.error(f"فشلت واجهة برمجة التطبيقات: {api_url}, الخطأ: {e}")
                continue
        
        logger.warning("جميع واجهات البرمجة فشلت في جلب القصص")
        return None
        
    except Exception as e:
        logger.error(f"خطأ في جلب قصص سناب شات: {e}")
        return None

# وظيفة لتحميل الوسائط من رابط
def download_media(url, media_type):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = safe_api_request(url, headers)
        
        if response and response.status_code == 200:
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
@bot.message_handler(regexp=r"(^[a-zA-Z0-9._-]{3,}$|snapchat\.com/add/)")
def handle_snapchat_username(message):
    try:
        # استخراج اسم المستخدم من الرسالة
        text = message.text.strip()
        
        # معالجة الأشكال المختلفة للأسماء
        if "@" in text:
            username = text.replace("@", "")  # إزالة @ إذا وجد
        elif "snapchat.com/add/" in text:
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
        
        # التحقق أولاً إذا كان المستخدم موجوداً
        user_exists = check_snapchat_user(username)
        if not user_exists:
            bot.edit_message_text(f"❌ المستخدم @{username} غير موجود على سناب شات.", 
                                 message.chat.id, wait_msg.message_id)
            return
        
        # جلب القصص
        stories = get_snapchat_stories(username)
        
        if not stories or len(stories) == 0:
            bot.edit_message_text(f"❌ لم أتمكن من العثور على أي قصص للمستخدم @{username}. قد يكون:\n• الحساب خاصاً\n• لا يوجد قصص حالياً\n• هناك قيود على الحساب", 
                                 message.chat.id, wait_msg.message_id)
            return
        
        bot.edit_message_text(f"✅ تم العثور على {len(stories)} قصة! جاري التحميل...", 
                             message.chat.id, wait_msg.message_id)
        
        # تحميل وإرسال كل قصة
        success_count = 0
        for i, story in enumerate(stories, 1):
            try:
                media_url = story.get('url') or story.get('media_url') or story.get('video_url') or story.get('image_url')
                if not media_url:
                    continue
                
                media_type = 'video' if 'video' in media_url.lower() or '.mp4' in media_url.lower() else 'image'
                
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
                try:
                    bot.delete_message(message.chat.id, progress_msg.message_id)
                except:
                    pass
                
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
        try:
            bot.send_message(message.chat.id, "❌ حدث خطأ أثناء معالجة الطلب. حاول مرة أخرى.")
        except:
            pass

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
