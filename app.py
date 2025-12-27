import streamlit as st
import feedparser
import trafilatura
from groq import Groq
import time
from datetime import datetime
import concurrent.futures

# ==========================================
# 1. إعدادات الصفحة
# ==========================================
st.set_page_config(
    page_title="وكيل يقين - التفويض الكامل",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. تصميم CSS الاحترافي
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;800&display=swap');
    html, body, [class*="css"] {font-family: 'Cairo', sans-serif; direction: rtl;}
    
    .main-header {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        font-size: 2.5rem; font-weight: 800; text-align: center; margin-bottom: 0.5rem;
    }
    .content-box {background-color: #fff; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; border: 1px solid #f1f5f9;}
    .seo-box {border-right: 4px solid #10b981; background-color: #fcfdfd;}
    .source-tag {display: inline-block; background: #e0f2fe; color: #0369a1; padding: 2px 8px; margin: 2px; border-radius: 15px; font-size: 0.75rem;}
    .stButton>button {width: 100%; border-radius: 8px; font-weight: bold;}
    
    /* إخفاء العناصر غير الضرورية */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. المصادر (قاعدة البيانات)
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
    """وظيفة المندوب الواحد"""
    entries = []
    try:
        # مهلة 5 ثواني فقط لكل مصدر حتى لا يعطل البقية
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
    
    # حساب عدد المناديب المطلوب (مندوب لكل جريدة)
    num_workers = len(feeds) if len(feeds) > 0 else 1
    
    progress_bar = st.progress(0, text=f"🚀 إطلاق {num_workers} مندوباً لجلب الأخبار...")
    
    # Max Workers = عدد الجرائد (توازي كامل)
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        future_to_source = {executor.submit(fetch_single_feed, src, url, limit_per_source): src for src, url in feeds.items()}
        
        completed_count = 0
        total = len(feeds)
        
        for future in concurrent.futures.as_completed(future_to_source):
            try:
                data = future.result()
                all_items.extend(data)
            except:
                pass
            
            completed_count += 1
            # تحديث الشريط بسرعة
            progress_bar.progress(int((completed_count / total) * 100), text=f"تم استلام تقارير {completed_count}/{total} جريدة")
            
    progress_bar.empty()
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
# 5. الواجهة الرسومية
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3208/3208761.png", width=50)
    st.markdown("### لوحة التحكم")
    
    cat = st.selectbox("القسم:", list(RSS_SOURCES.keys()))
    
    current = list(RSS_SOURCES[cat].keys())
    with st.expander(f"المناديب النشطين ({len(current)})"):
        st.markdown("".join([f"<span class='source-tag'>{s}</span>" for s in current]), unsafe_allow_html=True)
    
    st.markdown("---")
    limit = st.slider("عمق البحث:", 5, 30, 10) 
    tone = st.select_slider("النبرة:", ["رسمي", "تحليلي", "تفاعلي"])
    ins = st.text_input("توجيهات:")
    
    if st.button("🚀 مسح شامل (فوري)", type="primary"):
        st.cache_data.clear()
        st.rerun()

st.markdown("<div class='main-header'>وكيل يقين</div>", unsafe_allow_html=True)

# تشغيل التوازي الكامل
news = fetch_news_parallel(cat, limit)

if news:
    c1, c2 = st.columns(2)
    c1.metric("إجمالي الأخبار الملتقطة", len(news))
    c2.metric("سرعة الاستجابة", "قصوى ⚡")
    
    opts = [f"【{n['source']}】 {n['title']}" for n in news]
    idx = st.selectbox("اختر خبراً:", range(len(opts)), format_func=lambda x: opts[x])
    
    if st.button("✨ صياغة فورية"):
        sel = news[idx]
        with st.spinner("جاري المعالجة..."):
            txt = get_text(sel['link'])
            
        if txt:
            col1, col2 = st.columns([1, 1.2])
            col1.markdown(f"<div class='content-box'>{txt[:1500]}...</div>", unsafe_allow_html=True)
            with col2:
                with st.spinner("Llama 3.3 يكتب..."):
                    res = rewrite(txt, tone, ins)
                    st.markdown(f"<div class='content-box seo-box'>{res}</div>", unsafe_allow_html=True)
                    st.download_button("تحميل TXT", res, "article.txt")
        else: st.error("الموقع محمي.")
else:
    st.info("اضغط زر المسح الشامل للبدء")
