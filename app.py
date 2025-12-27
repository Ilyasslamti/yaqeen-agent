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
    page_title="وكيل يقين - غرفة الأخبار المركزية",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS لتحسين المظهر وجعله يشبه لوحات التحكم الاحترافية
st.markdown("""
<style>
    .main-header {font-size: 2.2rem; color: #1E3A8A; font-weight: bold; text-align: center; margin-bottom: 0.5rem;}
    .sub-header {font-size: 1.1rem; color: #555; text-align: center; margin-bottom: 2rem;}
    .news-card {
        padding: 1rem; 
        border-radius: 8px; 
        border: 1px solid #eee; 
        background-color: white; 
        margin-bottom: 0.8rem;
        transition: transform 0.2s;
    }
    .news-card:hover {transform: scale(1.01); border-color: #1E3A8A;}
    .source-badge {
        background-color: #e3f2fd; 
        color: #1565c0; 
        padding: 2px 8px; 
        border-radius: 4px; 
        font-size: 0.8rem; 
        font-weight: bold;
    }
    /* إخفاء علامة القفل الخاصة بـ Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. قاعدة بيانات الـ 60 مصدر (محدثة وشاملة)
# ==========================================
RSS_SOURCES = {
    "🔵 أخبار الشمال (تطوان/المضيق/طنجة)": {
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
    "📰 صحف وطنية كبرى (رقمية وورقية)": {
        "هسبريس": "https://www.hespress.com/feed",
        "العمق المغربي": "https://al3omk.com/feed",
        "مدار 21": "https://madar21.com/feed",
        "اليوم 24": "https://www.alyaoum24.com/feed",
        "كود": "https://www.goud.ma/feed",
        "زنقة 20": "https://www.rue20.com/feed",
        "الأحداث المغربية": "https://ahdath.info/feed",
        "الصباح": "https://assabah.ma/feed",
        "بيان اليوم": "https://bayanealyaoume.press.ma/feed",
        "رسالة الأمة": "https://risalatalomma.ma/feed",
        "برلمان.كوم": "https://www.barlamane.com/feed",
        "فبراير": "https://www.febrayer.com/feed",
        "هبة بريس": "https://ar.hibapress.com/feed",
        "الصحيفة": "https://www.assahifa.com/feed",
        "لكم": "https://lakome2.com/feed",
        "بديل": "https://badeel.info/feed",
        "الأيام 24": "https://www.alayam24.com/feed",
        "عبر": "https://aabbir.com/feed",
        "آشكاين": "https://achkayen.com/feed",
        "أنفاس بريس": "https://anfaspress.com/feed",
        "الأول": "https://alaoual.com/feed",
        "بناصا": "https://banassa.com/feed",
        "سفيركم": "https://safir24.ma/feed",
    },
    "🌍 جهات المملكة (الصحراء/الشرق/الوسط)": {
        "أكادير 24": "https://agadir24.info/feed",
        "الداخلة نيوز": "https://www.dakhlanews.com/feed",
        "مراكش الان": "https://www.marrakechalaan.com/feed",
        "وجدة سيتي": "https://www.oujdacity.net/feed",
        "ناظور سيتي": "https://www.nadorcity.com/feed",
        "سوس 24": "https://souss24.com/feed",
        "فاس نيوز": "https://fesnews.media/feed",
        "مكناس بريس": "https://meknespress.com/feed",
    },
    "⚽ رياضة مغربية وعالمية": {
        "البطولة": "https://www.elbotola.com/rss",
        "هسبريس الرياضية": "https://hesport.com/feed",
        "المنتخب": "https://almountakhab.com/rss",
        "هاي كورة": "https://hihi2.com/feed",
        "360 سبورت": "https://sport.le360.ma/rss",
    },
    "💰 مال وأعمال وتكنولوجيا": {
        "إيكو نيوز": "https://econews.ma/feed",
        "تحدي": "https://tahaddy.net/feed",
        "لوماتان (اقتصادي)": "https://lematin.ma/rss",
        "التقنية (عالم التقنية)": "https://www.tech-wd.com/wd/feed",
    }
}

# ==========================================
# 3. المنطق البرمجي (Backend Logic)
# ==========================================

# إعداد مفتاح API بشكل آمن من Secrets
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except Exception as e:
    st.error("⚠️ خطأ في مفتاح API. يرجى التأكد من إضافته في إعدادات Secrets في Streamlit Cloud.")
    st.stop()

@st.cache_data(ttl=300) # تحديث كل 5 دقائق
def fetch_news_by_category(category):
    """جلب الأخبار من الفئة المختارة"""
    news_items = []
    feeds = RSS_SOURCES.get(category, {})
    
    # واجهة تحميل تفاعلية
    status_text = st.empty()
    progress_bar = st.progress(0)
    total = len(feeds)
    
    for i, (source_name, url) in enumerate(feeds.items()):
        status_text.caption(f"📡 جاري الاتصال بـ: {source_name}...")
        try:
            # مهلة زمنية قصيرة لتجاوز المصادر البطيئة
            feed = feedparser.parse(url)
            if feed.entries:
                # نأخذ أحدث خبرين فقط لتسريع القائمة
                for entry in feed.entries[:2]:
                    news_items.append({
                        "title": entry.title,
                        "link": entry.link,
                        "source": source_name,
                        "published": entry.get("published", ""),
                        "summary": entry.get("summary", "")[:120] + "..."
                    })
        except Exception:
            continue # تخطي المصدر في حال الخطأ
        progress_bar.progress((i + 1) / total)
    
    status_text.empty()
    progress_bar.empty()
    return news_items

def extract_article(url):
    """سحب نص المقال"""
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            return trafilatura.extract(downloaded)
    except:
        return None
    return None

def rewrite_with_yaqeen(text, tone, user_instructions):
    """إعادة الصياغة باستخدام Gemini Pro"""
    
    # 🔴 التعديل الأساسي هنا: استخدام gemini-pro المستقر
    model = genai.GenerativeModel('gemini-pro')
    
    prompt = f"""
    أنت محرر صحفي خبير في "وكيل يقين"، تعمل لصالح شبكة "هاشمي بريس".
    المهمة: إعادة صياغة الخبر التالي ليكون جاهزاً للنشر فوراً.
    
    النص الأصلي:
    {text}
    
    التعليمات الصارمة:
    1. النبرة المطلوبة: {tone}.
    2. تعليمات إضافية من المدير: {user_instructions}
    3. العنوان: اكتب عنواناً جديداً احترافياً يجذب القارئ (SEO Friendly).
    4. الهيكل: مقدمة قوية تلخص الخبر، ثم التفاصيل، ثم خلفية عن الموضوع إذا لزم الأمر.
    5. التنسيق: استخدم العناوين الفرعية (Bold) لتسهيل القراءة.
    6. الدقة: لا تغير الأرقام أو الأسماء أو الأماكن الواردة في الخبر الأصلي.
    
    المخرجات:
    أريد المقال كاملاً مع العنوان والوسوم (Hashtags) في النهاية.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"عذراً، حدث خطأ تقني أثناء المعالجة: {str(e)}"

# ==========================================
# 4. واجهة التطبيق (UI)
# ==========================================

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3208/3208761.png", width=70)
    st.title("🦅 وكيل يقين")
    st.caption("نظام الرصد الصحفي الذكي v1.0")
    st.markdown("---")
    
    selected_category = st.selectbox("📂 اختر قسم المصادر:", list(RSS_SOURCES.keys()))
    
    st.markdown("### ✍️ إعدادات المحرر")
    tone = st.select_slider("الأسلوب:", options=["رسمي ومحايد", "تحليلي وعميق", "سريع وعاجل"], value="رسمي ومحايد")
    user_instructions = st.text_input("تعليمات خاصة:", placeholder="مثلاً: لخصه في فقرتين فقط...")
    
    if st.button("تحديث الأخبار 🔄"):
        st.cache_data.clear()
        st.rerun()
        
    st.markdown("---")
    st.info("تم التطوير بواسطة: إلياس لمتي")

st.markdown("<div class='main-header'>وكيل يقين - غرفة الأخبار المركزية</div>", unsafe_allow_html=True)
st.info(f"يتم الآن رصد المصادر من قسم: **{selected_category}**")

# عملية الجلب
news_list = fetch_news_by_category(selected_category)

if news_list:
    # عرض القائمة
    article_options = [f"【{item['source']}】 {item['title']}" for item in news_list]
    selected_idx = st.selectbox("🔎 اختر مقالاً للمعالجة:", range(len(article_options)), format_func=lambda x: article_options[x])
    
    selected_article = news_list[selected_idx]
    
    # زر البدء
    if st.button("🚀 تحليل وإعادة صياغة المقال", type="primary"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.warning("المقال الأصلي")
            st.markdown(f"**{selected_article['title']}**")
            st.caption(f"المصدر: {selected_article['source']} | الرابط: {selected_article['link']}")
            
            with st.spinner("جاري سحب النص من المصدر..."):
                original_text = extract_article(selected_article['link'])
            
            if original_text:
                st.text_area("النص الخام:", original_text, height=400)
            else:
                st.error("⚠️ تعذر سحب النص تلقائياً (الموقع محمي). المرجو النسخ اليدوي.")
                original_text = st.text_area("ألصق النص هنا يدوياً:")

        with col2:
            st.success("✨ النسخة الجديدة (يقين)")
            if original_text:
                with st.spinner("جاري الكتابة بأسلوب صحفي محترف..."):
                    rewritten = rewrite_with_yaqeen(original_text, tone, user_instructions)
                    st.markdown(rewritten)
                    
                    # تحميل الملف
                    st.download_button(
                        label="📥 تحميل المقال (TXT)", 
                        data=rewritten, 
                        file_name=f"Yaqeen_News_{datetime.now().strftime('%H%M')}.txt"
                    )
else:
    st.warning("لم يتم العثور على أخبار جديدة، أو هناك مشكلة في الاتصال ببعض المصادر.")                    })
        except Exception:
            continue # تخطي المصدر في حال الخطأ
        progress_bar.progress((i + 1) / total)
    
    status_text.empty()
    progress_bar.empty()
    return news_items

