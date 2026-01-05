import streamlit as st
import feedparser
import trafilatura
from groq import Groq
import concurrent.futures
import json
import os
import socket
import requests
from datetime import datetime

# ==========================================
# 0. الإعدادات العامة والهوية
# ==========================================
SYSTEM_VERSION = "V17.0_MEGA_SOURCES"
ACCESS_PASSWORD = "Manager_Tech_2026"
DB_FILE = "news_db_v17.json"
st.set_page_config(page_title="وكيل يقين الصحفي - 50 مصدراً", page_icon="🗞️", layout="wide")
socket.setdefaulttimeout(35)

# ==========================================
# 1. محرك الصياغة (Professional SEO Writer)
# ==========================================
def rewrite_pro_seo(text, tone, keyword):
    try:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        prompt = f"""أنت رئيس تحرير خبير في Yoast SEO. صغ مقالاً احترافياً نابضاً بالحياة.
        الكلمة المفتاحية: {keyword}
        القواعد الصارمة:
        - طول الجملة: أقل من 18 كلمة (استخدم النقطة باستمرار).
        - المبني للمعلوم: اجعل الفاعل بطل الجملة دائماً.
        - كلمات الانتقال: نوع الروابط (بالموازاة مع، وفي خضم ذلك، علاوة على).
        - التنسيق: عناوين فرعية نصية، فقرات قصيرة جداً، لا رموز Markdown، لا كلمة مغناطيسياً.
        الأسلوب: {tone}.
        النص: {text[:3800]}"""
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.4
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"خطأ في الذكاء الاصطناعي: {str(e)}"

# ==========================================
# 2. نظام الحماية (Login)
# ==========================================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown("<h2 style='text-align:center;'>🔐 نظام يقين المحصن - مجموعة الماندجر</h2>", unsafe_allow_html=True)
    pwd = st.text_input("أدخل مفتاح الوصول:", type="password")
    if st.button("دخول"):
        if pwd == ACCESS_PASSWORD:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("مفتاح الوصول غير صحيح!")
    st.stop()

# ==========================================
# 3. القائمة العملاقة (50 مصدراً إخبارياً)
# ==========================================
RSS_SOURCES = {
    "الصحافة الوطنية (20 مصدر) 🇲🇦": {
        "هسبريس": "https://www.hespress.com/feed", "شوف تيفي": "https://chouftv.ma/feed",
        "العمق المغربي": "https://al3omk.com/feed", "زنقة 20": "https://www.rue20.com/feed",
        "هبة بريس": "https://ar.hibapress.com/feed", "اليوم 24": "https://alyaoum24.com/feed",
        "كود": "https://www.goud.ma/feed", "برلمان.كوم": "https://www.barlamane.com/feed",
        "تليكسبريس": "https://telexpresse.com/feed", "Le360 عربي": "https://ar.le360.ma/rss",
        "فبراير": "https://www.febrayer.com/feed", "آشكاين": "https://achkayen.com/feed",
        "الجريدة 24": "https://aljarida24.ma/feed", "لكم": "https://lakome2.com/feed",
        "عبر": "https://aabbir.com/feed", "سفيركم": "https://safir24.com/feed",
        "باناصا": "https://banassa.com/feed", "الأيام 24": "https://www.alayam24.com/feed",
        "الصباح": "https://assabah.ma/feed", "الأحداث المغربية": "https://ahdath.info/feed"
    },
    "أخبار الشمال والجهات (15 مصدر) 🌊": {
        "شمال بوست": "https://chamalpost.net/feed", "بريس تطوان": "https://presstetouan.com/feed",
        "طنجة 24": "https://tanja24.com/feed", "تطوان بريس": "https://tetouanpress.ma/feed",
        "طنجة نيوز": "https://tanjanews.com/feed", "كاب 24": "https://cap24.tv/feed",
        "صدى تطوان": "https://sadatetouan.com/feed", "أكادير 24": "https://agadir24.info/feed",
        "مراكش الآن": "https://www.marrakechalaan.com/feed", "ناظور سيتي": "https://www.nadorcity.com/rss/",
        "دوزيم": "https://2m.ma/ar/news/rss.xml", "ماب إكسبريس": "https://www.mapexpress.ma/ar/feed/",
        "الجهة 24": "https://aljahia24.ma/feed", "فاس نيوز": "https://fesnews.media/feed",
        "ريف بوست": "https://rifpost.com/feed"
    },
    "دولية واقتصاد (8 مصادر) 🌍": {
        "سكاي نيوز": "https://www.skynewsarabia.com/rss/v1/middle-east.xml",
        "الجزيرة": "https://www.aljazeera.net/alritem/rss/rss.xml",
        "فرانس 24": "https://www.france24.com/ar/rss",
        "BBC عربي": "https://www.bbc.com/arabic/index.xml",
        "اقتصادكم": "https://www.economistcom.ma/feed",
        "انفستنغ": "https://sa.investing.com/rss/news.rss",
        "سي إن إن عربية": "https://arabic.cnn.com/rss/cnnarabic.rss",
        "يورونيوز": "https://arabic.euronews.com/rss?level=vertical&name=news"
    },
    "رياضة، فن ولايف ستايل (7 مصادر) ⚽": {
        "البطولة": "https://www.elbotola.com/rss", "هسبريس رياضة": "https://hesport.com/feed",
        "المنتخب": "https://almountakhab.com/rss", "لالة مولاتي": "https://www.lallamoulati.ma/feed/",
        "سلطانة": "https://soltana.ma/feed", "غالية": "https://ghalia.ma/feed",
        "هاي كورة": "https://hihi2.com/feed"
    }
}

