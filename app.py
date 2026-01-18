import streamlit as st
import feedparser
import trafilatura
import json
import os
import socket
import concurrent.futures
import base64
from openai import OpenAI
from duckduckgo_search import DDGS

# ==========================================
# 0. استيراد الترسانة (المكتبة الخاصة)
# ==========================================
try:
    from manadger_lib import RSS_DATABASE, get_safe_key, ELITE_PROMPT
except ImportError:
    st.error("❌ خطأ حرج: ملف manadger_lib.py مفقود. تأكد من وجوده بجانب ملف app.py")
    st.stop()

# ==========================================
# 1. إعدادات الصفحة الأساسية
# ==========================================
ACCESS_PASSWORD = "Manager_Tech_2026"
DB_FILE = "news_db_v27.json"
socket.setdefaulttimeout(40)

st.set_page_config(
    page_title="منادجر تك | منصة السيادة", 
    page_icon="🛡️", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --------------------------------------------------
# دالة الشعار
# --------------------------------------------------
def get_base64_logo():
    if os.path.exists("logo.png"):
        with open("logo.png", "rb") as f:
            data = f.read()
        encoded = base64.b64encode(data).decode()
        return f'<img src="data:image/png;base64,{encoded}" style="width: 150px; max-width: 100%; display: block; margin: 0 auto 15px auto; border-radius: 10px;">'
    return ""

logo_html = get_base64_logo()

# ==========================================
# 2. منطقة التصميم (CSS) - إصلاح العنوان الجذري
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;700;900&display=swap');
    
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at 10% 20%, #020617 0%, #0f172a 90%);
    }
    
    html, body, p, div, span, label, button, input, textarea {
        font-family: 'Cairo', sans-serif !important;
        direction: rtl;
        text-align: right;
    }
    
    p, div, span, label { color: #e2e8f0; }

    /* === إصلاح العنوان الجذري (The Fix) === */
    /* نلغي استخدام h1 للمقال ونستبدله بكلاس خاص */
    .custom-header {
        background-color: #ffffff !important; /* خلفية بيضاء صلبة */
        color: #1e3a8a !important;            /* لون أزرق غامق */
        padding: 20px !important;
        border-bottom: 4px solid #2563eb !important;
        margin-bottom: 30px !important;
        font-size: 2rem !important;
        font-weight: 900 !important;
        text-align: center !important;
        display: block !important;
        width: 100% !important;
        border-radius: 10px 10px 0 0;
        line-height: 1.4 !important;
        /* الخصائص التالية تمنع التداخل */
        position: relative !important;
        z-index: 999 !important;
        opacity: 1 !important;
    }

    /* === حاوية الهيرو === */
    .hero-container {
        display: flex !important; flex-direction: column !important; align-items: center !important;
        justify-content: center !important; text-align: center !important;
        padding: 40px 20px;
        background: linear-gradient(180deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%);
        border-radius: 20px; border: 1px solid rgba(59, 130, 246, 0.2);
        box-shadow: 0 0 30px rgba(59, 130, 246, 0.1);
        margin-bottom: 30px; width: 100% !important; max-width: 800px;
        margin-left: auto; margin-right: auto;
    }
    
    .hero-title {
        text-align: center !important; font-size: 3.5rem !important;
        background: linear-gradient(to right, #60a5fa, #3b82f6);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent !important;
        color: #3b82f6 !important; margin-bottom: 10px; line-height: 1.2 !important;
        width: 100%; display: block;
    }

    /* === صندوق المقال === */
    .article-output {
        background-color: #ffffff !important;
        padding: 0 !important; /* إزالة الحشو ليملأ العنوان العرض */
        border-radius: 12px;
        border: 1px solid #ddd;
        border-right: 8px solid #2563eb;
        box-shadow: 0 10px 40px rgba(0,0,0,0.5);
        margin-top: 30px;
        direction: rtl;
        overflow: hidden; /* لضمان عدم خروج العنوان */
    }
    
    .article-body {
        padding: 30px 40px; /* حشو للنص فقط */
        line-height: 2.4;
        font-size: 1.2rem;
        color: #1e293b !important;
        text-align: justify;
    }
    
    .article-body p, .article-body div { color: #1e293b !important; }

    /* === الأزرار والمدخلات === */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] div {
        background-color: #1e293b !important; color: #ffffff !important;
        border: 1px solid #475569 !important; border-radius: 10px !important; direction: rtl;
    }
    
    .stButton>button {
        background: linear-gradient(90deg, #2563eb, #1d4ed8) !important; color: white !important;
        border: none; padding: 0.8rem 2rem; font-size: 1.2rem !important;
        border-radius: 12px; width: 100%; height: 4rem; font-family: 'Cairo', sans-serif !important; font-weight: bold;
    }

    /* === الجوال === */
    @media only screen and (max-width: 600px) {
        .hero-title { font-size: 2.5rem !important; }
        .custom-header { font-size: 1.5rem !important; padding: 15px !important; }
        .article-body { padding: 20px !important; font-size: 1rem !important; line-height: 1.8 !important; }
        img { max-width: 100% !important; height: auto !important; margin: 0 auto !important; display: block !important; }
    }

    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}

</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. محرك الصور
# ==========================================
def get_yoast_seo_images(keyword, headline):
    if keyword and len(keyword) > 2 and "هاشمي" not in keyword:
        query = keyword
    else:
        query = " ".join(headline.split()[:5])
        
    try:
        with DDGS() as ddgs:
            results = ddgs.images(query, region="wt-wt", safesearch="off", max_results=3, type_image="photo")
            return [r['image'] for r in results]
    except: return []

# ==========================================
# 4. محرك الصياغة
# ==========================================
def run_samba_writer(text, keyword):
    api_key = get_safe_key()
    if not api_key: return "⚠️ خطأ حرج: لم يتم العثور على مفاتيح API."

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
        clean_article = raw_article.replace("هاشمي بريس:", "").replace("هاشمي بريس :", "").replace("العنوان:", "").strip()
        return clean_article

    except Exception as e: return f"❌ خطأ أثناء المعالجة: {str(e)}"

# ==========================================
# 5. واجهة الدخول
# ==========================================
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown(f"""
        <div class="hero-container">
            {logo_html}
            <h1 class="hero-title">MANAGER TECH</h1>
            <h3 style="color: #e2e8f0;">نظام السيادة المعلوماتية | V35.0 Fixed</h3>
            <p style="color: #94a3b8; font-size: 1.1rem;">محرك بـ 200 مصدر • نظام تحرير صارم • CSS مصحح</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            st.markdown("<h3 style='text-align: center; color: #60a5fa;'>🔐 بوابة الوصول</h3>", unsafe_allow_html=True)
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
# 6. واجهة النظام الداخلية
# ==========================================
mini_logo = logo_html.replace('150px', '50px').replace('display: block;', 'display: inline-block;').replace('margin: 0 auto 15px auto;', 'margin: 0;')

st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; background: rgba(255,255,255,0.05); padding: 15px; border-radius: 12px;">
        <div style="display: flex; align-items: center; gap: 15px;">
            {mini_logo}
            <h2 style="color: #60a5fa; margin: 0;">رادار منادجر تك</h2>
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
# 7. التبويبات والتشغيل
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
            
            selected_idx = st.selectbox("حدد الهدف للمعالجة:", range(len(news_list)), format_func=lambda x: f"[{news_list[x]['source']}] {news_list[x]['title']}", key=f"sel_{i}")
            keyword_input = st.text_input("الكلمة المفتاحية (SEO Strategy):", key=f"kw_{i}", placeholder="اتركها فارغة للتلقائي...")

            if st.button("🚀 هندسة المقال بأسلوب صحفي شامل", key=f"run_{i}"):
                final_keyword = keyword_input.strip() if keyword_input.strip() != "" else "منادجر تك"
                
                with st.spinner("منادجر يحلل البيانات ويصيغ التحفة..."):
                    try:
                        raw_data = trafilatura.fetch_url(news_list[selected_idx]['link'])
                        main_text = trafilatura.extract(raw_data)
                    except: main_text = None
                    
                    if main_text:
                        article = run_samba_writer(main_text, final_keyword)
                        lines = article.split('\n')
                        headline = lines[0]
                        body = "\n".join(lines[1:])
                        
                        st.markdown("---")
                        
                        # هنا التصحيح: استخدام div بدل h1 لضمان عدم ظهور العنوان في الخلفية
                        st.markdown(f"""
                        <div class='article-output'>
                            <div class='custom-header'>{headline}</div>
                            <div class='article-body'>{body}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown("<br><h3>🖼️ وسائط متوافقة مع Yoast SEO</h3>", unsafe_allow_html=True)
                        images = get_yoast_seo_images(final_keyword, headline)
                        
                        if images:
                            cols = st.columns(len(images))
                            for idx, img_url in enumerate(images):
                                with cols[idx]:
                                    st.image(img_url, use_container_width=True)
                                    st.caption(f"📝 Alt Text: {final_keyword}")
                        else: st.warning("لم يتم العثور على صور دقيقة.")
                        
                        st.text_area("نسخة النشر (Raw Text):", article, height=300)
                    else: st.error("فشل الرادار في سحب النص.")
        else: st.info("الرادار خامل. اضغط زر التحديث.")

st.markdown(f"""
    <div style='text-align: center; color: #475569; margin-top: 50px; border-top: 1px solid #1e293b; padding-top: 20px;'>
        {mini_logo.replace('50px', '30px')}
        <br>Developed by Manadger Tech © 2026
    </div>
""", unsafe_allow_html=True)
