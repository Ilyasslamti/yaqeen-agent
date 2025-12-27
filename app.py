import streamlit as st
import feedparser
import trafilatura
from groq import Groq
import concurrent.futures
import json
import os
import time
from datetime import datetime, timedelta
import pytz

# ==========================================
# 1. إعدادات الصفحة
# ==========================================
st.set_page_config(
    page_title="وكيل يقين - الأرشيف الذكي",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ملف قاعدة البيانات
DB_FILE = "news_db.json"

# ==========================================
# 2. تصميم CSS (الآمن والسريع)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
    * { font-family: 'Cairo', sans-serif !important; }

    /* محاذاة آمنة للهاتف */
    h1, h2, h3, h4, h5, h6, .stMarkdown, .stText, p { text-align: right !important; }
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] { direction: rtl; text-align: right; }
    
    /* صناديق العرض */
    .news-card {
        background-color: #ffffff; border: 1px solid #eee;
        padding: 15px; border-radius: 8px; margin-bottom: 10px;
        text-align: right; direction: rtl;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .seo-result {
        background-color: #f0fdf4; border-right: 4px solid #16a34a;
        padding: 20px; border-radius: 8px; text-align: right; direction: rtl;
    }
    
    .status-badge {
        background-color: #e0f2fe; color: #0284c7;
        padding: 5px 10px; border-radius: 15px; font-size: 0.8rem;
    }

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
        "طنجة نيوز": "https://tanjanews.com/feed",
        "صدى تطوان": "https://sadatetouan.com/feed",
        "الشمال 24": "https://achamal24.com/feed",
    },
    "صحف وطنية": {
        "هسبريس": "https://www.hespress.com/feed",
        "العمق": "https://al3omk.com/feed",
        "مدار 21": "https://madar21.com/feed",
        "كود": "https://www.goud.ma/feed",
        "اليوم 24": "https://www.alyaoum24.com/feed",
        "زنقة 20": "https://www.rue20.com/feed",
        "الصباح": "https://assabah.ma/feed",
    },
    "رياضة": {
        "البطولة": "https://www.elbotola.com/rss",
        "هسبريس الرياضية": "https://hesport.com/feed",
        "المنتخب": "https://almountakhab.com/rss",
        "هاي كورة": "https://hihi2.com/feed",
    }
}

# ==========================================
# 4. المنطق (إدارة البيانات والذكاء الاصطناعي)
# ==========================================

# تهيئة Groq بأمان
try:
    if "GROQ_API_KEY" in st.secrets:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    else:
        st.error("⚠️ مفتاح GROQ مفقود في Secrets")
        st.stop()
except Exception as e:
    st.error(f"خطأ في الاتصال: {e}")
    st.stop()

# --- نظام إدارة الملفات (Backend) ---

def fetch_single_feed(source_name, url, limit):
    """جلب مصدر واحد"""
    entries = []
    try:
        d = feedparser.parse(url)
        for e in d.entries[:limit]:
            # نحفظ فقط البيانات الضرورية لتقليل حجم الملف
            entries.append({
                "title": e.title,
                "link": e.link,
                "source": source_name,
                "published": e.get("published", str(datetime.now()))
            })
    except: pass
    return entries

def update_database(limit_per_source=15):
    """تحديث قاعدة البيانات (عملية ثقيلة)"""
    all_data = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for category, feeds in RSS_SOURCES.items():
            category_items = []
            future_to_src = {executor.submit(fetch_single_feed, src, url, limit_per_source): src for src, url in feeds.items()}
            
            for future in concurrent.futures.as_completed(future_to_src):
                category_items.extend(future.result())
            
            all_data[category] = category_items
            
    # إضافة طابع زمني
    db_content = {
        "last_updated": datetime.now().timestamp(),
        "data": all_data
    }
    
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db_content, f, ensure_ascii=False)
    
    return db_content

def load_database():
    """قراءة قاعدة البيانات (عملية سريعة)"""
    # 1. التحقق من وجود الملف
    if not os.path.exists(DB_FILE):
        return None, "جديد"
        
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            db = json.load(f)
            
        last_updated = datetime.fromtimestamp(db['last_updated'])
        now = datetime.now()
        
        # 2. منطق المسح الليلي (2:30 صباحاً)
        # نتحقق هل نحن الآن بعد 2:30 صباحاً وآخر تحديث كان قبل 2:30
        tz = pytz.timezone('Africa/Casablanca') # توقيت المغرب
        morocco_now = datetime.now(tz)
        
        if morocco_now.hour == 2 and morocco_now.minute >= 30 and last_updated.day != morocco_now.day:
             return None, "expired_nightly"

        # 3. منطق الساعة الواحدة
        diff = now - last_updated
        if diff.total_seconds() > 3600: # أكثر من ساعة (3600 ثانية)
            return db, "expired_hour" # نعيد القديم مؤقتاً لكن نشير أنه منتهي
            
        return db, "valid"
        
    except:
        return None, "corrupted"

