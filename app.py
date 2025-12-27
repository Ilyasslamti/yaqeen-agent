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
    page_title="وكيل يقين - Llama 3 Edition",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS
st.markdown("""
<style>
    .main-header {font-size: 2.2rem; color: #f55036; text-align: center; margin-bottom: 0.5rem;} /* لون Groq البرتقالي */
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
    },
    "📰 صحف وطنية": {
        "هسبريس": "https://www.hespress.com/feed",
        "العمق": "https://al3omk.com/feed",
        "مدار 21": "https://madar21.com/feed",
        "كود": "https://www.goud.ma/feed",
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
    # نستخدم Llama 3 70B لأنه الأقوى للعربية
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
            model="llama3-70b-8192", # النموذج الأقوى والمجاني حالياً
            temperature=0.7,
        )
        return chat_completion.choices[0].message.content
    except Exception as e: return f"خطأ Groq: {str(e)}"

# ==========================================
# 4. الواجهة
# ==========================================
with st.sidebar:
    st.title("🦅 يقين (Groq)")
    st.caption("يعمل بمحرك Llama 3 السريع")
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
                with st.spinner("جاري الكتابة (بسرعة البرق)..."):
                    res = rewrite(txt, tone, ins)
                    st.success("النتيجة"); st.markdown(res)
        else: st.error("تعذر جلب النص (الموقع محمي)")
else:
    st.warning("لا توجد أخبار حالياً.")
