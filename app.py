import streamlit as st
import feedparser
import trafilatura
import json
import os
import socket
import concurrent.futures
import base64
import requests
from openai import OpenAI
from duckduckgo_search import DDGS
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
st.set_page_config(page_title="يقين بريس | غرفة العمليات", page_icon="🦅", layout="wide")

# إعدادات الأمان والشبكة
ua = UserAgent()
socket.setdefaulttimeout(30)

# ==========================================
# 1. دوال النظام (Core Functions)
# ==========================================

# دالة جلب الصور مع تحسين الكاش لعدم استهلاك الموارد
@st.cache_data(ttl=3600) # يحفظ الصور في الذاكرة لمدة ساعة
def get_base64_logo():
    if os.path.exists("logo.png"):
        with open("logo.png", "rb") as f:
            data = f.read()
        encoded = base64.b64encode(data).decode()
        return f'<img src="data:image/png;base64,{encoded}" style="width: 120px; display: block; margin: 0 auto;">'
    return ""

# نظام جلب الأخبار (محرك الرادار) - محسن للسرعة
@st.cache_data(ttl=900, show_spinner=False) # تحديث كل 15 دقيقة تلقائياً
def fetch_news_category(category_name, sources):
    news_items = []
    
    def fetch_single_source(source_name, url):
        try:
            # استخدام User-Agent لتجنب الحظر
            feed = feedparser.parse(url, agent=ua.random)
            if not feed.entries: return []
            
            return [{
                "title": entry.title,
                "link": entry.link,
                "source": source_name,
                "summary": getattr(entry, 'summary', '')[:200] + "..."
            } for entry in feed.entries[:6]] # نكتفي بـ 6 أخبار حديثة لكل مصدر للسرعة
        except:
            return []

    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        future_to_url = {executor.submit(fetch_single_source, name, url): name for name, url in sources.items()}
        for future in concurrent.futures.as_completed(future_to_url):
            data = future.result()
            if data: news_items.extend(data)
    
    return news_items

# محرك معالجة النصوص (الذكاء الاصطناعي)
def process_article_with_ai(link, keyword):
    try:
        # 1. سحب المحتوى بذكاء
        downloaded = trafilatura.fetch_url(link)
        if not downloaded: return None, "فشل سحب الرابط"
        
        main_text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
        if not main_text or len(main_text) < 100: return None, "المتوى قصير جداً أو محمي"

        # 2. تنظيف إضافي
        soup = BeautifulSoup(main_text, "html.parser")
        clean_text = soup.get_text()[:4000] # نرسل فقط 4000 حرف لتوفير التوكنز

        # 3. استدعاء الماندجر AI
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
# 2. الواجهة الرسومية (UI)
# ==========================================

# CSS مخصص للوضع الداكن الاحترافي
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; direction: rtl; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    .block-container { padding-top: 2rem; }
    h1, h2, h3 { color: #4aa3df !important; }
    .news-card { background-color: #262730; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-right: 5px solid #4aa3df; }
</style>
""", unsafe_allow_html=True)

# الهيدر
col_logo, col_title = st.columns([1, 4])
with col_logo:
    st.markdown(get_base64_logo(), unsafe_allow_html=True)
with col_title:
    st.title("منصة يقين بريس | YAQEEN PRESS")
    st.caption("نظام السيادة المعلوماتية - نسخة السحابة V2.0")

# التحقق من كلمة المرور (يفضل نقلها لـ st.secrets لاحقاً)
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    pwd = st.text_input("🔑 كود الدخول:", type="password")
    if st.button("دخول"):
        if pwd == "Manager_Tech_2026": # غير هذا لاحقاً!
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("كود خاطئ")
    st.stop()

# ==========================================
# 3. منطقة العمليات
# ==========================================

# القائمة الجانبية (Sidebar) للتحكم
with st.sidebar:
    st.header("🎮 وحدة التحكم")
    selected_category = st.selectbox("اختار القطاع:", list(RSS_DATABASE.keys()))
    
    st.divider()
    keyword_input = st.text_input("الكلمة المفتاحية (SEO):", "يقين بريس")
    
    if st.button("مسح الكاش (تحديث إجباري)"):
        st.cache_data.clear()
        st.rerun()

# جلب الأخبار
with st.spinner(f"جاري الاتصال بالأقمار الصناعية لجلب أخبار {selected_category}..."):
    news_list = fetch_news_category(selected_category, RSS_DATABASE[selected_category])

if not news_list:
    st.warning("لم يتم العثور على أخبار، أو هناك مشكلة في الاتصال بالمصادر.")
    st.stop()

st.success(f"تم رصد {len(news_list)} خبراً ساخناً 🔥")

# عرض الأخبار واختيار أحدها
# نقوم بإنشاء قائمة للعرض فقط
display_options = [f"{item['source']} - {item['title']}" for item in news_list]
selected_index = st.selectbox("اختر الخبر للمعالجة:", range(len(news_list)), format_func=lambda x: display_options[x])

target_news = news_list[selected_index]

# زر التنفيذ
if st.button(f"🚀 صياغة الخبر: {target_news['title'][:30]}..."):
    st.info(f"المصدر: {target_news['source']} | جاري المعالجة...")
    
    article_content, error = process_article_with_ai(target_news['link'], keyword_input)
    
    if error:
        st.error(f"حدث خطأ: {error}")
    else:
        st.balloons()
        st.markdown("### ✨ المقال الجاهز للنشر")
        
        # تقسيم العنوان عن المحتوى (افتراض أن السطر الأول عنوان)
        lines = article_content.split('\n')
        title = lines[0].replace('العنوان:', '').strip()
        body = '\n'.join(lines[1:])
        
        # عرض منسق
        st.text_input("العنوان المقترح:", value=title)
        st.text_area("نص المقال (جاهز للنسخ):", value=body, height=400)
        
        st.markdown("---")
        st.markdown(f"**رابط المصدر:** [اضغط هنا]({target_news['link']})")
