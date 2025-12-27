import streamlit as st
import feedparser
import trafilatura
from groq import Groq
import concurrent.futures

# ==========================================
# 1. إعدادات الصفحة
# ==========================================
st.set_page_config(
    page_title="وكيل يقين",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. تصميم CSS (الوضع الآمن للهواتف)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
    
    /* تطبيق الخط على الجميع */
    * {
        font-family: 'Cairo', sans-serif !important;
    }

    /* هام جداً: لا نستخدم direction: rtl للصفحة كاملة لتجنب تداخل القائمة */
    
    /* محاذاة العناوين والنصوص لليمين */
    h1, h2, h3, h4, h5, h6, .stMarkdown, .stText, p {
        text-align: right !important;
    }
    
    /* جعل حقول الإدخال تكتب من اليمين */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        direction: rtl;
        text-align: right;
    }
    
    /* تنسيق القائمة الجانبية (النصوص لليمين لكن الهيكل ثابت) */
    section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] h1 {
        text-align: right;
    }

    /* الصناديق المخصصة للمحتوى (هنا نطبق RTL بأمان) */
    .arabic-box {
        direction: rtl;
        text-align: right;
        background-color: #ffffff;
        border: 1px solid #e5e5e5;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .seo-result {
        direction: rtl;
        text-align: right;
        background-color: #f0fdf4; /* خلفية خضراء فاتحة جداً */
        border-right: 4px solid #16a34a;
        padding: 20px;
        border-radius: 8px;
    }

    /* إخفاء العناصر التقنية */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. المصادر
# ==========================================
RSS_SOURCES = {
    "🔵 أخبار الشمال": {
        "شمال بوست": "https://chamalpost.net/feed",
        "بريس تطوان": "https://presstetouan.com/feed",
        "تطوان بريس": "https://tetouanpress.ma/feed",
        "طنجة 24": "https://tanja24.com/feed",
        "كاب 24": "https://cap24.tv/feed",
        "طنجة نيوز": "https://tanjanews.com/feed",
        "صدى تطوان": "https://sadatetouan.com/feed",
        "الشمال 24": "https://achamal24.com/feed",
        "طنجة الأدبية": "https://aladabia.net/feed",
    },
    "📰 صحف وطنية": {
        "هسبريس": "https://www.hespress.com/feed",
        "العمق": "https://al3omk.com/feed",
        "مدار 21": "https://madar21.com/feed",
        "اليوم 24": "https://www.alyaoum24.com/feed",
        "كود": "https://www.goud.ma/feed",
        "زنقة 20": "https://www.rue20.com/feed",
        "الصباح": "https://assabah.ma/feed",
        "هبة بريس": "https://ar.hibapress.com/feed",
        "الصحيفة": "https://www.assahifa.com/feed",
        "الأحداث المغربية": "https://ahdath.info/feed",
        "فبراير": "https://www.febrayer.com/feed",
    },
    "⚽ رياضة": {
        "البطولة": "https://www.elbotola.com/rss",
        "هسبريس الرياضية": "https://hesport.com/feed",
        "المنتخب": "https://almountakhab.com/rss",
        "هاي كورة": "https://hihi2.com/feed",
        "360 سبورت": "https://sport.le360.ma/rss",
    },
    "💰 اقتصاد وتكنولوجيا": {
        "إيكو نيوز": "https://econews.ma/feed",
        "تحدي": "https://tahaddy.net/feed",
        "لوماتان (اقتصادي)": "https://lematin.ma/rss",
        "التقنية": "https://www.tech-wd.com/wd/feed",
    }
}

# ==========================================
# 4. المنطق (Groq + Threads)
# ==========================================
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("⚠️ مفتاح GROQ_API_KEY مفقود!")
    st.stop()

def fetch_single_feed(source_name, url, limit):
    entries = []
    try:
        d = feedparser.parse(url) 
        for e in d.entries[:limit]:
            entries.append({"title": e.title, "link": e.link, "source": source_name})
    except: pass
    return entries

@st.cache_data(ttl=300)
def fetch_news_parallel(category, limit_per_source):
    feeds = RSS_SOURCES.get(category, {})
    all_items = []
    
    num_workers = len(feeds) if len(feeds) > 0 else 1
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        future_to_source = {executor.submit(fetch_single_feed, src, url, limit_per_source): src for src, url in feeds.items()}
        for future in concurrent.futures.as_completed(future_to_source):
            try:
                data = future.result()
                all_items.extend(data)
            except: pass
            
    return all_items

def get_text(url):
    try:
        d = trafilatura.fetch_url(url)
        return trafilatura.extract(d) if d else None
    except: return None

def rewrite(text, tone, instr):
    prompt = f"""
    أنت خبير سيو ومحرر صحفي (Senior Editor) في "هاشمي بريس".
    المهمة: إعادة صياغة الخبر التالي بشكل احترافي.
    
    المعطيات:
    - النص: {text}
    - النبرة: {tone}
    - ملاحظات: {instr}

    المطلوب:
    1. عنوان جذاب (SEO).
    2. مقدمة، متن، وخاتمة.
    3. وسوم (Hashtags).
    
    اللغة: عربية فصحى سليمة.
    """
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.6,
            max_tokens=2500
        )
        return chat_completion.choices[0].message.content
    except Exception as e: return f"خطأ: {str(e)}"

# ==========================================
# 5. واجهة المستخدم (Layout)
# ==========================================
with st.sidebar:
    st.markdown("### 🦅 لوحة التحكم")
    
    cat = st.selectbox("القسم:", list(RSS_SOURCES.keys()))
    
    # عرض المصادر بطريقة نصية بسيطة جداً لتجنب المشاكل
    current = list(RSS_SOURCES[cat].keys())
    with st.expander("المصادر المتاحة"):
        st.caption(" - ".join(current))
    
    st.markdown("---")
    limit = st.slider("عدد الأخبار:", 5, 30, 10) 
    tone = st.select_slider("النبرة:", ["رسمي", "تحليلي", "تفاعلي"])
    ins = st.text_input("توجيهات:")
    
    if st.button("تحديث المصادر", type="primary"):
        st.cache_data.clear()
        st.rerun()

# المتن الرئيسي
st.markdown("<h1 style='text-align: center; color: #1e3a8a;'>وكيل يقين</h1>", unsafe_allow_html=True)

# الجلب
news = fetch_news_parallel(cat, limit)

if news:
    st.info(f"تم جلب {len(news)} خبراً بنجاح (وضع السرعة القصوى)")
    
    opts = [f"【{n['source']}】 {n['title']}" for n in news]
    idx = st.selectbox("اختر الخبر:", range(len(opts)), format_func=lambda x: opts[x])
    
    if st.button("✨ بدء الصياغة"):
        sel = news[idx]
        with st.spinner("جاري القراءة..."):
            txt = get_text(sel['link'])
            
        if txt:
            # استخدام أعمدة قياسية
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### النص الأصلي")
                # عرض النص داخل صندوق RTL مخصص
                st.markdown(f"<div class='arabic-box'>{txt[:800]}...</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown("#### صياغة هاشمي بريس")
                with st.spinner("جاري الكتابة..."):
                    res = rewrite(txt, tone, ins)
                    # عرض النتيجة داخل صندوق SEO مخصص
                    st.markdown(f"<div class='seo-result'>{res}</div>", unsafe_allow_html=True)
                    st.download_button("تحميل المقال", res, "article.txt")
        else:
            st.warning("تعذر قراءة النص (الموقع محمي). حاول مع خبر آخر.")
else:
    st.write("اضغط زر التحديث في القائمة الجانبية.")
