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
    page_title="وكيل يقين - الطيار الآلي",
    page_icon="🦅",
    layout="wide"
)

DB_FILE = "news_db.json"

# ==========================================
# 2. CSS (التصميم المستقر)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
    * { font-family: 'Cairo', sans-serif !important; }
    h1, h2, h3, h4, h5, h6, .stMarkdown, .stText, p { text-align: right !important; }
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] { direction: rtl; text-align: right; }
    .news-card { background: #fff; padding: 15px; border-radius: 8px; margin-bottom: 10px; text-align: right; direction: rtl; border: 1px solid #eee; }
    .seo-result { background: #f0fdf4; border-right: 4px solid #16a34a; padding: 20px; border-radius: 8px; text-align: right; direction: rtl; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
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
# 4. المحرك الخلفي (Backend Logic)
# ==========================================
try:
    if "GROQ_API_KEY" in st.secrets:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    else:
        st.warning("⚠️ مفتاح Groq مفقود")
        client = None
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
    """الدالة التي تقوم بالعمل الشاق"""
    print(f"[{datetime.now()}] بدء التحديث الخلفي...")
    all_data = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for category, feeds in RSS_SOURCES.items():
            cat_items = []
            futures = [executor.submit(fetch_single_feed, src, url, 15) for src, url in feeds.items()]
            for f in concurrent.futures.as_completed(futures):
                cat_items.extend(f.result())
            all_data[category] = cat_items
            
    db_content = {
        "last_updated": datetime.now().timestamp(),
        "data": all_data
    }
    # الكتابة الذرية لتجنب تلف الملف
    temp_file = DB_FILE + ".tmp"
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(db_content, f, ensure_ascii=False)
    os.replace(temp_file, DB_FILE)
    print(f"[{datetime.now()}] تم التحديث وحفظ الملف.")

# --- نظام الجدولة الخلفية (Background Scheduler) ---
@st.cache_resource
def start_background_worker():
    """هذا العامل يعمل في الخلفية للأبد ولا يتوقف"""
    def worker_loop():
        while True:
            try:
                # 1. التحقق من الملف
                if os.path.exists(DB_FILE):
                    with open(DB_FILE, 'r', encoding='utf-8') as f:
                        db = json.load(f)
                    last_ts = db.get('last_updated', 0)
                else:
                    last_ts = 0

                now = datetime.now()
                last_time = datetime.fromtimestamp(last_ts)
                
                # توقيت المغرب للتنظيف
                tz_ma = pytz.timezone('Africa/Casablanca')
                now_ma = datetime.now(tz_ma)

                # شرط 1: التنظيف الساعة 2:30 صباحاً
                if now_ma.hour == 2 and 30 <= now_ma.minute <= 35:
                    if os.path.exists(DB_FILE):
                        os.remove(DB_FILE)
                        print("🧹 تم تنظيف الأرشيف اليومي.")
                        # ننتظر قليلاً حتى لا يكرر الحذف في نفس الدقيقة
                        time.sleep(400) 
                        continue

                # شرط 2: التحديث كل ساعة
                diff = now - last_time
                if diff.total_seconds() > 3600 or last_ts == 0:
                    update_database_logic()
                
                # ننام دقيقة قبل الفحص التالي
                time.sleep(60)
                
            except Exception as e:
                print(f"خطأ في العامل الخلفي: {e}")
                time.sleep(60)

    # تشغيل الخيط في الخلفية
    t = threading.Thread(target=worker_loop, daemon=True)
    t.start()
    return t

# تشغيل العامل الخلفي مرة واحدة فقط
start_background_worker()

# ==========================================
# 5. الواجهة الأمامية (Frontend)
# ==========================================
def get_text(url):
    try:
        d = trafilatura.fetch_url(url)
        return trafilatura.extract(d) if d else None
    except: return None

def rewrite(text, tone, instr):
    if not client: return "خطأ: المفتاح غير موجود"
    prompt = f"""
    أنت محرر صحفي. أعد صياغة هذا الخبر لـ "هاشمي بريس".
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

st.title("🦅 وكيل يقين - الأرشيف التلقائي")

# قراءة البيانات للعرض
if os.path.exists(DB_FILE):
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        db = json.load(f)
    
    last_up = datetime.fromtimestamp(db['last_updated']).strftime('%H:%M')
    st.caption(f"📅 آخر تحديث للنظام: {last_up} (يتم التحديث تلقائياً كل ساعة)")
    
    with st.sidebar:
        st.header("التحكم")
        cat = st.selectbox("القسم", list(db['data'].keys()))
        news_list = db['data'][cat]
        tone = st.select_slider("النبرة", ["رسمي", "تحليلي", "تفاعلي"])
        ins = st.text_input("توجيهات")
        if st.button("تحديث يدوي قسري"):
            with st.spinner("جاري التحديث..."):
                update_database_logic()
            st.rerun()

    # عرض الأخبار
    opts = [f"【{n['source']}】 {n['title']}" for n in news_list]
    idx = st.selectbox("اختر الخبر:", range(len(opts)), format_func=lambda x: opts[x])
    
    if st.button("✨ صياغة"):
        sel = news_list[idx]
        with st.status("جاري العمل..."):
            txt = get_text(sel['link'])
            if txt:
                res = rewrite(txt, tone, ins)
                col1, col2 = st.columns(2)
                col1.info("الأصل"); col1.markdown(f"<div class='news-card'>{txt[:500]}...</div>", unsafe_allow_html=True)
                col2.success("النتيجة"); col2.markdown(f"<div class='seo-result'>{res}</div>", unsafe_allow_html=True)
                st.download_button("تحميل", res, "art.txt")
            else: st.error("الموقع محمي")

else:
    st.warning("⏳ النظام يقوم بالتمهيد الأولي وجلب الأخبار... يرجى تحديث الصفحة بعد دقيقة.")
    # إذا لم يوجد ملف، العامل الخلفي سيقوم بإنشائه قريباً
