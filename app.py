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
# 0. إعدادات الهوية والذكاء الاصطناعي
# ==========================================
SYSTEM_VERSION = "V17.5_TITAN_SEO"
ACCESS_PASSWORD = "Manager_Tech_2026"
DB_FILE = "news_db_v17.json"

st.set_page_config(
    page_title="يقين AI | المنصة الجبارة",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 1. واجهة الجوال (Custom CSS for Mobile & UI)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');
    
    html, body, [class*="st-"] {
        font-family: 'Cairo', sans-serif;
        text-align: right;
        direction: rtl;
    }
    
    /* تنسيق الحاوية الرئيسية للجوال */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 5rem;
    }

    /* الهيدر الجبار */
    .mega-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        padding: 40px 20px;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }

    /* صندوق إخراج المقال */
    .article-box {
        background: #ffffff;
        color: #1a202c;
        padding: 25px;
        border-radius: 15px;
        border-right: 8px solid #3b82f6;
        line-height: 2;
        font-size: 1.2rem;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        margin-top: 20px;
        text-align: justify;
    }

    /* تخصيص الأزرار لتناسب اللمس في الجوال */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 4rem;
        background: #1e3a8a;
        color: white;
        font-weight: 900;
        font-size: 1.1rem;
        border: none;
        transition: 0.3s;
    }
    
    .stButton>button:hover {
        background: #2563eb;
        transform: translateY(-2px);
    }

    /* إخفاء القوائم غير الضرورية في الجوال */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. محرك الصياغة الجبار (The Content Architect)
# ==========================================
def run_titan_writer(text, tone, keyword):
    try:
        if "GROQ_API_KEY" not in st.secrets:
            return "خطأ: يرجى إضافة مفتاح GROQ في إعدادات المنصة."
        
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        
        # البرومبت الذي يمنع التكرار ويحترم السيو بشكل جبار
        prompt = f"""
        أنت رئيس تحرير "الماندجر" للصحافة الرقمية وخبير SEO عالمي. 
        حول النص "الضعيف والمكرر" التالي إلى مقال صحفي "نخبوي" يتصدر محركات البحث.

        الخوارزمية المطلوبة (التزام صارم):
        1. **مكافحة التكرار الروبوتي:** ممنوع تكرار الجمل أو الأفكار. إذا وجدت فكرة مكررة 10 مرات، ادمجها في جملة واحدة قوية ومركزة.
        2. **هندسة العناوين:** صغ عنواناً "انفجارياً" يبدأ بـ ({keyword})، يثير الفضول ولا يحتوي على كلمة 'مغناطيسياً'.
        3. **قاعدة الـ 18 كلمة:** ممنوع نهائياً أن تتجاوز أي جملة 18 كلمة. ضع نقطة (.) فوراً وابدأ جملة جديدة بروح جديدة.
        4. **كلمات الانتقال (Yoast Green):** ادمج روابط احترافية (بالموازاة مع ذلك، علاوة على، ومن جهة أخرى، وفي سياق متصل).
        5. **المبني للمعلوم:** اجعل الفاعل هو القائد (كشف، أعلن، فجر، تصدر).
        6. **الهيكل:** عنوان H1، مقدمة ساحرة، وعناوين فرعية نصية (بدون رموز Markdown).

        الأسلوب: {tone}.
        الكلمة المفتاحية: {keyword}.
        النص الأصلي: {text[:3800]}
        """
        
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.5
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"عذراً إلياس، حدث خطأ تقني: {str(e)}"

# ==========================================
# 3. نظام الحماية الذكي
# ==========================================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown("<div class='mega-header'><h1>🦅 منصة يقين AI</h1><p>إدارة الماندجر - دخول المسرح لهم فقط</p></div>", unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        pwd = st.text_input("مفتاح الوصول الجبار:", type="password")
        if st.button("فتح المنصة"):
            if pwd == ACCESS_PASSWORD:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("مفتاح خاطئ! هذا النظام محمي من طرف الماندجر.")
    st.stop()

