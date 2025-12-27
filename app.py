import streamlit as st
import feedparser
import trafilatura
from groq import Groq
import concurrent.futures
import time

# 1. إعداد الصفحة (بدون تعقيدات)
st.set_page_config(
    page_title="وكيل يقين",
    page_icon="🦅",
    layout="wide"
)

# 2. التنسيق الآمن (Safe CSS)
# هذا التنسيق يضمن ظهور العربية بشكل جميل دون كسر القوائم
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    * { font-family: 'Cairo', sans-serif; }
    
    /* محاذاة النصوص لليمين بدلاً من قلب الصفحة */
    .stMarkdown, .stText, .stHeader, h1, h2, h3, p, div {
        text-align: right;
    }
    
    /* تنسيق خاص للبطاقات */
    .news-card {
        background: #fff;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #ddd;
        margin-bottom: 10px;
        text-align: right;
        direction: rtl;
    }
    
    .result-box {
        background: #fdfdfd;
        border-right: 5px solid #2ecc71;
        padding: 20px;
        border-radius: 5px;
        text-align: right;
        direction: rtl;
        white-space: pre-wrap; /* الحفاظ على تنسيق الفقرات */
    }
    
    /* إصلاح اتجاه المدخلات */
    input, textarea, .stSelectbox {
        direction: rtl;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# 3. بيانات المصادر
RSS_SOURCES = {
    "أخبار الشمال": {
        "شمال بوست": "https://chamalpost.net/feed",
        "بريس تطوان": "https://presstetouan.com/feed",
        "طنجة 24": "https://tanja24.com/feed",
        "تطوان بريس": "https://tetouanpress.ma/feed",
    },
    "صحف وطنية": {
        "هسبريس": "https://www.hespress.com/feed",
        "العمق": "https://al3omk.com/feed",
        "مدار 21": "https://madar21.com/feed",
        "كود": "https://www.goud.ma/feed",
    },
    "رياضة": {
        "البطولة": "https://www.elbotola.com/rss",
        "هسبريس الرياضية": "https://hesport.com/feed",
    }
}

# 4. التحقق من المفتاح والاتصال
try:
    if "GROQ_API_KEY" in st.secrets:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    else:
        st.error("⛔ خطأ: لم يتم العثور على مفتاح GROQ_API_KEY في Secrets")
        st.stop()
except Exception as e:
    st.error(f"حدث خطأ أثناء تهيئة Groq: {e}")
    st.stop()

# دوال العمليات
def fetch_feed(source_name, url, limit):
    """جلب الأخبار من مصدر واحد"""
    posts = []
    try:
        d = feedparser.parse(url)
        for e in d.entries[:limit]:
            posts.append({
                "title": e.title,
                "link": e.link,
                "source": source_name
            })
    except: pass
    return posts

@st.cache_data(ttl=300)
def get_all_news(category, limit):
    """جلب متوازي للأخبار"""
    feeds = RSS_SOURCES.get(category, {})
    all_news = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_feed, src, url, limit) for src, url in feeds.items()]
        for future in concurrent.futures.as_completed(futures):
            all_news.extend(future.result())
            
    return all_news

def get_article_text(url):
    try:
        downloaded = trafilatura.fetch_url(url)
        return trafilatura.extract(downloaded) if downloaded else None
    except: return None

def process_with_ai(text, tone, instructions):
    prompt = f"""
    تصرف كصحفي محترف في "هاشمي بريس".
    المهمة: أعد صياغة الخبر التالي.
    
    النص الأصلي: {text[:3000]}
    
    الشروط:
    1. العنوان: جذاب ومتوافق مع SEO (H1).
    2. الأسلوب: {tone}.
    3. تعليمات إضافية: {instructions}.
    4. اللغة: عربية فصحى قوية.
    
    اكتب المقال مباشرة دون مقدمات.
    """
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"خطأ في المعالجة: {e}"

# 5. الواجهة الرئيسية
st.title("🦅 وكيل يقين")

# القائمة الجانبية
with st.sidebar:
    st.header("الإعدادات")
    category = st.selectbox("القسم", list(RSS_SOURCES.keys()))
    limit = st.slider("عدد الأخبار", 5, 20, 10)
    st.divider()
    tone = st.selectbox("النبرة", ["رسمي", "تحليلي", "عاجل"])
    notes = st.text_input("ملاحظات")
    
    if st.button("تحديث", type="primary"):
        st.cache_data.clear()
        st.rerun()

# جلب الأخبار
news_items = get_all_news(category, limit)

if not news_items:
    st.warning("جاري تحميل الأخبار... اضغط تحديث إذا تأخر الأمر.")
else:
    # عرض القائمة
    options = [f"{item['source']} - {item['title']}" for item in news_items]
    selected_idx = st.selectbox("اختر خبراً:", range(len(options)), format_func=lambda x: options[x])
    
    if st.button("🚀 ابدأ الصياغة"):
        selected_item = news_items[selected_idx]
        
        with st.status("جاري العمل...", expanded=True) as status:
            st.write("1. جاري سحب النص الأصلي...")
            original_text = get_article_text(selected_item['link'])
            
            if original_text:
                st.write("2. جاري الكتابة باستخدام Llama 3.3...")
                result = process_with_ai(original_text, tone, notes)
                status.update(label="تم الانتهاء!", state="complete", expanded=False)
                
                # عرض النتيجة
                col1, col2 = st.columns(2)
                with col1:
                    st.info("النص الأصلي")
                    st.markdown(f"<div class='news-card'>{original_text[:500]}...</div>", unsafe_allow_html=True)
                with col2:
                    st.success("النتيجة النهائية")
                    st.markdown(f"<div class='result-box'>{result}</div>", unsafe_allow_html=True)
            else:
                status.update(label="فشل العملية", state="error")
                st.error("تعذر سحب النص من المصدر (قد يكون محمياً).")
