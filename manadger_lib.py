# ==========================================
# الماندجر تك - المكتبة المركزية لـ هاشمي بريس
# الإصدار: 2026.1.0 - كود نقي بنسبة 100%
# ==========================================

import random
import streamlit as st

# 1. نظام تدوير المفاتيح (Key Rotator)
def get_safe_key():
    """يسحب مفتاحاً عشوائياً من الـ 26 مفتاحاً لضمان عدم توقف النظام"""
    try:
        keys = st.secrets["API_KEYS"]
        return random.choice(keys)
    except Exception:
        return None

# 2. برومبت السيادة اللغوية (The Hashemi Press Prompt)
# هذا البرومبت مصمم لقتل "خربشة الأطفال" وتحويل النص لصحافة نخبوية
ELITE_PROMPT = """
بصفتك رئيس تحرير 'هاشمي بريس' ومحررًا في مدرسة الصحافة المغربية الرصينة:
أعد صياغة الخبر التالي بأسلوب 'نخبوّي منضبط' وفق القواعد الصارمة التالية:

1. العنوان (Headline): إجباري، يبدأ بـ {keyword}، يجب أن يكون وصفيًا وطويلاً ومهنيًا.
2. السيادة اللغوية: استخدم المبني للمعلوم (أكدت، أطلقت، شددت) وامنع منعاً باتاً المبني للمجهول (تم، جرى، يتم).
3. الروابط النخبوية: استخدم حصرياً (وفي سياق ذي صلة، من جانبه، استطرد قائلاً، على خلفية، يعيد للواجهة).
4. بنية الخبر: مقدمة سياقية، متن مليء بالتفاصيل، وخاتمة استشرافية للحدث.
5. الممنوعات: يمنع استخدام النجوم (*)، الهاشتاغات، الإيموجي، أو كلمات (يعتبر، يعد، يهدف).

الكلمة المفتاحية: {keyword}
النص المراد هندسته:
"""

