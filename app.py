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
# 0. إعدادات النظام (تحديث قسري)
# ==========================================
SYSTEM_VERSION = "V9.0_SEO_MASTER" 
st.set_page_config(page_title="يقين - Manadger Tech", page_icon="🦅", layout="wide")
socket.setdefaulttimeout(15) 
DB_FILE = "news_db_v8.json"

# ==========================================
# 1. نظام التنظيف الذكي والدورة اليومية
# ==========================================
# وظيفة لمسح البيانات في الساعة 3 صباحاً لبدء دورة جديدة
def auto_purge_at_3am():
    now = datetime.now()
    if now.hour == 3:
        if os.path.exists(DB_FILE):
            try:
                os.remove(DB_FILE)
                st.cache_data.clear()
            except: pass

auto_purge_at_3am()

if "sys_version" not in st.session_state:
    st.session_state["sys_version"] = SYSTEM_VERSION
    st.cache_data.clear()

# ==========================================
# 2. المصادر (القائمة الضخمة)
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
    },
    "الصحافة الوطنية (شامل) 🇲🇦": {
        "هسبريس": "https://www.hespress.com/feed",
        "شوف تيفي": "https://chouftv.ma/feed",
        "برلمان.كوم": "https://www.barlamane.com/feed",
        "هبة بريس": "https://ar.hibapress.com/feed",
        "اليوم 24": "https://www.alyaoum24.com/feed",
        "زنقة 20": "https://www.rue20.com/feed",
        "فبراير": "https://www.febrayer.com/feed",
        "العمق": "https://al3omk.com/feed",
        "مدار 21": "https://madar21.com/feed",
        "كود": "https://www.goud.ma/feed",
        "الصباح": "https://assabah.ma/feed",
        "الأحداث المغربية": "https://ahdath.info/feed",
        "آشكاين": "https://achkayen.com/feed",
        "الأيام 24": "https://www.alayam24.com/feed",
        "لكم": "https://lakome2.com/feed",
        "أنفاس بريس": "https://anfaspress.com/feed",
        "باناصا": "https://banassa.com/feed",
        "عبر": "https://aabbir.com/feed",
        "Le360 (عربي)": "https://ar.le360.ma/rss",
        "المصدر ميديا": "https://almasdar.ma/feed",
        "تليكسبريس": "https://telexpresse.com/feed",
        "سفيركم": "https://safir24.com/feed",
        "بديل": "https://badil.info/feed",
        "الجريدة 24": "https://aljarida24.ma/feed",
        "كواليس": "https://kawalis.ma/feed",
    },
    "فن ومشاهير 🎭": {
        "لالة مولاتي": "http://www.lallamoulati.ma/feed/",
        "سلطانة": "https://soltana.ma/feed",
        "غالية": "https://ghalia.ma/feed",
        "هسبريس فن": "https://www.hespress.com/art-et-culture/feed",
        "سيدتي": "https://www.sayidaty.net/rss/3",
        "اليوم 24 فن": "https://alyaoum24.com/category/%D9%81%D9%86/feed",
        "شوف تيفي فن": "https://chouftv.ma/category/%D9%81%D9%86-%D9%88-%D9%85%D8%B4%D8%A7%D9%87%D9%8A%D8%B1/feed",
    },
    "الرياضة ⚽": {
        "البطولة": "https://www.elbotola.com/rss",
        "هسبريس رياضة": "https://hesport.com/feed",
        "المنتخب": "https://almountakhab.com/rss",
        "هاي كورة": "https://hihi2.com/feed",
        "360 سبورت": "https://sport.le360.ma/rss",
    }
}

