import streamlit as st
import feedparser
import trafilatura
from groq import Groq
import concurrent.futures
import json
import os
import socket
import requests # المكتبة الجديدة لكسر الحماية
from datetime import datetime

# ==========================================
# 0. إعدادات النظام
# ==========================================
st.set_page_config(page_title="يقين - Manadger Tech", page_icon="🦅", layout="wide")
socket.setdefaulttimeout(15) # زيادة المهلة قليلاً
DB_FILE = "news_db_v6.json" # إصدار جديد

# ==========================================
# 1. المصادر
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
    "الرياضية": {
        "البطولة": "https://www.elbotola.com/rss",
        "هسبريس رياضة": "https://hesport.com/feed",
        "المنتخب": "https://almountakhab.com/rss",
        "هاي كورة": "https://hihi2.com/feed",
    }
}

# ==========================================
# 2. تصميم الواجهة (Manadger Tech)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
    
    * { font-family: 'Cairo', sans-serif !important; }
    h1, h2, h3, h4, h5, h6, p, div, span, label, button, .stMarkdown, .stText { text-align: right; }
    
    /* الترويسة */
    .brand-header {
        text-align: center; background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 25px; border-radius: 15px; margin-bottom: 20px; border-bottom: 4px solid #1e3a8a;
    }
    .brand-title { color: #1e3a8a; font-size: 2.2rem; font-weight: 800; margin: 0; }
    .company-tag { background-color: #1e3a8a; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; }

    /* التبويبات */
    .stTabs [data-baseweb="tab-list"] { justify-content: center; background: #fff; border-radius: 10px; padding: 5px; }
    .stTabs [data-baseweb="tab"] { font-weight: 700; color: #495057; }
    .stTabs [aria-selected="true"] { color: #1e3a8a !important; border-bottom: 3px solid #1e3a8a !important; }

    /* البطاقات */
    .news-card {
        background: white; border: 1px solid #e2e8f0; border-right: 5px solid #3b82f6;
        border-radius: 10px; padding: 15px; margin-bottom: 10px; direction: rtl; text-align: right;
    }
    .result-box {
        background: #f0fdf4; border: 1px solid #bbf7d0; border-right: 5px solid #22c55e;
        border-radius: 10px; padding: 20px; direction: rtl; margin-top: 15px;
    }
    .stButton>button { width: 100%; border-radius: 8px; height: 50px; font-weight: 700; }
    
    #MainMenu {visibility: visible;} footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. المنطق (مع كسر الحماية)
# ==========================================
try:
    if "GROQ_API_KEY" in st.secrets:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    else: client = None
except: client = None

# هذه هي الدالة المعدلة لكسر الحماية
def fetch_feed_items(source_name, url):
    items = []
    # قناع المتصفح (خداع السيرفرات)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        # 1. طلب المحتوى كمتصفح
        response = requests.get(url, headers=headers, timeout=10)
        # 2. تمرير المحتوى لـ feedparser
        if response.status_code == 200:
            d = feedparser.parse(response.content)
            for e in d.entries[:10]:
                items.append({
                    "title": e.title, "link": e.link, "source": source_name,
                    "published": e.get("published", "")
                })
        else:
            # محاولة احتياطية
            d = feedparser.parse(url)
            for e in d.entries[:10]:
                items.append({"title": e.title, "link": e.link, "source": source_name, "published": ""})
                
    except Exception: 
        pass
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
    prompt = f"أنت محرر صحفي لـ هاشمي بريس. أعد صياغة الخبر: {text[:2500]}. الأسلوب: {tone}. ملاحظات: {instr}. العنوان H1."
    try:
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile", temperature=0.7
        )
        return res.choices[0].message.content
    except Exception as e: return str(e)

# ==========================================
# 4. الواجهة الأمامية
# ==========================================

# A. الترويسة
st.markdown("""
<div class='brand-header'>
    <h1 class='brand-title'>يقين - وكيل ذكاء اصطناعي</h1>
    <span class='company-tag'>من شركة Manadger Tech</span>
    <p style='color:#666; margin-top:5px'>نظام رصد وتحرير الأخبار الذكي</p>
</div>
""", unsafe_allow_html=True)

# B. البيانات
db = load_db()

# C. التبويبات
cats = list(RSS_SOURCES.keys())
tabs = st.tabs(cats)

for i, cat_name in enumerate(cats):
    with tabs[i]:
        # التأكد من وجود البيانات
        if cat_name in db and "data" in db and cat_name in db["data"] and len(db["data"][cat_name]) > 0:
            news_list = db["data"][cat_name]
        else:
            # محاولة قراءة الهيكل القديم إذا وجد
            if cat_name in db and isinstance(db[cat_name], list):
                news_list = db[cat_name]
            else:
                news_list = []

        if news_list:
            # العرض
            c1, c2 = st.columns([3, 1])
            with c1: st.success(f"✅ تم جلب {len(news_list)} مقال")
            with c2:
                if st.button("🔄 تحديث", key=f"up_{i}"):
                    with st.spinner(f"جاري سحب {cat_name}..."):
                        if "data" not in db: db["data"] = {} # إصلاح الهيكل
                        # حفظ في المكانين لضمان التوافق
                        items = update_category_data(cat_name)
                        db["data"][cat_name] = items 
                        db[cat_name] = items
                        save_db(db)
                    st.rerun()

            opts = [f"{n['source']} | {n['title']}" for n in news_list]
            idx = st.selectbox("اختر المقال:", range(len(opts)), format_func=lambda x: opts[x], key=f"sel_{i}")

            with st.expander("⚙️ خيارات الصياغة"):
                tone = st.select_slider("الأسلوب", ["رسمي", "تحليلي", "تفاعلي"], key=f"tn_{i}")
                ins = st.text_input("توجيهات", key=f"in_{i}")

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
            st.warning(f"لا توجد مقالات محفوظة في {cat_name}")
            if st.button(f"📥 جلب مقالات {cat_name} الآن", type="primary", key=f"init_{i}"):
                with st.spinner("جاري الاتصال بالمصادر (مع كسر الحماية)..."):
                    items = update_category_data(cat_name)
                    if "data" not in db: db["data"] = {}
                    db["data"][cat_name] = items
                    db[cat_name] = items
                    save_db(db)
                st.rerun()