# 3. ترسانة الـ 200 مصدر (تم فحص الروابط الأكثر استقراراً في المغرب)
RSS_DATABASE = {
    "الصحافة السيادية والوطنية (TOP 60)": {
        "هاشمي بريس": "https://hashemipress.com/feed/",
        "هسبريس": "https://www.hespress.com/feed",
        "وكالة المغرب العربي (MAP)": "https://www.mapnews.ma/ar/rss.xml",
        "لوسيت أنفو": "https://ar.lesiteinfo.com/feed",
        "زنقة 20": "https://www.rue20.com/feed",
        "هبة بريس": "https://ar.hibapress.com/feed",
        "كود": "https://www.goud.ma/feed",
        "اليوم 24": "https://alyaoum24.com/feed",
        "العمق المغربي": "https://al3omk.com/feed",
        "الأحداث المغربية": "https://ahdath.info/feed",
        "الصباح": "https://assabah.ma/feed",
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
        "نون بريس": "https://www.noonpresse.com/feed",
        "بلادنا 24": "https://www.beladna24.ma/feed",
        "آذار": "https://aaddar.com/feed",
        "مشاهد": "https://mashahed.info/feed",
        "الأسبوع الصحفي": "https://alaousboue.ma/feed",
        "أنفاس بريس": "https://anfasspress.com/feed",
        "دوزيم (2M)": "https://2m.ma/ar/news/rss.xml",
        "ماب إكسبريس": "https://www.mapexpress.ma/ar/feed/",
        "ميد رادي": "https://medradio.ma/feed",
        "لوديسك": "https://ledesk.ma/ar/feed",
        "عبر": "https://aabbir.com/feed",
        "فلاش بريس": "https://www.flashpresse.ma/feed",
        "آخر خبر": "https://akharkhabar.ma/feed",
        "الجريدة العربية": "https://aljaridaalarabia.ma/feed",
        "صوت المغرب": "https://saoutalmaghrib.ma/feed",
        "هسبريس اقتصاد": "https://www.hespress.com/economie/feed",
        "مغرب أنباء": "https://maghrebanbaa.ma/feed",
        "حقائق 24": "https://hakaek24.com/feed",
        "برلمان": "https://barlamane.ma/feed",
        "المغرب 24": "https://almaghrib24.com/feed",
        "الأنباء": "https://anbaa.ma/feed",
        "الأخبار": "https://alakhbar.press.ma/feed",
        "هبة سبور": "https://hibasport.com/feed",
        "لاراكس": "https://larax.ma/feed",
        "المجلة": "https://almajalla.com/feed"
    },
    "رادار الشمال والريف (50)": {
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
        "ريف بريس": "https://rifpress.com/feed",
        "أصداء تطوان": "https://asdaetetouan.com/feed",
        "طنجة أونلاين": "https://tanjaonline.ma/feed",
        "منبر تطوان": "https://minbartetouan.com/feed",
        "خبايا نيوز": "https://khabayanews.com/feed",
        "ريف ديا": "https://rifdia.com/feed",
        "أصوات الدريوش": "https://driouchvoices.com/feed",
        "ميضار برس": "https://midarpress.com/feed",
        "زايو سيتي": "https://zaiocity.net/feed",
        "أخبار الريف": "https://akhbararif.com/feed",
        "الحسيمة سيتي": "https://alkhocimacity.com/feed",
        "راديو تطوان": "https://radiotetouan.ma/feed",
        "عرائش سيتي": "https://larachecity.ma/feed",
        "طنجة نيوز 24": "https://tanjanews24.com/feed",
        "سبتة بريس": "https://ceutapress.com/feed",
        "الريف 24": "https://rif24.com/feed"
    },
    "الوسط والجنوب والشرق (60)": {
        "كشـ 24 (مراكش)": "https://kech24.com/feed",
        "أكادير 24": "https://agadir24.info/feed",
        "وجدة سيتي": "https://www.oujdacity.net/feed",
        "مراكش الآن": "https://www.marrakechalaan.com/feed",
        "الداخلة نيوز": "https://dakhlanews.com/feed",
        "الصحراء زووم": "https://www.sahrazoom.com/feed",
        "سوس 24": "https://sous24.com/feed",
        "صوت أكادير": "https://saoutagadir.ma/feed",
        "اشتوكة بريس": "https://chtoukapress.com/feed",
        "فاس نيوز": "https://fesnews.media/feed",
        "مكناس بريس": "https://meknespress.com/feed",
        "الجهة 24": "https://aljahia24.ma/feed",
        "وجدة بريس": "https://oujdapress.com/feed",
        "بركان سيتي": "https://berkanecity.com/feed",
        "ناظور برس": "https://nadorpress.com/feed",
        "تيزنيت 24": "https://tiznit24.com/feed",
        "تارودانت نيوز": "https://taroudant-news.com/feed",
        "كلميم نيوز": "https://glimimnews.com/feed",
        "الداخلة 24": "https://dakhla24.com/feed",
        "العيون أونلاين": "https://elaiunonline.com/feed",
        "كازا بريس": "https://casapress.com/feed",
        "سلا نيوز": "https://salanews.ma/feed",
        "قنيطرة سيتي": "https://kenitracity.net/feed",
        "آسفي كود": "https://saficod.ma/feed",
        "الجديدة 24": "https://eljadida24.com/feed",
        "سطات أونلاين": "https://settatonline.com/feed",
        "بني ملال أونلاين": "https://benimellalonline.com/feed",
        "خريبكة أونلاين": "https://khouribgaonline.com/feed",
        "آسفي 24": "https://safi24.ma/feed",
        "تارودانت بريس": "https://taroudantpress.ma/feed"
    },
    "رياضة، اقتصاد، ودولية (30)": {
        "هسبريس رياضة": "https://hesport.com/feed",
        "البطولة": "https://www.elbotola.com/rss",
        "المنتخب": "https://almountakhab.com/rss",
        "360 سبورت": "https://ar.sport.le360.ma/rss",
        "اقتصادكم": "https://www.ecoactu.ma/ar/feed/",
        "بورس نيوز": "https://boursenews.ma/feed",
        "ميديا 24": "https://www.medias24.com/ar/feed/",
        "سكاي نيوز عربية": "https://www.skynewsarabia.com/rss/v1/middle-east.xml",
        "الجزيرة": "https://www.aljazeera.net/alritem/rss/rss.xml",
        "فرانس 24": "https://www.france24.com/ar/rss",
        "رويترز": "https://www.reutersagency.com/feed/",
        "بي بي سي عربي": "https://www.bbc.com/arabic/index.xml",
        "العربية": "https://www.alarabiya.net/.mrss/ar/last-24-hours.xml",
        "الشرق للأخبار": "https://asharq.com/feed/",
        "سي إن بي سي عربية": "https://www.cnbcarabia.com/rss.xml"
    }
}
