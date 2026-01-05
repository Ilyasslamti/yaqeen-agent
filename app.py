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
# 0. إعدادات النظام (V11.0 - Professional Article Architect)
# ==========================================
SYSTEM_VERSION = "V11.0_PRO_ARCHITECT" 
st.set_page_config(page_title="يقين AI - معمار المقالات", page_icon="✍️", layout="wide")
socket.setdefaulttimeout(15) 
DB_FILE = "news_db_v8.json"

# ==========================================
# 1. نظام التنظيف الذكي (3 صباحاً)
# ==========================================
def auto_purge_at_3am():
    now = datetime.now()
    if now.hour == 3:
        if os.path.exists(DB_FILE):
            try:
                os.remove(DB_FILE)
                st.cache_data.clear()
            except: pass

auto_purge_at_3am()

# ==========================================
# 2. المصادر (نفس القائمة الضخمة)
# ==========================================
RSS_SOURCES = {
    "أخبار الشمال 🌊": {
        "شمال بوست": "https://chamalpost.net/feed", "بريس تطوان": "https://presstetouan.com/feed",
        "طنجة 24": "https://tanja24.com/feed", "تطوان بريس": "https://tetouanpress.ma/feed",
    },
    "الصحافة الوطنية 🇲🇦": {
        "هسبريس": "https://www.hespress.com/feed", "شوف تيفي": "https://chouftv.ma/feed",
        "العمق": "https://al3omk.com/feed", "زنقة 20": "https://www.rue20.com/feed",
    },
    "الرياضة ⚽": {
        "البطولة": "https://www.elbotola.com/rss", "هسبريس رياضة": "https://hesport.com/feed",
    }
}

# ==========================================
# 3. CSS (تنسيق واجهة المحرر)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
    html, body, [class*="st-"] { font-family: 'Cairo', sans-serif; text-align: right; }
    .brand-header {
        text-align: center; background: #1e3a8a; color: white; padding: 2rem; border-radius: 15px; margin-bottom: 2rem;
    }
    .article-output {
        background-color: #ffffff; color: #1a1a1a; padding: 25px; border-radius: 10px;
        border: 1px solid #e0e0e0; line-height: 1.8; font-size: 1.1rem; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .stButton>button { background-color: #1e3a8a; color: white; font-weight: 800; height: 3.5rem; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. محرك صياغة المقالات الاحترافي (The Architect)
# ==========================================
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except: client = None

def rewrite_article_architect(text, tone, instr):
    if not client: return "خطأ: المفتاح مفقود"
    
    prompt = f"""
    أنت رئيس تحرير محترف وخبير SEO. مهمتك هي تحويل النص الخام إلى "مقال صحفي متكامل" وليس مجرد نصوص متفرقة.
    
    الهيكل المطلوب للمقال (التزام صارم):
    1. **العنوان الرئيسي (H1):** عنوان مثير، قوي، ومباشر يحتوي على الكلمة المفتاحية.
    2. **المقدمة (Lead):** فقرة واحدة مكثفة (حوالي 30-40 كلمة) تلخص الخبر وتجذب القارئ، مع استخدام المبني للمعلوم.
    3. **العناوين الفرعية (H2):** أضف عنوانين فرعيين على الأقل لتنظيم الأفكار.
    4. **الجسم (Body):** فقرات متسلسلة ومنطقية. كل فقرة لا تتجاوز 3 أسطر.
    5. **قواعد Yoast SEO الصارمة:**
       - حوّل كل جمل المبني للمجهول إلى مبني للمعلوم (أقل من 10% مبني للمجهول).
       - الجمل قصيرة جداً (أقل من 20 كلمة للجملة).
       - ربط الفقرات بكلمات انتقال (علاوة على ذلك، ومن جهة أخرى، وفي هذا السياق).
    
    الأسلوب: {tone}. ملاحظات إضافية: {instr}.
    
    النص الأصلي:
    {text[:3500]}
    """
    
    try:
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile", temperature=0.4 # حرارة منخفضة لضمان الالتزام بالهيكل
        )
        return res.choices[0].message.content
    except Exception as e: return f"خطأ: {str(e)}"

# ==========================================
# 5. الواجهة الأمامية
# ==========================================
st.markdown("<div class='brand-header'><h1>يقين AI - معمار المقالات الاحترافية</h1><p>توليد مقالات صحفية متكاملة متوافقة مع Yoast SEO</p></div>", unsafe_allow_html=True)

