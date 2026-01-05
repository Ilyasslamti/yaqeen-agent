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

# 1. إعدادات أساسية
st.set_page_config(page_title="وكيل يقين الصحفي", page_icon="📰", layout="wide")
ACCESS_PASSWORD = "Manager_Tech_2026"
DB_FILE = "news_db_v16.json"
socket.setdefaulttimeout(30)

# 2. محرك الصياغة (دالة مستقلة)
def run_ai_writer(text, tone, keyword):
    try:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        prompt = f"""أنت رئيس تحرير خبير في Yoast SEO. صغ مقالاً احترافياً بناءً على النص.
        الكلمة المفتاحية: {keyword}
        القواعد: جمل قصيرة جداً (أقل من 18 كلمة)، استخدم النقطة باستمرار، مبني للمعلوم، كلمات انتقال متنوعة، عناوين فرعية نصية، بدون رموز Markdown نهائياً، ولا تذكر كلمة مغناطيسي.
        الأسلوب: {tone}.
        النص: {text[:3800]}"""
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.4
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"خطأ تقني: {str(e)}"

# 3. نظام الحماية
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔐 تسجيل الدخول - وكيل يقين")
    pwd = st.text_input("أدخل مفتاح الوصول:", type="password")
    if st.button("دخول"):
        if pwd == ACCESS_PASSWORD:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("المفتاح خطأ")
    st.stop()

# 4. المصادر الكاملة (تظهر فقط بعد الدخول)
RSS_SOURCES = {
    "الصحافة الوطنية 🇲🇦": {
        "هسبريس": "https://www.hespress.com/feed",
        "شوف تيفي": "https://chouftv.ma/feed",
        "العمق المغربي": "https://al3omk.com/feed",
        "زنقة 20": "https://www.rue20.com/feed",
        "هبة بريس": "https://ar.hibapress.com/feed",
        "اليوم 24": "https://alyaoum24.com/feed",
        "Le360 عربي": "https://ar.le360.ma/rss",
        "آشكاين": "https://achkayen.com/feed"
    },
    "أخبار الشمال 🌊": {
        "شمال بوست": "https://chamalpost.net/feed",
        "بريس تطوان": "https://presstetouan.com/feed",
        "طنجة 24": "https://tanja24.com/feed",
        "تطوان بريس": "https://tetouanpress.ma/feed",
        "طنجة نيوز": "https://tanjanews.com/feed"
    },
    "دولية واقتصاد 🌍": {
        "سكاي نيوز": "https://www.skynewsarabia.com/rss/v1/middle-east.xml",
        "الجزيرة": "https://www.aljazeera.net/alritem/rss/rss.xml",
        "فرانس 24": "https://www.france24.com/ar/rss",
        "اقتصادكم": "https://www.economistcom.ma/feed"
    },
    "رياضة وفن ⚽": {
        "البطولة": "https://www.elbotola.com/rss",
        "هسبريس رياضة": "https://hesport.com/feed",
        "لالة مولاتي": "https://www.lallamoulati.ma/feed/",
        "هاي كورة": "https://hihi2.com/feed"
    }
}

st.markdown("<h1 style='text-align:center;'>وكيل يقين الصحفي - Manadger Tech</h1>", unsafe_allow_html=True)

# 5. إدارة البيانات
if os.path.exists(DB_FILE):
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        db = json.load(f)
else:
    db = {"data": {}}

# 6. التبويبات والمنطق
tabs = st.tabs(list(RSS_SOURCES.keys()))
for i, cat in enumerate(list(RSS_SOURCES.keys())):
    with tabs[i]:
        if st.button(f"🔄 تحديث {cat}", key=f"btn_{i}"):
            all_news = []
            def fetch_single(n, u):
                try:
                    d = feedparser.parse(u)
                    return [{"title": e.title, "link": e.link, "source": n} for e in d.entries[:10]]
                except: return []
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as exec:
                futures = [exec.submit(fetch_single, name, url) for name, url in RSS_SOURCES[cat].items()]
                for f in concurrent.futures.as_completed(futures):
                    all_news.extend(f.result())
            db["data"][cat] = all_news
            with open(DB_FILE, 'w', encoding='utf-8') as f:
                json.dump(db, f, ensure_ascii=False)
            st.rerun()

        if cat in db["data"] and db["data"][cat]:
            news_list = db["data"][cat]
            choice = st.selectbox("اختر المقال:", range(len(news_list)), format_func=lambda x: f"[{news_list[x]['source']}] {news_list[x]['title']}", key=f"sel_{i}")
            
            c1, c2 = st.columns(2)
            with c1:
                tone = st.selectbox("الأسلوب:", ["تحقيق صحفي", "تقرير سريع", "تحليل SEO"], key=f"tone_{i}")
            with c2:
                keyword = st.text_input("الكلمة المفتاحية:", key=f"key_{i}")

            if st.button("🚀 صياغة المقال", key=f"go_{i}"):
                with st.spinner("جاري المعالجة..."):
                    raw = trafilatura.fetch_url(news_list[choice]['link'])
                    txt = trafilatura.extract(raw)
                    if txt:
                        res = run_ai_writer(txt, tone, keyword)
                        st.markdown("### ✅ المقال المطور")
                        st.write(res)
                        st.text_area("نسخة النشر:", res, height=300)
                    else:
                        st.error("فشل السحب")
        else:
            st.info("اضغط تحديث.")

st.markdown("---")
st.caption("وكيل يقين V16.7 - مجموعة الماندجر للتطوير 2026")
