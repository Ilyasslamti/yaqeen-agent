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
# 1. إعدادات الصفحة (Mobile Optimized)
# ==========================================
st.set_page_config(
    page_title="وكيل يقين AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed" # جعل القائمة مغلقة افتراضياً على الموبايل لتوفير المساحة
)

DB_FILE = "news_db.json"

# ==========================================
# 2. CSS الاحترافي (مراعي للموبايل والحاسوب)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    
    /* توحيد الخط */
    * { font-family: 'Cairo', sans-serif !important; }

    /* تحسينات عامة للمحاذاة */
    h1, h2, h3, h4, h5, h6, .stMarkdown, .stText, p { text-align: right !important; }
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] { direction: rtl; text-align: right; }

    /* تصميم البطاقات (Cards) - ممتاز للموبايل */
    .news-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-right: 4px solid #3b82f6; /* أزرق */
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 15px;
        text-align: right;
        direction: rtl;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        transition: transform 0.2s;
    }
    
    /* تصميم صندوق النتيجة (AI Result) */
    .seo-result {
        background: #f0fdfa; /* تيل فاتح */
        border: 1px solid #ccfbf1;
        border-right: 4px solid #0d9488; /* لون مميز للذكاء الاصطناعي */
        padding: 20px;
        border-radius: 12px;
        text-align: right;
        direction: rtl;
        margin-top: 10px;
    }

    /* تحسين الأزرار للموبايل (أكبر وأوضح) */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        font-weight: 700;
        padding: 0.5rem 1rem;
        min-height: 50px; /* ارتفاع مناسب للإصبع */
        font-size: 16px !important;
    }
    
    /* زر الذكاء الاصطناعي الخاص */
    div[data-testid="stButton"] button {
        border: none;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    
    div[data-testid="stButton"] button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
    }

    /* إخفاء العناصر المزعجة */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    
    /* تحسين عرض الموبايل للنصوص */
    @media (max-width: 640px) {
        h1 { font-size: 1.8rem !important; }
        .stMarkdown p { font-size: 1rem !important; }
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. المصادر
# ==========================================
RSS_SOURCES = {
    "أخبار الشمال": {
        "شمال بوست": "https://chamalpost.net/feed",
        "بريس تطوان": "https://presstetouan.com/feed",
        "طنجة 24": "https://tanja24.com/feed",
        "تطوان بريس": "https://tetouanpress.ma/feed",
        "كاب 24": "https://cap24.tv/feed",
    },
    "صحف وطنية": {
        "هسبريس": "https://www.hespress.com/feed",
        "العمق": "https://al3omk.com/feed",
        "مدار 21": "https://madar21.com/feed",
        "كود": "https://www.goud.ma/feed",
        "الصباح": "https://assabah.ma/feed",
    },
    "رياضة": {
        "البطولة": "https://www.elbotola.com/rss",
        "هسبريس الرياضية": "https://hesport.com/feed",
    }
}

# ==========================================
# 4. المحرك الخلفي (Backend)
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

# --- الخلفية (Background Worker) ---
@st.cache_resource
def start_background_worker():
    def worker_loop():
        while True:
            try:
                if os.path.exists(DB_FILE):
                    with open(DB_FILE, 'r', encoding='utf-8') as f: db = json.load(f)
                    last_ts = db.get('last_updated', 0)
                else: last_ts = 0

                now = datetime.now()
                tz_ma = pytz.timezone('Africa/Casablanca')
                now_ma = datetime.now(tz_ma)

                if now_ma.hour == 2 and 30 <= now_ma.minute <= 35:
                    if os.path.exists(DB_FILE):
                        os.remove(DB_FILE)
                        time.sleep(400) 
                        continue

                diff = now - datetime.fromtimestamp(last_ts)
                if diff.total_seconds() > 3600 or last_ts == 0:
                    update_database_logic()
                time.sleep(60)
            except: time.sleep(60)

    t = threading.Thread(target=worker_loop, daemon=True)
    t.start()
    return t

start_background_worker()

# ==========================================
# 5. الواجهة الأمامية (AI & Mobile UI)
# ==========================================
def get_text(url):
    try:
        d = trafilatura.fetch_url(url)
        return trafilatura.extract(d) if d else None
    except: return None

def rewrite(text, tone, instr):
    if not client: return "خطأ: المفتاح مفقود"
    prompt = f"""
    أنت محرر ذكاء اصطناعي متقدم لـ "هاشمي بريس".
    المهمة: أعد صياغة الخبر باحترافية SEO.
    النص: {text[:2500]}
    الأسلوب: {tone}. ملاحظات: {instr}.
    العنوان: H1 جذاب.
    """
    try:
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.7
        )
        return res.choices[0].message.content
    except Exception as e: return str(e)

