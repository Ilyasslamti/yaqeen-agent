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
    page_title="وكيل يقين - خبير SEO",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS لتحسين تجربة القراءة (Typography)
st.markdown("""
<style>
    .main-header {font-size: 2.2rem; color: #1e3a8a; text-align: center; margin-bottom: 0.5rem; font-family: 'Segoe UI', sans-serif;}
    .seo-box {border: 1px solid #d1d5db; padding: 20px; border-radius: 8px; background-color: #ffffff; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);}
    .meta-tag {font-size: 0.9rem; color: #6b7280; font-family: monospace; background: #f3f4f6; padding: 5px; border-radius: 4px;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. المصادر (قائمة مختارة)
# ==========================================
RSS_SOURCES = {
    "🔵 أخبار الشمال": {
        "شمال بوست": "https://chamalpost.net/feed",
        "بريس تطوان": "https://presstetouan.com/feed",
        "تطوان بريس": "https://tetouanpress.ma/feed",
        "طنجة 24": "https://tanja24.com/feed",
    },
    "📰 صحف وطنية": {
        "هسبريس": "https://www.hespress.com/feed",
        "العمق": "https://al3omk.com/feed",
        "مدار 21": "https://madar21.com/feed",
        "كود": "https://www.goud.ma/feed",
        "زنقة 20": "https://www.rue20.com/feed",
    },
    "⚽ رياضة": {
        "البطولة": "https://www.elbotola.com/rss",
        "هسبريس الرياضية": "https://hesport.com/feed",
    }
}

# ==========================================
# 3. المنطق (Groq Engine)
# ==========================================
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("⚠️ خطأ: تأكد من وضع مفتاح GROQ_API_KEY في إعدادات Secrets")
    st.stop()

@st.cache_data(ttl=300)
def fetch_news(category):
    items = []
    feeds = RSS_SOURCES.get(category, {})
    for src, url in feeds.items():
        try:
            f = feedparser.parse(url)
            for e in f.entries[:2]:
                items.append({"title": e.title, "link": e.link, "source": src})
        except: continue
    return items

def get_text(url):
    try:
        d = trafilatura.fetch_url(url)
        return trafilatura.extract(d) if d else None
    except: return None

def rewrite(text, tone, instr):
    # ============================================================
    # 🧠 برومبت خبير السيو (SEO Expert Prompt)
    # ============================================================
    prompt = f"""
    أنت خبير سيو تحريري من المستوى المتقدم، تعمل بعقلية محرر مواقع إخبارية ومواقع متصدّرة في Google.
    مهمتك هي إعادة صياغة المقال التالي صياغة احترافية 100% مع الحفاظ على المعنى الأساسي، وتحسين الأسلوب، وتعزيز القابلية للقراءة، ورفع فرص التصدّر في نتائج البحث.

    التعليمات الإلزامية:
    1. أعد كتابة المقال بلغة عربية سليمة، قوية، صحفية/تحليلية، بعيدة عن التكرار والركاكة.
    2. النبرة المطلوبة: {tone}
    3. تعليمات خاصة من المدير: {instr}
    
    استراتيجية السيو (SEO Strategy):
    - استخرج الكلمات المفتاحية الأساسية والثانوية تلقائيًا من سياق المقال.
    - أدمج الكلمة المفتاحية الأساسية في: العنوان الرئيسي (H1)، الفقرة الأولى، أحد العناوين الفرعية، والخاتمة.
    - وزّع الكلمات الثانوية بشكل طبيعي داخل النص دون حشو.

    الهيكل المطلوب للمخرجات:
    1. **عنوان رئيسي (H1):** جذاب (SEO Title) لا يتجاوز 60 حرفًا.
    2. **وصف ميتا (Meta Description):** احترافي لا يتجاوز 155 حرفًا.
    3. **المحتوى:** مقسم لعناوين فرعية (H2/H3) وفقرات قصيرة (2-3 أسطر).
    4. **الخاتمة:** تلخيص قوي.
    5. **الإضافات:** - 3 عناوين بديلة محسّنة للسيو.
       - قائمة الكلمات المفتاحية المستخدمة.

    امنع تمامًا: الحشو، التكرار، والعناوين المضللة.
    استخدم أسلوباً نشطاً (Active Voice) وكلمات انتقالية ذكية.

    النص الأصلي للمقال:
    {text}
    """
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a world-class SEO Editor and Copywriter for an Arabic News Agency."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile", # الموديل الأقوى
            temperature=0.6,
            max_tokens=3000
        )
        return chat_completion.choices[0].message.content
    except Exception as e: return f"خطأ تقني: {str(e)}"

# ==========================================
# 4. واجهة المستخدم
# ==========================================
with st.sidebar:
    st.title("🦅 يقين (SEO Edition)")
    st.markdown("---")
    cat = st.selectbox("القسم:", list(RSS_SOURCES.keys()))
    
    st.markdown("### ⚙️ إعدادات المقال")
    tone = st.select_slider("النبرة:", ["رصين وموضوعي", "تحليلي", "تفاعلي ومثير"])
    ins = st.text_input("توجيهات إضافية:", placeholder="مثلاً: التركيز على الأرقام...")
    
    if st.button("تحديث المصادر 🔄"): 
        st.cache_data.clear()
        st.rerun()

st.markdown("<div class='main-header'>وكيل يقين - المحرر الذكي</div>", unsafe_allow_html=True)

news = fetch_news(cat)
if news:
    opts = [f"{n['source']}: {n['title']}" for n in news]
    idx = st.selectbox("اختر خبراً:", range(len(opts)), format_func=lambda x: opts[x])
    
    if st.button("🚀 تحليل وصياغة (SEO)", type="primary"):
        sel = news[idx]
        with st.spinner("جاري سحب المحتوى..."):
            txt = get_text(sel['link'])
            
        if txt:
            col1, col2 = st.columns([1, 1.3])
            
            with col1:
                st.info("النص الأصلي")
                st.text_area("المصدر", txt, height=600, disabled=True)
            
            with col2:
                st.success("نسخة SEO الاحترافية (جاهزة للنشر)")
                with st.spinner("جاري تطبيق معايير Google Helpful Content..."):
                    res = rewrite(txt, tone, ins)
                    st.markdown(f"<div class='seo-box'>{res}</div>", unsafe_allow_html=True)
        else: 
            st.error("تعذر سحب النص (الموقع محمي).")
else:
    st.warning("جاري البحث عن أخبار...")    }
}

# ==========================================
# 3. المنطق (Groq Engine)
# ==========================================
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("⚠️ تأكد من وضع مفتاح GROQ_API_KEY في Secrets")
    st.stop()

@st.cache_data(ttl=300)
def fetch_news(category):
    items = []
    feeds = RSS_SOURCES.get(category, {})
    for src, url in feeds.items():
        try:
            f = feedparser.parse(url)
            for e in f.entries[:2]:
                items.append({"title": e.title, "link": e.link, "source": src})
        except: continue
    return items

def get_text(url):
    try:
        d = trafilatura.fetch_url(url)
        return trafilatura.extract(d) if d else None
    except: return None

def rewrite(text, tone, instr):
    # استخدام الموديل الجديد Llama 3.3 (الأحدث والأقوى)
    prompt = f"""
    أنت صحفي خبير في "هاشمي بريس".
    المهمة: أعد صياغة الخبر التالي بشكل احترافي جداً.
    
    التعليمات:
    1. الأسلوب: {tone}
    2. ملاحظات: {instr}
    3. العنوان: ضع عنواناً جديداً جذاباً.
    4. اللغة: عربية فصحى سليمة وصحفية.
    
    النص الأصلي:
    {text}
    """
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a professional Arabic journalist editor."},
                {"role": "user", "content": prompt}
            ],
            # هنا قمنا بالتحديث للموديل الجديد
            model="llama-3.3-70b-versatile",
            temperature=0.7,
        )
        return chat_completion.choices[0].message.content
    except Exception as e: return f"خطأ Groq: {str(e)}"

# ==========================================
# 4. الواجهة
# ==========================================
with st.sidebar:
    st.title("🦅 يقين (Llama 3.3)")
    st.caption("Powered by Groq")
    cat = st.selectbox("القسم:", list(RSS_SOURCES.keys()))
    tone = st.select_slider("الأسلوب:", ["رسمي", "تحليلي", "عاجل"])
    ins = st.text_input("تعليمات:")
    if st.button("تحديث"): st.cache_data.clear(); st.rerun()

st.markdown("<div class='main-header'>وكيل يقين الصحفي</div>", unsafe_allow_html=True)

news = fetch_news(cat)
if news:
    opts = [f"{n['source']}: {n['title']}" for n in news]
    idx = st.selectbox("اختر خبراً:", range(len(opts)), format_func=lambda x: opts[x])
    if st.button("🚀 معالجة فورية"):
        sel = news[idx]
        txt = get_text(sel['link'])
        if txt:
            col1, col2 = st.columns(2)
            col1.info("الأصل"); col1.text_area("", txt, height=300)
            with col2:
                with st.spinner("جاري الكتابة..."):
                    res = rewrite(txt, tone, ins)
                    st.success("النتيجة"); st.markdown(res)
        else: st.error("تعذر جلب النص (الموقع محمي)")
else:
    st.warning("لا توجد أخبار حالياً.")

