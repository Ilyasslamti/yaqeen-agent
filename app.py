
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

# ==========================================
# 0. الإعدادات والتهيئة
# ==========================================
st.set_page_config(
    page_title="Yaqeen Press | سيادة الخبر",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

try:
    from manadger_lib import RSS_DATABASE, get_safe_key, ELITE_PROMPT
except ImportError:
    st.error("❌ ملف manadger_lib.py مفقود.")
    st.stop()

ua = UserAgent()
socket.setdefaulttimeout(30)

if 'page' not in st.session_state: st.session_state.page = 'login'

# ==========================================
# 1. التصميم الملكي (مع إصلاح الأيقونات)
# ==========================================
def inject_royal_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');
        
        /* 1. تطبيق الخط على الحاويات الرئيسية والنصوص الصريحة فقط */
        html, body, .stApp {
            font-family: 'Tajawal', sans-serif;
        }
        
        /* إجبار النصوص العربية فقط على الخط، وعدم لمس الأيقونات (span/div العامة) */
        h1, h2, h3, h4, h5, h6, p, label, input, textarea, button {
            font-family: 'Tajawal', sans-serif !important;
            direction: rtl;
        }
        
        /* خلفية التطبيق */
        .stApp {
            background-color: #0f172a;
            background-image: radial-gradient(at 10% 10%, #1e293b 0, transparent 50%), radial-gradient(at 90% 90%, #0f172a 0, transparent 50%);
        }
        
        /* إخفاء الهيدر والفوتر الافتراضي */
        header[data-testid="stHeader"] { visibility: hidden; }
        footer { visibility: hidden; }
        
        /* === إصلاح زر القائمة (السهم) === */
        /* نعيد الخط الافتراضي للأزرار العلوية لكي تظهر الأيقونات */
        button[kind="header"] {
            font-family: sans-serif !important;
        }
        div[data-testid="stSidebarCollapseButton"] span {
            font-family: sans-serif !important; /* هذا يعيد سهم الإغلاق */
        }
        
        /* === إصلاح القائمة المنسدلة (التفاف النص) === */
        div[data-baseweb="select"] span {
            white-space: normal !important;
            height: auto !important;
        }
        
        /* === تصميم الهيدر === */
        .royal-header {
            background: rgba(30, 41, 59, 0.8);
            border-bottom: 2px solid #fbbf24;
            padding: 1.5rem;
            margin-bottom: 2rem;
            border-radius: 0 0 15px 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            backdrop-filter: blur(10px);
            box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        }
        
        .brand-title {
            color: white;
            font-size: 1.8rem;
            font-weight: 800;
            text-shadow: 0 0 10px rgba(0,0,0,0.3);
        }
        
        /* === البطاقات === */
        div[data-testid="stExpander"], div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #1e293b;
            border: 1px solid #334155;
            border-radius: 10px;
        }
        
        /* تصحيح ألوان النصوص */
        p, span, div { color: #cbd5e1; }
        h1, h2, h3, h4 { color: #f8fafc !important; }
        
        /* === الأزرار === */
        .stButton>button {
            background: linear-gradient(90deg, #2563eb 0%, #1d4ed8 100%);
            color: white !important;
            border: none;
            height: 3rem;
            font-weight: bold;
            border-radius: 8px;
            font-family: 'Tajawal', sans-serif !important;
        }

        /* موبايل */
        @media only screen and (max-width: 600px) {
            .royal-header { flex-direction: column; text-align: center; gap: 10px; }
            .brand-title { font-size: 1.5rem; }
        }
    </style>
    """, unsafe_allow_html=True)

inject_royal_css()

# ==========================================
# 2. المنطق البرمجي
# ==========================================

def render_header():
    date_now = time.strftime("%d-%m-%Y")
    html = f"""
    <div class="royal-header">
        <div>
            <div class="brand-title">🦅 يقين بريس</div>
            <div style="color: #94a3b8; font-size: 0.8rem;">نظام السيادة المعلوماتية</div>
        </div>
        <div style="text-align: left;">
            <div style="background:#dc2626; color:white; padding:2px 10px; border-radius:12px; font-size:0.7rem; display:inline-block; font-weight:bold;">● LIVE</div>
            <div style="color: #cbd5e1; font-weight: bold; font-size: 0.9rem; margin-top:5px;">{date_now}</div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

@st.cache_data(ttl=900, show_spinner=False)
def scan_news_sector(category, sources):
    items = []
    def fetch(name, url):
        try:
            feed = feedparser.parse(url, agent=ua.random)
            if not feed.entries: return []
            return [{
                "title": e.title, "link": e.link, "source": name,
                "published": e.get('published', '')[:16]
            } for e in feed.entries[:5]]
        except: return []

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
        futures = {ex.submit(fetch, n, u): n for n, u in sources.items()}
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res: items.extend(res)
    return items

def smart_editor_ai(link, keyword):
    try:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.markdown("📡 **جاري سحب البيانات...**")
        progress_bar.progress(20)
        
        downloaded = trafilatura.fetch_url(link)
        if not downloaded: raise Exception("المصدر محمي")
        
        progress_bar.progress(50)
        raw = trafilatura.extract(downloaded)
        if not raw: raise Exception("المحتوى فارغ")
        
        soup = BeautifulSoup(raw, "html.parser")
        clean_text = soup.get_text()[:4500]
        
        progress_bar.progress(80)
        status_text.markdown("🧠 **المعالج الذكي يعمل...**")
        
        api_key = get_safe_key()
        if not api_key: raise Exception("مفتاح API مفقود")
        
        client = OpenAI(api_key=api_key, base_url="https://api.sambanova.ai/v1")
        response = client.chat.completions.create(
            model='Meta-Llama-3.3-70B-Instruct',
            messages=[
                {"role": "system", "content": "أنت محرر صحفي مخضرم. أعد صياغة الخبر بأسلوب احترافي وعنوان جذاب."},
                {"role": "user", "content": ELITE_PROMPT.format(keyword=keyword) + f"\n\nالنص:\n{clean_text}"}
            ],
            temperature=0.3
        )
        
        progress_bar.progress(100)
        time.sleep(0.5)
        progress_bar.empty()
        status_text.empty()
        return response.choices[0].message.content, None
    except Exception as e:
        return None, str(e)

# ==========================================
# 3. واجهة المستخدم
# ==========================================

if st.session_state.page == 'login':
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("<h3 style='text-align: center; color: #60a5fa !important;'>🔐 الدخول</h3>", unsafe_allow_html=True)
            with st.form("login_frm"):
                pwd = st.text_input("الكود السري", type="password")
                if st.form_submit_button("دخول", use_container_width=True):
                    if pwd == "Manager_Tech_2026":
                        st.session_state.page = 'newsroom'
                        st.rerun()
                    else:
                        st.error("خطأ")

elif st.session_state.page == 'newsroom':
    render_header()
    
    with st.sidebar:
        # === إصلاح توسيط الشعار (الحل بالتقسيم) ===
        if os.path.exists("logo.png"):
            # نقسم العمود لثلاثة أجزاء، ونضع الصورة في المنتصف
            col_l, col_c, col_r = st.columns([1, 2, 1])
            with col_c:
                st.image("logo.png", width=110)
        else:
            st.markdown("<h3 style='text-align:center'>🦅 Yaqeen</h3>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 🎛️ التحكم")
        selected_cat = st.radio("الأقسام:", list(RSS_DATABASE.keys()))
        st.divider()
        keyword_input = st.text_input("SEO Keyword", "يقين بريس")
        
        if st.button("🔄 تحديث", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        if st.button("🔒 خروج", use_container_width=True):
            st.session_state.page = 'login'
            st.rerun()

    st.markdown(f"<h4 style='border-right: 4px solid #fbbf24; padding-right: 10px; color:white !important;'>📡 {selected_cat}</h4>", unsafe_allow_html=True)
    
    with st.spinner("جاري المسح..."):
        news_list = scan_news_sector(selected_cat, RSS_DATABASE[selected_cat])

    if news_list:
        col_list, col_editor = st.columns([1, 1.5], gap="medium")
        news_map = {f"{item['title']}": item for item in news_list}
        
        with col_list:
            st.info(f"{len(news_list)} خبر جديد")
            selected_title = st.selectbox("🔻 اختر خبراً:", list(news_map.keys()))
            target_news = news_map[selected_title]
            
            with st.container(border=True):
                st.markdown(f"<h4 style='color: #60a5fa !important; margin:0;'>{target_news['title']}</h4>", unsafe_allow_html=True)
                st.caption(f"{target_news['source']} | {target_news['published']}")
                st.markdown(f"[🔗 المصدر الأصلي]({target_news['link']})")
                
            if st.button("⚡ تحرير الخبر", use_container_width=True, type="primary"):
                content, error = smart_editor_ai(target_news['link'], keyword_input)
                if error:
                    st.error(error)
                else:
                    st.session_state['current_article'] = content

        with col_editor:
            st.markdown("#### 📝 المحرر")
            
            if 'current_article' in st.session_state:
                raw_txt = st.session_state['current_article']
                lines = raw_txt.split('\n')
                final_title = lines[0].replace('العنوان:', '').strip()
                final_body = '\n'.join(lines[1:])
                
                with st.container(border=True):
                    st.text_input("العنوان", value=final_title)
                    st.text_area("المقال", value=final_body, height=500)
                    st.success("جاهز للنشر")
            else:
                st.markdown("<div style='text-align:center; padding:40px; color:#64748b; border:2px dashed #334155; border-radius:10px;'>اختر خبراً لبدء المعالجة</div>", unsafe_allow_html=True)
    else:
        st.warning("لا توجد أخبار")
