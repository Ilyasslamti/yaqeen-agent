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
# 0. الإعدادات والتهيئة (Setup)
# ==========================================
st.set_page_config(
    page_title="Yaqeen Press | غرفة الأخبار",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# التحقق من المكتبة الخاصة
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
# 1. محرك التصميم "الجزيرة ستايل" (Newsroom CSS)
# ==========================================
def inject_newsroom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Almarai:wght@300;400;700;800&display=swap');
        
        /* === 1. الهيكل العام والألوان === */
        .stApp {
            background-color: #f4f6f8; /* رمادي فاتح جداً مريح للعين */
            font-family: 'Almarai', sans-serif !important;
            direction: rtl;
        }
        
        /* === 2. الهيدر (Header) === */
        header { visibility: hidden; } /* إخفاء هيدر ستريم ليت الافتراضي */
        
        .news-header {
            background: #003057; /* أزرق الجزيرة الداكن */
            padding: 15px 20px;
            color: white;
            border-bottom: 4px solid #bfa058; /* الخط الذهبي المميز */
            margin-bottom: 20px;
            border-radius: 0 0 10px 10px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            display: flex;
            align-items: center;
            justify_content: space-between;
        }

        /* === 3. شريط عاجل (Breaking News) === */
        .breaking-news {
            background-color: #c00; /* أحمر الأخبار العاجلة */
            color: white;
            padding: 8px 15px;
            font-weight: bold;
            font-size: 0.9rem;
            display: flex;
            align-items: center;
            border-radius: 4px;
            margin-bottom: 15px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .breaking-label {
            background: rgba(0,0,0,0.2);
            padding: 2px 8px;
            margin-left: 10px;
            border-radius: 3px;
        }

        /* === 4. بطاقات الأخبار (News Cards) === */
        div[data-testid="stExpander"] {
            background-color: #ffffff;
            border: 1px solid #e1e4e8;
            border-radius: 8px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.05);
            margin-bottom: 10px;
        }
        div[data-testid="stExpander"] p {
            color: #333333;
        }
        
        /* العناوين داخل التطبيق */
        h1, h2, h3 {
            color: #003057 !important;
            font-weight: 800 !important;
        }

        /* === 5. القائمة الجانبية (Sidebar) === */
        section[data-testid="stSidebar"] {
            background-color: #ffffff;
            border-left: 1px solid #e1e4e8;
        }
        
        /* === 6. الأزرار (Buttons) === */
        .stButton>button {
            background-color: #004d99; /* أزرق مؤسساتي */
            color: white;
            border: none;
            border-radius: 4px;
            height: 45px;
            font-weight: bold;
            transition: background 0.3s;
        }
        .stButton>button:hover {
            background-color: #003057;
        }

        /* تحسينات الموبايل */
        @media only screen and (max-width: 600px) {
            .news-header { flex-direction: column; text-align: center; }
            h1 { font-size: 1.5rem !important; }
        }
    </style>
    """, unsafe_allow_html=True)

inject_newsroom_css()

# ==========================================
# 2. الترسانة البرمجية (Logic)
# ==========================================

@st.cache_data(ttl=3600)
def get_header_html():
    """رأس الصفحة بتصميم القناة الإخبارية"""
    # يمكنك وضع رابط الشعار الخاص بك هنا مكان النص
    logo_area = """
    <div style="display: flex; align-items: center; gap: 15px;">
        <h2 style="color: white !important; margin: 0; letter-spacing: 1px;">يقين بريس</h2>
        <span style="background: rgba(255,255,255,0.2); padding: 2px 8px; font-size: 0.8rem; border-radius: 4px;">Live Coverage</span>
    </div>
    """
    
    return f"""
    <div class="news-header">
        {logo_area}
        <div style="font-size: 0.9rem; opacity: 0.9;">{time.strftime("%A, %d %B %Y")}</div>
    </div>
    """

@st.cache_data(ttl=900, show_spinner=False)
def scan_news_sector(category, sources):
    items = []
    def fetch(name, url):
        try:
            feed = feedparser.parse(url, agent=ua.random)
            if not feed.entries: return []
            return [{
                "title": e.title, "link": e.link, "source": name,
                "published": e.get('published', '')[:16] # تقصير التاريخ
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
        # محاكاة التحميل الاحترافي
        with st.status("جاري الاتصال بغرفة التحرير...", expanded=True) as status:
            status.write("📡 استقبال إشارة المصدر...")
            downloaded = trafilatura.fetch_url(link)
            if not downloaded: raise Exception("المصدر محمي أو غير متاح")
            
            status.write("📝 استخراج النص وتنقيحه...")
            raw = trafilatura.extract(downloaded)
            if not raw: raise Exception("النص فارغ")
            
            soup = BeautifulSoup(raw, "html.parser")
            clean_text = soup.get_text()[:4000]
            
            status.write("🧠 صياغة الخبر بأسلوب يقين بريس...")
            api_key = get_safe_key()
            if not api_key: raise Exception("مفتاح API مفقود")
            
            client = OpenAI(api_key=api_key, base_url="https://api.sambanova.ai/v1")
            response = client.chat.completions.create(
                model='Meta-Llama-3.3-70B-Instruct',
                messages=[
                    {"role": "system", "content": "أنت محرر صحفي أول في قناة إخبارية كبرى. اكتب الخبر بمهنية عالية، لغة عربية فصحى قوية، وموضوعية تامة."},
                    {"role": "user", "content": ELITE_PROMPT.format(keyword=keyword) + f"\n\nالنص:\n{clean_text}"}
                ],
                temperature=0.3
            )
            status.update(label="✅ تمت العملية بنجاح", state="complete", expanded=False)
            return response.choices[0].message.content, None
    except Exception as e:
        return None, str(e)

# ==========================================
# 3. واجهة المستخدم (The Interface)
# ==========================================

# --- تسجيل الدخول (بسيط وأنيق) ---
if st.session_state.page == 'login':
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br><h1 style='text-align: center; color: #003057 !important;'>بوابة التحرير</h1>", unsafe_allow_html=True)
        with st.form("login_frm"):
            pwd = st.text_input("كلمة المرور:", type="password")
            if st.form_submit_button("دخول", use_container_width=True):
                # استخدم st.secrets["APP_PASSWORD"] في الإنتاج
                if pwd == "Manager_Tech_2026": 
                    st.session_state.page = 'newsroom'
                    st.rerun()
                else:
                    st.error("بيانات الدخول غير صحيحة")

# --- غرفة الأخبار (Newsroom Dashboard) ---
elif st.session_state.page == 'newsroom':
    
    # 1. الشريط العلوي (الهيدر)
    st.markdown(get_header_html(), unsafe_allow_html=True)
    
    # 2. القائمة الجانبية (فلاتر الأخبار)
    with st.sidebar:
        st.markdown("### 🎛️ وحدة التحكم")
        selected_cat = st.radio("الأقسام:", list(RSS_DATABASE.keys()))
        st.markdown("---")
        keyword_input = st.text_input("SEO Keyword:", "يقين بريس")
        
        if st.button("تحديث المصادر 🔄"):
            st.cache_data.clear()
            st.rerun()
            
        if st.button("تسجيل خروج 🔒"):
            st.session_state.page = 'login'
            st.rerun()

    # 3. شريط الأخبار العاجلة (محاكاة)
    st.markdown(f"""
    <div class="breaking-news">
        <span class="breaking-label">عاجل</span>
        <span>جاري رصد آخر التطورات في قسم: {selected_cat} - تحديث مستمر على مدار الساعة</span>
    </div>
    """, unsafe_allow_html=True)

    # 4. عرض الأخبار
    col_main, col_details = st.columns([1.5, 1])
    
    with st.spinner("جاري جلب الأنباء من المصادر..."):
        news_list = scan_news_sector(selected_cat, RSS_DATABASE[selected_cat])

    if news_list:
        news_map = {f"{item['source']}: {item['title']}": item for item in news_list}
        
        # العمود الأيمن: القائمة والاختيار
        with col_main:
            st.subheader(f"📌 نشرة {selected_cat}")
            selected_news_key = st.selectbox("اختر خبراً للتحرير:", list(news_map.keys()), label_visibility="collapsed")
            target_news = news_map[selected_news_key]
            
            # بطاقة تفاصيل الخبر الأصلي
            st.info(f"""
            **المصدر:** {target_news['source']}
            \n**العنوان الأصلي:** {target_news['title']}
            \n**التوقيت:** {target_news['published']}
            \n[🔗 رابط المصدر الأصلي]({target_news['link']})
            """)
            
            if st.button("✨ بدء الصياغة الصحفية (AI)", use_container_width=True):
                content, error = smart_editor_ai(target_news['link'], keyword_input)
                if error:
                    st.error(error)
                else:
                    st.session_state['generated_article'] = content
        
        # العمود الأيسر: منطقة العمل والنتيجة
        with col_details:
            st.subheader("📝 المحرر الذكي")
            
            if 'generated_article' in st.session_state:
                raw_art = st.session_state['generated_article']
                lines = raw_art.split('\n')
                
                final_title = lines[0].replace('العنوان:', '').strip()
                final_body = '\n'.join(lines[1:])
                
                with st.container(border=True):
                    st.markdown("#### المسودة النهائية")
                    title_edit = st.text_input("العنوان:", value=final_title)
                    body_edit = st.text_area("المحتوى:", value=final_body, height=400)
                    
                    st.success("جاهز للنشر على المنصة")
            else:
                st.markdown("""
                <div style="text-align: center; padding: 50px; color: #888;">
                    يرجى اختيار خبر من القائمة لبدء المعالجة
                </div>
                """, unsafe_allow_html=True)

    else:
        st.warning("لا توجد أخبار جديدة في هذا القسم حالياً.")
