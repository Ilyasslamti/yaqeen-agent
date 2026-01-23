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
# 0. الإعدادات الأساسية
# ==========================================
st.set_page_config(
    page_title="Yaqeen Press | سيادة الخبر",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# محاولة استيراد المكتبة الخاصة
try:
    from manadger_lib import RSS_DATABASE, get_safe_key, ELITE_PROMPT
except ImportError:
    st.error("❌ ملف manadger_lib.py مفقود. النظام لا يعمل بدونه.")
    st.stop()

# إعدادات الشبكة
ua = UserAgent()
socket.setdefaulttimeout(30)

# إدارة جلسة المستخدم
if 'page' not in st.session_state: st.session_state.page = 'login'

# ==========================================
# 1. التصميم الملكي (Royal CSS)
# ==========================================
def inject_royal_css():
    st.markdown("""
    <style>
        /* استيراد خط تجوال */
        @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');
        
        /* تطبيق الخط والاتجاه */
        html, body, [class*="css"], div, h1, h2, h3, h4, p, span, button, input {
            font-family: 'Tajawal', sans-serif !important;
            direction: rtl;
        }
        
        /* الخلفية العامة: كحلي ملكي داكن */
        .stApp {
            background-color: #0f172a;
            background-image: radial-gradient(at 10% 10%, #1e293b 0, transparent 50%), radial-gradient(at 90% 90%, #0f172a 0, transparent 50%);
        }
        
        /* إخفاء عناصر ستريم ليت المزعجة */
        header { visibility: hidden; }
        footer { visibility: hidden; }
        
        /* === تصميم الهيدر (News Ticker Style) === */
        .royal-header {
            background: rgba(30, 41, 59, 0.7);
            border-bottom: 2px solid #fbbf24; /* خط ذهبي */
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 0 0 15px 15px;
            backdrop-filter: blur(10px);
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 10px 30px -10px rgba(0,0,0,0.5);
        }
        
        .brand-title {
            color: white;
            font-size: 2rem;
            font-weight: 800;
            text-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
        }
        
        .live-badge {
            background: #ef4444;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.8rem;
            box-shadow: 0 0 10px #ef4444;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }

        /* === القائمة الجانبية === */
        section[data-testid="stSidebar"] {
            background-color: #1e293b;
            border-left: 1px solid #334155;
        }
        
        /* === البطاقات (Cards) === */
        div[data-testid="stExpander"], div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #1e293b;
            border: 1px solid #334155;
            border-radius: 10px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        }
        
        p, span, div { color: #cbd5e1 !important; } /* لون نص فاتح */
        h1, h2, h3, h4 { color: #f8fafc !important; } /* عناوين بيضاء */
        
        /* === الأزرار (Gold & Blue) === */
        .stButton>button {
            background: linear-gradient(90deg, #2563eb 0%, #1d4ed8 100%);
            color: white !important;
            border: none;
            height: 3.5rem;
            font-weight: bold;
            font-size: 1.1rem;
            border-radius: 8px;
            transition: transform 0.2s;
        }
        .stButton>button:hover {
            transform: scale(1.02);
            box-shadow: 0 0 15px rgba(37, 99, 235, 0.5);
        }

        /* === إصلاح حقول الإدخال === */
        .stTextInput>div>div>input, .stTextArea>div>div>textarea {
            background-color: #0f172a;
            color: white;
            border: 1px solid #475569;
        }

    </style>
    """, unsafe_allow_html=True)

inject_royal_css()

# ==========================================
# 2. المنطق البرمجي (المصحح 100%)
# ==========================================

def render_header():
    date_now = time.strftime("%A | %d %B %Y")
    # استخدام HTML آمن ومباشر
    html = f"""
    <div class="royal-header">
        <div>
            <div class="brand-title">🦅 يقين بريس</div>
            <div style="color: #94a3b8; font-size: 0.9rem;">غرفة العمليات المركزية</div>
        </div>
        <div style="text-align: left;">
            <div class="live-badge">● بث مباشر</div>
            <div style="color: #cbd5e1; margin-top: 5px; font-weight: bold;">{date_now}</div>
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
        # واجهة تقدم أنيقة
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.markdown("📡 **جاري الاتصال بالقمر الصناعي...**")
        progress_bar.progress(10)
        
        downloaded = trafilatura.fetch_url(link)
        if not downloaded: raise Exception("المصدر محمي بجدار ناري")
        
        progress_bar.progress(40)
        status_text.markdown("🔓 **فك تشفير المحتوى واستخراج النص...**")
        
        raw = trafilatura.extract(downloaded)
        if not raw: raise Exception("المحتوى فارغ")
        
        soup = BeautifulSoup(raw, "html.parser")
        clean_text = soup.get_text()[:4500]
        
        progress_bar.progress(70)
        status_text.markdown("🧠 **المعالج الذكي (AI) يكتب المقال...**")
        
        api_key = get_safe_key()
        if not api_key: raise Exception("مفتاح API مفقود")
        
        client = OpenAI(api_key=api_key, base_url="https://api.sambanova.ai/v1")
        response = client.chat.completions.create(
            model='Meta-Llama-3.3-70B-Instruct',
            messages=[
                {"role": "system", "content": "أنت محرر صحفي مخضرم في 'يقين بريس'. أعد صياغة الخبر بأسلوب احترافي، مباشر، وخالٍ من الحشو، مع عنوان جذاب."},
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
# 3. واجهة المستخدم (التطبيق)
# ==========================================

# --- صفحة الدخول ---
if st.session_state.page == 'login':
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("<h2 style='text-align: center; color: #60a5fa !important;'>🔐 بوابة الدخول</h2>", unsafe_allow_html=True)
            with st.form("login_frm"):
                pwd = st.text_input("كود المرور", type="password")
                if st.form_submit_button("فتح النظام", use_container_width=True):
                    if pwd == "Manager_Tech_2026":
                        st.session_state.page = 'newsroom'
                        st.rerun()
                    else:
                        st.error("الكود خاطئ!")

# --- غرفة الأخبار (الواجهة الرئيسية) ---
elif st.session_state.page == 'newsroom':
    render_header()
    
    # القائمة الجانبية
    with st.sidebar:
        # إصلاح نهائي لخطأ Generator: استخدام if تقليدي
        if os.path.exists("logo.png"):
            st.image("logo.png", width=130)
        else:
            st.markdown("### 🦅 Manadger Tech")
        
        st.markdown("### 🎛️ لوحة التحكم")
        selected_cat = st.radio("اختر القسم:", list(RSS_DATABASE.keys()))
        
        st.divider()
        keyword_input = st.text_input("🔑 الكلمة المفتاحية (SEO)", "يقين بريس")
        
        if st.button("🔄 تحديث البيانات", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
            
        if st.button("🔒 إغلاق الجلسة", use_container_width=True):
            st.session_state.page = 'login'
            st.rerun()

    # المحتوى الرئيسي
    st.markdown(f"<h3 style='border-right: 5px solid #fbbf24; padding-right: 15px;'>📡 رادار الأخبار: {selected_cat}</h3>", unsafe_allow_html=True)
    
    with st.spinner("جاري المسح الضوئي للمصادر..."):
        news_list = scan_news_sector(selected_cat, RSS_DATABASE[selected_cat])

    if news_list:
        # تخطيط الصفحة: قائمة (يمين) - محرر (يسار)
        col_list, col_editor = st.columns([1, 1.5], gap="large")
        
        news_map = {f"{item['source']} | {item['title']}": item for item in news_list}
        
        with col_list:
            st.info(f"تم التقاط {len(news_list)} إشارة.")
            selected_key = st.selectbox("اختر الخبر:", list(news_map.keys()), label_visibility="collapsed")
            target_news = news_map[selected_key]
            
            # بطاقة تفاصيل الخبر (تصميم داكن)
            with st.container(border=True):
                st.markdown(f"<h4 style='color: #60a5fa !important;'>{target_news['title']}</h4>", unsafe_allow_html=True)
                st.markdown(f"""
                <div style='background: rgba(255,255,255,0.05); padding: 10px; border-radius: 5px; margin: 10px 0;'>
                    <b>المصدر:</b> {target_news['source']}<br>
                    <b>التاريخ:</b> {target_news['published']}
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"[🔗 معاينة المصدر الأصلي]({target_news['link']})")
                
            if st.button("⚡ معالجة الخبر (AI)", use_container_width=True, type="primary"):
                content, error = smart_editor_ai(target_news['link'], keyword_input)
                if error:
                    st.error(error)
                else:
                    st.session_state['current_article'] = content

        with col_editor:
            st.markdown("#### 📝 المحرر الذكي")
            
            if 'current_article' in st.session_state:
                raw_txt = st.session_state['current_article']
                lines = raw_txt.split('\n')
                final_title = lines[0].replace('العنوان:', '').strip()
                final_body = '\n'.join(lines[1:])
                
                with st.container(border=True):
                    st.text_input("عنوان المقال المقترح", value=final_title)
                    st.text_area("نص المقال الجاهز", value=final_body, height=500)
                    st.success("✅ المقال جاهز للنشر!")
            else:
                st.markdown("""
                <div style="border: 2px dashed #334155; border-radius: 10px; padding: 50px; text-align: center; color: #64748b;">
                    <h3>مساحة العمل فارغة</h3>
                    <p>اختر خبراً من القائمة واضغط زر المعالجة لبدء التحرير</p>
                </div>
                """, unsafe_allow_html=True)

    else:
        st.warning("⚠️ لا توجد إشارات. الرادار لم يلتقط أي أخبار جديدة.")
