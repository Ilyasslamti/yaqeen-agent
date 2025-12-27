import streamlit as st
import feedparser
import trafilatura
from groq import Groq
import concurrent.futures

# ==========================================
# 1. إعدادات الصفحة
# ==========================================
st.set_page_config(
    page_title="وكيل يقين - النسخة المستقرة",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. تصميم CSS (تم الإصلاح)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
    
    /* تطبيق الخط العربي على كل العناصر */
    * {
        font-family: 'Cairo', sans-serif !important;
    }

    /* إصلاح التشوه: نجعل النصوص عربية لكن لا نقلب هيكل الصفحة بالكامل */
    .stApp {
        direction: rtl; 
    }
    
    /* ضبط القائمة الجانبية لتظهر يمين الشاشة بشكل صحيح */
    section[data-testid="stSidebar"] {
        direction: rtl;
        text-align: right;
    }

    /* العناوين */
    h1, h2, h3, .main-header {
        font-family: 'Cairo', sans-serif;
        text-align: center;
        color: #1e3a8a; /* أزرق ملكي */
    }

    /* الصناديق والبطاقات */
    .content-box {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        text-align: right; /* ضمان محاذاة النص لليمين */
        direction: rtl;
    }

    .seo-box {
        background-color: #f8fafc;
        border-right: 5px solid #10b981; /* خط أخضر جمالي */
    }

    /* تحسين شكل الأزرار */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
        height: 3em;
    }

    /* إصلاح القوائم المنسدلة */
    .stSelectbox, .stSlider {
        direction: rtl;
    }

    /* إخفاء عناصر تقنية غير ضرورية */
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
# 4. المنطق (محرك التوازي الأقصى)
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
    except:
        pass
    return entries

@st.cache_data(ttl=300)
def fetch_news_parallel(category, limit_per_source):
    feeds = RSS_SOURCES.get(category, {})
    all_items = []
    
    # استخدام التوازي الكامل (مندوب لكل جريدة)
    num_workers = len(feeds) if len(feeds) > 0 else 1
    
    with st.spinner('جاري الاتصال بجميع المصادر في وقت واحد...'):
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
# 5. الواجهة الرسومية (المنظمة)
# ==========================================
with st.sidebar:
    st.title("🦅 لوحة التحكم")
    st.markdown("---")
    
    cat = st.selectbox("القسم:", list(RSS_SOURCES.keys()))
    
    # عرض المصادر بشكل نصي بسيط لتجنب كسر التصميم
    current = list(RSS_SOURCES[cat].keys())
    with st.expander(f"المصادر ({len(current)})"):
        st.write("، ".join(current))
    
    st.markdown("---")
    limit = st.slider("عمق البحث:", 5, 30, 10) 
    tone = st.select_slider("النبرة:", ["رسمي", "تحليلي", "تفاعلي"])
    ins = st.text_input("توجيهات:")
    
    if st.button("🚀 تحديث المصادر", type="primary"):
        st.cache_data.clear()
        st.rerun()

# المتن الرئيسي
st.markdown("<h1 style='text-align: center; color: #1e3a8a;'>وكيل يقين</h1>", unsafe_allow_html=True)

# تشغيل
news = fetch_news_parallel(cat, limit)

if news:
    # إحصائيات سريعة
    col1, col2 = st.columns(2)
    col1.success(f"تم جلب {len(news)} خبراً")
    col2.info("النظام: متصل وسريع ⚡")
    
    opts = [f"【{n['source']}】 {n['title']}" for n in news]
    idx = st.selectbox("اختر خبراً:", range(len(opts)), format_func=lambda x: opts[x])
    
    if st.button("✨ صياغة فورية"):
        sel = news[idx]
        with st.spinner("جاري المعالجة..."):
            txt = get_text(sel['link'])
            
        if txt:
            c1, c2 = st.columns([1, 1])
            # استخدام Markdown عادي لتجنب مشاكل CSS المعقدة
            with c1:
                st.subheader("النص الأصلي")
                st.text_area("", txt, height=400)
            with c2:
                st.subheader("النسخة المحسنة")
                with st.spinner("Llama 3.3 يكتب..."):
                    res = rewrite(txt, tone, ins)
                    st.markdown(f"<div class='content-box seo-box'>{res}</div>", unsafe_allow_html=True)
                    st.download_button("تحميل TXT", res, "article.txt")
        else: st.error("الموقع محمي.")
else:
    st.info("اضغط زر التحديث للبدء")