# دالات جلب وتحميل البيانات (نفس الدوال السابقة)
def fetch_feed_items(source_name, url):
    items = []
    try:
        d = feedparser.parse(url)
        for e in d.entries[:8]: items.append({"title": e.title, "link": e.link, "source": source_name})
    except: pass
    return items

def update_category_data(category):
    all_items = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_feed_items, src, url) for src, url in RSS_SOURCES[category].items()]
        for f in concurrent.futures.as_completed(futures): all_items.extend(f.result())
    return all_items

# إدارة قاعدة البيانات
if os.path.exists(DB_FILE):
    with open(DB_FILE, 'r', encoding='utf-8') as f: db = json.load(f)
else: db = {"data": {}}

tabs = st.tabs(list(RSS_SOURCES.keys()))
for i, cat_name in enumerate(list(RSS_SOURCES.keys())):
    with tabs[i]:
        if cat_name in db["data"]:
            news_list = db["data"][cat_name]
            idx = st.selectbox("اختر الخبر الأساسي:", range(len(news_list)), format_func=lambda x: f"[{news_list[x]['source']}] {news_list[x]['title']}", key=f"s_{i}")
            
            c1, c2 = st.columns(2)
            with c1: tone = st.selectbox("نبرة المقال:", ["تحقيق صحفي رصين", "تقرير إخباري سريع", "مقال رأي تحليلي"], key=f"t_{i}")
            with c2: instr = st.text_input("كلمات مفتاحية مستهدفة:", key=f"i_{i}")

            if st.button("🚀 توليد المقال الاحترافي", key=f"g_{i}"):
                with st.status("🏗️ جاري هندسة المقال وتنسيق الفقرات...", expanded=True):
                    raw = trafilatura.fetch_url(news_list[idx]['link'])
                    txt = trafilatura.extract(raw)
                    if txt:
                        final_article = rewrite_article_architect(txt, tone, instr)
                        st.markdown("### ✅ المقال النهائي الجاهز")
                        st.markdown(f"<div class='article-output'>{final_article}</div>", unsafe_allow_html=True)
                        st.text_area("نسخة الخام (للووردبريس):", final_article, height=300)
                    else: st.error("فشل في سحب النص")
        else:
            if st.button(f"جلب أخبار {cat_name}"):
                db["data"][cat_name] = update_category_data(cat_name)
                with open(DB_FILE, 'w', encoding='utf-8') as f: json.dump(db, f, ensure_ascii=False)
                st.rerun()

st.markdown("---")
st.caption("نظام 'يقين' - الإصدار الاحترافي V11.0 - إدارة الماندجر")
# ==========================================
# 2. المصادر الضخمة المحدثة
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
    "الصحافة الوطنية 🇲🇦": {
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
        "Le360 (عربي)": "https://ar.le360.ma/rss",
    },
    "الرياضة ⚽": {
        "البطولة": "https://www.elbotola.com/rss",
        "هسبريس رياضة": "https://hesport.com/feed",
        "المنتخب": "https://almountakhab.com/rss",
        "هاي كورة": "https://hihi2.com/feed",
    }
}

