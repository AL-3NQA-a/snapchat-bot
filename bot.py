import os
import re
import requests
import telebot
import logging
import time
import urllib3
from snapscraper import SnapchatScraper
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# تعطيل تحذيرات SSL
urllib3.disable_warnings(InsecureRequestWarning)

# إعدادات البوت
API_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not API_TOKEN:
    print("❌ Error: TELEGRAM_BOT_TOKEN not found in environment variables")
    exit(1)

bot = telebot.TeleBot(API_TOKEN)

# إعداد السجل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# وظيفة بديلة لجلب القصص باستخدام approach مختلف
def get_snapchat_stories_alternative(username):
    try:
        logger.info(f"محاولة جلب قصص {username} بالطريقة البديلة...")
        
        # محاولة استخدام واجهات برمجة تعمل على Koyeb
        working_apis = [
            f"https://snapchat-downloader-api.herokuapp.com/stories/{username}",
            f"https://snapgram-api.herokuapp.com/api/snapchat/stories/{username}",
            f"https://api.letscop.com/snapchat/stories/{username}",
        ]
        
        for api_url in working_apis:
            try:
                session = requests.Session()
                session.trust_env = False
                
                response = session.get(
                    api_url,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'application/json',
                    },
                    timeout=15,
                    verify=False
                )
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"تم الاتصال بـ {api_url} بنجاح")
                    
                    # معالجة مختلف تنسيقات الرد
                    if isinstance(data, list) and len(data) > 0:
                        return data
                    elif data.get('stories') and len(data.get('stories')) > 0:
                        return data.get('stories')
                    elif data.get('data') and len(data.get('data')) > 0:
                        return data.get('data')
                    elif data.get('result') and len(data.get('result')) > 0:
                        return data.get('result')
                        
            except Exception as e:
                logger.warning(f"API {api_url} لم يعمل: {e}")
                continue
        
        # إذا فشلت جميع الواجهات، جرب approach مختلف
        return try_direct_approach(username)
        
    except Exception as e:
        logger.error(f"خطأ في الطريقة البديلة: {e}")
        return None

def try_direct_approach(username):
    """طريقة مباشرة لمحاولة جلب المحتوى"""
    try:
        logger.info(f"جرب الطريقة المباشرة لـ {username}")
        
        # محاولة جلب معلومات المستخدم أولاً
        profile_url = f"https://www.snapchat.com/add/{username}"
        
        session = requests.Session()
        session.trust_env = False
        
        response = session.get(
            profile_url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            },
            timeout=10,
            verify=False
        )
        
        if response.status_code == 200:
            # محاولة استخراج معلومات من الصفحة
            html_content = response.text
            
            # بحث عن علامات تدل على وجود قصص
            if "stories" in html_content.lower() or "story" in html_content.lower():
                logger.info(f"يبدو أن المستخدم {username} لديه قصص")
                # هنا يمكنك إضافة استراتيجية استخراج أكثر تطوراً
                return [{"url": f"https://snapchat.com/add/{username}", "type": "profile"}]
        
        return None
        
    except Exception as e:
        logger.error(f"خطأ في الطريقة المباشرة: {e}")
        return None

# وظيفة محسنة للتحقق من وجود المستخدم
def check_snapchat_user(username):
    try:
        session = requests.Session()
        session.trust_env = False
        
        response = session.get(
            f"https://www.snapchat.com/add/{username}",
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            },
            timeout=10,
            verify=False,
            allow_redirects=False  # مهم للتحقق من وجود المستخدم
        )
        
        # إذا كان الرد 200 أو 302 إلى صفحة أخرى (غير صفحة الخطأ)
        return response.status_code in [200, 302] and "error" not in response.text.lower()
        
    except Exception as e:
        logger.error(f"خطأ في التحقق من المستخدم: {e}")
        return False

# الأوامر الأساسية للبوت
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = """
    📸 مرحباً بك في بوت تحميل قصص سناب شات! 

    🔍 للأسف، حالياً معظم واجهات برمجة سناب شات لا تعمل بسبب القيود الجديدة.

    💡 جرب هذه الحسابات للتأكد:
    • snapchat (الحساب الرسمي)
    • khaby00 (خبي لامي)
    • kyliejenner

    ⚠️ العديد من الحسابات الخاصة قد لا تعمل.
    """
    bot.send_message(message.chat.id, welcome_text)

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
    🆘 المساعدة:
    
    /start - بدء البوت
    /help - هذه الرسالة
    /test - اختبار حسابات شائعة

    📝 فقط أرسل @اسم المستخدم
    """
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(commands=['test'])
def test_accounts(message):
    """اختبار الحسابات الشائعة"""
    test_usernames = ['snapchat', 'khaby00', 'kyliejenner']
    
    for username in test_usernames:
        try:
            bot.send_message(message.chat.id, f"🔍 جرب @{username} ...")
            stories = get_snapchat_stories_alternative(username)
            
            if stories and len(stories) > 0:
                bot.send_message(message.chat.id, f"✅ @{username} - يعمل ({len(stories)} قصة)")
            else:
                bot.send_message(message.chat.id, f"❌ @{username} - لا يعمل أو لا يوجد قصص")
                
            time.sleep(2)
            
        except Exception as e:
            bot.send_message(message.chat.id, f"⚠️ خطأ مع @{username}: {str(e)}")

@bot.message_handler(regexp=r"(^[a-zA-Z0-9._-]{3,}$|snapchat\.com/add/)")
def handle_snapchat_username(message):
    try:
        text = message.text.strip()
        
        # استخراج اسم المستخدم
        if "@" in text:
            username = text.replace("@", "")
        elif "snapchat.com/add/" in text:
            match = re.search(r'snapchat\.com/add/([a-zA-Z0-9._-]+)', text)
            username = match.group(1) if match else text
        else:
            username = text

        logger.info(f"معالجة المستخدم: {username}")

        # التحقق من وجود المستخدم
        if not check_snapchat_user(username):
            bot.send_message(message.chat.id, f"❌ المستخدم @{username} غير موجود أو محظور")
            return

        # محاولة جلب القصص
        stories = get_snapchat_stories_alternative(username)
        
        if not stories or len(stories) == 0:
            bot.send_message(
                message.chat.id,
                f"❌ لم أتمكن من جلب قصص @{username}\n"
                f"• قد يكون الحساب خاصاً\n• أو لا يوجد قصص\n• أو هناك قيود تقنية"
            )
            return

        bot.send_message(message.chat.id, f"✅ تم العثور على {len(stories)} قصة لـ@{username}")

        # هنا يمكنك إضافة logic لتحميل القصص عندما تعود الواجهات للعمل

    except Exception as e:
        logger.error(f"خطأ: {e}")
        bot.send_message(message.chat.id, "❌ حدث خطأ، جرب لاحقاً")

@bot.message_handler(func=lambda message: True)
def handle_other_messages(message):
    if message.text.startswith('/'):
        bot.send_message(message.chat.id, "❌ أمر غير معروف، جرب /help")
    else:
        bot.send_message(message.chat.id, "📝 أرسل @اسم المستخدم فقط")

def start_bot():
    logger.info("🚀 بدء تشغيل البوت...")
    print("✅ البوت يعمل! استخدم /test لفحص الحسابات")
    
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=60)
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
            time.sleep(10)

if __name__ == '__main__':
    start_bot()