# --- العنوان والشعار ---
st.markdown("<h1 style='text-align: center; color: #1e3a8a;'>🤖 وكيل يقين AI</h1>", unsafe_allow_html=True)

if os.path.exists(DB_FILE):
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        db = json.load(f)
    
    # القائمة الجانبية (للهاتف تكون مغلقة، وللحاسوب مفتوحة حسب الرغبة)
    with st.sidebar:
        st.header("⚙️ لوحة التحكم")
        cat = st.selectbox("📂 القسم", list(db['data'].keys()))
        news_list = db['data'][cat]
        
        st.divider()
        st.subheader("🧠 إعدادات الذكاء الاصطناعي")
        tone = st.select_slider("نبرة المحرر", ["رسمي", "تحليلي", "تفاعلي"])
        ins = st.text_input("توجيهات خاصة (اختياري)")
        
        st.divider()
        if st.button("🔄 تحديث يدوي فوري"):
            with st.spinner("جاري التحديث..."):
                update_database_logic()
            st.rerun()

    # عرض الأخبار
    # نستخدم selectbox لأنه أسهل على الموبايل من الجداول الكبيرة
    st.markdown(f"**الأخبار المتاحة في الأرشيف:** {len(news_list)} خبر")
    
    opts = [f"【{n['source']}】 {n['title']}" for n in news_list]
    idx = st.selectbox("👇 اختر الخبر من القائمة:", range(len(opts)), format_func=lambda x: opts[x])
    
    # زر التشغيل الجديد (أيقونة الذكاء الاصطناعي)
    # استخدمنا type="primary" ليكون ملوناً وواضحاً على الهاتف
    if st.button("✨ تشغيل المحرر الذكي (AI Rewrite)", type="primary"):
        sel = news_list[idx]
        
        with st.status("🤖 جاري المعالجة الذكية...", expanded=True) as s:
            st.write("📥 سحب البيانات...")
            txt = get_text(sel['link'])
            if txt:
                st.write("🧠 Llama 3.3 يفكر ويكتب...")
                res = rewrite(txt, tone, ins)
                s.update(label="تمت الصياغة بنجاح!", state="complete", expanded=False)
                
                # تخطيط مرن (للحاسوب عمودين، وللهاتف ينزلون تحت بعض تلقائياً)
                c1, c2 = st.columns([1, 1])
                
                with c1:
                    st.info("📄 النص الأصلي")
                    st.markdown(f"<div class='news-card' style='max-height: 300px; overflow-y: auto;'>{txt[:600]}...</div>", unsafe_allow_html=True)
                
                with c2:
                    st.success("✨ النتيجة (هاشمي بريس)")
                    st.markdown(f"<div class='seo-result'>{res}</div>", unsafe_allow_html=True)
                    # زر التحميل (بديل النسخ الصعب على الموبايل)
                    st.download_button("📥 تحميل المقال (TXT)", res, f"yaqeen_ai_{int(time.time())}.txt", key="dl_btn")
            else:
                s.update(label="فشل العملية", state="error")
                st.error("الموقع محمي، حاول مع خبر آخر.")

else:
    st.warning("⏳ النظام يجهز نفسه لأول مرة... (انتظر دقيقة ثم حدث الصفحة)")