# ==========================================
# 3. CSS (تحسين العرض)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
    html, body, h1, h2, h3, h4, h5, h6, p, div, span, label, button, input, textarea, .stMarkdown, .stText {
        font-family: 'Cairo', sans-serif; text-align: right;
    }
    .brand-header {
        text-align: center; background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 20px; border-radius: 15px; border-bottom: 4px solid #1e3a8a; margin-bottom: 20px;
    }
    .main-title { color: #1e3a8a; font-size: 2.2rem; font-weight: 800; margin: 0; }
    .company-badge { background-color: #1e3a8a; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; display: inline-block; margin-bottom: 5px; }
    .comparison-box {
        height: 500px; overflow-y: auto; padding: 15px; border-radius: 8px;
        border: 1px solid #ddd; direction: rtl; text-align: right; font-size: 0.95rem; line-height: 1.8;
    }
    .original-text { background-color: #f8f9fa; border-right: 4px solid #6c757d; }
    .new-text { background-color: #f0fdf4; border-right: 4px solid #22c55e; font-weight: 500; }
    .stButton>button { width: 100%; border-radius: 8px; height: 50px; font-weight: 700; font-size: 16px; }
    #MainMenu {visibility: visible;} footer {visibility: hidden;}
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
        d = feedparser.parse(url)
        if not d.entries:
            resp = requests.get(url, headers=headers, timeout=10)
            d = feedparser.parse(resp.content)
            
        for e in d.entries[:8]:
            items.append({
                "title": e.title, "link": e.link, "source": source_name,
                "published": e.get("published", "")
            })
    except: pass
    return items

def update_category_data(category):
    feeds = RSS_SOURCES[category]
    all_items = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
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

# دالة الصياغة الاحترافية المحسنة لـ SEO
def rewrite_pro(text, tone, instr):
    if not client: return "خطأ: المفتاح مفقود"
    
    prompt = f"""
    أنت خبير محتوى رقمي وSEO محترف. أعد صياغة الخبر التالي بقوة واحترافية لتصدر محركات البحث.
    
    المعايير المطلوبة (تذكر Yoast SEO):
    1. العنوان: صغ عنواناً (H1) جذاباً جداً، فريداً، ويحتوي الكلمة المفتاحية الرئيسية.
    2. الهيكل: مقدمة قوية، فقرات منظمة بذكاء، وخاتمة شاملة.
    3. الكلمات المفتاحية: ادمج كلمات مفتاحية قوية وذات صلة بشكل طبيعي لرفع ترتيب المقال.
    4. الجودة: لغة عربية متينة وقوية، مع تجنب الحشو.
    
    الأسلوب المطلوب: {tone}.
    ملاحظات إضافية: {instr}.
    
    النص الأصلي:
    {text[:3500]}
    """
    
    try:
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile", temperature=0.6
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
    <p style='color:#6c757d; margin-top:5px'>غرفة التحرير الاحترافية (SEO Optimized)</p>
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
            with c1: st.success(f"متاح {len(news_list)} مقال في {cat_name}")
            with c2:
                if st.button("🔄 تحديث القائمة", key=f"up_{i}"):
                    with st.spinner("جاري جلب المصادر..."):
                        if "data" not in db: db["data"] = {}
                        db["data"][cat_name] = update_category_data(cat_name)
                        save_db(db)
                    st.rerun()

            opts = [f"{n['source']} | {n['title']}" for n in news_list]
            idx = st.selectbox("اختر المقال:", range(len(opts)), format_func=lambda x: opts[x], key=f"sel_{i}")

            with st.expander("⚙️ إعدادات المحرر"):
                tone = st.select_slider("الأسلوب", ["رسمي", "تحليلي", "تفاعلي"], key=f"tn_{i}")
                ins = st.text_input("توجيهات SEO إضافية", key=f"in_{i}")

            if st.button("🚀 صياغة احترافية تصدر البحث", type="primary", key=f"go_{i}"):
                sel = news_list[idx]
                with st.status("🏗️ جاري بناء المقال وفق معايير SEO...", expanded=True) as status:
                    txt = get_text(sel['link'])
                    if txt:
                        res = rewrite_pro(txt, tone, ins)
                        status.update(label="تمت الصياغة بنجاح!", state="complete", expanded=False)
                        
                        st.markdown("---")
                        st.subheader("🏁 المقال النهائي")
                        st.text_area("جاهز للنسخ (Yoast SEO):", res, height=400)
                        
                        comp_c1, comp_c2 = st.columns(2)
                        with comp_c1:
                            st.info("النص الأصلي")
                            st.markdown(f"<div class='comparison-box original-text'>{txt[:2000]}...</div>", unsafe_allow_html=True)
                        with comp_c2:
                            st.success("صياغة يقين AI")
                            st.markdown(f"<div class='comparison-box new-text'>{res}</div>", unsafe_allow_html=True)
                        
                        st.download_button("📥 تحميل النص", res, "article_seo.txt", key=f"dl_{i}")
                    else:
                        status.update(label="فشل سحب المحتوى", state="error")
                        st.error("الموقع محمي أو الرابط غير صالح")
        else:
            st.warning(f"لا توجد مقالات في {cat_name}")
            if st.button(f"📥 جلب مقالات {cat_name} الآن", type="primary", key=f"init_{i}"):
                with st.spinner("جاري الاتصال بالمصادر..."):
                    if "data" not in db: db["data"] = {}
                    db["data"][cat_name] = update_category_data(cat_name)
                    save_db(db)
                st.rerun()
