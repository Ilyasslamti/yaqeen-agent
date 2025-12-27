import streamlit as st
import feedparser
import trafilatura
from groq import Groq
import time
from datetime import datetime

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
# 2. التصميم الاحترافي (CSS Injection)
# ==========================================
st.markdown("""
<style>
    /* استيراد خط 'Cairo' العربي من جوجل */
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;800&display=swap');

    /* تطبيق الخط على كامل التطبيق */
    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
        direction: rtl; /* ضمان الاتجاه من اليمين لليسار */
    }

    /* تحسين العنوان الرئيسي */
    .main-header {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    .sub-header {
        text-align: center;
        color: #64748b;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }

    /* تصميم البطاقات (Cards) للنصوص */
    .content-box {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 25px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        border: 1px solid #f1f5f9;
        margin-bottom: 20px;
    }

    .original-box {
        border-right: 4px solid #94a3b8; /* رمادي للنص الأصلي */
    }

    .seo-box {
        border-right: 4px solid #10b981; /* أخضر للنتيجة النهائية */
        background-color: #fcfdfd;
    }

    /* تحسين الأزرار */
    .stButton>button {
        width: 100%;
        background: linear-gradient(45deg, #2563eb, #1d4ed8);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2);
    }

    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 8px rgba(37, 99, 235, 0.3);
        background: linear-gradient(45deg, #1d4ed8, #1e40af);
    }

    /* تحسين القائمة الجانبية */
    section[data-testid="stSidebar"] {
        background-color: #f8fafc;
        border-left: 1px solid #e2e8f0;
    }

    /* وسوم المصادر */
    .source-tag {
        display: inline-block;
        background-color: #e0f2fe;
        color: #0369a1;
        padding: 4px 10px;
        margin: 3px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        border: 1px solid #bae6fd;
    }

    /* إخفاء عناصر Streamlit الافتراضية */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. بيانات المصادر
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
    },
    "📰 صحف وطنية": {
        "هسبريس": "https://www.hespress.com/feed",
        "العمق": "https://al3omk.com/feed",
        "مدار 21": "https://madar21.com/feed",
        "اليوم 24": "https://www.alyaoum24.com/feed",
        "كود": "https://www.goud.ma/feed",
        "زنقة 20": "https://www.rue20.com/feed",
        "الأحداث المغربية": "https://ahdath.info/feed",
        "الصباح": "https://assabah.ma/feed",
        "هبة بريس": "https://ar.hibapress.com/feed",
        "الصحيفة": "https://www.assahifa.com/feed",
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
        "التقنية (عالم التقنية)": "https://www.tech-wd.com/wd/feed",
    }
}

# ==========================================
# 4. المنطق البرمجي (Backend)
# ==========================================
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("⚠️ خطأ: يرجى التأكد من مفتاح GROQ_API_KEY في الإعدادات.")
    st.stop()

@st.cache_data(ttl=300)
def fetch_news(category, limit_per_source):
    items = []
    feeds = RSS_SOURCES.get(category, {})
    
    # Custom Progress Bar styling needed? Streamlit's default is fine for now.
    my_bar = st.progress(0, text="جاري الاتصال بغرف الأخبار...")
    total_feeds = len(feeds)
    
    for i, (src, url) in enumerate(feeds.items()):
        try:
            f = feedparser.parse(url)
            for e in f.entries[:limit_per_source]:
                items.append({"title": e.title, "link": e.link, "source": src})
        except: continue
        
        percent = int(((i + 1) / total_feeds) * 100)
        my_bar.progress(percent, text=f"جاري سحب: {src}")
        
    my_bar.empty()
    return items

def get_text(url):
    try:
        d = trafilatura.fetch_url(url)
        return trafilatura.extract(d) if d else None
    except: return None

def rewrite(text, tone, instr):
    prompt = f"""
    أنت خبير سيو ومحرر صحفي (Senior Editor) لدى "هاشمي بريس".
    المهمة: أعد هندسة الخبر التالي ليتصدر محركات البحث ويجذب القراء.

    البيانات المدخلة:
    - النص الأصلي: {text}
    - النبرة المطلوبة: {tone}
    - ملاحظات إضافية: {instr}

    المطلوب (Strict Format):
    1. عنوان H1 جذاب (Click-worthy) وغير مضلل.
    2. مقدمة قوية تحتوي الكلمة المفتاحية.
    3. محتوى مقسم بذكاء (عناوين فرعية H2).
    4. خاتمة تلخيصية.
    5. قسم خاص بالـ SEO في النهاية (وصف ميتا + وسوم).
    
    اللغة: عربية فصحى صحفية عالية المستوى.
    """
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a professional News Editor and SEO Specialist."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.6,
            max_tokens=2500
        )
        return chat_completion.choices[0].message.content
    except Exception as e: return f"خطأ تقني: {str(e)}"

# ==========================================
# 5. بناء الواجهة (Frontend Layout)
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3208/3208761.png", width=60)
    st.title("لوحة تحكم يقين")
    st.markdown("---")
    
    # 1. Selection
    st.markdown("### 📂 المصادر")
    cat = st.selectbox("اختر القسم الصحفي:", list(RSS_SOURCES.keys()))
    
    # Source Tags
    current_sources = list(RSS_SOURCES[cat].keys())
    with st.expander(f"👁️ عرض المصادر النشطة ({len(current_sources)})"):
        sources_html = "".join([f"<span class='source-tag'>{s}</span>" for s in current_sources])
        st.markdown(sources_html, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 2. Controls
    st.markdown("### ⚙️ الإعدادات")
    limit = st.slider("عمق البحث (خبر/جريدة):", 5, 30, 15)
    tone = st.select_slider("نبرة الصياغة:", ["رسمي ومحايد", "تحليلي معمق", "سوشيال/تفاعلي"])
    ins = st.text_input("توجيهات خاصة للمحرر:")
    
    st.markdown("---")
    if st.button("🚀 بدء المسح الشامل", type="primary"): 
        st.cache_data.clear()
        st.rerun()

# Main Area
st.markdown("<div class='main-header'>وكيل يقين للصحافة الذكية</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>نظام الرصد وإعادة الصياغة بتقنية Llama 3.3</div>", unsafe_allow_html=True)

# Fetching Logic
news = fetch_news(cat, limit)

if news:
    # Top Stats
    c1, c2, c3 = st.columns(3)
    c1.metric("إجمالي الأخبار", len(news))
    c2.metric("المصادر النشطة", len(current_sources))
    c3.metric("تاريخ التحديث", datetime.now().strftime("%H:%M"))
    
    st.markdown("---")
    
    # News Selector
    opts = [f"【{n['source']}】 {n['title']}" for n in news]
    idx = st.selectbox("📝 اختر خبراً للمعالجة:", range(len(opts)), format_func=lambda x: opts[x])
    
    if st.button("✨ تحليل وصياغة المقال (SEO)"):
        sel = news[idx]
        with st.spinner("جاري سحب البيانات وتحليل النص..."):
            txt = get_text(sel['link'])
            
        if txt:
            col1, col2 = st.columns([1, 1.2])
            
            with col1:
                st.markdown("### 📄 النص الأصلي")
                st.markdown(f"<div class='content-box original-box'>{txt[:2000]}... (عرض جزئي)</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown("### 🦅 نسخة هاشمي بريس")
                with st.spinner("Llama 3.3 يقوم بالكتابة الآن..."):
                    res = rewrite(txt, tone, ins)
                    st.markdown(f"<div class='content-box seo-box'>{res}</div>", unsafe_allow_html=True)
                    
                    # Download Button moved inside container logic if possible, or below
                    st.download_button("📥 تحميل المقال (TXT)", res, file_name="article.txt")
        else: 
            st.error("تعذر سحب النص. قد يكون الموقع يستخدم حماية عالية.")

else:
    st.info("👈 اضغط على 'بدء المسح الشامل' من القائمة الجانبية لبدء العمل.")
