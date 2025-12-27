import streamlit as st
import feedparser
import trafilatura
from groq import Groq
import concurrent.futures

# ==========================================
# 1. إعدادات الصفحة
# ==========================================
st.set_page_config(
    page_title="وكيل يقين - المحرر الذكي",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. إصلاح التصميم (CSS الآمن)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
    
    /* تطبيق الخط على الجميع */
    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
    }

    /* الحل السحري: بدلاً من قلب الموقع كاملاً وتشويهه 
       نقوم بمحاذاة النصوص فقط لليمين داخل الحاويات
    */
    
    /* محاذاة العناوين والنصوص العادية */
    .stMarkdown, .stText, h1, h2, h3, h4, h5, h6, p, div {
        text-align: right;
    }
    
    /* محاذاة القوائم المنسدلة والمدخلات */
    .stSelectbox div[data-baseweb="select"], .stTextInput input {
        direction: rtl;
        text-align: right;
    }

    /* صناديق المحتوى المخصصة */
    .content-box {
        direction: rtl;
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 15px;
        text-align: right; /* مهم جداً */
    }

    .seo-box {
        direction: rtl;
        background-color: #f8f9fa;
        border-right: 5px solid #10b981;
        text-align: right;
    }

    /* تحسين الأزرار */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
    }

    /* إخفاء القوائم التقنية */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
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
# 4. المنطق (سريع ومتوازي)
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
    
    # التوازي الكامل
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
    المهمة: أعد هندسة الخبر التالي.
    
    المدخلات:
    - النص: {text}
    - النبرة: {tone}
    - ملاحظات: {instr}

    المطلوب:
    1. عنوان H1 مغناطيسي (SEO).
    2. مقدمة تجذب القارئ فوراً.
    3. جسم المقال مقسم بعناوين فرعية H2.
    4. خاتمة و 3 وسوم قوية.
    
    اللغة: عربية فصحى حديثة وسلسة.
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
# 5. الواجهة (النظيفة)
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3208/3208761.png", width=50)
    st.markdown("### لوحة التحكم")
    
    cat = st.selectbox("القسم:", list(RSS_SOURCES.keys()))
    
    # عرض أسماء المصادر بطريقة بسيطة لا تكسر التصميم
    current = list(RSS_SOURCES[cat].keys())
    with st.expander(f"المصادر ({len(current)})"):
        st.caption("، ".join(current))
    
    st.markdown("---")
    limit = st.slider("عمق البحث:", 5, 30, 10) 
    tone = st.select_slider("النبرة:", ["رسمي", "تحليلي", "تفاعلي"])
    ins = st.text_input("توجيهات:")
    
    if st.button("🚀 تحديث المصادر", type="primary"):
        st.cache_data.clear()
        st.rerun()

# العنوان الرئيسي
st.markdown("<h1 style='text-align: center; color: #1e3a8a;'>وكيل يقين</h1>", unsafe_allow_html=True)

# التشغيل
news = fetch_news_parallel(cat, limit)

if news:
    # إحصائيات
    c1, c2 = st.columns(2)
    c1.metric("عدد الأخبار", len(news))
    c2.metric("الحالة", "نشط ⚡")
    
    opts = [f"【{n['source']}】 {n['title']}" for n in news]
    idx = st.selectbox("اختر خبراً:", range(len(opts)), format_func=lambda x: opts[x])
    
    if st.button("✨ صياغة فورية"):
        sel = news[idx]
        with st.spinner("جاري المعالجة..."):
            txt = get_text(sel['link'])
            
        if txt:
            # هنا نستخدم الـ HTML المخصص لضمان اتجاه النص
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("النص الأصلي")
                # عرض النص داخل صندوق مخصص
                st.markdown(f"<div class='content-box'>{txt[:1000]}...</div>", unsafe_allow_html=True)
            
            with col2:
                st.subheader("النسخة المحسنة")
                with st.spinner("Llama 3.3 يكتب..."):
                    res = rewrite(txt, tone, ins)
                    # عرض النتيجة
                    st.markdown(f"<div class='content-box seo-box'>{res}</div>", unsafe_allow_html=True)
                    st.download_button("تحميل TXT", res, "article.txt")
        else: st.error("الموقع محمي.")
else:
    st.info("اضغط زر التحديث للبدء")