# ==========================================
# 4. الواجهة والمنطق
# ==========================================
st.markdown("<h1 style='text-align:center; color:#1e3a8a;'>وكيل يقين الصحفي - Manadger Tech</h1>", unsafe_allow_html=True)

if os.path.exists(DB_FILE):
    with open(DB_FILE, 'r', encoding='utf-8') as f: db = json.load(f)
else: db = {"data": {}}

tabs = st.tabs(list(RSS_SOURCES.keys()))
for i, cat in enumerate(list(RSS_SOURCES.keys())):
    with tabs[i]:
        if st.button(f"🔄 تحديث {cat}", key=f"up_{i}"):
            with st.spinner("جاري جلب البيانات من المصادر..."):
                all_items = []
                def f_task(n, u):
                    try:
                        d = feedparser.parse(u)
                        return [{"title": e.title, "link": e.link, "source": n} for e in d.entries[:10]]
                    except: return []
                with concurrent.futures.ThreadPoolExecutor(max_workers=20) as exec:
                    results = list(exec.map(lambda p: f_task(*p), RSS_SOURCES[cat].items()))
                    for res in results: all_items.extend(res)
                db["data"][cat] = all_items
                with open(DB_FILE, 'w', encoding='utf-8') as f: json.dump(db, f, ensure_ascii=False)
            st.rerun()

        if cat in db["data"] and db["data"][cat]:
            news_list = db["data"][cat]
            choice = st.selectbox("اختر المقال:", range(len(news_list)), format_func=lambda x: f"[{news_list[x]['source']}] {news_list[x]['title']}", key=f"s_{i}")
            c1, c2 = st.columns(2)
            with c1: tone = st.selectbox("الأسلوب الصحفي:", ["تحقيق مثير", "تقرير سريع", "تحليل SEO"], key=f"t_{i}")
            with c2: keyword = st.text_input("الكلمة المفتاحية:", key=f"k_{i}")

            if st.button("🚀 هندسة وصياغة المقال", key=f"r_{i}"):
                with st.spinner("جاري بناء المقال..."):
                    raw = trafilatura.fetch_url(news_list[choice]['link'])
                    txt = trafilatura.extract(raw)
                    if txt:
                        final = rewrite_pro_seo(txt, tone, keyword)
                        st.markdown("### ✅ النتيجة النهائية")
                        st.write(final)
                        st.text_area("للنسخ المباشر:", final, height=400)
                    else: st.error("الموقع محمي")
        else: st.info("اضغط تحديث.")

st.markdown("---")
st.caption("وكيل يقين V17.0 - 50 مصدراً - إدارة الماندجر 2026")
