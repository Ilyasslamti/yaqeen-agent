import streamlit as st
import feedparser
import trafilatura
import os
import socket
import concurrent.futures
import base64
from openai import OpenAI
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

# استيراد المكتبة الخاصة
try:
    from manadger_lib import RSS_DATABASE, get_safe_key, ELITE_PROMPT
except ImportError:
    st.error("❌ ملف manadger_lib.py مفقود.")
    st.stop()

# ==========================================
# 0. الإعدادات والتهيئة
# ==========================================
st.set_page_config(page_title="يقين بريس | موبايل", page_icon="🦅", layout="wide")

# إعدادات الأمان والشبكة
ua = UserAgent()
socket.setdefaulttimeout(30)

# ==========================================
# 1. دوال النظام (Core Functions)
# ==========================================

@st.cache_data(ttl=3600)
def get_base64_logo():
    if os.path.exists("logo.png"):
        with open("logo.png", "rb") as f:
            data = f.read()
        encoded = base64.b64encode(data).decode()
        # تنسيق يجعل الصورة متجاوبة (Responsive)
        return f'<img src="data:image/png;base64,{encoded}" style="max-width: 100%; width: 120px; display: block; margin: 0 auto;">'
    return ""

@st.cache_data(ttl=900, show_spinner=False)
def fetch_news_category(category_name, sources):
    news_items = []
    
    def fetch_single_source(source_name, url):
        try:
            feed = feedparser.parse(url, agent=ua.random)
            if not feed.entries: return []
            return [{
                "title": entry.title,
                "link": entry.link,
                "source": source_name,
                "published": entry.get('published', '')
            } for entry in feed.entries[:6]]
        except:
            return []

    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        future_to_url = {executor.submit(fetch_single_source, name, url): name for name, url in sources.items()}
        for future in concurrent.futures.as_completed(future_to_url):
            data = future.result()
            if data: news_items.extend(data)
    
    return news_items

def process_article_with_ai(link, keyword):
    try:
        downloaded = trafilatura.fetch_url(link)
        if not downloaded: return None, "فشل سحب الرابط"
        main_text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
        if not main_text or len(main_text) < 100: return None, "المتوى قصير جداً"

        soup = BeautifulSoup(main_text, "html.parser")
        clean_text = soup.get_text()[:4000]

        api_key = get_safe_key()
        if not api_key: return None, "مفتاح API مفقود"

        client = OpenAI(api_key=api_key, base_url="https://api.sambanova.ai/v1")
        response = client.chat.completions.create(
            model='Meta-Llama-3.3-70B-Instruct',
            messages=[
                {"role": "system", "content": "أنت محرر صحفي مخضرم في 'يقين بريس'. اكتب بأسلوب استقصائي رصين."},
                {"role": "user", "content": ELITE_PROMPT.format(keyword=keyword) + f"\n\nالنص الأصلي:\n{clean_text}"}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content, None
    except Exception as e:
        return None, str(e)

# ==========================================
# 2. تصميم الواجهة المتجاوب (Responsive UI)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Tajawal', sans-serif;
        direction: rtl;
    }

    /* === تنسيقات عامة === */
    h1 { color: #4aa3df !important; font-size: 2.2rem !important; text-align: center; }
    h2, h3 { color: #e0e0e0 !important; }
    .stButton>button { 
        border-radius: 12px; 
        font-weight: bold; 
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        border: none;
        color: white;
    }

    /* === 📱 قواعد الجوال الصارمة (Mobile Rules) === */
    @media only screen and (max-width: 600px) {
        
        /* تقليل الهوامش الجانبية للاستفادة من الشاشة */
        .block-container {
            padding-top: 1rem !important;
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }

        /* تصغير العنوان الرئيسي ليناسب الجوال */
        h1 { font-size: 1.5rem !important; margin-bottom: 0.5rem !important; }
        
        /* جعل الأزرار عريضة وسهلة اللمس */
        .stButton>button {
            width: 100% !important;
            height: 3.5rem !important; /* ارتفاع مريح للإبهام */
            font-size: 1.1rem !important;
            margin-top: 10px;
        }

        /* تحسين شكل القوائم المنسدلة */
        .stSelectbox div[data-baseweb="select"] {
            font-size: 1rem !important;
        }
        
        /* إخفاء العناصر غير الضرورية */
        header {visibility: hidden;}
        footer {visibility: hidden;}
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. واجهة التطبيق
# ==========================================

# التحقق من كلمة المرور
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(get_base64_logo(), unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>بوابة الدخول 🔐</h3>", unsafe_allow_html=True)
        with st.form("login"):
            pwd = st.text_input("الكود السري:", type="password")
            sub = st.form_submit_button("دخول للنظام")
            if sub:
                if pwd == "Manager_Tech_2026":
                    st.session_state.auth = True
                    st.rerun()
                else:
                    st.error("⛔ كود خاطئ")
    st.stop()

# --- بعد تسجيل الدخول ---

# القائمة الجانبية (تتحول لأيقونة في الموبايل تلقائياً)
with st.sidebar:
    st.image("logo.png", width=100) if os.path.exists("logo.png") else None
    st.title("لوحة التحكم")
    selected_category = st.selectbox("📡 اختر الرادار:", list(RSS_DATABASE.keys()))
    st.divider()
    keyword_input = st.text_input("🔑 الكلمة المفتاحية (SEO):", "يقين بريس")
    if st.button("🔄 تحديث البيانات"):
        st.cache_data.clear()
        st.rerun()

# الرأس
st.markdown(f"<h1 style='text-align: center;'>أخبار {selected_category}</h1>", unsafe_allow_html=True)

# جلب البيانات
with st.spinner("جاري المسح..."):
    news_list = fetch_news_category(selected_category, RSS_DATABASE[selected_category])

if news_list:
    # عرض الأخبار في بطاقات (Container) لتبدو جميلة على الموبايل
    st.success(f"تم التقاط {len(news_list)} إشارة.")
    
    # تحويل القائمة لقاموس لسهولة البحث
    news_map = {f"{item['source']} | {item['title']}": item for item in news_list}
    
    selected_title = st.selectbox("اختر خبراً للمعالجة:", list(news_map.keys()))
    target_news = news_map[selected_title]

    # عرض تفاصيل الخبر المحدد
    with st.expander("📄 تفاصيل الخبر الأصلي (اضغط للعرض)", expanded=True):
        st.markdown(f"**المصدر:** {target_news['source']}")
        st.markdown(f"**العنوان:** [{target_news['title']}]({target_news['link']})")
        st.caption(f"نشر في: {target_news.get('published', 'غير محدد')}")

    # زر المعالجة الكبير
    if st.button("✨ صياغة الخبر الآن (AI)"):
        progress_text = st.empty()
        progress_text.info("الذكاء الاصطناعي يقرأ ويحلل...")
        
        article_content, error = process_article_with_ai(target_news['link'], keyword_input)
        
        if error:
            st.error(f"حدث خطأ: {error}")
        else:
            progress_text.empty()
            st.balloons()
            
            # معالجة الناتج للعرض
            lines = article_content.split('\n')
            final_title = lines[0].replace('العنوان:', '').strip()
            final_body = '\n'.join(lines[1:])
            
            # العرض النهائي
            st.markdown("### 📝 المقال الجاهز")
            st.text_input("العنوان:", value=final_title)
            st.text_area("المحتوى:", value=final_body, height=400)
            st.success("جاهز للنسخ والنشر! 🚀")

else:
    st.warning("الرادار لم يلتقط شياً. تأكد من الاتصال أو جرب قسماً آخر.")
