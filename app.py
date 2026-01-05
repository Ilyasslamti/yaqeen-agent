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
# 0. إعدادات النظام والهوية (SEO MASTER)
# ==========================================
SYSTEM_VERSION = "V16.0_SEO_MASTER" 
ACCESS_PASSWORD = "Manager_Tech_2026" 

st.set_page_config(page_title="وكيل يقين الصحفي - SEO Edition", page_icon="📈", layout="wide")
socket.setdefaulttimeout(25) 
DB_FILE = "news_db_v16.json"

# ==========================================
# 1. نظام الحماية
# ==========================================
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if not st.session_state["authenticated"]:
        st.markdown("<div style='text-align: center; background: #1e3a8a; color: white; padding: 2rem; border-radius: 15px;'><h1>🔐 وكيل يقين الصحفي</h1><p>من مجموعة منادجر للتطوير وحلول الويب</p></div>", unsafe_allow_html=True)
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
# 2. محرك الصياغة الهندسي (SEO ARCHITECT)
# ==========================================
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except: client = None

def rewrite_seo_architect(text, tone, keyword):
    if not client: return "خطأ في الاتصال بالذكاء الاصطناعي"
    
    # هذا الـ Prompt هو سر القوة في تصدر النتائج
    prompt = f"""
    بصفتك خبير محتوى رقمي ومتخصص في Yoast SEO، أعد صياغة النص التالي لتحويله إلى مقال صحفي احترافي متكامل.
    
    الكلمة المفتاحية المستهدفة: {keyword}
    
    الخطة الهندسية للمقال (التزام صارم):
    1. العنوان الرئيسي: صغ عنواناً نصياً (بدون رموز) "مغناطيسياً" يبدأ بالكلمة المفتاحية أو يتضمنها في أول 3 كلمات.
    2. المقدمة (Focus): فقرة افتتاحية قوية (30 كلمة) تحتوي الكلمة المفتاحية وتلخص الحدث، مع استخدام أفعال مباشرة.
    3. العناوين الفرعية (H2): قسّم المقال بعناوين فرعية نصية (بدون رموز) تعبر عن محتوى الفقرات القادمة.
    4. معايير Yoast SEO للقراءة (Readability):
       - استخدم كلمات انتقال بكثافة (مثل: علاوة على ذلك، في المقابل، ومن هذا المنطلق، ونتيجة لذلك).
       - طول الجملة: ممنوع تجاوز 18 كلمة لكل جملة. استخدم النقطة باستمرار.
       - المبني للمعلوم: حوّل كل الجمل لمبني للمعلوم (Active Voice).
       - طول الفقرة: 3 أسطر بحد أقصى للفقرة الواحدة.
    
    الأسلوب المطلوب: {tone}.
    
    النص الأصلي:
    {text[:3800]}
    """
    
    try:
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile", 
            temperature=0.4 # توازن مثالي بين الإبداع والالتزام بالقواعد
        )
        return res.choices[0].message.content
    except Exception as e: return f"خطأ تقني: {str(e)}"

