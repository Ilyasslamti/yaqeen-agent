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
# 0. الإعدادات
# ==========================================
st.set_page_config(
    page_title="يقين بريس | CMS",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# التحقق من الترسانة
try:
    from manadger_lib import RSS_DATABASE, get_safe_key, ELITE_PROMPT
except ImportError:
    st.error("❌ ملف manadger_lib.py مفقود.")
    st.stop()

ua = UserAgent()
socket.setdefaulttimeout(25)

if 'page' not in st.session_state: st.session_state.page = 'login'

# ==========================================
# 1. تصميم "المينيماليزم" (النظافة البصرية)
# ==========================================
def inject_clean_css():
    st.markdown("""
    <style>
        /* استيراد خط 'Cairo' العصري */
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');
        
        /* تطبيق الخط */
        html, body, [class*="css"], div, h1, h2, h3, p, span, button, input, textarea {
            font-family: 'Cairo', sans-serif !important;
            direction: rtl;
        }
        
        /* خلفية نظيفة تماماً */
        .stApp {
            background-color: #f8f9fa; /* رمادي فاتح جداً جداً */
        }
        
        /* إخفاء الهيدر الافتراضي */
        header { visibility: hidden; }
        
        /* === تصميم الهيدر الجديد (بسيط جداً) === */
        .simple-header {
            background-color: white;
            padding: 1.5rem;
            border-bottom: 1px solid #e5e7eb;
            margin-bottom: 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .brand-text {
            color: #111827; /* أسود فحمي */
            font-size: 1.8rem;
            font-weight: 900;
            letter-spacing: -0.5px;
        }
        
        .status-badge {
            background-color: #ecfdf5;
            color: #059669;
            padding: 0.4rem 1rem;
            border-radius: 9999px;
            font-size: 0.85rem;
            font-weight: 700;
            border: 1px solid #d1fae5;
        }

        /* === تحسين القائمة الجانبية === */
        section[data-testid="stSidebar"] {
            background-color: white;
            border-left: 1px solid #e5e7eb;
        }
        
        /* === البطاقات والحاويات === */
        div[data-testid="stExpander"], div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: white;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.02);
            transition: box-shadow 0.2s;
        }
        
        div[data-testid="stVerticalBlockBorderWrapper"]:hover {
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        }

        /* === الأزرار (تصميم Apple/Stripe) === */
        .stButton>button {
            background-color: #2563eb; /* أزرق ملكي صافي */
            color: white !important;
            font-weight: 600;
            border-radius: 8px;
            border: none;
            padding: 0.5rem 1rem;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            transition: all 0.2s;
        }
        .stButton>button:hover {
            background-color: #1d4ed8;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        
        /* === النصوص === */
        h1, h2, h3 { color: #111827 !important; }
        p, span, div { color: #374151 !important; }
        
        /* تمييز الروابط */
        a { color: #2563eb !important; text-decoration: none; }
        a:hover { text-decoration: underline; }

        /* موبايل */
        @media only screen and (max-width: 600px) {
            .simple-header { flex-direction: column; gap: 1rem; text-align: center; }
            .block-container { padding-top: 1rem !important; }
        }
    </style>
    """, unsafe_allow_html=True)

inject_clean_css()

# ==========================================
# 2. المنطق (Backend)
# ==========================================

def render_simple_header():
    date_str = time.strftime("%Y-%m-%d")
    st.markdown(f"""
    <div class="simple-header">
        <div style="display:flex; align-items:center; gap:10px;">
            <div class="brand-text">🦅 يقين بريس</div>
            <span style="color:#6b7280; font-size:0.9rem; margin-top:5px;">لوحة التحكم المركزية</span>
        </div>
        <div style="display:flex; align-items:center; gap:15px;">
            <span style="color:#6b7280; font-size:0.9rem;">{date_str}</span>
            <div class="status-badge">● متصل</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

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
        # محاكاة بسيطة وأنيقة
        progress = st.progress(0)
        status = st.empty()
        
        status.caption("جاري الاتصال بالمصدر...")
        progress.progress(20)
        downloaded = trafilatura.fetch_url(link)
        if not downloaded: raise Exception("المصدر محمي")
        
        status.caption("تنظيف النص واستخراج المحتوى...")
        progress.progress(50)
        raw = trafilatura.extract(downloaded)
        if not raw: raise Exception("المحتوى فارغ")
        
        soup = BeautifulSoup(raw, "html.parser")
        clean_text = soup.get_text()[:4500]
        
        status.caption("جاري الصياغة باستخدام الذكاء الاصطناعي...")
        progress.progress(80)
        
        api_key = get_safe_key()
        if not api_key: raise Exception("No API Key")
        
        client = OpenAI(api_key=api_key, base_url="https://api.sambanova.ai/v1")
        response = client.chat.completions.create(
            model='Meta-Llama-3.3-70B-Instruct',
            messages=[
                {"role": "system", "content": "أنت محرر صحفي مخضرم. أعد صياغة الخبر بأسلوب احترافي، مباشر، وخالٍ من الحشو."},
                {"role": "user", "content": ELITE_PROMPT.format(keyword=keyword) + f"\n\nالنص:\n{clean_text}"}
            ],
            temperature=0.3
        )
        
        progress.progress(100)
        time.sleep(0.5)
        progress.empty()
        status.empty()
        
        return response.choices[0].message.content, None
    except Exception as e:
        return None, str(e)

# ==========================================
# 3. الواجهة (UI)
# ==========================================

# --- صفحة الدخول (Clean Login) ---
if st.session_state.page == 'login':
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        # حاوية بيضاء بظل خفيف للدخول
        with st.container(border=True):
            st.markdown("<h2 style='text-align:center; margin-bottom:20px;'>تسجيل الدخول</h2>", unsafe_allow_html=True)
            with st.form("login_frm"):
                pwd = st.text_input("كلمة المرور", type="password")
                if st.form_submit_button("دخول للنظام", use_container_width=True):
                    if pwd == "Manager_Tech_2026":
                        st.session_state.page = 'newsroom'
                        st.rerun()
                    else:
                        st.error("كلمة المرور غير صحيحة")

# --- لوحة التحكم (Dashboard) ---
elif st.session_state.page == 'newsroom':
    render_simple_header()
    
    # القائمة الجانبية
    with st.sidebar:
        st.markdown("### الإعدادات")
        selected_cat = st.selectbox("قسم الأخبار", list(RSS_DATABASE.keys()))
        keyword_input = st.text_input("الكلمة المفتاحية (SEO)", "يقين بريس")
        
        st.markdown("---")
        col_side1, col_side2 = st.columns(2)
        with col_side1:
            if st.button("تحديث", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        with col_side2:
            if st.button("خروج", use_container_width=True):
                st.session_state.page = 'login'
                st.rerun()

    # المحتوى الرئيسي
    st.markdown(f"### 📡 آخر الأخبار: {selected_cat}")
    
    with st.spinner("جاري التحديث..."):
        news_list = scan_news_sector(selected_cat, RSS_DATABASE[selected_cat])

    if news_list:
        # تنسيق الشبكة (Grid Layout)
        col_right, col_left = st.columns([1.2, 2], gap="large")
        
        news_map = {f"{item['source']} | {item['title']}": item for item in news_list}
        
        # القائمة (يمين)
        with col_right:
            st.markdown("#### قائمة المصادر")
            selected_key = st.radio("اختر خبراً:", list(news_map.keys()), label_visibility="collapsed")
            target_news = news_map[selected_key]
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # بطاقة تفاصيل الخبر المختار (بسيطة ونظيفة)
            with st.container(border=True):
                st.markdown(f"**{target_news['title']}**")
                st.caption(f"{target_news['source']} • {target_news['published']}")
                st.markdown(f"[عرض المصدر الأصلي 🔗]({target_news['link']})")
                
                if st.button("⚡ صياغة الخبر الآن", use_container_width=True):
                    content, error = smart_editor_ai(target_news['link'], keyword_input)
                    if error:
                        st.error(error)
                    else:
                        st.session_state['current_article'] = content

        # المحرر (يسار)
        with col_left:
            st.markdown("#### مساحة التحرير")
            
            if 'current_article' in st.session_state:
                raw_txt = st.session_state['current_article']
                lines = raw_txt.split('\n')
                final_title = lines[0].replace('العنوان:', '').strip()
                final_body = '\n'.join(lines[1:])
                
                with st.container(border=True):
                    # حقول إدخال نظيفة
                    st.text_input("عنوان المقال", value=final_title)
                    st.text_area("نص المقال", value=final_body, height=600)
                    
                    st.success("✅ المقال جاهز للنشر")
            else:
                # رسالة فارغة أنيقة
                st.markdown("""
                <div style="text-align:center; padding:4rem; color:#9ca3af; border:2px dashed #e5e7eb; border-radius:12px;">
                    <p style="font-size:1.2rem; margin-bottom:10px;">👋 مرحباً بك في المحرر</p>
                    <p style="font-size:0.9rem;">اختر خبراً من القائمة لبدء العمل</p>
                </div>
                """, unsafe_allow_html=True)

    else:
        st.info("لا توجد أخبار متاحة حالياً. يرجى التحديث.")
