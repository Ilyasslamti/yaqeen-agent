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
    page_title="وكيل يقين - النسخة الشاملة",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS
st.markdown("""
<style>
    .main-header {font-size: 2.2rem; color: #1e3a8a; text-align: center; margin-bottom: 0.5rem; font-family: 'Segoe UI', sans-serif;}
    .seo-box {border: 1px solid #d1d5db; padding: 20px; border-radius: 8px; background-color: #ffffff;}
    .source-tag {
        display: inline-block; background-color: #f3f4f6; color: #374151;
        padding: 4px 8px; margin: 2px; border-radius: 6px; font-size: 0.85rem; border: 1px solid #e5e7eb;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. المصادر
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
# 3. المنطق (Groq)
# ==========================================
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("⚠️ خطأ: مفتاح GROQ_API_KEY مفقود في Secrets")
    st.stop()

@st.cache_data(ttl=300)
def fetch_news(category, limit_per_source):
    items = []
    feeds = RSS_SOURCES.get(category, {})
    
    progress_text = "جاري الاتصال بغرف الأخبار..."
    my_bar = st.progress(0, text=progress_text)
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
    أنت خبير سيو ومحرر صحفي (Senior Editor).
    المهمة: أعد صياغة الخبر التالي ليكون جاهزاً للنشر في "هاشمي بريس".

    التعليمات:
    1. أعد الكتابة بلغة عربية قوية وصحفية.
    2. النبرة: {tone}
    3. تعليمات: {instr}
    
    معايير السيو (SEO):
    - استخرج الكلمة المفتاحية وضعها في العنوان والمقدمة.
    - اكتب عنواناً رئيسياً (H1) جذاباً.
    - اكتب وصف ميتا (Meta Description) دقيق.
    - قسّم النص إلى عناوين فرعية (H2, H3).
    - اقترح 3 وسوم (Tags).

    النص الأصلي:
    {text}
    """
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an expert Arabic News Editor & SEO Specialist."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.6,
            max_tokens=2500
        )
        return chat_completion.choices[0].message.content
    except Exception as e: return f"خطأ تقني: {str(e)}"

# ==========================================
# 4. واجهة المستخدم
# ==========================================
with st.sidebar:
    st.title("🦅 يقين (Pro)")
    st.markdown("---")
    
    # اختيار القسم وعرض الجرائد
    cat = st.selectbox("📂 القسم:", list(RSS_SOURCES.keys()))
    
    # عرض الجرائد (الميزة الجديدة)
    current_sources = list(RSS_SOURCES[cat].keys())
    with st.expander(f"👁️ عرض مصادر هذا القسم ({len(current_sources)})", expanded=True):
        sources_html = "".join([f"<span class='source-tag'>{s}</span>" for s in current_sources])
        st.markdown(sources_html, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # التحكم
    limit = st.slider("عدد الأخبار/جريدة:", 5, 30, 15)
    
    st.markdown("### ✍️ المحرر")
    tone = st.select_slider("النبرة:", ["رسمي", "تحليلي", "تفاعلي"])
    ins = st.text_input("توجيهات:")
    
    if st.button("تحديث المصادر 🔄", type="primary"): 
        st.cache_data.clear()
        st.rerun()

st.markdown("<div class='main-header'>وكيل يقين - غرفة التحرير</div>", unsafe_allow_html=True)

# التشغيل
news = fetch_news(cat, limit)

if news:
    count = len(news)
    st.success(f"تم رصد **{count}** مقالاً.")
    
    opts = [f"【{n['source']}】 {n['title']}" for n in news]
    idx = st.selectbox("اختر خبراً:", range(len(opts)), format_func=lambda x: opts[x])
    
    if st.button("🚀 صياغة احترافية (SEO)"):
        sel = news[idx]
        with st.spinner("جاري المعالجة..."):
            txt = get_text(sel['link'])
            
        if txt:
            col1, col2 = st.columns([1, 1.3])
            col1.info("النص الأصلي"); col1.text_area("", txt, height=600, disabled=True)
            with col2:
                st.success("النسخة المحسنة")
                with st.spinner("Llama 3.3 يكتب..."):
                    res = rewrite(txt, tone, ins)
                    st.markdown(f"<div class='seo-box'>{res}</div>", unsafe_allow_html=True)
        else: st.error("تعذر سحب النص.")
else:
    st.info("اضغط 'تحديث المصادر' للبدء...")