# ==========================================
# 3. الواجهة والمنطق البرمجي
# ==========================================
if check_password():
    
    RSS_SOURCES = {
        "الصحافة الوطنية 🇲🇦": {
            "هسبريس": "https://www.hespress.com/feed", "شوف تيفي": "https://chouftv.ma/feed",
            "العمق المغربي": "https://al3omk.com/feed", "زنقة 20": "https://www.rue20.com/feed",
            "هبة بريس": "https://ar.hibapress.com/feed", "اليوم 24": "https://alyaoum24.com/feed"
        },
        "أخبار الشمال والجهات 🌊": {
            "شمال بوست": "https://chamalpost.net/feed", "بريس تطوان": "https://presstetouan.com/feed",
            "طنجة 24": "https://tanja24.com/feed", "تطوان بريس": "https://tetouanpress.ma/feed"
        },
        "أخبار دولية واقتصاد 🌍": {
            "سكاي نيوز عربية": "https://www.skynewsarabia.com/rss/v1/middle-east.xml",
            "الجزيرة نت": "https://www.aljazeera.net/alritem/rss/rss.xml",
            "اقتصادكم": "https://www.economistcom.ma/feed"
        },
        "فن ورياضة ⚽": {
            "البطولة": "https://www.elbotola.com/rss", "هسبريس رياضة": "https://hesport.com/feed",
            "لالة مولاتي": "https://www.lallamoulati.ma/feed/"
        }
    }

    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
        html, body, [class*="st-"] { font-family: 'Cairo', sans-serif; text-align: right; }
        .article-output {
            white-space: pre-wrap; background-color: #ffffff; color: #111; padding: 35px; 
            border-radius: 12px; border: 1px solid #cfd8dc; line-height: 2.1; font-size: 1.2rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .stButton>button { background: #1e3a8a; color: white; border-radius: 10px; height: 3.5rem; font-weight: bold;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div style='text-align: center; background: #1e3a8a; color: white; padding: 1rem; border-radius: 10px; margin-bottom: 2rem;'><h1>وكيل يقين الصحفي - خبير SEO</h1></div>", unsafe_allow_html=True)

    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f: db = json.load(f)
    else: db = {"data": {}}

    tabs = st.tabs(list(RSS_SOURCES.keys()))
    for i, cat in enumerate(list(RSS_SOURCES.keys())):
        with tabs[i]:
            if st.button(f"🔄 تحديث قائمة {cat}", key=f"up_{i}"):
                with st.spinner("جاري جلب آخر الأخبار..."):
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
                    with open(DB_FILE, 'w', encoding='utf-8') as f: json.dump(db, f, ensure_ascii=False)
                st.rerun()

            if cat in db["data"] and db["data"][cat]:
                news = db["data"][cat]
                choice = st.selectbox("اختر المقال المراد هندسته:", range(len(news)), format_func=lambda x: f"[{news[x]['source']}] {news[x]['title']}", key=f"s_{i}")
                
                c1, c2 = st.columns(2)
                with c1: tone = st.selectbox("الأسلوب:", ["تحقيق صحفي رصين", "تقرير إخباري سريع", "تحليل تفاعلي"], key=f"t_{i}")
                with c2: keyword = st.text_input("الكلمة المفتاحية (SEO):", placeholder="مثال: نفق الرباط..", key=f"k_{i}")

                if st.button("🚀 توليد مقال احترافي متصدر", key=f"r_{i}"):
                    with st.status("🏗️ جاري بناء المقال وفق معايير Yoast SEO...", expanded=True):
                        raw = trafilatura.fetch_url(news[choice]['link'])
                        txt = trafilatura.extract(raw)
                        if txt:
                            final_content = rewrite_seo_architect(txt, tone, keyword)
                            st.markdown("### ✅ المقال النهائي المنسق")
                            st.markdown(f"<div class='article-output'>{final_content}</div>", unsafe_allow_html=True)
                            st.text_area("نسخة النشر المباشر:", final_content, height=450)
                        else: st.error("المصدر يمنع السحب")
            else: st.info("اضغط تحديث لجلب البيانات.")

    st.markdown("---")
    st.markdown("<p style='text-align:center; color:#666;'>وكيل يقين الصحفي V16.0 - تطوير وحلول الماندجر</p>", unsafe_allow_html=True)        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            password_input = st.text_input("مفتاح الوصول:", type="password")
            if st.button("تسجيل الدخول"):
                if password_input == ACCESS_PASSWORD:
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error("❌ مفتاح الوصول غير صحيح!")
        return False
    return True

# ==========================================
# 2. نظام التنظيف الذكي (3 صباحاً)
# ==========================================
def auto_purge_at_3am():
    now = datetime.now()
    if now.hour == 3:
        if os.path.exists(DB_FILE):
            try:
                os.remove(DB_FILE)
                st.cache_data.clear()
            except: pass

auto_purge_at_3am()

# ==========================================
# بدء تنفيذ البرنامج بعد التحقق من الهوية
# ==========================================
if check_password():
    
    # قائمة المصادر الموسعة
    RSS_SOURCES = {
        "الصحافة الوطنية 🇲🇦": {
            "هسبريس": "https://www.hespress.com/feed",
            "شوف تيفي": "https://chouftv.ma/feed",
            "العمق المغربي": "https://al3omk.com/feed",
            "زنقة 20": "https://www.rue20.com/feed",
            "هبة بريس": "https://ar.hibapress.com/feed",
            "اليوم 24": "https://alyaoum24.com/feed",
            "Le360": "https://ar.le360.ma/rss",
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

    # تنسيق الواجهة
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
        html, body, [class*="st-"] { font-family: 'Cairo', sans-serif; text-align: right; }
        .brand-header {
            text-align: center; background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
            color: white; padding: 2rem; border-radius: 15px; margin-bottom: 2rem;
        }
        .article-output {
            white-space: pre-wrap; background-color: #ffffff; color: #111; padding: 30px; 
            border-radius: 12px; border: 1px solid #cfd8dc; line-height: 2; font-size: 1.15rem;
        }
        .stButton>button { background: #1e3a8a; color: white; border-radius: 10px; height: 3.5rem; width: 100%; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='brand-header'><h1>وكيل يقين الصحفي</h1><p>من مجموعة منادجر للتطوير وحلول الويب</p></div>", unsafe_allow_html=True)

    # المنطق البرمجي لجلب الأخبار
    try:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    except: client = None

    def fetch_items(name, url):
        try:
            d = feedparser.parse(url)
            return [{"title": e.title, "link": e.link, "source": name} for e in d.entries[:10]]
        except: return []

    def rewrite_pro(text, tone, instr):
        if not client: return "خطأ: تأكد من مفتاح API"
        prompt = f"أنت خبير SEO. صغ مقالاً احترافياً بدون رموز Markdown. عنوان جذاب في البداية. جمل قصيرة (<18 كلمة). مبني للمعلوم. فقرات قصيرة. الأسلوب: {tone}. الكلمة المفتاحية: {instr}. النص: {text[:3800]}"
        try:
            res = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile", temperature=0.3
            )
            return res.choices[0].message.content
        except Exception as e: return str(e)

    # قاعدة البيانات
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f: db = json.load(f)
    else: db = {"data": {}}

    tabs = st.tabs(list(RSS_SOURCES.keys()))
    for i, cat in enumerate(list(RSS_SOURCES.keys())):
        with tabs[i]:
            if st.button(f"🔄 تحديث أخبار {cat}", key=f"upd_{i}"):
                with st.spinner("جاري الجلب..."):
                    all_news = []
                    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as exec:
                        futures = [exec.submit(fetch_items, n, u) for n, u in RSS_SOURCES[cat].items()]
                        for f in concurrent.futures.as_completed(futures): all_news.extend(f.result())
                    db["data"][cat] = all_news
                    with open(DB_FILE, 'w', encoding='utf-8') as f: json.dump(db, f, ensure_ascii=False)
                st.rerun()

            if cat in db["data"] and db["data"][cat]:
                news = db["data"][cat]
                choice = st.selectbox("اختر المقال:", range(len(news)), format_func=lambda x: f"[{news[x]['source']}] {news[x]['title']}", key=f"sel_{i}")
                
                c1, c2 = st.columns(2)
                with c1: tone = st.selectbox("النبرة:", ["إخباري", "تحليلي", "تفاعلي"], key=f"tn_{i}")
                with c2: instr = st.text_input("الكلمة المفتاحية (SEO):", key=f"kw_{i}")

                if st.button("🚀 هندسة وصياغة المقال", key=f"run_{i}"):
                    with st.status("🏗️ جاري العمل...", expanded=True):
                        raw = trafilatura.fetch_url(news[choice]['link'])
                        txt = trafilatura.extract(raw)
                        if txt:
                            final = rewrite_pro(txt, tone, instr)
                            st.markdown("### ✅ المقال النهائي")
                            st.markdown(f"<div class='article-output'>{final}</div>", unsafe_allow_html=True)
                            st.text_area("نسخة للنشر:", final, height=400)
                        else: st.error("المصدر محمي.")
            else:
                st.info("اضغط تحديث لجلب البيانات.")

    st.markdown("---")
    st.markdown("<p style='text-align:center; color:#666;'>وكيل يقين الصحفي - إصدار V15.0 محصن - إدارة الماندجر</p>", unsafe_allow_html=True)
