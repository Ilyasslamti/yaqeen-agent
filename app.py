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

# محاولة استيراد المكتبة الخاصة
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
# 1. محرك التصميم (CSS Fix) - إصلاح الخطوط والهيدر
# ==========================================
def inject_newsroom_css():
    st.markdown("""
    <style>
        /* استيراد الخط بقوة */
        @import url('https://fonts.googleapis.com/css2?family=Almarai:wght@300;400;700;800&display=swap');
        
        /* تطبيق الخط على كل عنصر في الصفحة بالقوة الجبرية */
        html, body, [class*="css"], div, h1, h2, h3, p, span, button, input {
            font-family: 'Almarai', sans-serif !important;
            direction: rtl;
        }
        
        /* لون الخلفية مثل المواقع الإخبارية */
        .stApp {
            background-color: #f0f2f5;
        }
        
        /* إخفاء الهيدر الافتراضي المزعج */
        header { visibility: hidden; }
        
        /* تصميم الهيدر الجديد (الأزرق الداكن) */
        .news-header {
            background: linear-gradient(90deg, #003057 0%, #005090 100%);
            padding: 1.5rem 2rem;
            color: white;
            border-bottom: 5px solid #bfa058; /* الخط الذهبي */
            border-radius: 0 0 15px 15px;
            margin-bottom: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.15);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        /* شريط عاجل (الأحمر) */
        .breaking-bar {
            background-color: #d93025;
            color: white;
            padding: 12px;
            border-radius: 6px;
            font-weight: bold;
            margin-bottom: 25px;
            display: flex;
            align-items: center;
            box-shadow: 0 3px 6px rgba(0,0,0,0.1);
        }
        
        /* تحسين البطاقات */
        div[data-testid="stExpander"] {
            background: white;
            border: 1px solid #ddd;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            border-radius: 8px;
        }
        
        /* الأزرار الاحترافية */
        .stButton>button {
            background-color: #003057;
            color: white;
            border-radius: 6px;
            height: 3rem;
            font-weight: bold;
            border: none;
            transition: 0.3s;
        }
        .stButton>button:hover {
            background-color: #bfa058;
            color: white;
            transform: translateY(-2px);
        }

        /* إصلاحات الموبايل */
        @media only screen and (max-width: 600px) {
            .news-header { flex-direction: column; text-align: center; gap: 10px; padding: 1rem; }
            .block-container { padding-top: 1rem !important; }
            h1 { font-size: 1.4rem !important; }
        }
    </style>
    """, unsafe_allow_html=True)

inject_newsroom_css()

# ==========================================
# 2. دوال العرض والمنطق
# ==========================================

# دالة الهيدر (تم إصلاح خطأ الـ div الظاهر)
def render_header():
    date_str = time.strftime("%A | %d-%m-%Y")
    
    html_code = f"""
    <div class="news-header">
        <div style="display: flex; flex-direction: column;">
            <h1 style="color: white !important; margin: 0; font-size: 2rem; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">يقين بريس</h1>
            <span style="font-size: 0.9rem; opacity: 0.9; letter-spacing: 1px;">Sovereignty Platform</span>
        </div>
        <div style="text-align: left;">
            <div style="font-weight: bold; font-size: 1.2rem; color: #bfa058;">{date_str}</div>
            <div style="background: rgba(255,255,255,0.15); padding: 4px 12px; border-radius: 20px; display: inline-block; margin-top: 5px; font-size: 0.8rem;">
                🔴 Live Coverage
            </div>
        </div>
    </div>
    """
    # الحل الجذري هنا: unsafe_allow_html=True
    st.markdown(html_code, unsafe_allow_html=True)

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

# --- صفحة تسجيل الدخول ---
if st.session_state.page == 'login':
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br><h2 style='text-align:center; color:#003057;'>بوابة يقين بريس</h2>", unsafe_allow_html=True)
        with st.form("login_frm"):
            pwd = st.text_input("كود الدخول:", type="password")
            if st.form_submit_button("تسجيل الدخول", use_container_width=True):
                # يمكنك استبدال هذا لاحقاً بـ st.secrets
                if pwd == "Manager_Tech_2026":
                    st.session_state.page = 'newsroom'
                    st.rerun()
                else:
                    st.error("خطأ في الكود")

# --- غرفة الأخبار ---
elif st.session_state.page == 'newsroom':
    
    # 1. عرض الهيدر (بالطريقة الصحيحة)
    render_header()
    
    # 2. القائمة الجانبية
    with st.sidebar:
        # إصلاح مشكلة الشعار (استخدام if العادية)
        if os.path.exists("logo.png"):
            st.image("logo.png", width=120)
        else:
            st.markdown("### 🦅 Yaqeen")
        
        st.markdown("### 🎛️ التحكم")
        selected_cat = st.radio("الأقسام:", list(RSS_DATABASE.keys()))
        st.divider()
        keyword_input = st.text_input("SEO Keyword:", "يقين بريس")
        
        if st.button("تحديث 🔄"):
            st.cache_data.clear()
            st.rerun()
            
        if st.button("خروج 🔒"):
            st.session_state.page = 'login'
            st.rerun()

    # 3. شريط عاجل
    st.markdown(f"""
    <div class="breaking-bar">
        <span style="background:rgba(255,255,255,0.2); padding:2px 8px; border-radius:4px; margin-left:10px;">عاجل</span>
        <span>تغطية حية ومباشرة لقسم: {selected_cat}</span>
    </div>
    """, unsafe_allow_html=True)

    # 4. المحتوى الرئيسي
    with st.spinner("جاري الاتصال بالمراسلين (جلب الأخبار)..."):
        news_list = scan_news_sector(selected_cat, RSS_DATABASE[selected_cat])

    if news_list:
        # تقسيم الشاشة
        col_list, col_editor = st.columns([1, 2])
        
        news_map = {f"{item['source']} - {item['title']}": item for item in news_list}
        
        # العمود الأيمن: القائمة
        with col_list:
            st.subheader("📌 شريط الأنباء")
            selected_key = st.selectbox("اختر الخبر:", list(news_map.keys()), label_visibility="collapsed")
            target_news = news_map[selected_key]
            
            with st.container(border=True):
                st.markdown(f"**{target_news['title']}**")
                st.caption(f"المصدر: {target_news['source']} | {target_news['published']}")
                st.markdown(f"[رابط المصدر]({target_news['link']})")
                
            if st.button("✨ تحرير هذا الخبر", use_container_width=True):
                content, error = smart_editor_ai(target_news['link'], keyword_input)
                if error:
                    st.error(error)
                else:
                    st.session_state['current_article'] = content

        # العمود الأيسر: المحرر
        with col_editor:
            st.subheader("📝 المحرر الصحفي")
            
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
                st.info("اختر خبراً من القائمة واضغط 'تحرير' لبدء العمل.")

    else:
        st.warning("لا توجد أخبار متاحة حالياً.")
