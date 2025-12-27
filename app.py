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
# 0. إعدادات الصفحة
# ==========================================
st.set_page_config(page_title="وكيل يقين AI", page_icon="🦅", layout="wide")
socket.setdefaulttimeout(10)
DB_FILE = "news_db_tabs.json"

# ==========================================
# 1. المصادر
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
# 2. CSS (التصحيح: عدم إجبار الأيقونات على تغيير الخط)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    
    /* تطبيق الخط على النصوص العربية فقط وليس الأيقونات */
    h1, h2, h3, h4, h5, h6, p, div, span, label, .stMarkdown, .stText {
        font-family: 'Cairo', sans-serif;
        text-align: right;
    }
    
    /* استثناء الأيقونات من الخط العربي لكي لا تتشوه */
    .material-icons, .icon-button, i {
        font-family: inherit !important;
    }

    /* محاذاة العناصر لليمين */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] { 
        direction: rtl; text-align: right; 
    }
    
    /* البطاقات */
    .news-card {
        background: #fff; border: 1px solid #ddd; padding: 15px; 
        border-radius: 8px; margin-bottom: 10px; text-align: right; direction: rtl;
    }
    
    /* الأزرار */
    .stButton>button { width: 100%; height: 50px; font-weight: bold; border-radius: 10px; }
    
    /* إخفاء الفوتر */
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. المنطق
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
# 4. الواجهة (نظام التبويبات - Tabs)
# ==========================================

st.markdown("<h2 style='text-align: center; color: #1e3a8a;'>🦅 وكيل يقين</h2>", unsafe_allow_html=True)

# تحميل البيانات
db = load_db()

# إنشاء تبويبات للأقسام (أفضل للموبايل)
cats = list(RSS_SOURCES.keys())
tabs = st.tabs(cats) # سيظهر شريط في الأعلى للتنقل بين الأقسام

# التعامل مع كل تبويب
for i, cat_name in enumerate(cats):
    with tabs[i]:
        # محتوى التبويب
        if cat_name in db and len(db[cat_name]) > 0:
            news_list = db[cat_name]
            
            # زر تحديث صغير
            if st.button(f"🔄 تحديث {cat_name}", key=f"btn_up_{i}"):
                with st.spinner("جاري التحديث..."):
                    items = update_category_data(cat_name)
                    db[cat_name] = items
                    save_db(db)
                st.rerun()

            st.success(f"متاح {len(news_list)} خبر")
            
            # قائمة الأخبار
            opts = [f"{n['source']} - {n['title']}" for n in news_list]
            idx = st.selectbox("اختر الخبر:", range(len(opts)), format_func=lambda x: opts[x], key=f"sel_{i}")
            
            # إعدادات سريعة
            with st.expander("⚙️ إعدادات الصياغة"):
                tone = st.select_slider("النبرة", ["رسمي", "تحليلي", "عاجل"], key=f"tone_{i}")
                ins = st.text_input("توجيهات", key=f"ins_{i}")

            # زر الصياغة
            if st.button("✨ صياغة الخبر", key=f"go_{i}", type="primary"):
                sel = news_list[idx]
                with st.status("جاري العمل..."):
                    txt = get_text(sel['link'])
                    if txt:
                        res = rewrite(txt, tone, ins)
                        st.markdown("---")
                        st.subheader("النتيجة:")
                        st.markdown(f"<div class='news-card' style='background:#f0fdf4'>{res}</div>", unsafe_allow_html=True)
                        st.download_button("📥 تحميل", res, "article.txt", key=f"dl_{i}")
                    else: st.error("الموقع محمي")
        else:
            # إذا كان القسم فارغاً
            st.warning(f"لا توجد أخبار في {cat_name}")
            if st.button(f"📥 جلب الأخبار الآن", key=f"init_{i}", type="primary"):
                with st.spinner("جاري الاتصال بالمصادر..."):
                    items = update_category_data(cat_name)
                    db[cat_name] = items
                    save_db(db)
                st.rerun()

