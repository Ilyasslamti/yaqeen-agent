import streamlit as st
import feedparser
import trafilatura
import json
import os
import socket
import concurrent.futures
import base64
import urllib.parse
from openai import OpenAI
# تم إزالة مكتبة البحث عن الصور لأننا لم نعد نحتاجها
# from duckduckgo_search import DDGS 

# استيراد الترسانة
try:
    from manadger_lib import RSS_DATABASE, get_safe_key, ELITE_PROMPT
except ImportError:
    st.error("❌ خطأ: ملف manadger_lib.py مفقود.")
    st.stop()

# ==========================================
# 0. الإعدادات
# ==========================================
ACCESS_PASSWORD = "Manager_Tech_2026"
DB_FILE = "news_db_v27.json"
socket.setdefaulttimeout(40)

st.set_page_config(page_title="منادجر تك | منصة السيادة", page_icon="🛡️", layout="wide")

# دالة الشعار
def get_base64_logo():
    if os.path.exists("logo.png"):
        with open("logo.png", "rb") as f:
            data = f.read()
        encoded = base64.b64encode(data).decode()
        return f'<img src="data:image/png;base64,{encoded}" class="responsive-logo">'
    return ""

logo_html = get_base64_logo()

# ==========================================
# ⚠️ منطقة التصميم (CSS) - نفس النسخة V34.1
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;700;900&display=swap');
    
    /* 1. إعدادات عامة */
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at 10% 20%, #020617 0%, #0f172a 90%);
    }
    html, body, p, div, span, label {
        font-family: 'Cairo', sans-serif !important;
        direction: rtl;
        text-align: right;
        color: #e2e8f0 !important;
    }
    
    /* ============================================================
       🖥️ تنسيق الحاسوب (Desktop)
       ============================================================ */
    
    /* الشعار */
    .responsive-logo {
        width: 220px;
        margin-bottom: 20px;
        border-radius: 15px;
        display: block;
        margin-left: auto;
        margin-right: auto;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }

    /* حاوية الهيرو - التوسيط الإجباري */
    .hero-container {
        padding: 80px 40px;
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.4) 0%, rgba(15, 23, 42, 0.6) 100%);
        border-radius: 30px;
        border: 1px solid rgba(59, 130, 246, 0.1);
        box-shadow: 0 20px 60px rgba(0,0,0,0.4);
        margin-bottom: 50px;
        max-width: 900px;
        margin-left: auto !important;
        margin-right: auto !important;
        
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
    }
    
    /* إجبار النصوص داخل الهيرو على التوسط */
    .hero-container h1, 
    .hero-container h3, 
    .hero-container p,
    .hero-container div {
        text-align: center !important;
        width: 100% !important;
        margin-left: auto !important;
        margin-right: auto !important;
        display: block !important;
    }
    
    /* عنوان الهيرو */
    .hero-title {
        font-size: 5rem !important;
        font-weight: 900 !important;
        background: linear-gradient(to right, #60a5fa, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent !important;
        margin-bottom: 10px !important;
        letter-spacing: -2px;
    }
    
    /* ورقة المقال */
    .article-output {
        background-color: #ffffff !important;
        padding: 60px;
        border-radius: 20px;
        border-right: 10px solid #2563eb;
        line-height: 2.6;
        font-size: 1.4rem;
        box-shadow: 0 20px 50px rgba(0,0,0,0.5);
        margin-top: 40px;
        max-width: 900px;
        margin-left: auto;
        margin-right: auto;
    }
    
    /* الأزرار */
    .stButton>button {
        height: 4.5rem;
        font-size: 1.3rem !important;
        border-radius: 15px;
        background: linear-gradient(90deg, #2563eb, #1d4ed8) !important;
        color: white !important;
        border: none;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .stButton>button:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 30px rgba(37, 99, 235, 0.4);
    }

    /* ============================================================
       📱 تنسيق الجوال (Mobile)
       ============================================================ */
    @media only screen and (max-width: 768px) {
        
        .responsive-logo {
            width: 140px;
            margin-bottom: 15px;
        }

        .hero-container {
            padding: 40px 15px;
            margin-bottom: 20px;
            width: 100% !important;
            border-radius: 15px;
            background: rgba(30, 41, 59, 0.8);
        }
        
        .hero-title {
            font-size: 2.5rem !important;
            margin-bottom: 10px !important;
            line-height: 1.2;
        }
        
        .hero-container h3 { 
            font-size: 1.1rem !important; 
            margin-bottom: 5px !important;
        }
        .hero-container p { 
            font-size: 0.9rem !important; 
            line-height: 1.6 !important;
        }

        .article-output {
            padding: 25px 15px !important;
            font-size: 1.1rem !important;
            border-radius: 10px;
            border-right: 5px solid #2563eb;
            line-height: 1.8 !important;
            width: 100% !important;
        }

        .stButton>button {
            height: 3.5rem !important;
            font-size: 1rem !important;
            margin-bottom: 10px;
        }
        
        .block-container {
            padding-top: 1rem !important;
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }
    }

    /* إصلاح المدخلات */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] div {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 1px solid #475569 !important;
        border-radius: 10px !important;
    }
    .article-output, .article-output p, .article-output div {
        color: #1e293b !important; 
        text-align: justify;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. محرك الصياغة
# ==========================================
def run_samba_writer(text, keyword):
    api_key = get_safe_key()
    if not api_key: return "⚠️ خطأ في المفاتيح."

    try:
        client = OpenAI(api_key=api_key, base_url="https://api.sambanova.ai/v1")
        formatted_prompt = ELITE_PROMPT.format(keyword=keyword) + f"\n\n{text[:4500]}"
        
        response = client.chat.completions.create(
            model='Meta-Llama-3.3-70B-Instruct', 
            messages=[
                {"role": "system", "content": "محرر صحفي نخبوي - منادجر تك"},
                {"role": "user", "content": formatted_prompt}
            ],
            temperature=0.4
        )
        
        raw_article = response.choices[0].message.content
        clean_article = raw_article.replace(":", "").replace(" :", "").replace("العنوان:", "").strip()
        return clean_article

    except Exception as e: return f"❌ خطأ: {str(e)}"

# ==========================================
# 3. واجهة الدخول (Hero Login)
# ==========================================
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown(f"""
        <div class="hero-container">
            {logo_html}
            <h1 class="hero-title">MANADGER TECH</h1>
            <h3 style="color: #e2e8f0; margin-bottom: 10px;">نظام السيادة المعلوماتية | V35.0</h3>
            <p style="color: #94a3b8; font-size: 1.1rem; line-height: 1.6;">رادار بـ 200 مصدر • 26 محرك ذكاء اصطناعي • صياغة نخبوية</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            st.markdown("<h3 style='text-align: center; color: #60a5fa;'>🔐 تسجيل الدخول</h3>", unsafe_allow_html=True)
            pwd = st.text_input("مفتاح الترسانة:", type="password")
            submitted = st.form_submit_button("اقتحام النظام 🚀")
            if submitted:
                if pwd == ACCESS_PASSWORD:
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error("⛔ مفتاح الوصول غير صحيح.")
    st.stop()

# ==========================================
# 4. واجهة النظام الداخلية
# ==========================================
st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; background: rgba(255,255,255,0.05); padding: 15px; border-radius: 12px;">
        <div style="display: flex; align-items: center; gap: 15px;">
            {logo_html.replace('class="responsive-logo"', 'style="width: 50px; border-radius: 8px;"')}
            <h2 style="color: #60a5fa; margin: 0; font-size: 1.5rem;">رادار الماندجر</h2>
        </div>
        <span style="background: #2563eb; color: white; padding: 5px 15px; border-radius: 20px; font-size: 0.9rem; font-weight: bold;">ONLINE</span>
    </div>
""", unsafe_allow_html=True)

if os.path.exists(DB_FILE):
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f: db = json.load(f)
    except: db = {"data": {}}
else: db = {"data": {}}

# ==========================================
# 5. التشغيل
# ==========================================
tabs = st.tabs([f"📡 {k}" for k in RSS_DATABASE.keys()])

for i, cat in enumerate(list(RSS_DATABASE.keys())):
    with tabs[i]:
        col_act1, col_act2 = st.columns([3, 1])
        with col_act2:
            if st.button(f"🔄 تحديث الرادار", key=f"up_{i}"):
                with st.spinner(f"جاري مسح {cat} بتقنية التوازي..."):
                    all_news = []
                    def fetch_task(name, url):
                        try:
                            feed = feedparser.parse(url)
                            return [{"title": e.title, "link": e.link, "source": name} for e in feed.entries[:10]]
                        except: return []
                    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
                        futures = [executor.submit(fetch_task, n, u) for n, u in RSS_DATABASE[cat].items()]
                        for f in concurrent.futures.as_completed(futures): all_news.extend(f.result())
                    db["data"][cat] = all_news
                    with open(DB_FILE, 'w', encoding='utf-8') as f: json.dump(db, f, ensure_ascii=False)
                st.rerun()

        if cat in db["data"] and db["data"][cat]:
            news_list = db["data"][cat]
            st.markdown(f"<h4 style='color: #cbd5e1;'>📑 تم رصد {len(news_list)} خبراً في هذا القطاع</h4>", unsafe_allow_html=True)
            
            selected_idx = st.selectbox("حدد الهدف:", range(len(news_list)), format_func=lambda x: f"[{news_list[x]['source']}] {news_list[x]['title']}", key=f"sel_{i}")
            keyword_input = st.text_input("الكلمة المفتاحية (SEO):", key=f"kw_{i}", placeholder="اتركها فارغة للتلقائي...")

            if st.button("🚀 هندسة المقال بأسلوب صجفي احترافي", key=f"run_{i}"):
                final_keyword = keyword_input.strip() if keyword_input.strip() != "" else ""
                
                with st.spinner("الماندجر يحلل البيانات ويصيغ التحفة..."):
                    raw_data = trafilatura.fetch_url(news_list[selected_idx]['link'])
                    main_text = trafilatura.extract(raw_data)
                    
                    if main_text:
                        article = run_samba_writer(main_text, final_keyword)
                        
                        lines = article.split('\n')
                        headline = lines[0]
                        body = "\n".join(lines[1:])
                        
                        st.markdown("---")
                        st.markdown(f"<h1 style='color: #3b82f6; text-align: center; margin-bottom: 20px; text-shadow: 0 0 10px rgba(59,130,246,0.5);'>{headline}</h1>", unsafe_allow_html=True)
                        st.markdown(f"<div class='article-output'>{body}</div>", unsafe_allow_html=True)
                        
                        # --- مركز عمليات النشر ---
                        st.markdown("---")
                        st.markdown("### 📤 مركز التوزيع الرقمي")
                        
                        ac1, ac2, ac3 = st.columns(3)
                        with ac1:
                            html_content = f"<h2>{headline}</h2>\n{body.replace(chr(10), '<br>')}"
                            st.markdown("##### 📝 ووردبريس")
                            st.code(html_content, language='html')
                        with ac2:
                            social_text = f"🔴 {headline}\n\n{body[:500]}...\n\n🔗 لقراءة المزيد: [رابط الموقع]\n#{final_keyword.replace(' ', '_')} #هاشمي_بريس"
                            st.markdown("##### 📘 فيسبوك")
                            st.code(social_text, language='text')
                        with ac3:
                            whatsapp_msg = urllib.parse.quote(f"🔴 *{headline}*\n\n{body[:200]}...\n\nتابع التفاصيل: [الرابط]")
                            st.markdown("##### 💬 واتساب")
                            st.link_button("إرسال عبر WhatsApp 🚀", f"https://wa.me/?text={whatsapp_msg}")

                    else: st.error("فشل الرادار في سحب النص.")
        else:
            st.info("الرادار خامل. اضغط زر التحديث.")

st.markdown(f"""
    <div style='text-align: center; color: #475569; margin-top: 50px; border-top: 1px solid #1e293b; padding-top: 20px;'>
        {logo_html.replace('class="responsive-logo"', 'style="width: 40px; margin-bottom: 5px; border-radius: 5px;"')}
        <br>Developed by Manadger Tech © 2026
    </div>
""", unsafe_allow_html=True)