def extract_article(url):
    """سحب نص المقال"""
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            return trafilatura.extract(downloaded)
    except:
        return None
    return None

def rewrite_with_yaqeen(text, tone, user_instructions):
    """إعادة الصياغة بالذكاء الاصطناعي"""
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    أنت محرر صحفي خبير في "وكيل يقين".
    المهمة: إعادة صياغة الخبر التالي للنشر.
    
    النص الأصلي:
    {text}
    
    التعليمات:
    1. النبرة: {tone}.
    2. تعليمات إضافية من المدير: {user_instructions}
    3. العنوان: عنوان احترافي جذاب (SEO).
    4. الهيكل: مقدمة، تفاصيل، خاتمة.
    5. التنسيق: استخدم Bold للعناوين الفرعية.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"خطأ في المعالجة: {str(e)}"

# ==========================================
# 4. واجهة التطبيق (UI)
# ==========================================

with st.sidebar:
    st.title("🦅 وكيل يقين")
    st.markdown("---")
    selected_category = st.selectbox("اختر قسم المصادر:", list(RSS_SOURCES.keys()))
    
    st.markdown("### ✍️ إعدادات المحرر")
    tone = st.select_slider("الأسلوب:", options=["رسمي", "تحليلي", "تفاعلي/سوشيال"], value="رسمي")
    user_instructions = st.text_input("تعليمات خاصة (اختياري):", placeholder="مثلاً: ركز على تصريح الوزير...")
    
    if st.button("تحديث الأخبار 🔄"):
        st.cache_data.clear()
        st.rerun()

