import streamlit as st
import feedparser
import trafilatura
import json
import os
import socket
import concurrent.futures
import base64  # مكتبة معالجة الصور
from openai import OpenAI
from duckduckgo_search import DDGS

# استيراد الترسانة من المكتبة
try:
    from manadger_lib import RSS_DATABASE, get_safe_key, ELITE_PROMPT
except ImportError:
    st.error("❌ خطأ: ملف manadger_lib.py مفقود.")
    st.stop()

# ==========================================
# 0. الإعدادات والجماليات (لم يتم المساس بها)
# ==========================================
ACCESS_PASSWORD = "Manager_Tech_2026"
DB_FILE = "news_db_v27.json"
socket.setdefaulttimeout(40)

st.set_page_config(page_title="الماندجر تك | منصة السيادة", page_icon="🛡️", layout="wide")

# دالة لتحويل الشعار إلى كود لدمجه في التصميم
def get_base64_logo():
    if os.path.exists("logo.png"):
        with open("logo.png", "rb") as f:
            data = f.read()
        encoded = base64.b64encode(data).decode()
        # تنسيق الشعار: عرض 180 بكسل وتوسطه
        return f'<img src="data:image/png;base64,{encoded}" style="width: 180px; margin-bottom: 20px; border-radius: 10px;">'
    return "" # إذا لم توجد الصورة لا يظهر شيء

logo_html = get_base64_logo()

# ==========================================
# ⚠️ منطقة التصميم (CSS) - نفس النسخة V28.1
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;700;900&display=swap');
    
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at 10% 20%, #020617 0%, #0f172a 90%);
    }
    
    html, body, p, div, span, label {
        font-family: 'Cairo', sans-serif !important;
        direction: rtl;
        text-align: right;
        color: #e2e8f0 !important;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Cairo', sans-serif !important;
        color: #ffffff !important;
        font-weight: 800 !important;
    }

    .hero-container {
        text-align: center;
        padding: 50px 20px;
        background: linear-gradient(180deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%);
        border-radius: 20px;
        border: 1px solid rgba(59, 130, 246, 0.2);
        box-shadow: 0 0 30px rgba(59, 130, 246, 0.1);
        margin-bottom: 40px;
    }
    
    .hero-title {
        font-size: 4rem !important;
        background: linear-gradient(to right, #60a5fa, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent !important;
        color: #3b82f6 !important;
        text-shadow: 0px 0px 30px rgba(37, 99, 235, 0.3);
        margin-bottom: 10px;
    }

    .stTextInput input, .stSelectbox div[data-baseweb="select"] div {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 1px solid #475569 !important;
        border-radius: 10px !important;
    }
    
    div[data-baseweb="popover"] li {
        background-color: #0f172a !important;
        color: white !important;
    }

    .article-output {
        background-color: #ffffff !important;
        padding: 40px;
        border-radius: 12px;
        border-right: 8px solid #2563eb;
        line-height: 2.4;
        font-size: 1.3rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.5);
        margin-top: 30px;
    }
    
    .article-output, .article-output p, .article-output div {
        color: #1e293b !important; 
        text-align: justify;
    }

    .stButton>button {
        background: linear-gradient(90deg, #2563eb, #1d4ed8) !important;
        color: white !important;
        border: none;
        padding: 0.8rem 2rem;
        font-size: 1.2rem !important;
        border-radius: 12px;
        width: 100%;
        height: 4rem;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3);
    }
    
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 10px 25px rgba(37, 99, 235, 0.6);
    }

    .stTabs [data-baseweb="tab-list"] {
        background-color: rgba(30, 41, 59, 0.5);
        padding: 10px;
        border-radius: 15px;
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #94a3b8 !important;
        font-weight: bold;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2563eb !important;
        color: white !important;
        border-radius: 8px;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. محرك البحث عن الصور (نظام Yoast SEO)
# ==========================================
def get_yoast_seo_images(keyword, headline):
    if keyword and len(keyword) > 2 and "هاشمي" not in keyword:
        query = keyword
    else:
        query = " ".join(headline.split()[:5])
        
    try:
        with DDGS() as ddgs:
            results = ddgs.images(
                query, 
                region="wt-wt",
                safesearch="off", 
                max_results=3,
                type_image="photo"
            )
            return [r['image'] for r in results]
    except: return []

# ==========================================
# 2. محرك الصياغة النخبوية (لم يتم المساس به)
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
                {"role": "system", "content": "محرر صحفي نخبوي - الماندجر تك"},
                {"role": "user", "content": formatted_prompt}
            ],
            temperature=0.4
        )
        
        raw_article = response.choices[0].message.content
        
        clean_article = raw_article.replace("هاشمي بريس:", "").replace("هاشمي بريس :", "").replace("العنوان:", "").strip()
        return clean_article

    except Exception as e: return f"❌ خطأ: {str(e)}"

