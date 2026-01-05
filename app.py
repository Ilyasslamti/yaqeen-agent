import streamlit as st
import feedparser
import trafilatura
from groq import Groq
import concurrent.futures
import json
import os
import socket
import requests
from datetime import datetime

# ==========================================
# 0. إعدادات النظام والهوية
# ==========================================
SYSTEM_VERSION = "V16.4_FULL_SOURCES" 
ACCESS_PASSWORD = "Manager_Tech_2026" 

st.set_page_config(page_title="وكيل يقين الصحفي - المصادر الكاملة", page_icon="📰", layout="wide")
socket.setdefaulttimeout(30) 
DB_FILE = "news_db_v16.json"

# ==========================================
# 1. نظام الحماية
# ==========================================
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if not st.session_state["authenticated"]:
        st.markdown("<div style='text-align: center; background: #1e3a8a; color: white; padding: 2rem; border-radius: 15px;'><h1>🔐 وكيل يقين الصحفي</h1><p>إدارة الماندجر - نظام السحب الشامل</p></div>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            password_input = st.text_input("أدخل مفتاح الوصول:", type="password")
            if st.button("دخول للنظام"):
                if password_input == ACCESS_PASSWORD:
                    st.session_state["authenticated"] = True
                    st.rerun()
                else: st.error("❌ المفتاح غير صحيح")
        return False
    return True

# ==========================================
# 2. محرك الصياغة (السيو القوي والجمل القصيرة)
# ==========================================
try:
    if "GROQ_API_KEY" in st.secrets:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    else: client = None
except: client = None

def rewrite_seo_architect(text, tone, keyword):
    if not client: return "خطأ: مفتاح API مفقود"
    prompt = f"""
    بصفتك خبير Yoast SEO، أعد صياغة النص بجمل قصيرة جداً (أقل من 18 كلمة لكل جملة).
    الكلمة المفتاحية: {keyword}
    
    الضوابط:
    1. انهِ الجملة بنقطة فور اكتمال الفكرة البسيطة. 
    2. استخدم المبني للمعلوم حصراً.
    3. العناوين الفرعية نصية خالية من الرموز تماماً.
    4. نوع في روابط الجمل (لذلك، ومن جهة، وبالتوازي).
    
    الأسلوب: {tone}.
    النص: {text[:3800]}
    """
    try:
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile", temperature=0.3
        )
        return res.choices[0].message.content
    except Exception as e: return f"خطأ: {str(e)}"

