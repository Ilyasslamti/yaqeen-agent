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
# 0. الإعدادات والتحصين
# ==========================================
SYSTEM_VERSION = "V19.0_INVESTIGATIVE_PRO"
ACCESS_PASSWORD = "Manager_Tech_2026"
DB_FILE = "news_db_v19.json"

st.set_page_config(page_title="يقين AI | المحرر الاستقصائي", page_icon="🕵️‍♂️", layout="wide")
socket.setdefaulttimeout(40)

# ==========================================
# 1. محرك الهندسة الصحفية "الاستقصائية" (The Beast)
# ==========================================
def run_investigative_writer(text, tone, keyword):
    try:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        # برومبت جبار يركز على العمق، الترابط، واللغة الراقية
        prompt = f"""
        أنت محرر استقصائي وخبير في الشؤون الاستراتيجية والاقتصادية. 
        حول المادة الخام التالية إلى "مقال استقصائي معمق" يتسم بالرصانة والجزالة اللغوية.
        
        البروتوكول الصارم للماندجر إلياس:
        1. **لغة النخبة:** ابتعد تماماً عن الجمل القصيرة البدائية. ابْنِ فقرات مترابطة، طويلة النفس، واستخدم الفواصل (،) لخلق تدفق فكري مستمر.
        2. **التحليل السوسيواقتصادي:** لا تكتفِ بسرد الخبر، بل اربط الظواهر ببعضها (مثلاً: ربط غسل الأموال بتعثر العقار كظاهرة بنيوية).
        3. **بنية الـ SEO الاحترافية:** العنوان يجب أن يكون "زلزالاً" فكرياً يبدأ بـ ({keyword})، مع عناوين فرعية (H2) تحمل طابعاً تحليلياً (مثلاً: 'هندسة التضليل الجبائي' بدلاً من 'استغلال المكاتب').
        4. **كلمات الانتقال السيادية:** استخدم روابط لغوية فخمة (وتأسيساً على ما تقدم، وفي مقلب آخر من المشهد، بيد أن التدقيق في التفاصيل يكشف، ولعل اللافت في الأمر..).
        5. **منع التكرار والتهريج:** احذف الحشو، ادمج المتشابه، وقدم محتوى "دَسِماً" يشرف "مجموعة الماندجر".
        
        الأسلوب: {tone}. الكلمة المفتاحية: {keyword}.
        النص الخام للمعالجة:
        {text[:4000]}
        """
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.6 # رفع مستوى الإبداع اللغوي
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"خطأ تقني: {str(e)}"

# ==========================================
# 2. نظام الدخول
# ==========================================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown("<h2 style='text-align:center;'>🔐 دخول المحرر الاستقصائي - Manadger Tech</h2>", unsafe_allow_html=True)
    pwd = st.text_input("مفتاح الوصول الجبار:", type="password")
    if st.button("دخول"):
        if pwd == ACCESS_PASSWORD:
            st.session_state["authenticated"] = True
            st.rerun()
        else: st.error("المفتاح غير صحيح")
    st.stop()

# ==========================================
# 3. القائمة الكاملة والنهائية (53 مصدراً) - لن تُحذف أبداً
# ==========================================
RSS_SOURCES = {
    "الصحافة الوطنية 🇲🇦": {
        "هسبريس": "https://www.hespress.com/feed", "شوف تيفي": "https://chouftv.ma/feed",
        "العمق المغربي": "https://al3omk.com/feed", "زنقة 20": "https://www.rue20.com/feed",
        "هبة بريس": "https://ar.hibapress.com/feed", "اليوم 24": "https://alyaoum24.com/feed",
        "كود": "https://www.goud.ma/feed", "Le360": "https://ar.le360.ma/rss",
        "فبراير": "https://www.febrayer.com/feed", "آشكاين": "https://achkayen.com/feed",
        "الجريدة 24": "https://aljarida24.ma/feed", "لكم": "https://lakome2.com/feed",
        "عبر": "https://aabbir.com/feed", "سفيركم": "https://safir24.com/feed",
        "باناصا": "https://banassa.com/feed", "الأيام 24": "https://www.alayam24.com/feed",
        "برلمان.كوم": "https://www.barlamane.com/feed", "تليكسبريس": "https://telexpresse.com/feed",
        "الصباح": "https://assabah.ma/feed", "الأحداث المغربية": "https://ahdath.info/feed"
    },
    "أخبار الشمال والجهات 🌊": {
        "شمال بوست": "https://chamalpost.net/feed", "بريس تطوان": "https://presstetouan.com/feed",
        "طنجة 24": "https://tanja24.com/feed", "تطوان بريس": "https://tetouanpress.ma/feed",
        "طنجة نيوز": "https://tanjanews.com/feed", "كاب 24": "https://cap24.tv/feed",
        "صدى تطوان": "https://sadatetouan.com/feed", "أكادير 24": "https://agadir24.info/feed",
        "مراكش الآن": "https://www.marrakechalaan.com/feed", "ناظور سيتي": "https://www.nadorcity.com/rss/",
        "دوزيم": "https://2m.ma/ar/news/rss.xml", "ماب إكسبريس": "https://www.mapexpress.ma/ar/feed/",
        "الجهة 24": "https://aljahia24.ma/feed", "فاس نيوز": "https://fesnews.media/feed",
        "ريف بوست": "https://rifpost.com/feed"
    },
    "دولية واقتصاد 🌍": {
        "سكاي نيوز": "https://www.skynewsarabia.com/rss/v1/middle-east.xml",
        "الجزيرة": "https://www.aljazeera.net/alritem/rss/rss.xml",
        "فرانس 24": "https://www.france24.com/ar/rss",
        "BBC عربي": "https://www.bbc.com/arabic/index.xml",
        "اقتصادكم": "https://www.economistcom.ma/feed",
        "انفستنغ": "https://sa.investing.com/rss/news.rss",
        "العربية": "https://www.alarabiya.net/.mrss/ar/last-24-hours.xml",
        "RT عربي": "https://arabic.rt.com/rss/"
    },
    "رياضة وفن ⚽": {
        "البطولة": "https://www.elbotola.com/rss", "هسبريس رياضة": "https://hesport.com/feed",
        "المنتخب": "https://almountakhab.com/rss", "لالة مولاتي": "https://www.lallamoulati.ma/feed/",
        "سلطانة": "https://soltana.ma/feed", "غالية": "https://ghalia.ma/feed",
        "هاي كورة": "https://hihi2.com/feed", "في الجول": "https://www.filgoal.com/rss"
    }
}

