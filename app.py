import streamlit as st
import feedparser
import trafilatura
import os
import socket
import concurrent.futures
import base64
import time
from openai import OpenAI
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

# محاولة استيراد المكتبة الخاصة مع حماية النظام
try:
    from manadger_lib import RSS_DATABASE, get_safe_key, ELITE_PROMPT
except ImportError:
    st.error("❌ ملف الترسانة (manadger_lib.py) مفقود. النظام لا يعمل بدونه.")
    st.stop()

# ==========================================
# 0. إعدادات السيادة (Configuration)
# ==========================================
st.set_page_config(
    page_title="Yaqeen OS | غرفة العمليات",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تهيئة الشبكة
ua = UserAgent()
socket.setdefaulttimeout(25)

# إدارة الحالة (Session State) للتنقل السلس
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'logs' not in st.session_state: st.session_state.logs = []

# ==========================================
# 1. المحرك البصري (Advanced CSS)
# ==========================================
def inject_custom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
        
        /* الخلفية العامة: تدرج لوني عميق */
        .stApp {
            background: radial-gradient(circle at 10% 20%, #0f172a 0%, #020617 90%);
            font-family: 'Cairo', sans-serif !important;
            direction: rtl;
        }

        /* الكروت الزجاجية (Glassmorphism) */
        .css-1r6slb0, .stMarkdown, .stButton {
            color: #e2e8f0;
        }
        
        div[data-testid="stExpander"] {
            background: rgba(30, 41, 59, 0.4);
            border: 1px solid rgba(148, 163, 184, 0.1);
            border-radius: 12px;
            backdrop-filter: blur(10px);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }

        /* العناوين */
        h1, h2, h3 {
            background: linear-gradient(to left, #60a5fa, #3b82f6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 900 !important;
        }

        /* الأزرار الاحترافية */
        .stButton>button {
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
            border: none;
            color: white;
            padding: 0.6rem 1rem;
            border-radius: 8px;
            font-weight: bold;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 4px 14px 0 rgba(37, 99, 235, 0.39);
        }
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(37, 99, 235, 0.23);
        }

        /* تحسينات الموبايل الصارمة */
        @media only screen and (max-width: 600px) {
            .block-container { padding: 1rem 0.5rem !important; }
            h1 { font-size: 1.8rem !important; }
            .stButton>button { width: 100%; height: 3.5rem; font-size: 1.1rem; }
            /* إخفاء الهوامش الزائدة */
            div[data-testid="stSidebarUserContent"] { padding-top: 1rem; }
        }
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# ==========================================
# 2. الترسانة التقنية (Backend Logic)
# ==========================================

@st.cache_data(ttl=3600)
def get_logo_html():
    """جلب الشعار مع معالجة غيابه بأناقة"""
    if os.path.exists("logo.png"):
        with open("logo.png", "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        return f'<img src="data:image/png;base64,{encoded}" style="width: 140px; display: block; margin: 0 auto 20px auto; filter: drop-shadow(0 0 10px rgba(59,130,246,0.5));">'
    return "<h2 style='text-align:center'>🦅 YAQEEN</h2>"

@st.cache_data(ttl=900, show_spinner=False)
def scan_radar(category, sources):
    """محرك المسح الراداري المتوازي"""
    items = []
    def scan_single(name, url):
        try:
            feed = feedparser.parse(url, agent=ua.random)
            if not feed.entries: return []
            return [{
                "title": e.title, "link": e.link, "source": name,
                "published": e.get('published', 'N/A')
            } for e in feed.entries[:5]]
        except: return []

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as exc:
        futures = {exc.submit(scan_single, n, u): n for n, u in sources.items()}
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res: items.extend(res)
    return items

def ai_engine_core(link, keyword):
    """نواة الذكاء الاصطناعي مع محاكاة سجل العمليات"""
    log_container = st.empty()
    
    try:
        # 1. الاختراق (Screapping)
        log_container.code(f"📡 Establishing connection to: {link[:30]}...", language="bash")
        downloaded = trafilatura.fetch_url(link)
        if not downloaded: raise Exception("Connection Refused / Protected")
        
        # 2. الاستخراج (Extraction)
        log_container.code("🔓 Decrypting content structure...", language="bash")
        raw_text = trafilatura.extract(downloaded, include_comments=False)
        if not raw_text or len(raw_text) < 100: raise Exception("Content Empty")
        
        # 3. التنظيف (Sanitization)
        log_container.code("🧹 Sanitizing noise and ads...", language="bash")
        soup = BeautifulSoup(raw_text, "html.parser")
        clean_text = soup.get_text()[:5000]
        
        # 4. المعالجة (Processing)
        log_container.code("🧠 Injecting AI Prompt Vectors...", language="bash")
        api_key = get_safe_key()
        if not api_key: raise Exception("API Key Depleted")
        
        client = OpenAI(api_key=api_key, base_url="https://api.sambanova.ai/v1")
        response = client.chat.completions.create(
            model='Meta-Llama-3.3-70B-Instruct',
            messages=[
                {"role": "system", "content": "You are a specialized elite editor for 'Yaqeen Press'."},
                {"role": "user", "content": ELITE_PROMPT.format(keyword=keyword) + f"\n\nSOURCE:\n{clean_text}"}
            ],
            temperature=0.35
        )
        
        log_container.empty() # تنظيف السجلات عند النجاح
        return response.choices[0].message.content, None
        
    except Exception as e:
        log_container.empty()
        return None, str(e)

# ==========================================
# 3. واجهة التحكم (Flow Control)
# ==========================================

# --- شاشة تسجيل الدخول ---
if st.session_state.page == 'login':
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(get_logo_html(), unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #94a3b8;'>بوابة الوصول الآمن</h3>", unsafe_allow_html=True)
        
        with st.form("auth_matrix"):
            # استخدام st.secrets هو الأسلوب الاحترافي (سنستخدم قيمة افتراضية للتجربة فقط)
            # في الإنتاج الحقيقي، ضع كلمة السر في Secrets Management
            password = st.text_input("مفتاح التشفير:", type="password")
            
            if st.form_submit_button("بدء الجلسة 🚀", use_container_width=True):
                # هنا يجب استبدال النص الثابت بـ st.secrets["APP_PASSWORD"]
                if password == "Manager_Tech_2026": 
                    st.session_state.page = 'dashboard'
                    st.rerun()
                else:
                    st.error("⛔ محاولة وصول غير مصرح بها.")

# --- لوحة القيادة (Dashboard) ---
elif st.session_state.page == 'dashboard':
    
    # القائمة الجانبية الذكية
    with st.sidebar:
        if os.path.exists("logo.png"): st.image("logo.png", width=100)
        st.markdown("### 🎮 مركز القيادة")
        
        # تحكم بالرادار
        target_sector = st.selectbox("اختر القطاع:", list(RSS_DATABASE.keys()))
        keyword_input = st.text_input("هدف الـ SEO:", "يقين بريس")
        
        st.divider()
        if st.button("🔒 إغلاق الجلسة"):
            st.session_state.page = 'login'
            st.rerun()
            
        st.caption("System Status: ONLINE 🟢")

    # المنطقة الرئيسية
    st.markdown(f"## 📡 رادار الأخبار: {target_sector}")
    
    # شريط الحالة العلوي (Stats)
    stat1, stat2, stat3 = st.columns(3)
    stat1.metric("المصادر النشطة", len(RSS_DATABASE[target_sector]))
    
    with st.spinner("جاري مسح الطيف الترددي للأخبار..."):
        news_data = scan_radar(target_sector, RSS_DATABASE[target_sector])
        
    stat2.metric("الإشارات الملتقطة", len(news_data))
    stat3.metric("كفاءة المعالجة", "98%")

    if news_data:
        # تحويل القائمة لقاموس للبحث السريع
        news_map = {f"[{item['source']}] {item['title']}": item for item in news_data}
        
        # اختيار الخبر
        selected_key = st.selectbox("حدد الهدف للمعالجة:", list(news_map.keys()), label_visibility="collapsed")
        target_item = news_map[selected_key]
        
        # بطاقة المعاينة (Preview Card)
        with st.container():
            st.markdown(f"""
            <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 10px; border-right: 4px solid #3b82f6;">
                <h4 style="margin:0;">{target_item['title']}</h4>
                <p style="color: #94a3b8; font-size: 0.9rem; margin-top: 5px;">
                    المصدر: {target_item['source']} | التاريخ: {target_item['published']}
                </p>
                <a href="{target_item['link']}" target="_blank" style="color: #60a5fa; text-decoration: none;">🔗 معاينة المصدر الأصلي</a>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # زر الإطلاق
        if st.button("⚡ تشغيل محرك الصياغة (AI Engine)", use_container_width=True):
            content, err = ai_engine_core(target_item['link'], keyword_input)
            
            if err:
                st.error(f"❌ فشل المهمة: {err}")
            else:
                st.balloons()
                
                # معالجة النتيجة
                lines = content.split('\n')
                final_title = lines[0].replace('العنوان:', '').strip()
                final_body = '\n'.join(lines[1:])
                
                st.success("✅ تمت المهمة بنجاح")
                
                # عرض النتيجة في تبويبات
                tab1, tab2 = st.tabs(["📝 المقال النهائي", "💻 كود HTML"])
                
                with tab1:
                    st.text_input("العنوان:", value=final_title)
                    st.text_area("المحتوى:", value=final_body, height=500)
                
                with tab2:
                    html_code = f"<h2>{final_title}</h2><p>{final_body.replace(chr(10), '<br>')}</p>"
                    st.code(html_code, language="html")

    else:
        st.warning("لم يتم العثور على بيانات. تحقق من اتصال الأقمار الصناعية (الإنترنت).")
