# ==========================================
# manadger_lib.py - مستودع أسلحة الماندجر تك
# الإصدار السيادي V27.8 - 2026
# ==========================================

import random
import streamlit as st

# 1. نظام تدوير المفاتيح الـ 26
def get_safe_key():
    try:
        keys = st.secrets["API_KEYS"]
        return random.choice(keys)
    except:
        return None

# 2. برومبت السيادة اللغوية (Hashemi Press Elite Prompt)
# تم الضبط لضمان العنوان في السطر الأول وحظر كلمة "هاشمي بريس:" في البداية
ELITE_PROMPT = """
بصفتك رئيس تحرير 'هاشمي بريس': أعد صياغة الخبر بأسلوب 'نخبوّي رصين' مع الالتزام الصارم بالهيكل التالي:

القواعد الذهبية:
1. السطر الأول: ضع عنواناً احترافياً يبدأ بـ {keyword}، يكون وصفيًا، طويلاً، وجذاباً.
2. السطر الثاني: اترك سطرًا فارغًا تمامًا.
3. السطر الثالث وما بعده: متن المقال بأسلوب صحفي رصين (جمل مركبة، روابط نخبوية، مبني للمعلوم).

الممنوعات:
- ممنوع تماماً البدء بعبارة "هاشمي بريس:" أو "العنوان:". ابدأ بالعنوان مباشرة.
- ممنوع استخدام النجوم (*)، الهاشتاغات، أو كلمات الركاكة (يعتبر، يعد، يهدف).

الكلمة المفتاحية: {keyword}
المحتوى المراد معالجته:
"""

# 3. ترسانة الـ 200 مصدر (المغرب وجوارها)
RSS_DATABASE = {
    "الصحافة السيادية والوطنية": {
        "هاشمي بريس": "https://hashemipress.com/feed/",
        "هسبريس": "https://www.hespress.com/feed",
        "MAP وكالة الأنباء": "https://www.mapnews.ma/ar/rss.xml",
        "لوسيت أنفو": "https://ar.lesiteinfo.com/feed",
        "زنقة 20": "https://www.rue20.com/feed",
        "هبة بريس": "https://ar.hibapress.com/feed",
        "كود": "https://www.goud.ma/feed",
        "اليوم 24": "https://alyaoum24.com/feed",
        "العمق المغربي": "https://al3omk.com/feed",
        "مدار 21": "https://madar21.com/feed",
        "برلمان.كوم": "https://www.barlamane.com/feed",
        "تليكسبريس": "https://telexpresse.com/feed",
        "آشكاين": "https://achkayen.com/feed",
        "فبراير": "https://www.febrayer.com/feed",
        "الجريدة 24": "https://aljarida24.ma/feed",
        "لكم 2": "https://lakome2.com/feed",
        "سفيركم": "https://safir24.com/feed",
        "بناصا": "https://banassa.com/feed",
        "منارة": "https://www.menara.ma/ar/rss",
        "الصحراء المغربية": "https://assahra.ma/rss",
        "بيان اليوم": "https://bayanealyaoume.press.ma/feed",
        "الاتحاد الاشتراكي": "https://alittihad.press.ma/feed",
        "رسالة الأمة": "https://الرسالة.ma/feed",
        "بلادنا 24": "https://www.beladna24.ma/feed",
        "آذار": "https://aaddar.com/feed",
        "مشاهد": "https://mashahed.info/feed",
        "دوزيم 2M": "https://2m.ma/ar/news/rss.xml",
        "ميد رادي": "https://medradio.ma/feed",
        "لوديسك": "https://ledesk.ma/ar/feed",
        "عبر": "https://aabbir.com/feed",
        "صوت المغرب": "https://saoutalmaghrib.ma/feed",
        "مغرب أنباء": "https://maghrebanbaa.ma/feed"
    },
    "رادار الشمال والريف": {
        "بريس تطوان": "https://presstetouan.com/feed",
        "طنجة 24": "https://tanja24.com/feed",
        "شمال بوست": "https://chamalpost.net/feed",
        "طنجة نيوز": "https://tanjanews.com/feed",
        "صدى تطوان": "https://sadatetouan.com/feed",
        "تطوان بريس": "https://tetouanpress.ma/feed",
        "العرائش نيوز": "https://larachenews.com/feed",
        "دليل الريف": "https://www.dalil-rif.com/rss.xml",
        "ريف بوست": "https://rifpost.com/feed",
        "طنجة أنتر": "https://tanjainter.com/feed",
        "وزان بريس": "https://ouazzanepress.com/feed",
        "شفشاون بريس": "https://chefchaouenpress.com/feed",
        "تطوان نيوز": "https://tetouannews.com/feed",
        "العرائش 24": "https://larache24.com/feed",
        "أصداء تطوان": "https://asdaetetouan.com/feed",
        "منبر تطوان": "https://minbartetouan.com/feed"
    },
    "الجهات والشرق والجنوب": {
        "كشـ 24": "https://kech24.com/feed",
        "أكادير 24": "https://agadir24.info/feed",
        "وجدة سيتي": "https://www.oujdacity.net/feed",
        "مراكش الآن": "https://www.marrakechalaan.com/feed",
        "الداخلة نيوز": "https://dakhlanews.com/feed",
        "الصحراء زووم": "https://www.sahrazoom.com/feed",
        "سوس 24": "https://sous24.com/feed",
        "فاس نيوز": "https://fesnews.media/feed",
        "ناظور سيتي": "https://www.nadorcity.com/rss/",
        "تارودانت نيوز": "https://taroudant-news.com/feed"
    },
    "رياضة واقتصاد ودولية": {
        "هسبريس رياضة": "https://hesport.com/feed",
        "البطولة": "https://www.elbotola.com/rss",
        "المنتخب": "https://almountakhab.com/rss",
        "اقتصادكم": "https://www.ecoactu.ma/ar/feed/",
        "سكاي نيوز": "https://www.skynewsarabia.com/rss/v1/middle-east.xml",
        "الجزيرة": "https://www.aljazeera.net/alritem/rss/rss.xml",
        "فرانس 24": "https://www.france24.com/ar/rss",
        "العربية": "https://www.alarabiya.net/.mrss/ar/last-24-hours.xml"
    }
}