# ==========================================
# 4. التنسيق والواجهة (Premium UI)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
    html, body, [class*="st-"] { font-family: 'Cairo', sans-serif; text-align: right; direction: rtl; }
    .article-output { white-space: pre-wrap; background-color: #ffffff; padding: 40px; border-radius: 20px; border: 1px solid #eee; line-height: 2.3; font-size: 1.3rem; text-align: justify; box-shadow: 0 10px 30px rgba(0,0,0,0.05); }
    .stButton>button { background: linear-gradient(90deg, #1e3a8a, #3b82f6); color: white; height: 3.8rem; border-radius: 12px; font-weight: 900; }
</style>
""", unsafe_allow_html=True)

st.title("🕵️‍♂️ وكيل يقين | المحرر الاستقصائي الاستراتيجي")

if os.path.exists(DB_FILE):
    with open(DB_FILE, 'r', encoding='utf-8') as f: db = json.load(f)
else: db = {"data": {}}

tabs = st.tabs(list(RSS_SOURCES.keys()))
for i, cat in enumerate(list(RSS_SOURCES.keys())):
    with tabs[i]:
        if st.button(f"🔄 جلب وتحليل مصادر {cat}", key=f"up_{i}"):
            with st.spinner("جاري استحضار البيانات وتحليل المسارات..."):
                all_news = []
                def fetch_t(n, u):
                    try:
                        d = feedparser.parse(u)
                        return [{"title": e.title, "link": e.link, "source": n} for e in d.entries[:10]]
                    except: return []
                with concurrent.futures.ThreadPoolExecutor(max_workers=25) as exec:
                    futures = [exec.submit(fetch_t, name, url) for name, url in RSS_SOURCES[cat].items()]
                    for f in concurrent.futures.as_completed(futures): all_news.extend(f.result())
                db["data"][cat] = all_news
                with open(DB_FILE, 'w', encoding='utf-8') as f: json.dump(db, f, ensure_ascii=False)
            st.rerun()

        if cat in db["data"] and db["data"][cat]:
            news_list = db["data"][cat]
            choice = st.selectbox("اختر المادة الخام للمقالة:", range(len(news_list)), format_func=lambda x: f"[{news_list[x]['source']}] {news_list[x]['title']}", key=f"sel_{i}")
            c1, c2 = st.columns(2)
            with c1: tone = st.selectbox("النبرة الاستراتيجية:", ["تحقيق استقصائي معمق", "تحليل سياسي/اقتصادي"], key=f"tn_{i}")
            with c2: keyword = st.text_input("الكلمة المفتاحية (SEO Master):", key=f"kw_{i}")

            if st.button("🚀 صياغة المقال الاستراتيجي", key=f"run_{i}"):
                with st.spinner("جاري هندسة المحتوى بصيغة استقصائية..."):
                    raw = trafilatura.fetch_url(news_list[choice]['link'])
                    txt = trafilatura.extract(raw)
                    if txt:
                        final = run_investigative_writer(txt, tone, keyword)
                        st.markdown("### ✅ المقال الاستقصائي الجاهز للنشر")
                        st.markdown(f<div class='article-output'>{final}</div>, unsafe_allow_html=True)
                        st.text_area("للنسخ المباشر:", final, height=500)
                    else: st.error("المصدر يرفض السحب الآلي.")
        else: st.info("اضغط تحديث لتفعيل المصادر.")

st.markdown("---")
st.caption("وكيل يقين V19.0 - إدارة الماندجر 2026 - الإصدار الاستقصائي النخبوي")