# ==========================================
# 3. CSS (تنسيق العرض الاحترافي)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
    html, body, h1, h2, h3, h4, h5, h6, p, div, span, label, button, input, textarea, .stMarkdown, .stText {
        font-family: 'Cairo', sans-serif; text-align: right;
    }
    .brand-header {
        text-align: center; background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 30px; border-radius: 15px; color: white; margin-bottom: 25px;
    }
    .comparison-box {
        height: 500px; overflow-y: auto; padding: 15px; border-radius: 8px;
        border: 1px solid #ddd; direction: rtl; text-align: right; font-size: 0.95rem; line-height: 1.8;
    }
    .original-text { background-color: #f9fafb; border-right: 4px solid #9ca3af; }
    .new-text { background-color: #f0fdf4; border-right: 4px solid #22c55e; font-weight: 500; }
    .stButton>button { width: 100%; border-radius: 8px; height: 50px; font-weight: 700; background-color: #1e3a8a; color: white; }
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. المنطق الخلفي (محرك الذكاء الاصطناعي الصارم)
# ==========================================
try:
    if "GROQ_API_KEY" in st.secrets:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    else: client = None
except: client = None

def fetch_feed_items(source_name, url):
    items = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/110.0.0.0 Safari/537.36'}
    try:
        d = feedparser.parse(url)
        if not d.entries:
            resp = requests.get(url, headers=headers, timeout=10)
            d = feedparser.parse(resp.content)
        for e in d.entries[:8]:
            items.append({"title": e.title, "link": e.link, "source": source_name})
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

def rewrite_strict_seo(text, tone, instr):
    if not client: return "خطأ: المفتاح مفقود"
    
    prompt = f"""
    أنت خبير صياغة محتوى رقمي محترف. أعد صياغة الخبر التالي بأسلوب {tone} مع الالتزام الصارم بمعايير Yoast SEO للقراءة:
    
    1. **قوة الفعل (المبني للمعلوم):** استبدل كل صيغ المبني للمجهول (مثل: تم، يُذكر، قيل) بصيغ مبني للمعلوم مباشرة (مثل: قرر، ذكر المحللون، أكدت المصادر). يجب أن يكون النص حيوياً ومباشراً.
    2. **قصر الجمل:** ممنوع استخدام جمل طويلة. يجب ألا تتجاوز أي جملة 20 كلمة. استخدم النقطة باستمرار لتقسيم الأفكار.
    3. **العنوان وجذب الانتباه:** صغ عنواناً قوياً (H1) يحتوي الكلمة المفتاحية في أوله.
    4. **التنسيق:** فقرات قصيرة جداً (سطرين إلى ثلاثة فقط للفقرة).
    5. **توجيهات SEO إضافية:** {instr}.
    
    النص الأصلي للتحويل:
    {text[:3800]}
    """
    
    try:
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile", 
            temperature=0.5 # تقليل الحرارة لضمان الدقة في طول الجمل
        )
        return res.choices[0].message.content
    except Exception as e: return f"خطأ في الصياغة: {str(e)}"

# ==========================================
# 5. الواجهة الأمامية
# ==========================================
st.markdown("""
<div class='brand-header'>
    <h1>وكيل يقين AI - المحرر الذكي</h1>
    <p>صياغة احترافية متوافقة 100% مع معايير Yoast SEO</p>
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
                    with st.spinner("جاري المسح..."):
                        if "data" not in db: db["data"] = {}
                        db["data"][cat_name] = update_category_data(cat_name)
                        save_db(db)
                    st.rerun()

            opts = [f"{n['source']} | {n['title']}" for n in news_list]
            idx = st.selectbox("اختر المقال:", range(len(opts)), format_func=lambda x: opts[x], key=f"sel_{i}")

            with st.expander("⚙️ إعدادات الصياغة الصارمة"):
                tone = st.select_slider("الأسلوب", ["إخباري", "تحليلي", "تفاعلي"], key=f"tn_{i}")
                ins = st.text_input("الكلمة المفتاحية المستهدفة", key=f"in_{i}")

            if st.button("✨ صياغة وتصحيح لغوي (SEO)", type="primary", key=f"go_{i}"):
                sel = news_list[idx]
                with st.status("🏗️ جاري الصياغة مع معالجة طول الجمل والمبني للمعلوم...", expanded=True) as status:
                    raw_html = trafilatura.fetch_url(sel['link'])
                    txt = trafilatura.extract(raw_html)
                    if txt:
                        res = rewrite_strict_seo(txt, tone, ins)
                        status.update(label="تمت الصياغة بنجاح!", state="complete", expanded=False)
                        
                        st.markdown("---")
                        st.subheader("🏁 المقال الجاهز للنشر")
                        st.text_area("انسخ المحتوى لـ Yoast SEO:", res, height=450)
                        
                        comp_c1, comp_c2 = st.columns(2)
                        with comp_c1:
                            st.info("النص الأصلي")
                            st.markdown(f"<div class='comparison-box original-text'>{txt[:2000]}...</div>", unsafe_allow_html=True)
                        with comp_c2:
                            st.success("صياغة يقين المحدثة")
                            st.markdown(f"<div class='comparison-box new-text'>{res}</div>", unsafe_allow_html=True)
                    else:
                        st.error("الموقع محمي")
        else:
            st.warning(f"لا توجد مقالات في {cat_name}")
            if st.button(f"📥 جلب مقالات {cat_name} الآن", type="primary", key=f"init_{i}"):
                with st.spinner("جاري الاتصال بالمصادر..."):
                    if "data" not in db: db["data"] = {}
                    db["data"][cat_name] = update_category_data(cat_name)
                    save_db(db)
                st.rerun()

st.markdown("---")
st.caption("تم التطوير بواسطة 'الماندجر' لضمان أعلى جودة في صياغة المحتوى الرقمي.")
