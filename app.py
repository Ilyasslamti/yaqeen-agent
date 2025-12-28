import streamlit as st
import feedparser
import trafilatura
from groq import Groq
import concurrent.futures
import json
import os
import socket
from datetime import datetime

# ==========================================
# 0. إعدادات النظام
# ==========================================
st.set_page_config(page_title="يقين - Manadger Tech", page_icon="🦅", layout="wide")
socket.setdefaulttimeout(10)
DB_FILE = "news_db_v3.json" # نسخة جديدة

# ==========================================
# 1. المصادر (تم تحديث قسم الفن)
# ==========================================
RSS_SOURCES = {
    "أخبار الشمال": {
        "شمال بوست": "https://chamalpost.net/feed",
        "بريس تطوان": "https://presstetouan.com/feed",
        "طنجة 24": "https://tanja24.com/feed",
        "تطوان بريس": "https://tetouanpress.ma/feed",
        "كاب 24": "https://cap24.tv/feed",
    },
    "صحافة المغرب": {
        "هسبريس": "https://www.hespress.com/feed",
        "العمق": "https://al3omk.com/feed",
        "مدار 21": "https://madar21.com/feed",
        "كود": "https://www.goud.ma/feed",
        "الصباح": "https://assabah.ma/feed",
    },
    "فن وثقافة": {
        "لالة مولاتي": "http://www.lallamoulati.ma/feed/",
        "سلطانة": "https://soltana.ma/feed",
        "غالية": "https://ghalia.ma/feed",
        "هسبريس فن": "https://www.hespress.com/art-et-culture/feed",
        "سيدتي": "https://www.sayidaty.net/rss/3",
        "إليكِ": "https://www.ilaiki.net/feed",
    },
    "الرياضة": {
        "البطولة": "https://www.elbotola.com/rss",
        "هسبريس رياضة": "https://hesport.com/feed",
        "المنتخب": "https://almountakhab.com/rss",
        "هاي كورة": "https://hihi2.com/feed",
    }
}

