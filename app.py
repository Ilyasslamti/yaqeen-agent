import streamlit as st
import feedparser
import trafilatura
from groq import Groq
import concurrent.futures
import json
import os
import time
import threading
from datetime import datetime
import pytz

# ==========================================
# 1. إعدادات الصفحة
# ==========================================
st.set_page_config(
    page_title="وكيل يقين AI",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded" # جعلناها مفتوحة لتراها بوضوح
)

DB_FILE = "news_db.json"

# ==========================================
# 2. CSS (التصميم المستقر للهاتف والحاسوب)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    
    * { font-family: 'Cairo', sans-serif !important; }

    /* محاذاة آمنة */
    h1, h2, h3, h4, h5, h6, .stMarkdown, .stText, p { text-align: right !important; }
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] { direction: rtl; text-align: right; }

    /* البطاقات */
    .news-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-right: 4px solid #3b82f6;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 15px;
        text-align: right;
        direction: rtl;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .seo-result {
        background: #f0fdfa;
        border: 1px solid #ccfbf1;
        border-right: 4px solid #0d9488;
        padding: 20px;
        border-radius: 12px;
        text-align: right;
        direction: rtl;
        margin-top: 10px;
    }

    /* الأزرار */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        font-weight: 700;
        min-height: 50px;
    }

    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. المصادر (تمت مراجعتها بدقة)
# ==========================================
RSS_SOURCES = {
    "أخبار الشمال 🌊": {
        "شمال بوست": "https://chamalpost.net/feed",
        "بريس تطوان": "https://presstetouan.com/feed",
        "طنجة 24": "https://tanja24.com/feed",
        "تطوان بريس": "https://tetouanpress.ma/feed",
        "كاب 24": "https://cap24.tv/feed",
        "طنجة نيوز": "https://tanjanews.com/feed",
        "صدى تطوان": "https://sadatetouan.com/feed",
        "الشمال 24": "https://achamal24.com/feed",
        "طنجة الأدبية": "https://aladabia.net/feed",
    },
    "أخبار المغرب 🇲🇦": {
        "هسبريس": "https://www.hespress.com/feed",
        "العمق": "https://al3omk.com/feed",
        "مدار 21": "https://madar21.com/feed",
        "كود": "https://www.goud.ma/feed",
        "الصباح": "https://assabah.ma/feed",
        "اليوم 24": "https://www.alyaoum24.com/feed",
        "زنقة 20": "https://www.rue20.com/feed",
        "فبراير": "https://www.febrayer.com/feed",
        "هبة بريس": "https://ar.hibapress.com/feed",
    },
    "فنية ومشاهير 🎭": {
        "سلطانة": "https://soltana.ma/feed",
        "لالة مولاتي": "http://www.lallamoulati.ma/feed/",
        "غالية": "https://ghalia.ma/feed",
        "هسبريس فن": "https://www.hespress.com/art-et-culture/feed",
        "اليوم 24 فن": "https://alyaoum24.com/category/%D9%81%D9%86/feed",
        "شوف تيفي فن": "https://chouftv.ma/category/%D9%81%D9%86-%D9%88-%D9%85%D8%B4%D8%A7%D9%87%D9%8A%D8%B1/feed",
        "سيدتي نت": "https://www.sayidaty.net/rss/3",
    },
    "الرياضية ⚽": {
        "البطولة": "https://www.elbotola.com/rss",
        "هسبريس الرياضية": "https://hesport.com/feed",
        "المنتخب": "https://almountakhab.com/rss",
        "هاي كورة": "https://hihi2.com/feed",
        "360 سبورت": "https://sport.le360.ma/rss",
    }
}

# ==========================================
# 4. المحرك الخلفي
# ==========================================
try:
    if "GROQ_API_KEY" in st.secrets:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    else: client = None
except: client = None

def fetch_single_feed(source_name, url, limit):
    entries = []
    try:
        d = feedparser.parse(url)
        for e in d.entries[:limit]:
            entries.append({
                "title": e.title,
                "link": e.link,
                "source": source_name,
                "published": e.get("published", str(datetime.now()))
            })
    except: pass
    return entries

def update_database_logic():
    """تحديث شامل لقاعدة البيانات"""
    all_data = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for category, feeds in RSS_SOURCES.items():
            cat_items = []
            futures = [executor.submit(fetch_single_feed, src, url, 15) for src, url in feeds.items()]
            for f in concurrent.futures.as_completed(futures):
                cat_items.extend(f.result())
            all_data[category] = cat_items
            
    db_content = { "last_updated": datetime.now().timestamp(), "data": all_data }
    temp_file = DB_FILE + ".tmp"
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(db_content, f, ensure_ascii=False)
    os.replace(temp_file, DB_FILE)

