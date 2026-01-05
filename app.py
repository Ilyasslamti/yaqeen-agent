import streamlit as st
import feedparser
import trafilatura
from openai import OpenAI
import concurrent.futures
import json
import os
import socket
import time

# ==========================================
# 0. إعدادات الهوية
# ==========================================
SYSTEM_VERSION = "V24.0_ELITE_JOURNALISM"
ACCESS_PASSWORD = "Manager_Tech_2026"
DB_FILE = "news_db_v24.json"

st.set_page_config(
    page_title="يقين AI | الصحافة الاحترافية",
    layout="wide"
)

socket.setdefaulttimeout(40)

# ==========================================
# 1. شاشة تحميل احترافية (آمنة)
# ==========================================
def loading_screen(message="جاري تهيئة النظام الصحفي..."):
    placeholder = st.empty()
    with placeholder.container():
        st.markdown(
            f"""
            <style>
            .loader-box {{
                padding: 60px;
                text-align: center;
                border-radius: 20px;
                background: #ffffff;
                box-shadow: 0 10px 30px rgba(0,0,0,0.06);
                font-family: Cairo, sans-serif;
            }}
            </style>
            <div class="loader-box">
                <h3>{message}</h3>
                <p>يرجى الانتظار...</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    time.sleep(1.2)
    placeholder.empty()

# ==========================================
# 2. نظام الدخول المعزول
# ==========================================
def auth_gate():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.title("دخول منصة يقين AI – إصدار الصحافة الاحترافية")
        pwd = st.text_input("مفتاح الوصول:", type="password")

        if st.button("فتح النظام"):
            if pwd == ACCESS_PASSWORD:
                st.session_state["authenticated"] = True
                loading_screen("جاري فتح المنصة الصحفية...")
                st.rerun()
            else:
                st.error("مفتاح الوصول غير صحيح")

        st.stop()

# استدعاء بوابة الدخول
auth_gate()

# ==========================================
# 3. محرك الصياغة الصحفية
# ==========================================
def run_samba_writer(text, tone, keyword):
    try:
        client = OpenAI(
            api_key=st.secrets["SAMBANOVA_API_KEY"],
            base_url="https://api.sambanova.ai/v1",
        )

        prompt = f"""
أنت صحفي محترف تكتب بأسلوب مؤسساتي رصين.

أعد صياغة النص وفق القواعد التالية:
- المبني للمعلوم بنسبة لا تقل عن 90%
- طول الجملة لا يتجاوز 25 كلمة
- تنويع بدايات الجمل
- عنوان رئيسي يبدأ بالكلمة المفتاحية: {keyword}
- إدراج عناوين فرعية نصية عند الانتقال بين الزوايا
- يمنع ذكر المصدر الأصلي

أسلوب الصياغة: {tone}

النص الأصلي:
{text[:4500]}
"""

        response = client.chat.completions.create(
            model="Meta-Llama-3.3-70B-Instruct",
            messages=[
                {"role": "system", "content": "أنت كاتب صحفي عربي محترف."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            top_p=0.9
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"خطأ تقني في محرك الصياغة: {str(e)}"

# ==========================================
# 4. المصادر (لم يتم لمسها نهائيًا)
# ==========================================
RSS_SOURCES = {
    "الصحافة الوطنية 🇲🇦": {
        "هسبريس": "https://www.hespress.com/feed",
        "شوف تيفي": "https://chouftv.ma/feed",
        "العمق المغربي": "https://al3omk.com/feed",
        "زنقة 20": "https://www.rue20.com/feed",
        "هبة بريس": "https://ar.hibapress.com/feed",
        "اليوم 24": "https://alyaoum24.com/feed",
        "كود": "https://www.goud.ma/feed",
        "Le360": "https://ar.le360.ma/rss",
        "فبراير": "https://www.febrayer.com/feed",
        "آشكاين": "https://achkayen.com/feed",
        "الجريدة 24": "https://aljarida24.ma/feed",
        "لكم": "https://lakome2.com/feed",
        "عبر": "https://aabbir.com/feed",
        "سفيركم": "https://safir24.com/feed",
        "باناصا": "https://banassa.com/feed",
        "الأيام 24": "https://www.alayam24.com/feed",
        "برلمان.كوم": "https://www.barlamane.com/feed",
        "تليكسبريس": "https://telexpresse.com/feed",
        "الصباح": "https://assabah.ma/feed",
        "الأحداث المغربية": "https://ahdath.info/feed",
        "مدار 21": "https://madar21.com/feed",
        "كيوسك أنفو": "https://kiosqueinfo.ma/feed",
        "آذار": "https://aaddar.com/feed",
        "مشاهد": "https://mashahed.info/feed"
    }
}

# ==========================================
# 5. الواجهة
# ==========================================
st.title("يقين AI | الصحافة الاحترافية")

if os.path.exists(DB_FILE):
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            db = json.load(f)
    except:
        db = {"data": {}}
else:
    db = {"data": {}}

tabs = st.tabs(list(RSS_SOURCES.keys()))

for i, cat in enumerate(RSS_SOURCES.keys()):
    with tabs[i]:
        if st.button(f"تحديث أخبار {cat}", key=f"up_{i}"):
            with st.spinner("جاري جلب الأخبار..."):
                all_news = []

                def fetch_feed(name, url):
                    try:
                        feed = feedparser.parse(url)
                        return [{"title": e.title, "link": e.link, "source": name} for e in feed.entries[:10]]
                    except:
                        return []

                with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                    futures = [
                        executor.submit(fetch_feed, name, url)
                        for name, url in RSS_SOURCES[cat].items()
                    ]
                    for f in concurrent.futures.as_completed(futures):
                        all_news.extend(f.result())

                db["data"][cat] = all_news
                with open(DB_FILE, "w", encoding="utf-8") as f:
                    json.dump(db, f, ensure_ascii=False)

            st.rerun()

        if cat in db["data"] and db["data"][cat]:
            news = db["data"][cat]
            idx = st.selectbox(
                "اختر الخبر:",
                range(len(news)),
                format_func=lambda x: f"[{news[x]['source']}] {news[x]['title']}"
            )

            tone = st.selectbox(
                "نبرة المقال:",
                ["تقرير صحفي احترافي", "تحليل استقصائي رصين"]
            )

            keyword = st.text_input("الكلمة المفتاحية (SEO):")

            if st.button("صياغة المقال"):
                raw = trafilatura.fetch_url(news[idx]["link"])
                text = trafilatura.extract(raw)

                if text:
                    result = run_samba_writer(text, tone, keyword)
                    st.markdown("### المقال النهائي")
                    st.text_area("", result, height=500)
                else:
                    st.error("تعذر استخراج النص من المصدر.")

        else:
            st.info("المرجو تحديث الأخبار أولًا.")

st.caption("يقين AI – إصدار الصحافة النخبوية – 2026")