# ==========================================
# 2. تصميم الواجهة (Manadger Tech Style)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
    
    /* توحيد الخط للنصوص العربية فقط */
    h1, h2, h3, h4, h5, h6, p, div, span, label, button, .stMarkdown, .stText {
        font-family: 'Cairo', sans-serif !important;
        text-align: right;
    }
    
    /* الهوية البصرية (الترويسة) */
    .brand-header {
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 15px;
        margin-bottom: 20px;
        border: 1px solid #dee2e6;
    }
    .brand-title {
        color: #1e3a8a;
        font-size: 2.2rem;
        font-weight: 800;
        margin: 0;
    }
    .brand-subtitle {
        color: #6c757d;
        font-size: 1.1rem;
        margin-top: 5px;
    }
    .company-tag {
        background-color: #1e3a8a;
        color: white;
        padding: 2px 10px;
        border-radius: 10px;
        font-size: 0.8rem;
        vertical-align: middle;
    }

    /* تحسين التبويبات (Tabs) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        justify-content: center;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #fff;
        border-radius: 8px;
        color: #495057;
        font-weight: 600;
        border: 1px solid #dee2e6;
        padding: 0 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1e3a8a !important;
        color: white !important;
        border: none;
    }

    /* البطاقات */
    .news-card {
        background: #fff; border: 1px solid #e9ecef; border-right: 5px solid #3b82f6;
        padding: 15px; border-radius: 10px; margin-bottom: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
        direction: rtl;
    }
    
    /* صندوق النتيجة */
    .result-box {
        background: #f0fdf4; border: 1px solid #bbf7d0; border-right: 5px solid #22c55e;
        padding: 20px; border-radius: 10px; direction: rtl;
    }

    /* الأزرار */
    .stButton>button { width: 100%; border-radius: 8px; font-weight: 700; height: 45px; }
    
    /* إخفاء العناصر التقنية */
    #MainMenu {visibility: visible;} footer {visibility: hidden;}
    
    /* إصلاح للموبايل */
    @media (max-width: 640px) {
        .brand-title { font-size: 1.6rem; }
        .stTabs [data-baseweb="tab"] { padding: 0 10px; font-size: 0.9rem; }
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. المنطق (Backend)
# ==========================================
try:
    if "GROQ_API_KEY" in st.secrets:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    else: client = None
except: client = None

def fetch_feed_items(source_name, url):
    items = []
    try:
        d = feedparser.parse(url)
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
            with open(DB_FILE, 'r', encoding='utf-8') as f: return json.load(f)
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
# 4. بناء الواجهة (الهيكلية الجديدة)
# ==========================================

# 1. الترويسة (Header)
st.markdown("""
<div class='brand-header'>
    <h1 class='brand-title'>🦅 يقين - <span style='font-size:1.5rem'>وكيل ذكاء اصطناعي</span></h1>
    <div style='margin-top:5px'>
        <span class='company-tag'>Manadger Tech</span>
    </div>
    <p class='brand-subtitle'>سكربت ناشر للكتاب والصحفيين</p>
</div>
""", unsafe_allow_html=True)

# 2. تحميل البيانات
db = load_db()

# 3. شريط التصنيفات (Tabs)
cats = list(RSS_SOURCES.keys())
tabs = st.tabs(cats)

# 4. محتوى التبويبات
for i, cat_name in enumerate(cats):
    with tabs[i]:
        # A. زر التحديث الخاص بالقسم
        col_msg, col_btn = st.columns([3, 1])
        
        # فحص وجود بيانات
        if cat_name in db and len(db[cat_name]) > 0:
            news_list = db[cat_name]
            with col_msg:
                st.info(f"متاح {len(news_list)} مقال في {cat_name}")
            with col_btn:
                if st.button("🔄 تحديث", key=f"r_{i}"):
                    with st.spinner("جاري جلب الجديد..."):
                        items = update_category_data(cat_name)
                        db[cat_name] = items
                        save_db(db)
                    st.rerun()

            # B. قائمة المقالات
            opts = [f"{n['source']} | {n['title']}" for n in news_list]
            idx = st.selectbox("اختر المقال:", range(len(opts)), format_func=lambda x: opts[x], key=f"s_{i}")

            # C. أدوات الصياغة (تظهر فقط بعد اختيار المقال)
            with st.expander("⚙️ إعدادات الصياغة (اختياري)", expanded=False):
                tone = st.select_slider("الأسلوب", ["رسمي", "تحليلي", "تفاعلي"], key=f"t_{i}")
                ins = st.text_input("توجيهات إضافية", key=f"in_{i}")

            # D. زر التنفيذ
            if st.button("✨ إعادة صياغة المقال", type="primary", key=f"g_{i}"):
                sel = news_list[idx]
                with st.status("جاري معالجة النص...", expanded=True):
                    st.write("📥 سحب المحتوى...")
                    txt = get_text(sel['link'])
                    if txt:
                        st.write("🧠 الذكاء الاصطناعي يكتب...")
                        res = rewrite(txt, tone, ins)
                        
                        st.markdown("---")
                        st.success("تمت الصياغة بنجاح!")
                        st.markdown(f"<div class='result-box'>{res}</div>", unsafe_allow_html=True)
                        st.download_button("📥 تحميل النص", res, "article.txt", key=f"d_{i}")
                    else:
                        st.error("عذراً، هذا الموقع محمي ولا يسمح بسحب النص.")

        else:
            # حالة القسم الفارغ
            st.warning(f"لا توجد مقالات محفوظة في {cat_name}")
            if st.button(f"📥 جلب مقالات {cat_name} الآن", type="primary", key=f"init_{i}"):
                with st.spinner("جاري الاتصال بالمصادر..."):
                    items = update_category_data(cat_name)
                    db[cat_name] = items
                    save_db(db)
                st.rerun()