# --- العامل الخلفي ---
@st.cache_resource
def start_background_worker():
    def worker_loop():
        while True:
            try:
                # التحقق من وجود الملف
                if not os.path.exists(DB_FILE):
                    update_database_logic()
                else:
                    with open(DB_FILE, 'r', encoding='utf-8') as f: db = json.load(f)
                    last_ts = db.get('last_updated', 0)
                    
                    # التحديث كل ساعة
                    if (datetime.now() - datetime.fromtimestamp(last_ts)).total_seconds() > 3600:
                        update_database_logic()

                # المسح الليلي (2:30 بتوقيت المغرب)
                tz = pytz.timezone('Africa/Casablanca')
                now = datetime.now(tz)
                if now.hour == 2 and 30 <= now.minute <= 35:
                    if os.path.exists(DB_FILE): os.remove(DB_FILE)
                    time.sleep(400)
                
                time.sleep(60)
            except: time.sleep(60)

    t = threading.Thread(target=worker_loop, daemon=True)
    t.start()
    return t

start_background_worker()

# ==========================================
# 5. الواجهة الأمامية والمنطق الذكي
# ==========================================
def get_text(url):
    try:
        d = trafilatura.fetch_url(url)
        return trafilatura.extract(d) if d else None
    except: return None

def rewrite(text, tone, instr):
    if not client: return "خطأ: المفتاح مفقود"
    prompt = f"""
    أنت محرر ذكي لـ "هاشمي بريس". أعد صياغة الخبر.
    النص: {text[:2500]}
    الأسلوب: {tone}. ملاحظات: {instr}.
    العنوان H1 جذاب.
    """
    try:
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.7
        )
        return res.choices[0].message.content
    except Exception as e: return str(e)

st.markdown("<h1 style='text-align: center; color: #1e3a8a;'>🤖 وكيل يقين AI</h1>", unsafe_allow_html=True)

# --- كود التصحيح الذاتي (Self-Healing Logic) ---
# هذا الكود يفحص إذا كانت الأقسام الجديدة مفقودة من الملف القديم
if os.path.exists(DB_FILE):
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            db = json.load(f)
        
        saved_keys = set(db['data'].keys())
        code_keys = set(RSS_SOURCES.keys())
        
        # إذا كان هناك اختلاف بين الكود والملف (أقسام ناقصة)
        if code_keys != saved_keys:
            st.warning("⚠️ تم اكتشاف أقسام جديدة (مثل الفنية والرياضية). جاري تحديث النظام تلقائياً...")
            update_database_logic() # فرض التحديث
            st.rerun() # إعادة تحميل الصفحة لإظهار الجديد
            
    except:
        # إذا كان الملف تالفاً
        update_database_logic()
        st.rerun()

# --- العرض ---
if os.path.exists(DB_FILE):
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        db = json.load(f)
    
    with st.sidebar:
        st.header("⚙️ الأقسام")
        cat = st.selectbox("📂 اختر القسم", list(db['data'].keys()))
        news_list = db['data'][cat]
        
        st.divider()
        st.subheader("🧠 الصياغة")
        tone = st.select_slider("النبرة", ["رسمي", "تحليلي", "تفاعلي"])
        ins = st.text_input("توجيهات")
        
        st.divider()
        if st.button("🔄 تحديث شامل"):
            with st.spinner("جاري التحديث..."):
                update_database_logic()
            st.rerun()

    if news_list:
        st.success(f"**{cat}:** تم جلب {len(news_list)} خبر.")
        
        opts = [f"【{n['source']}】 {n['title']}" for n in news_list]
        idx = st.selectbox("👇 القائمة:", range(len(opts)), format_func=lambda x: opts[x])
        
        if st.button("✨ صياغة ذكية (AI)", type="primary"):
            sel = news_list[idx]
            with st.status("🤖 جاري العمل...", expanded=True) as s:
                txt = get_text(sel['link'])
                if txt:
                    res = rewrite(txt, tone, ins)
                    s.update(label="تم!", state="complete", expanded=False)
                    
                    c1, c2 = st.columns([1, 1])
                    with c1:
                        st.info("الأصل")
                        st.markdown(f"<div class='news-card' style='max-height:300px;overflow-y:auto'>{txt[:600]}...</div>", unsafe_allow_html=True)
                    with c2:
                        st.success("النتيجة")
                        st.markdown(f"<div class='seo-result'>{res}</div>", unsafe_allow_html=True)
                        st.download_button("📥 تحميل", res, "article.txt")
                else:
                    s.update(label="فشل", state="error")
                    st.error("موقع محمي")
    else:
        st.warning("لا توجد أخبار هنا حالياً.")

else:
    st.info("⏳ جاري بناء قاعدة البيانات بالأقسام الجديدة... (انتظر دقيقة)")
