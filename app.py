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
# 1. إعدادات الصفحة
# ==========================================
st.set_page_config(page_title="وكيل يقين AI", page_icon="🦅", layout="wide")
socket.setdefaulttimeout(10)

DB_FILE = "news_db_final.json"

# ==========================================
# 2. CSS (إصلاح شامل للهاتف)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    * { font-family: 'Cairo', sans-serif !important; }
    
    /* إصلاح النصوص */
    .stMarkdown, .stText, h1, h2, h3, p, div { text-align: right !important; }
    
    /* بطاقات الأخبار */
    .news-card {
        background: #fff; border: 1px solid #ddd; padding: 15px; 
        border-radius: 8px; margin-bottom: 10px; text-align: right; direction: rtl;
    }
    
    /* صندوق النتيجة */
    .seo-box {
        background: #f0fdfa; border: 1px solid #ccfbf1; padding: 15px;
        border-radius: 8px; text-align: right; direction: rtl;
    }

    /* تكبير الأزرار للموبايل */
    .stButton>button { width: 100%; height: 60px; font-size: 18px; border-radius: 12px; }

    /* هام جداً: إظهار الهيدر لحل مشكلة السهم الغريب */
    header {visibility: visible !important;}
    #MainMenu {visibility: visible !important;}
    
    /* إخفاء الفوتر فقط */
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. المصادر
# ==========================================
RSS_SOURCES = {
    "أخبار الشمال 🌊": {
        "شمال بوست": "https://chamalpost.net/feed",
        "بريس تطوان": "https://presstetouan.com/feed",
        "طنجة 24": "https://tanja24.com/feed",
        "تطوان بريس": "https://tetouanpress.ma/feed",
        "كاب 24": "https://cap24.tv/feed",
    },
    "أخبار المغرب 🇲🇦": {
        "هسبريس": "https://www.hespress.com/feed",
        "العمق": "https://al3omk.com/feed",
        "مدار 21": "https://madar21.com/feed",
        "كود": "https://www.goud.ma/feed",
        "الصباح": "https://assabah.ma/feed",
    },
    "فنية ومشاهير 🎭": {
        "سلطانة": "https://soltana.ma/feed",
        "لالة مولاتي": "http://www.lallamoulati.ma/feed/",
        "غالية": "https://ghalia.ma/feed",
        "هسبريس فن": "https://www.hespress.com/art-et-culture/feed",
    },
    "الرياضية ⚽": {
        "البطولة": "https://www.elbotola.com/rss",
        "هسبريس الرياضية": "https://hesport.com/feed",
        "المنتخب": "https://almountakhab.com/rss",
    }
}

# ==========================================
# 4. دوال النظام
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
# 5. الواجهة الرئيسية (التصميم الجديد)
# ==========================================

st.markdown("<h1 style='text-align: center; color: #1e3a8a;'>🦅 وكيل يقين</h1>", unsafe_allow_html=True)

# تحميل البيانات
db = load_db()

# --- 1. اختيار القسم (في وسط الشاشة) ---
st.markdown("### 👇 اختر القسم الصحفي:")
all_cats = list(RSS_SOURCES.keys())

# استخدام radio button أفقي (أسهل للموبايل)
selected_cat = st.radio("الأقسام", all_cats, horizontal=True, label_visibility="collapsed")

# --- 2. التحكم في القسم ---
col_up, col_set = st.columns([2, 1])

with col_set:
    # إعدادات بسيطة
    with st.expander("⚙️ إعدادات الصياغة"):
        tone = st.select_slider("النبرة", ["رسمي", "تحليلي", "عاجل"])
        ins = st.text_input("توجيهات")

# --- 3. عرض الأخبار ---
if selected_cat in db and len(db[selected_cat]) > 0:
    news_list = db[selected_cat]
    
    with col_up:
        if st.button(f"🔄 تحديث {selected_cat}"):
            with st.spinner("جاري التحديث..."):
                items = update_category_data(selected_cat)
                db[selected_cat] = items
                save_db(db)
            st.rerun()

    st.success(f"متاح {len(news_list)} خبر في {selected_cat}")
    
    # القائمة
    opts = [f"{n['source']} - {n['title']}" for n in news_list]
    idx = st.selectbox("اختر الخبر:", range(len(opts)), format_func=lambda x: opts[x])
    
    # زر الصياغة
    if st.button("✨ صياغة الخبر الآن", type="primary"):
        sel = news_list[idx]
        with st.status("جاري العمل...", expanded=True):
            txt = get_text(sel['link'])
            if txt:
                res = rewrite(txt, tone, ins)
                
                st.markdown("---")
                st.subheader("النتيجة:")
                st.markdown(f"<div class='seo-box'>{res}</div>", unsafe_allow_html=True)
                st.download_button("📥 تحميل المقال", res, "article.txt")
            else: st.error("الموقع محمي")

else:
    # إذا كان القسم فارغاً
    st.warning(f"لا توجد أخبار محفوظة لقسم {selected_cat}")
    if st.button(f"📥 جلب أخبار {selected_cat} لأول مرة", type="primary"):
        with st.spinner("جاري الاتصال بالمصادر..."):
            items = update_category_data(selected_cat)
            db[selected_cat] = items
            save_db(db)
        st.rerun()