def get_text(url):
    try:
        d = trafilatura.fetch_url(url)
        return trafilatura.extract(d) if d else None
    except: return None

def rewrite(text, tone, instr):
    prompt = f"""
    أنت صحفي محترف في "هاشمي بريس".
    المهمة: أعد صياغة الخبر التالي للنشر.
    
    النص الأصلي: {text[:2500]}
    
    التعليمات:
    1. العنوان: جذاب (SEO H1).
    2. الأسلوب: {tone}.
    3. ملاحظات: {instr}.
    4. اللغة: عربية فصحى متينة.
    
    اكتب المقال مباشرة.
    """
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e: return f"خطأ: {e}"

# ==========================================
# 5. الواجهة الرئيسية
# ==========================================
st.title("🦅 يقين - غرفة التحرير")

# تحميل البيانات عند البدء
db_content, status = load_database()

# منطق التحديث التلقائي
need_update = False
msg_container = st.empty()

if status == "جديد":
    msg_container.info("🗂️ جاري بناء قاعدة البيانات لأول مرة...")
    need_update = True
elif status == "expired_nightly":
    msg_container.warning("🧹 تنظيف ليلي (02:30)... جاري بدء يوم جديد.")
    need_update = True
elif status == "expired_hour":
    msg_container.warning("⚠️ مرت ساعة منذ آخر تحديث. جاري جلب الأخبار الجديدة...")
    need_update = True
    
if need_update:
    with st.spinner("جاري الاتصال بالمصادر وتحديث الأرشيف..."):
        db_content = update_database()
    msg_container.success("تم التحديث بنجاح! ✅")
    time.sleep(1)
    msg_container.empty()
    st.rerun()

# القائمة الجانبية
with st.sidebar:
    st.header("لوحة التحكم")
    
    # عرض وقت آخر تحديث
    if db_content:
        last_up = datetime.fromtimestamp(db_content['last_updated'])
        st.caption(f"آخر تحديث: {last_up.strftime('%H:%M:%S')}")
    
    if st.button("🔄 تحديث يدوي الآن", type="primary"):
        with st.spinner("جاري التحديث القسري..."):
            update_database()
        st.rerun()
            
    st.divider()
    
    # اختيار الأخبار من الملف المحلي (سريع جداً)
    if db_content:
        cat = st.selectbox("القسم:", list(db_content['data'].keys()))
        news_list = db_content['data'][cat]
    else:
        news_list = []
        
    tone = st.select_slider("النبرة:", ["رسمي", "تحليلي", "تفاعلي"])
    ins = st.text_input("توجيهات:")

# العرض الرئيسي
if news_list:
    st.success(f"متاح {len(news_list)} خبراً في الأرشيف (تحميل فوري ⚡)")
    
    opts = [f"【{n['source']}】 {n['title']}" for n in news_list]
    idx = st.selectbox("اختر الخبر:", range(len(opts)), format_func=lambda x: opts[x])
    
    if st.button("✨ ابدأ الصياغة"):
        sel = news_list[idx]
        
        with st.status("جاري المعالجة...", expanded=True) as s:
            st.write("1. سحب النص الكامل...")
            txt = get_text(sel['link'])
            
            if txt:
                st.write("2. Llama 3.3 يكتب...")
                res = rewrite(txt, tone, ins)
                s.update(label="تمت المهمة!", state="complete", expanded=False)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.info("النص الأصلي")
                    st.markdown(f"<div class='news-card'>{txt[:600]}...</div>", unsafe_allow_html=True)
                with col2:
                    st.success("النتيجة")
                    st.markdown(f"<div class='seo-result'>{res}</div>", unsafe_allow_html=True)
                    st.download_button("تحميل TXT", res, "article.txt")
            else:
                s.update(label="فشل", state="error")
                st.error("الموقع محمي، تعذر سحب النص.")
else:
    st.error("قاعدة البيانات فارغة أو حدث خطأ.")
