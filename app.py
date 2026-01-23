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
    page_title="يقين بريس | غرفة الأخبار",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# التحقق من المكتبة
try:
    from manadger_lib import RSS_DATABASE, get_safe_key, ELITE_PROMPT
except ImportError:
    st.error("❌ ملف manadger_lib.py مفقود.")
    st.stop()

# إعدادات الشبكة
ua = UserAgent()
socket.setdefaulttimeout(25)

# إدارة الحالة
if 'page' not in st.session_state: st.session_state.page = 'login'

# ==========================================
# 1. محرك التصميم (CSS عالي الوضوح)
# ==========================================
def inject_high_contrast_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Almarai:wght@400;700;800&display=swap');
        
        /* تطبيق الخط والاتجاه */
        html, body, [class*="css"], div, h1, h2, h3, h4, p, span, button, input, textarea {
            font-family: 'Almarai', sans-serif !important;
            direction: rtl;
        }
        
        /* خلفية الصفحة */
        .stApp { background-color: #f4f6f9; }
        
        /* إخفاء هيدر ستريم ليت */
        header { visibility: hidden; }
        
        /* === 1. تحسين العناوين والنصوص === */
        /* جعل العناوين الفرعية داكنة جداً وواضحة */
        h1, h2, h3, .stSubheader {
            color: #002b50 !important; /* أزرق داكن جداً */
            font-weight: 900 !important;
            text-shadow: none !important;
        }
        
        p, div, span, label {
            color: #111111 !important; /* أسود حالك للنصوص */
        }
        
        /* === 2. الهيدر الأزرق === */
        .news-header {
            background: linear-gradient(90deg, #003057 0%, #004070 100%);
            padding: 1.5rem;
            color: white !important;
            border-bottom: 5px solid #bfa058;
            border-radius: 0 0 15px 15px;
            margin-bottom: 25px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .news-header h1, .news-header div { color: white !important; }

        /* === 3. شريط عاجل === */
        .breaking-bar {
            background-color: #d32f2f;
            color: white !important;
            padding: 10px 15px;
            border-radius: 6px;
            font-weight: bold;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .breaking-bar span { color: white !important; }

        /* === 4. تحسين البطاقات (Cards) === */
        div[data-testid="stExpander"], div[data-testid="stVerticalBlockBorderWrapper"] {
            background: white;
            border: 1px solid #d1d5db; /* حدود رمادية واضحة */
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        
        /* === 5. الأزرار === */
        .stButton>button {
            background-color: #003057;
            color: white !important;
            font-weight: bold;
            border-radius: 6px;
            height: 3rem;
            border: none;
            transition: 0.2s;
        }
        .stButton>button:hover {
            background-color: #bfa058;
            color: black !important;
        }

        /* إصلاحات الموبايل */
        @media only screen and (max-width: 600px) {
            .news-header { flex-direction: column; text-align: center; gap: 10px; }
            .block-container { padding-top: 1rem !important; }
        }
    </style>
    """, unsafe_allow_html=True)

inject_high_contrast_css()

# ==========================================
# 2. دوال النظام
# ==========================================

def render_header():
    date_str = time.strftime("%A | %d-%m-%Y")
    # تم إضافة !important للألوان لضمان ظهورها
    html = f"""
    <div class="news-header">
        <div style="display: flex; flex-direction: column;">
            <h1 style="color: white !important; margin: 0; font-size: 1.8rem;">يقين بريس</h1>
            <span style="font-size: 0.9rem; opacity: 0.9; color: #e0e0e0 !important;">Sovereignty Platform</span>
        </div>
        <div style="text-align: left;">
            <div style="font-weight: bold; font-size: 1.1rem; color: #bfa058 !important;">{date_str}</div>
            <div style="background: rgba(255,255,255,0.2); padding: 4px 10px; border-radius: 15px; font-size: 0.8rem; display: inline-block; margin-top: 5px; color: white !important;">
                🔴 Live
            </div>
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
        with st.status("⚙️ غرفة التحرير تعمل...", expanded=True) as status:
            status.write("📡 الاتصال بالمصدر...")
            downloaded = trafilatura.fetch_url(link)
            if not downloaded: raise Exception("المصدر محمي")
            
            raw = trafilatura.extract(downloaded)
            if not raw: raise Exception("المحتوى فارغ")
            
            soup = BeautifulSoup(raw, "html.parser")
            clean_text = soup.get_text()[:4500]
            
            status.write("🧠 المعالجة الذكية...")
            api_key = get_safe_key()
            if not api_key: raise Exception("No API Key")
            
            client = OpenAI(api_key=api_key, base_url="https://api.sambanova.ai/v1")
            response = client.chat.completions.create(
                model='Meta-Llama-3.3-70B-Instruct',
                messages=[
                    {"role": "system", "content": "أنت صحفي محترف في 'يقين بريس'. أعد صياغة الخبر بأسلوب إخباري رصين (مثل العربية/الجزيرة)."},
                    {"role": "user", "content": ELITE_PROMPT.format(keyword=keyword) + f"\n\nالنص:\n{clean_text}"}
                ],
                temperature=0.3
            )
            status.update(label="✅ تم", state="complete", expanded=False)
            return response.choices[0].message.content, None
    except Exception as e:
        return None, str(e)

# ==========================================
# 3. واجهة التطبيق
# ==========================================

if st.session_state.page == 'login':
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br><h2 style='text-align:center; color:#003057 !important;'>بوابة يقين بريس</h2>", unsafe_allow_html=True)
        with st.form("login_frm"):
            pwd = st.text_input("كود الدخول:", type="password")
            if st.form_submit_button("تسجيل الدخول", use_container_width=True):
                if pwd == "Manager_Tech_2026":
                    st.session_state.page = 'newsroom'
                    st.rerun()
                else:
                    st.error("خطأ في الكود")

elif st.session_state.page == 'newsroom':
    render_header()
    
    with st.sidebar:
        if os.path.exists("logo.png"):
            st.image("logo.png", width=120)
        else:
            st.markdown("### 🦅 Yaqeen")
        
        st.markdown("<h3 style='color:#003057; border-bottom: 2px solid #bfa058;'>🎛️ التحكم</h3>", unsafe_allow_html=True)
        selected_cat = st.radio("الأقسام:", list(RSS_DATABASE.keys()))
        st.divider()
        keyword_input = st.text_input("SEO Keyword:", "يقين بريس")
        
        if st.button("تحديث 🔄"):
            st.cache_data.clear()
            st.rerun()
        if st.button("خروج 🔒"):
            st.session_state.page = 'login'
            st.rerun()

    st.markdown(f"""
    <div class="breaking-bar">
        <span style="background:rgba(255,255,255,0.2); padding:2px 8px; border-radius:4px; margin-left:10px;">عاجل</span>
        <span>تغطية حية ومباشرة لقسم: {selected_cat}</span>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("جاري جلب الأخبار..."):
        news_list = scan_news_sector(selected_cat, RSS_DATABASE[selected_cat])

    if news_list:
        col_list, col_editor = st.columns([1, 2], gap="medium")
        news_map = {f"{item['source']} - {item['title']}": item for item in news_list}
        
        with col_list:
            # عنوان واضح وداكن
            st.markdown("<h3 style='color: #003057; border-right: 5px solid #003057; padding-right: 10px;'>📌 شريط الأنباء</h3>", unsafe_allow_html=True)
            
            selected_key = st.selectbox("اختر الخبر:", list(news_map.keys()), label_visibility="collapsed")
            target_news = news_map[selected_key]
            
            # بطاقة الخبر المحدد (High Visibility)
            with st.container(border=True):
                # عنوان الخبر باللون الأحمر الداكن للتمييز
                st.markdown(f"<h4 style='color: #d32f2f; margin-top:0;'>{target_news['title']}</h4>", unsafe_allow_html=True)
                
                st.markdown(f"""
                <div style='font-size: 0.9rem; margin-top: 10px;'>
                    <b>المصدر:</b> {target_news['source']}<br>
                    <b>التوقيت:</b> {target_news['published']}
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"<a href='{target_news['link']}' target='_blank' style='display:block; margin-top:10px; color:#003057; font-weight:bold;'>🔗 قراءة المصدر الأصلي</a>", unsafe_allow_html=True)
                
            if st.button("✨ تحرير هذا الخبر", use_container_width=True):
                content, error = smart_editor_ai(target_news['link'], keyword_input)
                if error:
                    st.error(error)
                else:
                    st.session_state['current_article'] = content

        with col_editor:
            # عنوان واضح وداكن
            st.markdown("<h3 style='color: #003057; border-right: 5px solid #bfa058; padding-right: 10px;'>📝 المحرر الصحفي</h3>", unsafe_allow_html=True)
            
            if 'current_article' in st.session_state:
                raw_txt = st.session_state['current_article']
                lines = raw_txt.split('\n')
                final_title = lines[0].replace('العنوان:', '').strip()
                final_body = '\n'.join(lines[1:])
                
                with st.container(border=True):
                    st.text_input("العنوان المقترح:", value=final_title)
                    st.text_area("نص المقال:", value=final_body, height=600)
                    st.success("جاهز للنشر")
            else:
                st.info("👈 اختر خبراً من القائمة على اليمين ثم اضغط 'تحرير' لبدء العمل.")

    else:
        st.warning("لا توجد أخبار متاحة حالياً.")
