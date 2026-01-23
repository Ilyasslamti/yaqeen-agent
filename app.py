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

# استيراد مكتبة الماندجر الخاصة
try:
    from manadger_lib import RSS_DATABASE, get_safe_key, ELITE_PROMPT
except ImportError:
    st.error("❌ ملف manadger_lib.py مفقود. تأكد من وجوده في نفس المجلد.")
    st.stop()

# ==========================================
# 0. الإعدادات والتهيئة
# ==========================================
st.set_page_config(page_title="يقين بريس | موبايل", page_icon="🦅", layout="wide")

# إعدادات الشبكة لتجنب التوقف
ua = UserAgent()
socket.setdefaulttimeout(30)

# ==========================================
# 1. دوال النظام (Core Functions)
# ==========================================

@st.cache_data(ttl=3600)
def get_base64_logo():
    """جلب الشعار وتحويله لـ Base64 لضمان ظهوره في كل الظروف"""
    if os.path.exists("logo.png"):
        with open("logo.png", "rb") as f:
            data = f.read()
        encoded = base64.b64encode(data).decode()
        return f'<img src="data:image/png;base64,{encoded}" style="max-width: 100%; width: 120px; display: block; margin: 0 auto;">'
    return ""

@st.cache_data(ttl=900, show_spinner=False)
def fetch_news_category(category_name, sources):
    """جلب الأخبار بالتوازي مع تخزين مؤقت (Cache) لمدة 15 دقيقة"""
    news_items = []
    
    def fetch_single_source(source_name, url):
        try:
            # استخدام متصفح وهمي لتجنب الحظر
            feed = feedparser.parse(url, agent=ua.random)
            if not feed.entries: return []
            
            # جلب آخر 6 أخبار فقط للسرعة
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
    """معالجة المقال: سحب -> تنظيف -> إعادة صياغة"""
    try:
        # 1. سحب المحتوى
        downloaded = trafilatura.fetch_url(link)
        if not downloaded: return None, "فشل سحب الرابط (قد يكون الموقع محمياً)"
        
        main_text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
        if not main_text or len(main_text) < 100: return None, "المحتوى قصير جداً"

        # 2. تنظيف إضافي
        soup = BeautifulSoup(main_text, "html.parser")
        clean_text = soup.get_text()[:4500] # نرسل جزءاً كافياً للـ AI

        # 3. استدعاء الذكاء الاصطناعي
        api_key = get_safe_key()
        if not api_key: return None, "مفتاح API مفقود أو غير صالح"

        client = OpenAI(api_key=api_key, base_url="https://api.sambanova.ai/v1")
        
        response = client.chat.completions.create(
            model='Meta-Llama-3.3-70B-Instruct',
            messages=[
                {"role": "system", "content": "أنت محرر صحفي مخضرم في 'يقين بريس'. مهمتك إعادة صياغة الأخبار بأسلوب احترافي، محايد، ومشوق."},
                {"role": "user", "content": ELITE_PROMPT.format(keyword=keyword) + f"\n\nالنص الأصلي للخبر:\n{clean_text}"}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content, None
    except Exception as e:
        return None, str(e)

# ==========================================
# 2. تصميم الواجهة (CSS Responsive)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Tajawal', sans-serif;
        direction: rtl;
    }

    h1 { color: #4aa3df !important; font-size: 2rem !important; text-align: center; margin-bottom: 20px; }
    
    /* تنسيق الأزرار */
    .stButton>button { 
        border-radius: 10px; 
        font-weight: bold; 
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        border: none;
        color: white;
        transition: all 0.3s ease;
    }
    .stButton>button:hover { transform: scale(1.02); }

    /* === 📱 قواعد الموبايل (Mobile Rules) === */
    @media only screen and (max-width: 600px) {
        .block-container {
            padding-top: 1rem !important;
            padding-left: 0.8rem !important;
            padding-right: 0.8rem !important;
        }
        h1 { font-size: 1.5rem !important; }
        .stButton>button {
            width: 100% !important;
            height: 3.5rem !important;
            font-size: 1.1rem !important;
            margin-top: 10px;
        }
        /* إخفاء عناصر التحكم العلوية لزيادة المساحة */
        header {visibility: hidden;}
        footer {visibility: hidden;}
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. منطق التطبيق (Application Logic)
# ==========================================

# نظام تسجيل الدخول البسيط
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(get_base64_logo(), unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #666;'>بوابة الدخول 🔐</h3>", unsafe_allow_html=True)
        with st.form("login_form"):
            pwd = st.text_input("كود المرور:", type="password")
            submitted = st.form_submit_button("تسجيل الدخول")
            if submitted:
                if pwd == "Manager_Tech_2026":
                    st.session_state.auth = True
                    st.rerun()
                else:
                    st.error("⛔ الكود غير صحيح")
    st.stop()

# --- واجهة المستخدم بعد الدخول ---

# القائمة الجانبية (تم إصلاح خطأ الصورة هنا)
with st.sidebar:
    # ✅ التصحيح: استخدام جملة شرطية صريحة لمنع طباعة الكائن
    if os.path.exists("logo.png"):
        st.image("logo.png", width=100)
    
    st.title("لوحة التحكم")
    selected_category = st.selectbox("📡 اختر القسم:", list(RSS_DATABASE.keys()))
    st.divider()
    keyword_input = st.text_input("🔑 كلمة مفتاحية (SEO):", "يقين بريس")
    
    if st.button("🔄 تحديث المصادر"):
        st.cache_data.clear()
        st.rerun()

# المحتوى الرئيسي
st.markdown(f"<h1>أخبار {selected_category}</h1>", unsafe_allow_html=True)

# جلب الأخبار
with st.spinner("جاري مسح المصادر..."):
    news_list = fetch_news_category(selected_category, RSS_DATABASE[selected_category])

if news_list:
    st.success(f"تم التقاط {len(news_list)} إشارة.")
    
    # تحويل القائمة لقاموس لسهولة الاختيار بالعنوان
    news_map = {f"{item['source']} | {item['title']}": item for item in news_list}
    
    # قائمة الاختيار
    selected_title = st.selectbox("اختر الخبر للمعالجة:", list(news_map.keys()))
    target_news = news_map[selected_title]

    # عرض التفاصيل (Expander يوفر مساحة في الموبايل)
    with st.expander("📄 تفاصيل الخبر الأصلي (اضغط هنا)", expanded=True):
        st.markdown(f"**المصدر:** {target_news['source']}")
        st.markdown(f"**العنوان:** [{target_news['title']}]({target_news['link']})")
        st.caption(f"تاريخ النشر: {target_news.get('published', 'غير متوفر')}")

    # زر المعالجة
    if st.button("✨ صياغة الخبر بالذكاء الاصطناعي"):
        status_box = st.empty()
        status_box.info("🤖 الماندجر يقرأ الخبر ويحلله...")
        
        article_content, error = process_article_with_ai(target_news['link'], keyword_input)
        
        if error:
            status_box.error(f"حدث خطأ: {error}")
        else:
            status_box.empty()
            st.balloons()
            
            # تنسيق المخرجات
            lines = article_content.split('\n')
            final_title = lines[0].replace('العنوان:', '').strip()
            final_body = '\n'.join(lines[1:])
            
            st.markdown("### 📝 النتيجة النهائية")
            st.text_input("العنوان المقترح:", value=final_title)
            st.text_area("نص المقال:", value=final_body, height=450)
            st.success("تمت الصياغة بنجاح! جاهز للنشر.")

else:
    st.warning("⚠️ لم يتم العثور على أخبار. قد يكون هناك ضغط على المصادر، حاول التحديث.")
