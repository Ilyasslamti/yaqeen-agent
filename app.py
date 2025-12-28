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
# 0. إعدادات النظام
# ==========================================
SYSTEM_VERSION = "V6.1_FINAL_CLEAN"
st.set_page_config(page_title="يقين - Manadger Tech", page_icon="🦅", layout="wide")
socket.setdefaulttimeout(10)
DB_FILE = "news_db_v6.json"

# ==========================================
# 1. نظام التنظيف (لضمان التحديث)
# ==========================================
if "sys_version" not in st.session_state:
    st.session_state["sys_version"] = SYSTEM_VERSION
    st.cache_data.clear()

# ==========================================
# 2. المصادر
# ==========================================
RSS_SOURCES = {
    "أخبار الشمال": {
        "شمال بوست": "https://chamalpost.net/feed",
        "بريس تطوان": "https://presstetouan.com/feed",
        "طنجة 24": "https://tanja24.com/feed",
        "تطوان بريس": "https://tetouanpress.ma/feed",
        "كاب 24": "https://cap24.tv/feed",
    },
    "الصحافة المغربية": {
        "هسبريس": "https://www.hespress.com/feed",
        "العمق": "https://al3omk.com/feed",
        "مدار 21": "https://madar21.com/feed",
        "كود": "https://www.goud.ma/feed",
        "الصباح": "https://assabah.ma/feed",
    },
    "فن ومشاهير": {
        "لالة مولاتي": "http://www.lallamoulati.ma/feed/",
        "سلطانة": "https://soltana.ma/feed",
        "غالية": "https://ghalia.ma/feed",
        "هسبريس فن": "https://www.hespress.com/art-et-culture/feed",
        "سيدتي": "https://www.sayidaty.net/rss/3",
    },
    "الرياضة": {
        "البطولة": "https://www.elbotola.com/rss",
        "هسبريس رياضة": "https://hesport.com/feed",
        "المنتخب": "https://almountakhab.com/rss",
        "هاي كورة": "https://hihi2.com/feed",
    }
}