# ==========================================
# 3. تشغيل النظام والمصادر الكاملة
# ==========================================
if check_password():
    
    # القائمة الكاملة كما طلبت
    RSS_SOURCES = {
        "الصحافة الوطنية 🇲🇦": {
            "هسبريس": "https://www.hespress.com/feed",
            "شوف تيفي": "https://chouftv.ma/feed",
            "العمق المغربي": "https://al3omk.com/feed",
            "زنقة 20": "https://www.rue20.com/feed",
            "هبة بريس": "https://ar.hibapress.com/feed",
            "اليوم 24": "https://alyaoum24.com/feed",
            "Le360 عربي": "https://ar.le360.ma/rss",
            "فبراير": "https://www.febrayer.com/feed",
            "آشكاين": "https://achkayen.com/feed",
            "الجريدة 24": "https://aljarida24.ma/feed"
        },
        "أخبار الشمال والجهات 🌊": {
            "شمال بوست": "https://chamalpost.net/feed",
            "بريس تطوان": "https://presstetouan.com/feed",
            "طنجة 24": "https://tanja24.com/feed",
            "تطوان بريس": "https://tetouanpress.ma/feed",
            "طنجة نيوز": "https://tanjanews.com/feed",
            "كاب 24": "https://cap24.tv/feed",
            "صدى تطوان": "https://sadatetouan.com/feed"
        },
        "أخبار دولية واقتصاد 🌍": {
            "سكاي نيوز عربية": "https://www.skynewsarabia.com/rss/v1/middle-east.xml",
            "الجزيرة نت": "https://www.aljazeera.net/alritem/rss/rss.xml",
            "فرانس 24": "https://www.france24.com/ar/rss",
            "BBC عربي": "https://www.bbc.com/arabic/index.xml",
            "اقتصادكم": "https://www.economistcom.ma/feed"
        },
        "فن، مشاهير ورياضة ⚽": {
            "البطولة": "https://www.elbotola.com/rss",
            "هسبريس رياضة": "https://hesport.com/feed",
            "المنتخب": "https://almountakhab.com/rss",
            "لالة مولاتي": "https://www.lallamoulati.ma/feed/",
            "سلطانة": "https://soltana.ma/feed",
            "هاي كورة": "https://hihi2.com/feed"
        }
    }

    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
        html, body, [class*="st-"] { font-family: 'Cairo', sans-serif; text-align: right; }
        .article-output { white-space: pre-wrap; background-color: #ffffff; padding: 30px; border-radius: 12px; border: 1px solid #cfd8dc; line-height: 2.1; font-size: 1.15rem; }
        .stButton>button { background: #1e3a8a; color: white; border-radius: 10px; height: 3.5rem; font-weight: bold; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f: db = json.load(f)
    else: db = {"data": {}}

    tabs = st.tabs(list(RSS_SOURCES.keys()))
    for i, cat in enumerate(list(RSS_SOURCES.keys())):
        with tabs[i]:
            if st.button(f"🔄 تحديث أخبار {cat}", key=f"up_{i}"):
                with st.spinner("جاري جلب البيانات من كافة المصادر..."):
                    all_news = []
                    def fetch(n, u):
                        try:
                            d = feedparser.parse(u)
                            return [{"title": e.title, "link": e.link, "source": n} for e in d.entries[:10]]
                        except: return []
                    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as exec:
                        futures = [exec.submit(fetch, name, url) for name, url in RSS_SOURCES[cat].items()]
                        for f in concurrent.futures.as_completed(futures): all_news.extend(f.result())
                    db["data"][cat] = all_news
                    with open(DB_FILE, 'w', encoding='utf-8') as f: json.dump(db, f, ensure_ascii=False)
                st.rerun()

            if cat in db["data"] and db["data"][cat]:
                news = db["data"][cat]
                choice = st.selectbox("اختر المقال:", range(len(news)), format_func=lambda x: f"[{news[x]['source']}] {news[x]['title']}", key=f"s_{i}")
                c1, c2 = st.columns(2)
                with c1: tone = st.selectbox("الأسلوب:", ["تقرير صحفي قصير", "تحقيق مثير", "تحليل SEO"], key=f"t_{i}")
                with c2: keyword = st.text_input("الكلمة المفتاحية:", key=f"k_{i}")

                if st.button("🚀 صياغة المقال الآن", key=f"r_{i}"):
                    with st.status("🏗️ جاري المعالجة...", expanded=True):
                        raw = trafilatura.fetch_url(news[choice]['link'])
                        txt = trafilatura.extract(raw)
                        if txt:
                            final = rewrite_seo_architect(txt, tone, keyword)
                            st.markdown("### ✅ المقال المطور")
                            st.markdown(f"<div class='article-output'>{final}</div>", unsafe_allow_html=True)
                            st.text_area("للنسخ المباشر:", final, height=400)
                        else: st.error("المصدر محمي.")
            else: st.info("اضغط تحديث.")

    st.markdown("---")
    st.markdown("<p style='text-align:center; color:#666;'>وكيل يقين الصحفي V16.4 - إدارة الماندجر</p>", unsafe_allow_html=True)                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error("❌ مفتاح الوصول غير صحيح!")
        return False
    return True

# ==========================================
# 2. محرك الهندسة الصحفية (SEO PRO ARCHITECT)
# ==========================================
try:
    if "GROQ_API_KEY" in st.secrets:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    else:
        client = None
except Exception:
    client = None

def rewrite_seo_architect(text, tone, keyword):
    if not client: 
        return "خطأ: تأكد من إعداد مفتاح GROQ_API_KEY في Secrets."
    
    prompt = f"""
    أنت رئيس تحرير خبير في المحتوى الفني والسياسي وSEO. حول هذا النص الجامد إلى مقال صحفي نابض بالحياة.
    الكلمة المفتاحية المستهدفة: {keyword}
    
    الخطة التحريرية (التزام صارم):
    1. العنوان: صغ عنواناً انفجارياً ومثيراً يتصدر نتائج البحث ويبدأ بالكلمة المفتاحية. 
       (تنبيه: لا تضف كلمات مثل 'مغناطيسياً' أو أي رموز مثل ## أو **).
    2. الأسلوب: لا تسرد حقائق فقط، اصنع قصة مشوقة. استخدم أفعالاً قوية (يفجر، يكشف، يقود، يتصدر).
    3. التنسيق: استخدم عناوين فرعية نصية واضحة في أسطر مستقلة (بدون رموز Markdown نهائياً).
    4. معايير Yoast SEO: 
       - نوع في كلمات الانتقال (بالموازاة مع ذلك، وفي غمرة هذا النجاح، ولم يقف الأمر عند هذا الحد).
       - جمل قصيرة ورشيقة (أقل من 18 كلمة).
       - المبني للمعلوم حصراً (اجعل الفاعل هو بطل الجملة).
       - الفقرات قصيرة (3 أسطر كحد أقصى).
    
    الأسلوب المطلوب: {tone}.
    النص الأصلي للمعالجة:
    {text[:3800]}
    """
    try:
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile", 
            temperature=0.6 # رفع درجة الإبداع اللغوي
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"خطأ تقني في الصياغة: {str(e)}"

# ==========================================
# 3. المنطق التشغيلي (Main Application)
# ==========================================
if check_password():
    
    RSS_SOURCES = {
        "الصحافة الوطنية 🇲🇦": {
            "هسبريس": "https://www.hespress.com/feed",
            "شوف تيفي": "https://chouftv.ma/feed",
            "العمق المغربي": "https://al3omk.com/feed",
            "زنقة 20": "https://www.rue20.com/feed",
            "هبة بريس": "https://ar.hibapress.com/feed",
            "اليوم 24": "https://alyaoum24.com/feed"
        },
        "أخبار الشمال والجهات 🌊": {
            "شمال بوست": "https://chamalpost.net/feed",
            "بريس تطوان": "https://presstetouan.com/feed",
            "طنجة 24": "https://tanja24.com/feed",
            "تطوان بريس": "https://tetouanpress.ma/feed"
        },
        "أخبار دولية واقتصاد 🌍": {
            "سكاي نيوز عربية": "https://www.skynewsarabia.com/rss/v1/middle-east.xml",
            "الجزيرة نت": "https://www.aljazeera.net/alritem/rss/rss.xml",
            "فرانس 24": "https://www.france24.com/ar/rss"
        },
        "فن ورياضة ⚽": {
            "البطولة": "https://www.elbotola.com/rss",
            "هسبريس رياضة": "https://hesport.com/feed",
            "لالة مولاتي": "https://www.lallamoulati.ma/feed/"
        }
    }

    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
        html, body, [class*="st-"] { font-family: 'Cairo', sans-serif; text-align: right; }
        .article-output {
            white-space: pre-wrap; background-color: #ffffff; color: #111; padding: 35px; 
            border-radius: 12px; border: 1px solid #cfd8dc; line-height: 2.2; font-size: 1.2rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }
        .stButton>button { background: #1e3a8a; color: white; border-radius: 10px; height: 3.5rem; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div style='text-align: center; background: #1e3a8a; color: white; padding: 1rem; border-radius: 10px; margin-bottom: 2rem;'><h1>وكيل يقين الصحفي - إصدار V16.2</h1></div>", unsafe_allow_html=True)

    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                db = json.load(f)
        except:
            db = {"data": {}}
    else:
        db = {"data": {}}

    tabs = st.tabs(list(RSS_SOURCES.keys()))
    for i, cat in enumerate(list(RSS_SOURCES.keys())):
        with tabs[i]:
            if st.button(f"🔄 تحديث {cat}", key=f"up_{i}"):
                with st.spinner("جاري جلب البيانات..."):
                    all_news = []
                    def fetch(n, u):
                        try:
                            d = feedparser.parse(u)
                            return [{"title": e.title, "link": e.link, "source": n} for e in d.entries[:10]]
                        except: return []
                    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as exec:
                        futures = [exec.submit(fetch, name, url) for name, url in RSS_SOURCES[cat].items()]
                        for f in concurrent.futures.as_completed(futures): all_news.extend(f.result())
                    db["data"][cat] = all_news
                    with open(DB_FILE, 'w', encoding='utf-8') as f:
                        json.dump(db, f, ensure_ascii=False)
                st.rerun()

            if cat in db["data"] and db["data"][cat]:
                news_list = db["data"][cat]
                choice = st.selectbox("اختر المقال المراد هندسته:", range(len(news_list)), format_func=lambda x: f"[{news_list[x]['source']}] {news_list[x]['title']}", key=f"sel_{i}")
                
                c1, c2 = st.columns(2)
                with c1:
                    tone = st.selectbox("الأسلوب الصحفي:", ["تحقيق صحفي مثير", "تقرير إخباري رصين", "تحليل تفاعلي سريع"], key=f"tn_{i}")
                with c2:
                    keyword = st.text_input("الكلمة المفتاحية (SEO):", key=f"kw_{i}")

                if st.button("🚀 صياغة المقال بمستوى احترافي", key=f"run_{i}"):
                    with st.status("🏗️ جاري هندسة المقال وتطبيق معايير Yoast SEO...", expanded=True):
                        raw_html = trafilatura.fetch_url(news_list[choice]['link'])
                        main_text = trafilatura.extract(raw_html)
                        if main_text:
                            final_article = rewrite_seo_architect(main_text, tone, keyword)
                            st.markdown("### ✅ المقال النهائي المنسق")
                            st.markdown(f"<div class='article-output'>{final_article}</div>", unsafe_allow_html=True)
                            st.text_area("نسخة النشر المباشر:", final_article, height=450)
                        else:
                            st.error("المصدر يمنع السحب التلقائي.")
            else:
                st.info("اضغط تحديث لجلب البيانات.")

    st.markdown("---")
    st.markdown("<p style='text-align:center; color:#666;'>وكيل يقين الصحفي - تطوير وحلول الماندجر للويب 2026</p>", unsafe_allow_html=True)