# ==========================================
# 3. واجهة الدخول (Hero Login) - مع الشعار
# ==========================================
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    # تصميم صفحة الهبوط
    st.markdown(f"""
        <div class="hero-container">
            {logo_html}
            <h1 class="hero-title">MANAGER TECH</h1>
            <h3 style="color: #e2e8f0;">نظام السيادة المعلوماتية | V28.3</h3>
            <p style="color: #94a3b8; font-size: 1.1rem;">رادار بـ 200 مصدر • 26 محرك ذكاء اصطناعي • صياغة نخبوية</p>
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
# 4. واجهة النظام الداخلية (Dashboard) - مع الشعار المصغر
# ==========================================

# الهيدر الداخلي
st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; background: rgba(255,255,255,0.05); padding: 15px; border-radius: 12px;">
        <div style="display: flex; align-items: center; gap: 15px;">
            {logo_html.replace('180px', '50px').replace('margin-bottom: 20px;', 'margin-bottom: 0;')}
            <h2 style="color: #60a5fa; margin: 0;">رادار الماندجر تك</h2>
        </div>
        <span style="background: #2563eb; color: white; padding: 5px 15px; border-radius: 20px; font-size: 0.9rem; font-weight: bold;">ONLINE</span>
    </div>
""", unsafe_allow_html=True)

# تحميل قاعدة البيانات
if os.path.exists(DB_FILE):
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f: db = json.load(f)
    except: db = {"data": {}}
else: db = {"data": {}}

# ==========================================
# 5. التبويبات والتشغيل
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
            
            selected_idx = st.selectbox(
                "حدد الهدف للمعالجة:", 
                range(len(news_list)), 
                format_func=lambda x: f"[{news_list[x]['source']}] {news_list[x]['title']}",
                key=f"sel_{i}"
            )
            
            keyword_input = st.text_input("الكلمة المفتاحية (SEO Strategy):", key=f"kw_{i}", placeholder="اتركها فارغة للتلقائي...")

            if st.button("🚀 هندسة المقال بأسلوب هاشمي بريس", key=f"run_{i}"):
                final_keyword = keyword_input.strip() if keyword_input.strip() != "" else "هاشمي بريس"
                
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
                        
                        st.markdown("<br><h3>🖼️ وسائط متوافقة مع Yoast SEO</h3>", unsafe_allow_html=True)
                        images = get_yoast_seo_images(final_keyword, headline)
                        
                        if images:
                            cols = st.columns(len(images))
                            for idx, img_url in enumerate(images):
                                with cols[idx]:
                                    st.image(img_url, use_container_width=True)
                                    st.caption(f"📝 Alt Text: {final_keyword}")
                        else:
                            st.warning("لم يتم العثور على صور دقيقة.")
                        
                        st.text_area("نسخة النشر (Raw Text):", article, height=300)
                    else: st.error("فشل الرادار في سحب النص من المصدر.")
        else:
            st.info("الرادار خامل. اضغط زر التحديث لتشغيل المجسات.")

# التذييل
st.markdown(f"""
    <div style='text-align: center; color: #475569; margin-top: 50px; border-top: 1px solid #1e293b; padding-top: 20px;'>
        {logo_html.replace('180px', '40px').replace('margin-bottom: 20px;', 'margin-bottom: 10px;')}
        <br>Developed by Manadger Tech © 2026
    </div>
""", unsafe_allow_html=True)
