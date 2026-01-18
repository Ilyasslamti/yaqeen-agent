import streamlit as st
import feedparser
import trafilatura
from groq import Groq
import concurrent.futures
import json
import os
import socket
import requests
import manadger_lib  # استدعاء مكتبة الماندجر

# ==========================================
# 0. إعدادات النظام
# ==========================================
SYSTEM_VERSION = "V34.0_CSS_FIX" # تحديث الإصدار لإجبار المتصفح على تحميل التصميم الجديد
st.set_page_config(page_title="يقين - Manadger Tech", page_icon="🦅", layout="wide")
socket.setdefaulttimeout(15)
DB_FILE = "news_db_v33.json"

# ==========================================
# 1. نظام التنظيف
# ==========================================
if "sys_version" not in st.session_state:
    st.session_state["sys_version"] = SYSTEM_VERSION
    st.cache_data.clear()

# ==========================================
# 2. المصادر (سحبها من المكتبة)
# ==========================================
RSS_SOURCES = manadger_lib.RSS_DATABASE

# ==========================================
# 3. CSS (تم إصلاح مشكلة العنوان الخلفي)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
    
    html, body, h1, h2, h3, h4, h5, h6, p, div, span, label, button, input, textarea, .stMarkdown, .stText {
        font-family: 'Cairo', sans-serif; text-align: right;
    }
    i, .material-icons, [data-testid="stExpander"] svg { font-family: initial !important; }

    /* --- إصلاح مشكلة العنوان المتداخل (هام جداً) --- */
    h1 {
        position: relative !important;  /* يمنع الظهور كخلفية */
        opacity: 1 !important;          /* يمنع الشفافية */
        z-index: 10 !important;         /* يجعله فوق كل العناصر */
        background: transparent !important;
        margin-bottom: 20px !important; /* يترك مسافة تحته */
        display: block !important;
        width: 100% !important;
        color: #1e3a8a !important;      /* لون أزرق غامق واضح */
    }

    .brand-header {
        text-align: center; background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 25px; border-radius: 15px; border-bottom: 4px solid #1e3a8a; margin-bottom: 20px;
    }
    .main-title { color: #1e3a8a; font-size: 2.2rem; font-weight: 800; margin: 0; }
    .company-badge { background-color: #1e3a8a; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; display: inline-block; }

    .stTabs [data-baseweb="tab-list"] { justify-content: center; background-color: #fff; border-radius: 10px; padding: 5px; }
    .stTabs [data-baseweb="tab"] { font-weight: 700; color: #495057; }
    .stTabs [aria-selected="true"] { color: #1e3a8a !important; border-bottom: 3px solid #1e3a8a !important; }

    .comparison-box {
        height: 600px; overflow-y: auto; padding: 25px; border-radius: 8px;
        border: 1px solid #ddd; direction: rtl; text-align: right; font-size: 1rem; line-height: 1.8;
    }
    
    /* تخصيص العناوين داخل المقال لضمان عدم تداخلها */
    .comparison-box h1 {
        font-size: 1.8rem !important;
        border-bottom: 2px solid #eee;
        padding-bottom: 15px;
        margin-top: 0 !important;
    }
    
    .comparison-box h2 {
        font-size: 1.4rem !important;
        color: #333 !important;
        margin-top: 25px !important;
        margin-bottom: 10px !important;
        font-weight: 800 !important;
    }

    .original-text { background-color: #f8f9fa; border-right: 4px solid #6c757d; }
    .new-text { background-color: #ffffff; border-right: 4px solid #22c55e; border-left: 1px solid #eee; }
    
    .stButton>button { width: 100%; border-radius: 8px; height: 50px; font-weight: 700; font-size: 16px; }
    #MainMenu {visibility: visible;} footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. المنطق الخلفي
# ==========================================

def get_groq_client():
    api_key = manadger_lib.get_safe_key()
    if api_key:
        return Groq(api_key=api_key)
    return None

def fetch_feed_items(source_name, url):
    items = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        d = feedparser.parse(url)
        if not d.entries:
            resp = requests.get(url, headers=headers, timeout=10)
            d = feedparser.parse(resp.content)
            
        for e in d.entries[:6]: 
            items.append({
                "title": e.title, "link": e.link, "source": source_name,
                "published": e.get("published", "")
            })
    except: pass
    return items

def update_category_data(category):
    feeds = RSS_SOURCES[category]
    all_items = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_feed_items, src, url) for src, url in feeds.items()]
        for f in concurrent.futures.as_completed(futures):
            all_items.extend(f.result())
    return all_items

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get("version") != SYSTEM_VERSION: return {}
                return data
        except: return {}
    return {}

def save_db(data):
    data["version"] = SYSTEM_VERSION
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

def get_text(url):
    try:
        d = trafilatura.fetch_url(url)
        return trafilatura.extract(d) if d else None
    except: return None

# --- المحرك القسري (Hard Enforcement Engine) ---
def smart_rewrite(text, keyword):
    client = get_groq_client()
    
    if not client:
        return "خطأ: لم يتم العثور على مفاتيح API صالحة في ملف Secrets.", "System Error"

    try:
        final_prompt = manadger_lib.ELITE_PROMPT.format(keyword=keyword)
        final_prompt += f"\n{text[:4000]}"
        
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": final_prompt}],
            model="llama-3.3-70b-versatile", 
            temperature=0.5 
        )
        return res.choices[0].message.content, "Groq (Elite Mode)"
    except Exception as e:
        return f"حدث خطأ أثناء المعالجة: {str(e)}", "Error"

# ==========================================
# 5. الواجهة الأمامية
# ==========================================

st.markdown("""
<div class='brand-header'>
    <span class='company-badge'>Manadger Tech</span>
    <h1 class='main-title'>وكيل يقين - Elite Edition</h1>
    <p style='color:#6c757d; margin-top:5px'>نظام التحرير الصارم V34.0</p>
</div>
""", unsafe_allow_html=True)

db = load_db()
cats = list(RSS_SOURCES.keys())
tabs = st.tabs(cats)

for i, cat_name in enumerate(cats):
    with tabs[i]:
        if "data" in db and cat_name in db["data"] and len(db["data"][cat_name]) > 0:
            news_list = db["data"][cat_name]
            
            c1, c2 = st.columns([3, 1])
            with c1: st.success(f"متاح {len(news_list)} خبر في {cat_name}")
            with c2:
                if st.button("🔄 تحديث المصادر", key=f"up_{i}"):
                    with st.spinner("جاري الاتصال بـترسانة المصادر..."):
                        if "data" not in db: db["data"] = {}
                        db["data"][cat_name] = update_category_data(cat_name)
                        save_db(db)
                    st.rerun()

            opts = [f"{n['source']} | {n['title']}" for n in news_list]
            idx = st.selectbox("اختر الخبر:", range(len(opts)), format_func=lambda x: opts[x], key=f"sel_{i}")

            st.info("👇 أدخل الكلمة المفتاحية لضبط SEO (إجباري لنتائج دقيقة)")
            keyword_input = st.text_input("الكلمة المفتاحية (Keyword)", value="أخبار المغرب", key=f"kw_{i}")

            if st.button("✨ صياغة صحفية احترافية", type="primary", key=f"go_{i}"):
                sel = news_list[idx]
                with st.status("جاري التحرير وفق القواعد الصارمة...", expanded=True) as status:
                    st.write("📥 سحب النص الأصلي...")
                    txt = get_text(sel['link'])
                    
                    if txt:
                        st.write("🧠 تطبيق برومبت الماندجر (Hard Enforcement)...")
                        res, provider = smart_rewrite(txt, keyword_input)
                        
                        if "Error" not in provider:
                            status.update(label=f"تم التحرير بنجاح!", state="complete", expanded=False)
                            
                            st.markdown("---")
                            comp_c1, comp_c2 = st.columns(2)
                            with comp_c1:
                                st.info("النص الأصلي")
                                st.markdown(f"<div class='comparison-box original-text'>{txt}</div>", unsafe_allow_html=True)
                            with comp_c2:
                                st.success(f"مقال هاشمي بريس ({provider})")
                                # استخدام markdown مباشرة بدون وضعه داخل div HTML لضمان قراءة العناوين بشكل صحيح
                                st.markdown(f"<div class='comparison-box new-text'>{res}</div>", unsafe_allow_html=True)
                            
                            st.download_button("📥 تحميل المقال (TXT)", res, "article.txt", key=f"dl_{i}")
                        else:
                            status.update(label="فشل", state="error")
                            st.error(res)
                    else:
                        status.update(label="فشل", state="error")
                        st.error("الموقع محمي أو النص غير متاح.")
        else:
            st.warning(f"لا توجد أخبار في {cat_name}")
            if st.button(f"📥 سحب أخبار {cat_name} الآن", type="primary", key=f"init_{i}"):
                with st.spinner("جاري الاتصال بترسانة المصادر..."):
                    if "data" not in db: db["data"] = {}
                    db["data"][cat_name] = update_category_data(cat_name)
                    save_db(db)
                st.rerun()
