# ==========================================
# manadger_lib.py - مستودع أسلحة الماندجر تك
# الإصدار السيادي V27.9 - ترسانة الـ 200
# ==========================================

import random
import streamlit as st

# 1. نظام تدوير المفاتيح الـ 26
def get_safe_key():
    try:
        keys = st.secrets["API_KEYS"]
        return random.choice(keys)
    except:
        return None

# 2. برومبت السيادة اللغوية
ELITE_PROMPT = """ELITE_PROMPT = r"""import streamlit as st
import feedparser
import trafilatura
import json
import os
import socket
import concurrent.futures
import base64
from openai import OpenAI
from duckduckgo_search import DDGS

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

# دالة الشعار (تعديل: إضافة كود التمركز الصارم HTML)
def get_base64_logo():
    if os.path.exists("logo.png"):
        with open("logo.png", "rb") as f:
            data = f.read()
        encoded = base64.b64encode(data).decode()
        # التغيير هنا: display: block و margin: 0 auto يجبران الصورة على التوسط
        return f'<img src="data:image/png;base64,{encoded}" style="width: 150px; max-width: 100%; display: block; margin: 0 auto 15px auto; border-radius: 10px;">'
    return ""

logo_html = get_base64_logo()

# ==========================================
# ⚠️ منطقة التصميم (CSS) - إصلاح التجاوب الجذري
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

    /* === حاوية الهيرو: فرض الترتيب العمودي والتوسط === */
    .hero-container {
        display: flex !important;
        flex-direction: column !important; /* العناصر فوق بعضها */
        align-items: center !important;     /* توسيط أفقي */
        justify-content: center !important; /* توسيط عمودي */
        text-align: center !important;      /* توسيط النصوص */
        
        padding: 40px 20px;
        background: linear-gradient(180deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%);
        border-radius: 20px;
        border: 1px solid rgba(59, 130, 246, 0.2);
        box-shadow: 0 0 30px rgba(59, 130, 246, 0.1);
        margin-bottom: 30px;
        width: 100% !important;
        max-width: 800px;
        margin-left: auto;
        margin-right: auto;
    }
    
    .hero-title {
        text-align: center !important;
        font-size: 3.5rem !important; /* حجم للكمبيوتر */
        background: linear-gradient(to right, #60a5fa, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent !important;
        color: #3b82f6 !important;
        text-shadow: 0px 0px 30px rgba(37, 99, 235, 0.3);
        margin-bottom: 10px;
        line-height: 1.2 !important;
        width: 100%;
    }
    
    .hero-container h3, .hero-container p {
        text-align: center !important;
        width: 100%;
        margin-left: auto !important;
        margin-right: auto !important;
    }

    /* === التنسيقات العامة الأخرى === */
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
        justify-content: center; /* توسيط التبويبات */
        flex-wrap: wrap;
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

    /* ============================================================
       📱 قواعد الجوال الصارمة (Mobile Strict Rules)
       ============================================================ */
    @media only screen and (max-width: 600px) {
        
        /* 1. إجبار حاوية الهيرو على الاحتواء الكامل */
        .hero-container {
            padding: 20px 10px !important;
            margin: 0 auto 20px auto !important;
            width: 95% !important;
        }
        
        /* 2. تصغير العنوان ليتناسب مع عرض الهاتف */
        .hero-title {
            font-size: 8vw !important; /* حجم نسبي للعرض */
            margin-bottom: 10px !important;
        }
        
        /* 3. النصوص الفرعية */
        .hero-container h3 { font-size: 1.1rem !important; }
        .hero-container p { font-size: 0.8rem !important; }

        /* 4. تنسيق المقال للقراءة على الهاتف */
        .article-output {
            padding: 15px !important;
            font-size: 1rem !important;
            border-right: 3px solid #2563eb !important;
            line-height: 1.6 !important;
        }

        /* 5. الأزرار */
        .stButton>button {
            height: 3.5rem !important;
            font-size: 1rem !important;
        }

        /* 6. منع الصور من الخروج عن الشاشة */
        img { 
            max-width: 100% !important; 
            height: auto !important; 
            margin: 0 auto !important; /* توسيط الصور */
            display: block !important;
        }
        
        /* 7. تقليل هوامش الصفحة العامة */
        .block-container {
            padding-top: 2rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. محرك الصور (Yoast SEO)
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
        clean_article = raw_article.replace("هاشمي بريس:", "").replace("هاشمي بريس :", "").replace("العنوان:", "").strip()
        return clean_article

    except Exception as e: return f"❌ خطأ: {str(e)}"

# ==========================================
# 3. واجهة الدخول
# ==========================================
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    # نستخدم f-string لدمج الشعار (logo_html) داخل واجهة الهيرو
    st.markdown(f"""
        <div class="hero-container">
            {logo_html}
            <h1 class="hero-title">MANAGER TECH</h1>
            <h3 style="color: #e2e8f0;">نظام السيادة المعلوماتية | V28.7</h3>
            <p style="color: #94a3b8; font-size: 1.1rem;">محرك بـ 200 مصدر • 26 محرك ذكاء اصطناعي • متوافق مع السيو</p>
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
# 4. واجهة النظام الداخلية
# ==========================================
# نستخدم replace لتصغير الشعار في الهيدر الداخلي
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
            
            selected_idx = st.selectbox(
                "حدد الهدف للمعالجة:", 
                range(len(news_list)), 
                format_func=lambda x: f"[{news_list[x]['source']}] {news_list[x]['title']}",
                key=f"sel_{i}"
            )
            
            keyword_input = st.text_input("الكلمة المفتاحية (SEO Strategy):", key=f"kw_{i}", placeholder="اتركها فارغة للتلقائي...")

            if st.button("🚀 هندسة المقال بأسلوب صحفي شامل", key=f"run_{i}"):
                final_keyword = keyword_input.strip() if keyword_input.strip() != "" else "منادجر تك"
                
                with st.spinner("منادجر يحلل البيانات ويصيغ التحفة..."):
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

st.markdown(f"""
    <div style='text-align: center; color: #475569; margin-top: 50px; border-top: 1px solid #1e293b; padding-top: 20px;'>
        {mini_logo.replace('50px', '30px')}
        <br>Developed by Manadger Tech © 2026
    </div>
""", unsafe_allow_html=True)

الكلمة المفتاحية: {keyword}
المحتوى المراد معالجته:
"""

# 3. ترسانة الـ 200 مصدر (شاملة ومفحوصة)
RSS_DATABASE = {
    "الصحافة السيادية والوطنية (60 مصدر)": {
        "هاشمي بريس": "https://hashemipress.com/feed/",
        "هسبريس": "https://www.hespress.com/feed",
        "MAP وكالة الأنباء": "https://www.mapnews.ma/ar/rss.xml",
        "لوسيت أنفو": "https://ar.lesiteinfo.com/feed",
        "زنقة 20": "https://www.rue20.com/feed",
        "هبة بريس": "https://ar.hibapress.com/feed",
        "كود": "https://www.goud.ma/feed",
        "اليوم 24": "https://alyaoum24.com/feed",
        "العمق المغربي": "https://al3omk.com/feed",
        "مدار 21": "https://madar21.com/feed",
        "برلمان.كوم": "https://www.barlamane.com/feed",
        "تليكسبريس": "https://telexpresse.com/feed",
        "آشكاين": "https://achkayen.com/feed",
        "فبراير": "https://www.febrayer.com/feed",
        "الجريدة 24": "https://aljarida24.ma/feed",
        "لكم 2": "https://lakome2.com/feed",
        "سفيركم": "https://safir24.com/feed",
        "بناصا": "https://banassa.com/feed",
        "منارة": "https://www.menara.ma/ar/rss",
        "الصحراء المغربية": "https://assahra.ma/rss",
        "بيان اليوم": "https://bayanealyaoume.press.ma/feed",
        "الاتحاد الاشتراكي": "https://alittihad.press.ma/feed",
        "رسالة الأمة": "https://الرسالة.ma/feed",
        "بلادنا 24": "https://www.beladna24.ma/feed",
        "آذار": "https://aaddar.com/feed",
        "مشاهد": "https://mashahed.info/feed",
        "دوزيم 2M": "https://2m.ma/ar/news/rss.xml",
        "ميد رادي": "https://medradio.ma/feed",
        "لوديسك": "https://ledesk.ma/ar/feed",
        "عبر": "https://aabbir.com/feed",
        "صوت المغرب": "https://saoutalmaghrib.ma/feed",
        "مغرب أنباء": "https://maghrebanbaa.ma/feed",
        "كاب 24": "https://cap24.tv/feed",
        "الأيام 24": "https://www.alayam24.com/feed",
        "نون بريس": "https://www.noonpresse.com/feed",
        "سياسي": "https://www.siyasi.com/feed",
        "الأسبوع الصحفي": "https://alaousboue.ma/feed",
        "أنفاس بريس": "https://anfasspress.com/feed",
        "فلاش بريس": "https://www.flashpresse.ma/feed",
        "آخر خبر": "https://akharkhabar.ma/feed",
        "ماب تيفي": "https://maptv.ma/feed",
        "الجريدة العربية": "https://aljaridaalarabia.ma/feed",
        "حقائق 24": "https://hakaek24.com/feed",
        "المغرب 24": "https://almaghrib24.com/feed",
        "الأنباء": "https://anbaa.ma/feed",
        "الأخبار": "https://alakhbar.press.ma/feed",
        "لاراكس": "https://larax.ma/feed",
        "المجلة": "https://almajalla.com/feed",
        "كازاوي": "https://casaoui.ma/feed",
        "بديل": "https://badil.info/feed",
        "أغورا": "https://agora.ma/feed",
        "المصدر": "https://almasdar.ma/feed",
        "الأول": "https://alaoual.com/feed",
        "مراكش بوست": "https://marrakechpost.com/feed",
        "طنجة الأدبية": "https://aladabia.net/feed",
        "هسبريس سياسة": "https://www.hespress.com/politique/feed",
        "هسبريس مجتمع": "https://www.hespress.com/societe/feed",
        "الحدث 24": "https://alhadath24.ma/feed",
        "مغرب تايمز": "https://maghrebtimes.ma/feed"
    },
    "رادار الشمال والريف (50 مصدر)": {
        "بريس تطوان": "https://presstetouan.com/feed",
        "طنجة 24": "https://tanja24.com/feed",
        "شمال بوست": "https://chamalpost.net/feed",
        "طنجة نيوز": "https://tanjanews.com/feed",
        "صدى تطوان": "https://sadatetouan.com/feed",
        "تطوان بريس": "https://tetouanpress.ma/feed",
        "العرائش نيوز": "https://larachenews.com/feed",
        "دليل الريف": "https://www.dalil-rif.com/rss.xml",
        "ريف بوست": "https://rifpost.com/feed",
        "طنجة أنتر": "https://tanjainter.com/feed",
        "وزان بريس": "https://ouazzanepress.com/feed",
        "شفشاون بريس": "https://chefchaouenpress.com/feed",
        "تطوان نيوز": "https://tetouannews.com/feed",
        "العرائش 24": "https://larache24.com/feed",
        "أصداء تطوان": "https://asdaetetouan.com/feed",
        "منبر تطوان": "https://minbartetouan.com/feed",
        "خبايا نيوز": "https://khabayanews.com/feed",
        "ريف ديا": "https://rifdia.com/feed",
        "أصوات الدريوش": "https://driouchvoices.com/feed",
        "ميضار برس": "https://midarpress.com/feed",
        "زايو سيتي": "https://zaiocity.net/feed",
        "أخبار الريف": "https://akhbararif.com/feed",
        "الحسيمة سيتي": "https://alkhocimacity.com/feed",
        "ألتريس بريس": "https://altrespress.com/feed",
        "راديو تطوان": "https://radiotetouan.ma/feed",
        "عرائش سيتي": "https://larachecity.ma/feed",
        "القصر نيوز": "https://ksarnews.com/feed",
        "طنجة نيوز 24": "https://tanjanews24.com/feed",
        "سبتة بريس": "https://ceutapress.com/feed",
        "الريف 24": "https://rif24.com/feed",
        "ناظور 24": "https://nador24.com/feed",
        "الحسيمة 24": "https://alhoceima24.com/feed",
        "كاب تطوان": "https://captetouan.com/feed",
        "مارتيل بريس": "https://martilpress.com/feed",
        "المضيق تيفي": "https://mdiqtv.ma/feed",
        "الفنيدق 24": "https://fnideq24.com/feed",
        "شمالي": "https://chamaly.ma/feed",
        "طنجة الكبرى": "https://tanjakobra.com/feed",
        "تطوان بلوس": "https://tetouanplus.com/feed",
        "ريف سيتي": "https://rifcity.ma/feed",
        "طنجة بريس": "https://tangerpress.com/feed",
        "أخبار تطوان": "https://akhbartetouan.com/feed",
        "العرائش أنفو": "https://laracheinfo.com/feed",
        "القصر الكبير": "https://ksarkebir.com/feed",
        "وزان 24": "https://ouazzane24.com/feed",
        "شفشاون 24": "https://chefchaouen24.com/feed",
        "الريف بريس": "https://rifpress.ma/feed",
        "ناظور أوبزيرفر": "https://nadorobserver.com/feed",
        "تطوان اليوم": "https://tetouantoday.com/feed",
        "طنجة الآن": "https://tangerwala.com/feed"
    },
    "الجهات والشرق والجنوب (50 مصدر)": {
        "كشـ 24": "https://kech24.com/feed",
        "أكادير 24": "https://agadir24.info/feed",
        "وجدة سيتي": "https://www.oujdacity.net/feed",
        "مراكش الآن": "https://www.marrakechalaan.com/feed",
        "الداخلة نيوز": "https://dakhlanews.com/feed",
        "الصحراء زووم": "https://www.sahrazoom.com/feed",
        "سوس 24": "https://sous24.com/feed",
        "فاس نيوز": "https://fesnews.media/feed",
        "ناظور سيتي": "https://www.nadorcity.com/rss/",
        "تارودانت نيوز": "https://taroudant-news.com/feed",
        "صوت أكادير": "https://saoutagadir.ma/feed",
        "اشتوكة بريس": "https://chtoukapress.com/feed",
        "مكناس بريس": "https://meknespress.com/feed",
        "الجهة 24": "https://aljahia24.ma/feed",
        "وجدة بريس": "https://oujdapress.com/feed",
        "بركان سيتي": "https://berkanecity.com/feed",
        "ناظور برس": "https://nadorpress.com/feed",
        "تيزنيت 24": "https://tiznit24.com/feed",
        "كلميم نيوز": "https://glimimnews.com/feed",
        "الداخلة 24": "https://dakhla24.com/feed",
        "العيون أونلاين": "https://elaiunonline.com/feed",
        "كازا بريس": "https://casapress.com/feed",
        "سلا نيوز": "https://salanews.ma/feed",
        "قنيطرة سيتي": "https://kenitracity.net/feed",
        "آسفي كود": "https://saficod.ma/feed",
        "الجديدة 24": "https://eljadida24.com/feed",
        "سطات أونلاين": "https://settatonline.com/feed",
        "بني ملال أونلاين": "https://benimellalonline.com/feed",
        "خريبكة أونلاين": "https://khouribgaonline.com/feed",
        "آسفي 24": "https://safi24.ma/feed",
        "تارودانت بريس": "https://taroudantpress.ma/feed",
        "العيون 24": "https://laayoune24.com/feed",
        "الداخلة مباشر": "https://dakhlamobachir.net/feed",
        "زاكورة بريس": "https://zagorapress.com/feed",
        "تنغير نيوز": "https://tinghirnews.com/feed",
        "ورزازات أونلاين": "https://ouarzazateonline.com/feed",
        "الراشيدية 24": "https://errachidia24.com/feed",
        "ميدلت بريس": "https://mideltpress.com/feed",
        "خنيفرة أونلاين": "https://khenifraonline.com/feed",
        "تازة نيوز": "https://tazanews.com/feed",
        "تاونات نت": "https://taounatenet.ma/feed",
        "جرسيف 24": "https://guercif24.com/feed",
        "بركان نيوز": "https://berkanenews.com/feed",
        "جرادة نيوز": "https://jeradanews.com/feed",
        "فجيج نيوز": "https://figuignews.com/feed",
        "السمارة نيوز": "https://smara-news.com/feed",
        "بوجدور 24": "https://boujdour24.com/feed",
        "طانطان 24": "https://tantan24.com/feed",
        "سيدي إفني 24": "https://sidiifni24.com/feed",
        "أكادير تيفي": "https://agadirtv.ma/feed"
    },
    "رياضة واقتصاد ودولية (40 مصدر)": {
        "هسبريس رياضة": "https://hesport.com/feed",
        "البطولة": "https://www.elbotola.com/rss",
        "المنتخب": "https://almountakhab.com/rss",
        "اقتصادكم": "https://www.ecoactu.ma/ar/feed/",
        "سكاي نيوز": "https://www.skynewsarabia.com/rss/v1/middle-east.xml",
        "الجزيرة": "https://www.aljazeera.net/alritem/rss/rss.xml",
        "فرانس 24": "https://www.france24.com/ar/rss",
        "العربية": "https://www.alarabiya.net/.mrss/ar/last-24-hours.xml",
        "360 سبورت": "https://ar.sport.le360.ma/rss",
        "بورس نيوز": "https://boursenews.ma/feed",
        "ميديا 24": "https://www.medias24.com/ar/feed/",
        "رويترز": "https://www.reutersagency.com/feed/",
        "بي بي سي عربي": "https://www.bbc.com/arabic/index.xml",
        "الشرق للأخبار": "https://asharq.com/feed/",
        "سي إن بي سي عربية": "https://www.cnbcarabia.com/rss.xml",
        "كووورة": "https://www.kooora.com/rss.xml",
        "هاي كورة": "https://hihi2.com/feed",
        "في الجول": "https://www.filgoal.com/rss",
        "هبة سبور": "https://hibasport.com/feed",
        "شوف سبور": "https://choufsport.com/feed",
        "كورة بريس": "https://koorapress.com/feed",
        "موروكو وورلد نيوز": "https://www.moroccoworldnews.com/feed",
        "الأخبار الاقتصادية": "https://economie.ma/feed",
        "المال": "https://almal.ma/feed",
        "تشالنج": "https://challenge.ma/feed",
        "ليكونوميست": "https://www.leconomiste.com/rss.xml",
        "إم إف إم": "https://mfm.ma/feed",
        "راديو مارس": "https://radiomars.ma/feed",
        "أصوات": "https://aswat.ma/feed",
        "القدس العربي": "https://www.alquds.co.uk/feed",
        "عربي 21": "https://arabi21.com/rss",
        "روسيا اليوم": "https://arabic.rt.com/rss",
        "الحرة": "https://www.alhurra.com/rss",
        "اندبندنت عربية": "https://www.independentarabia.com/rss",
        "دويتشه فيله": "https://rss.dw.com/xml/rss-ar-all",
        "رأي اليوم": "https://www.raialyoum.com/feed",
        "الجزيرة نت": "https://www.aljazeera.net/rss",
        "سي ان ان بالعربية": "https://arabic.cnn.com/rss",
        "يورونيوز": "https://arabic.euronews.com/rss",
        "سبوتنيك": "https://sputnikarabic.ae/export/rss2/archive/index.xml"
    }
}