# ==========================================
# 3. CSS (إصلاح الأيقونات والخطوط)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
    
    /* تطبيق الخط العربي على النصوص فقط */
    html, body, h1, h2, h3, h4, h5, h6, p, div, span, label, button, input, textarea, .stMarkdown, .stText {
        font-family: 'Cairo', sans-serif;
        text-align: right;
    }
    
    /* حماية الأيقونات من التشوه */
    i, .material-icons, [data-testid="stExpander"] svg, .st-emotion-cache-1pbqpg9 {
        font-family: initial !important;
    }

    /* الترويسة */
    .brand-header {
        text-align: center;
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 25px;
        border-radius: 15px;
        border-bottom: 4px solid #1e3a8a;
        margin-bottom: 20px;
    }
    .main-title { color: #1e3a8a; font-size: 2.2rem; font-weight: 800; margin: 0; }
    .company-badge { background-color: #1e3a8a; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; display: inline-block; margin-bottom: 5px; }

    /* التبويبات */
    .stTabs [data-baseweb="tab-list"] { justify-content: center; background-color: #fff; border-radius: 10px; padding: 5px; }
    .stTabs [data-baseweb="tab"] { font-weight: 700; color: #495057; }
    .stTabs [aria-selected="true"] { color: #1e3a8a !important; border-bottom: 3px solid #1e3a8a !important; }

    /* البطاقات */
    .news-card {
        background: white; border: 1px solid #e2e8f0; border-right: 5px solid #3b82f6;
        border-radius: 10px; padding: 15px; margin-bottom: 10px; direction: rtl; text-align: right;
    }

    /* صندوق النتيجة */
    .result-box {
        background: #f0fdf4; border: 1px solid #bbf7d0; border-right: 5px solid #22c55e;
        border-radius: 10px; padding: 20px; direction: rtl; margin-top: 15px;
    }

    /* الأزرار */
    .stButton>button { width: 100%; border-radius: 8px; height: 50px; font-weight: 700; font-size: 16px; }

    #MainMenu {visibility: visible;} 
    footer {visibility: hidden;}
    
    /* محاذاة المدخلات */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] { 
        direction: rtl; text-align: right; 
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. المنطق الخلفي
# ==========================================
try:
    if "GROQ_API_KEY" in st.secrets:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    else: client = None
except: client = None

def fetch_feed_items(source_name, url):
    items = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        # محاولة ذكية: مباشر ثم عبر Requests
        d = feedparser.parse(url)
        if not d.entries:
            resp = requests.get(url, headers=headers, timeout=8)
            d = feedparser.parse(resp.content)
            
        for e in d.entries[:10]:
            items.append({
                "title": e.title, "link": e.link, "source": source_name,
                "published": e.get("published", "")
            })
    except: pass
    return items

def update_category_data(category):
    feeds = RSS_SOURCES[category]
    all_items = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(fetch_feed_items, src, url) for src, url in feeds.items()]
        for f in concurrent.futures.as_completed(futures):
            all_items.extend(f.result())
    return all_items

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        except: return {}
    return {}

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

def get_text(url):
    try:
        d = trafilatura.fetch_url(url)
        return trafilatura.extract(d) if d else None
    except: return None

def rewrite(text, tone, instr):
    if not client: return "خطأ: المفتاح مفقود"
    prompt = f"أعد صياغة هذا الخبر لـ هاشمي بريس. الأسلوب: {tone}. ملاحظات: {instr}. النص: {text[:2500]}"
    try:
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile", temperature=0.7
        )
        return res.choices[0].message.content
    except Exception as e: return str(e)

# ==========================================
# 5. الواجهة الأمامية
# ==========================================

st.markdown("""
<div class='brand-header'>
    <span class='company-badge'>Manadger Tech</span>
    <h1 class='main-title'>وكيل يقين AI</h1>
    <p style='color:#6c757d; margin-top:5px'>غرفة التحرير الذكية</p>
</div>
""", unsafe_allow_html=True)

db = load_db()

# التبويبات (Tabs)
cats = list(RSS_SOURCES.keys())
tabs = st.tabs(cats)

for i, cat_name in enumerate(cats):
    with tabs[i]:
        # هل توجد بيانات؟
        if "data" in db and cat_name in db["data"] and len(db["data"][cat_name]) > 0:
            news_list = db["data"][cat_name]
            
            # معلومات وزر التحديث
            c1, c2 = st.columns([3, 1])
            with c1: st.success(f"متاح {len(news_list)} مقال")
            with c2:
                if st.button("🔄 تحديث", key=f"up_{i}"):
                    with st.spinner("جاري التحديث..."):
                        if "data" not in db: db["data"] = {}
                        db["data"][cat_name] = update_category_data(cat_name)
                        save_db(db)
                    st.rerun()

            # اختيار المقال
            opts = [f"{n['source']} | {n['title']}" for n in news_list]
            idx = st.selectbox("اختر المقال:", range(len(opts)), format_func=lambda x: opts[x], key=f"sel_{i}")

            # الإعدادات
            with st.expander("⚙️ خيارات الصياغة"):
                tone = st.select_slider("الأسلوب", ["رسمي", "تحليلي", "تفاعلي"], key=f"tn_{i}")
                ins = st.text_input("توجيهات", key=f"in_{i}")

            # التنفيذ
            if st.button("✨ إعادة صياغة المقال", type="primary", key=f"go_{i}"):
                sel = news_list[idx]
                with st.status("جاري العمل...", expanded=True):
                    st.write("📥 سحب النص...")
                    txt = get_text(sel['link'])
                    if txt:
                        st.write("🧠 الذكاء الاصطناعي يكتب...")
                        res = rewrite(txt, tone, ins)
                        st.success("تم!")
                        st.markdown(f"<div class='result-box'>{res}</div>", unsafe_allow_html=True)
                        st.download_button("📥 تحميل النص", res, "article.txt", key=f"dl_{i}")
                    else: st.error("الموقع محمي")
        else:
            # حالة القسم الفارغ
            st.warning(f"لا توجد مقالات محفوظة في {cat_name}")
            if st.button(f"📥 جلب مقالات {cat_name} الآن", type="primary", key=f"init_{i}"):
                with st.spinner("جاري الاتصال بالمصادر..."):
                    if "data" not in db: db["data"] = {}
                    db["data"][cat_name] = update_category_data(cat_name)
                    save_db(db)
                st.rerun()

# End of file
