import streamlit as st
import feedparser
import trafilatura
import google.generativeai as genai
import time
from datetime import datetime

# ==========================================
# 1. إعدادات الصفحة والهوية البصرية لـ "يقين"
# ==========================================
st.set_page_config(
    page_title="وكيل يقين للصحفيين | Yaqeen Agent",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تخصيص الواجهة بـ CSS بسيط
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; color: #1E3A8A; text-align: center; margin-bottom: 1rem;}
    .sub-header {font-size: 1.2rem; color: #4B5563; text-align: center;}
    .card {padding: 1.5rem; border-radius: 10px; border: 1px solid #e0e0e0; background-color: #f9f9f9; margin-bottom: 1rem;}
    .source-tag {background-color: #1E3A8A; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. قاعدة بيانات المصادر (أكثر من 40 مصدر)
# ==========================================
RSS_SOURCES = {
    "📰 وطنية وشاملة": {
        "هسبريس": "https://www.hespress.com/feed",
        "العمق المغربي": "https://al3omk.com/feed",
        "مدار 21": "https://madar21.com/feed",
        "اليوم 24": "https://www.alyaoum24.com/feed",
        "كود": "https://www.goud.ma/feed",
        "فبراير": "https://www.febrayer.com/feed",
        "هبة بريس": "https://ar.hibapress.com/feed",
        "الصحيفة": "https://www.assahifa.com/feed",
        "زنقة 20": "https://www.rue20.com/feed",
        "أخبارنا": "https://www.akhbarona.com/feed",
        "لكم": "https://lakome2.com/feed",
        "بديل": "https://badeel.info/feed",
        "الأيام 24": "https://www.alayam24.com/feed",
        "عبر": "https://aabbir.com/feed",
        "برلمان": "https://www.barlamane.com/feed",
    },
    "🌍 جهوية وشمالية (تطوان/طنجة/المضيق)": {
        "طنجة 24": "https://tanja24.com/feed",
        "شمال بوست": "https://chamalpost.net/feed",
        "تطوان بريس": "https://tetouanpress.ma/feed",
        "بريس تطوان": "https://presstetouan.com/feed",
        "أكادير 24": "https://agadir24.info/feed",
        "الداخلة نيوز": "https://www.dakhlanews.com/feed",
        "مراكش الان": "https://www.marrakechalaan.com/feed",
        "وجدة سيتي": "https://www.oujdacity.net/feed",
    },
    "⚽ رياضة": {
        "البطولة": "https://www.elbotola.com/rss",
        "هسبريس الرياضية": "https://hesport.com/feed",
        "كوورة لايف": "https://www.kooora-live.com/feed",
        "المنتخب": "https://almountakhab.com/rss",
    },
    "💰 اقتصاد وتكنولوجيا": {
        "إيكو نيوز": "https://econews.ma/feed",
        "لـو 360 (اقتصاد)": "https://ar.le360.ma/rss", # ملاحظة: قد يحتاج لفلترة
        "تحدي": "https://tahaddy.net/feed",
    }
}

# ==========================================
# 3. الدوال المنطقية (Logic)
# ==========================================

# إعداد مفتاح API بشكل آمن
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except:
    st.error("⚠️ لم يتم العثور على مفتاح API. يرجى إضافته في إعدادات Streamlit.")

@st.cache_data(ttl=600) # تحديث كل 10 دقائق
def fetch_news_by_category(category):
    """جلب الأخبار بناءً على الفئة المختارة لتسريع الأداء"""
    news_items = []
    feeds = RSS_SOURCES.get(category, {})
    
    # شريط تقدم وهمي لتحسين تجربة المستخدم
    progress_bar = st.progress(0)
    total = len(feeds)
    
    for i, (source_name, url) in enumerate(feeds.items()):
        try:
            feed = feedparser.parse(url)
            # نأخذ أحدث 3 أخبار فقط من كل مصدر لتجنب الإغراق
            for entry in feed.entries[:3]:
                news_items.append({
                    "title": entry.title,
                    "link": entry.link,
                    "source": source_name,
                    "published": entry.get("published", "غير محدد"),
                    "summary": entry.get("summary", "")[:150] + "..." # ملخص قصير
                })
        except Exception:
            continue
        progress_bar.progress((i + 1) / total)
    
    progress_bar.empty()
    # ترتيب الأخبار حسب الأحدث (إذا توفر التاريخ) أو عشوائياً بشكل طبيعي
    return news_items

def extract_article(url):
    """سحب نص المقال كاملاً"""
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            return trafilatura.extract(downloaded)
    except:
        return None
    return None

def rewrite_with_yaqeen(text, tone):
    """إعادة الصياغة باستخدام Gemini"""
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    أنت "وكيل يقين"، محرر صحفي خبير يعمل لدى مؤسسة إعلامية مرموقة.
    مهمتك: إعادة صياغة الخبر التالي بشكل احترافي جداً ليكون جاهزاً للنشر فوراً.
    
    النص الأصلي:
    {text}
    
    الشروط الصارمة:
    1. الأسلوب: {tone} (رصين، تحليلي، أو عاجل حسب الطلب).
    2. العنوان: اقترح عنواناً جديداً قوياً متوافقاً مع SEO (يجذب النقرات ولكن بصدق).
    3. الهيكل: مقدمة قوية، متن مفصل مقسم لفقرات، وخاتمة.
    4. البيانات: حافظ على جميع الأسماء، الأرقام، والتواريخ بدقة متناهية.
    5. المخرجات: أضف في النهاية قائمة بـ 5 وسوم (Hashtags) قوية.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"عذراً، حدث خطأ أثناء المعالجة: {str(e)}"

# ==========================================
# 4. واجهة المستخدم (UI)
# ==========================================

# الشريط الجانبي
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3208/3208761.png", width=70) # أيقونة رمزية
    st.title("وكيل يقين 🦅")
    st.markdown("---")
    
    selected_category = st.selectbox("📂 اختر تخصص المصادر:", list(RSS_SOURCES.keys()))
    
    st.markdown("### ⚙️ إعدادات الصياغة")
    tone = st.select_slider("نبرة المقال:", options=["حيادي ورصين", "تحليلي وعميق", "حماسي وعاجل"], value="حيادي ورصين")
    
    if st.button("🔄 تحديث المصادر الآن"):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.caption("تم التطوير بواسطة: إلياس لمتي")

# المنطقة الرئيسية
st.markdown("<div class='main-header'>وكيل يقين للرصد والتحرير الصحفي</div>", unsafe_allow_html=True)
st.markdown(f"<div class='sub-header'>جاري رصد المصادر من فئة: <b>{selected_category}</b></div>", unsafe_allow_html=True)
st.markdown("---")

# جلب الأخبار
news_list = fetch_news_by_category(selected_category)

if not news_list:
    st.warning("جاري الاتصال بالمصادر... أو لا توجد أخبار حالياً.")
else:
    # عرض القائمة للاختيار
    article_options = [f"[{item['source']}] {item['title']}" for item in news_list]
    selected_idx = st.selectbox("🔎 اختر خبراً لمعالجته:", range(len(article_options)), format_func=lambda x: article_options[x])
    
    selected_article = news_list[selected_idx]
    
    # زر التنفيذ
    if st.button("✨ ابدأ المعالجة عبر وكيل يقين", type="primary"):
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.info("📄 المصدر الأصلي")
            st.markdown(f"**العنوان:** {selected_article['title']}")
            st.markdown(f"**المصدر:** {selected_article['source']}")
            st.markdown(f"[رابط المقال الأصلي]({selected_article['link']})")
            
            with st.spinner('جاري قراءة المقال الأصلي...'):
                original_text = extract_article(selected_article['link'])
                
            if original_text:
                st.text_area("محتوى النص الخام:", value=original_text[:800]+"...", height=300, disabled=True)
            else:
                st.error("تعذر سحب النص تلقائياً (الموقع محمي). يرجى نسخ النص يدوياً.")
                original_text = st.text_area("ألصق النص هنا يدوياً إذا لزم الأمر:")

        with col2:
            st.success("🦅 مخرجات وكيل يقين")
            if original_text:
                with st.spinner('يقين يقوم بإعادة الصياغة الآن...'):
                    rewritten = rewrite_with_yaqeen(original_text, tone)
                    st.markdown(rewritten)
                    st.download_button(
                        label="تحميل المقال (TXT)",
                        data=rewritten,
                        file_name=f"Yaqeen_Article_{datetime.now().strftime('%H%M')}.txt",
                        mime="text/plain"
                    )
            else:
                st.write("بانتظار النص...")