# ==========================================
# 4. المصادر الـ 50 (القائمة الكاملة)
# ==========================================
RSS_SOURCES = {
    "الصحافة الوطنية 🇲🇦": {
        "هسبريس": "https://www.hespress.com/feed", "شوف تيفي": "https://chouftv.ma/feed",
        "العمق المغربي": "https://al3omk.com/feed", "زنقة 20": "https://www.rue20.com/feed",
        "هبة بريس": "https://ar.hibapress.com/feed", "اليوم 24": "https://alyaoum24.com/feed",
        "كود": "https://www.goud.ma/feed", "برلمان.كوم": "https://www.barlamane.com/feed",
        "تليكسبريس": "https://telexpresse.com/feed", "Le360": "https://ar.le360.ma/rss",
        "فبراير": "https://www.febrayer.com/feed", "آشكاين": "https://achkayen.com/feed",
        "عبر": "https://aabbir.com/feed", "سفيركم": "https://safir24.com/feed"
    },
    "أخبار الشمال والجهات 🌊": {
        "شمال بوست": "https://chamalpost.net/feed", "بريس تطوان": "https://presstetouan.com/feed",
        "طنجة 24": "https://tanja24.com/feed", "تطوان بريس": "https://tetouanpress.ma/feed",
        "طنجة نيوز": "https://tanjanews.com/feed", "كاب 24": "https://cap24.tv/feed",
        "صدى تطوان": "https://sadatetouan.com/feed", "أكادير 24": "https://agadir24.info/feed",
        "مراكش الآن": "https://www.marrakechalaan.com/feed", "الجهة 24": "https://aljahia24.ma/feed"
    },
    "دولية واقتصاد 🌍": {
        "سكاي نيوز": "https://www.skynewsarabia.com/rss/v1/middle-east.xml",
        "الجزيرة": "https://www.aljazeera.net/alritem/rss/rss.xml",
        "فرانس 24": "https://www.france24.com/ar/rss",
        "BBC عربي": "https://www.bbc.com/arabic/index.xml",
        "اقتصادكم": "https://www.economistcom.ma/feed",
        "انفستنغ": "https://sa.investing.com/rss/news.rss"
    },
    "رياضة وفن ⚽": {
        "البطولة": "https://www.elbotola.com/rss", "هسبريس رياضة": "https://hesport.com/feed",
        "المنتخب": "https://almountakhab.com/rss", "لالة مولاتي": "https://www.lallamoulati.ma/feed/",
        "سلطانة": "https://soltana.ma/feed", "هاي كورة": "https://hihi2.com/feed"
    }
}

# ==========================================
# 5. المنطق التشغيلي (The Engine)
# ==========================================
st.markdown("<div class='mega-header'><h1>وكيل يقين الصحفي</h1><p>من مجموعة منادجر للتطوير وحلول الويب</p></div>", unsafe_allow_html=True)

if os.path.exists(DB_FILE):
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f: db = json.load(f)
    except: db = {"data": {}}
else: db = {"data": {}}

tabs = st.tabs(list(RSS_SOURCES.keys()))
for i, cat in enumerate(list(RSS_SOURCES.keys())):
    with tabs[i]:
        if st.button(f"🔄 تحديث {cat}", key=f"up_{i}"):
            with st.spinner("جاري مسح 50 مصدراً..."):
                all_news = []
                def fetch_task(n, u):
                    try:
                        d = feedparser.parse(u)
                        return [{"title": e.title, "link": e.link, "source": n} for e in d.entries[:10]]
                    except: return []
                with concurrent.futures.ThreadPoolExecutor(max_workers=20) as exec:
                    futures = [exec.submit(fetch_task, name, url) for name, url in RSS_SOURCES[cat].items()]
                    for f in concurrent.futures.as_completed(futures): all_news.extend(f.result())
                db["data"][cat] = all_news
                with open(DB_FILE, 'w', encoding='utf-8') as f: json.dump(db, f, ensure_ascii=False)
            st.rerun()

        if cat in db["data"] and db["data"][cat]:
            news = db["data"][cat]
            choice = st.selectbox("اختر الخبر:", range(len(news)), format_func=lambda x: f"[{news[x]['source']}] {news[x]['title']}", key=f"sel_{i}")
            
            # أدوات تحكم مناسبة للجوال
            tone = st.selectbox("الأسلوب الصحفي:", ["تحقيق رصين (SEO)", "تقرير سريع", "مقال رأي"], key=f"t_{i}")
            keyword = st.text_input("الكلمة المفتاحية المستهدفة:", placeholder="أدخل الكلمة هنا للتصدر...", key=f"k_{i}")

            if st.button("🚀 هندسة المقال الجبار", key=f"go_{i}"):
                with st.spinner("جاري تدمير التكرار وبناء المقال..."):
                    raw = trafilatura.fetch_url(news[choice]['link'])
                    txt = trafilatura.extract(raw)
                    if txt:
                        res = run_titan_writer(txt, tone, keyword)
                        st.markdown("### ✅ المقال النهائي الجاهز")
                        st.markdown(f"<div class='article-box'>{res}</div>", unsafe_allow_html=True)
                        st.text_area("للنسخ السريع (ووردبريس):", res, height=350)
                    else: st.error("المصدر محمي تقنياً.")
        else:
            st.info("اضغط تحديث لجلب أخبار هذه الفئة.")

st.markdown("---")
st.markdown("<p style='text-align:center; color:#666; padding: 20px;'>وكيل يقين الصحفي V17.5 - إدارة الماندجر 2026</p>", unsafe_allow_html=True)
