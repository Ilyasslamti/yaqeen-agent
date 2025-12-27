import streamlit as st
import feedparser
import trafilatura
from groq import Groq
import concurrent.futures
import json
import os
import time
import threading
import socket
from datetime import datetime
import pytz

# ==========================================
# 0. ضبط المهلة (لحل مشكلة التوقف)
# ==========================================
socket.setdefaulttimeout(4)

# ==========================================
# 1. إعدادات الصفحة
# ==========================================
st.set_page_config(
    page_title="وكيل يقين AI",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DB_FILE = "news_db.json"

# ==========================================
# 2. CSS
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    * { font-family: 'Cairo', sans-serif !important; }
    h1, h2, h3, h4, h5, h6, .stMarkdown, .stText, p { text-align: right !important; }
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] { direction: rtl; text-align: right; }
    
    .news-card {
        background: #ffffff; border: 1px solid #e2e8f0; border-right: 4px solid #3b82f6;
        padding: 15px; border-radius: 12px; margin-bottom: 15px; text-align: right; direction: rtl;
    }
    .seo-result {
        background: #f0fdfa; border: 1px solid #ccfbf1; border-right: 4px solid #0d9488;
        padding: 20px; border-radius: 12px; text-align: right; direction: rtl; margin-top: 10px;
    }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: 700; min-height: 50px; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    @media (max-width: 640px) { h1 { font-size: 1.8rem !important; } }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. المصادر (تأكد أن الأقسام الجديدة هنا)
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

def update_database_logic(progress_callback=None):
    all_data = {}
    total_feeds = sum(len(v) for v in RSS_SOURCES.values())
    completed = 0
    
    # استخدام التوازي مع مهلة زمنية
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = []
        for category, feeds in RSS_SOURCES.items():
            for src, url in feeds.items():
                futures.append((executor.submit(fetch_single_feed, src, url, 15), category))
        
        results_map = {cat: [] for cat in RSS_SOURCES.keys()}
        
        for future, category in futures:
            try:
                items = future.result() 
                results_map[category].extend(items)
            except: pass
            
            completed += 1
            if progress_callback:
                progress_callback(completed / total_feeds)
                
    db_content = { "last_updated": datetime.now().timestamp(), "data": results_map }
    
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(db_content, f, ensure_ascii=False)
    except: pass

# --- العامل الخلفي ---
@st.cache_resource
def start_background_worker():
    def worker_loop():
        while True:
            try:
                if os.path.exists(DB_FILE):
                    with open(DB_FILE, 'r', encoding='utf-8') as f: db = json.load(f)
                    last_ts = db.get('last_updated', 0)
                    if (datetime.now() - datetime.fromtimestamp(last_ts)).total_seconds() > 3600:
                        update_database_logic()
                
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
# 5. الواجهة والذكاء الاصطناعي
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

# --- تهيئة أولية إذا لم يوجد ملف ---
if not os.path.exists(DB_FILE):
    st.info("جاري تهيئة النظام لأول مرة (قد يستغرق دقيقة)...")
    my_bar = st.progress(0)
    update_database_logic(progress_callback=my_bar.progress)
    my_bar.empty()
    st.rerun()

# --- العرض الرئيسي ---
# هنا التغيير الجذري: نقرأ الأقسام من الكود (RSS_SOURCES) وليس من الملف القديم
current_categories = list(RSS_SOURCES.keys())

# محاولة تحميل البيانات الموجودة
news_data = {}
if os.path.exists(DB_FILE):
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            db_full = json.load(f)
            news_data = db_full.get('data', {})
    except: pass

with st.sidebar:
    st.header("⚙️ التحكم")
    
    # 1. القائمة تقرأ الآن من الكود مباشرة (ستظهر كل الأقسام فوراً)
    cat = st.selectbox("📂 القسم", current_categories)
    
    # جلب الأخبار الخاصة بالقسم المختار من الذاكرة
    news_list = news_data.get(cat, [])
    
    st.divider()
    st.subheader("🧠 الصياغة")
    tone = st.select_slider("النبرة", ["رسمي", "تحليلي", "تفاعلي"])
    ins = st.text_input("توجيهات")
    
    st.divider()
    if st.button("🔄 تحديث شامل (Force Update)"):
        with st.spinner("جاري جلب آخر الأخبار..."):
            update_database_logic()
        st.rerun()

# منطقة النتائج
if news_list:
    st.success(f"**{cat}:** {len(news_list)} خبر متاح.")
    opts = [f"【{n['source']}】 {n['title']}" for n in news_list]
    idx = st.selectbox("👇 اختر الخبر:", range(len(opts)), format_func=lambda x: opts[x])
    
    if st.button("✨ تشغيل المحرر الذكي", type="primary"):
        sel = news_list[idx]
        with st.status("🤖 جاري العمل...", expanded=True) as s:
            txt = get_text(sel['link'])
            if txt:
                res = rewrite(txt, tone, ins)
                s.update(label="تم!", state="complete", expanded=False)
                
                c1, c2 = st.columns([1, 1])
                with c1:
                    st.write("النص الأصلي:")
                    st.markdown(f"<div class='news-card' style='max-height:300px;overflow-y:auto'>{txt[:600]}...</div>", unsafe_allow_html=True)
                with c2:
                    st.success("النتيجة:")
                    st.markdown(f"<div class='seo-result'>{res}</div>", unsafe_allow_html=True)
                    st.download_button("📥 تحميل", res, "article.txt")
            else:
                s.update(label="فشل", state="error")
                st.error("الموقع محمي")
else:
    # إذا اخترت قسماً جديداً ولم تجد فيه أخباراً بعد
    st.warning(f"القسم **'{cat}'** فارغ حالياً في الذاكرة.")
    if st.button(f"📥 جلب أخبار {cat} الآن"):
        with st.spinner("جاري التحديث..."):
            update_database_logic()
        st.rerun()