st.markdown("<div class='main-header'>وكيل يقين - سكربت يقست للاخبار </div>", unsafe_allow_html=True)
st.info(f"يتم الآن رصد المصادر من قسم: **{selected_category}**")

# عملية الجلب
news_list = fetch_news_by_category(selected_category)

if news_list:
    # عرض القائمة
    article_options = [f"【{item['source']}】 {item['title']}" for item in news_list]
    selected_idx = st.selectbox("اختر مقالاً للمعالجة:", range(len(article_options)), format_func=lambda x: article_options[x])
    
    selected_article = news_list[selected_idx]
    
    # زر البدء
    if st.button("🚀 تحليل وإعادة صياغة المقال", type="primary"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.warning("المقال الأصلي")
            st.markdown(f"**{selected_article['title']}**")
            with st.spinner("جاري سحب النص..."):
                original_text = extract_article(selected_article['link'])
            
            if original_text:
                st.text_area("", original_text, height=400)
            else:
                st.error("تعذر سحب النص تلقائياً. المرجو النسخ اليدوي.")
                original_text = st.text_area("ألصق النص هنا:")

  with col2:
            st.success("✨ النسخة الجديدة (يقين)")
            if original_text:
                with st.spinner("جاري الكتابة بأسلوب صحفي محترف..."):
                    rewritten = rewrite_with_yaqeen(original_text, tone, user_instructions)
                    st.markdown(rewritten)
                    
                    # تحميل الملف
                    st.download_button(
                        label="📥 تحميل المقال (TXT)", 
                        data=rewritten, 
                        file_name=f"Yaqeen_News_{datetime.now().strftime('%H%M')}.txt"
                    )
else:
    st.warning("لم يتم العثور على أخبار جديدة، أو هناك مشكلة في الاتصال ببعض المصادر.")
