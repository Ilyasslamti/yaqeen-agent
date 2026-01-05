import streamlit as st
import feedparser
import trafilatura
from openai import OpenAI
import concurrent.futures
import json
import os
import socket
from datetime import datetime
import time

# ==========================================
# 0. إعدادات الهوية (إصدار الصحافة الاحترافية)
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
# شاشة تحميل احترافية (آمنة)
# ==========================================
def loading_screen(message="جاري تهيئة النظام الصحفي..."):
    placeholder = st.empty()
    with placeholder.container():
        st.markdown(
            """
            <style>
            .loader-box {
                padding: 60px;
                text-align: center;
                border-radius: 20px;
                background: #ffffff;
                box-shadow: 0 10px 30px rgba(0,0,0,0.06);
                font-family: Cairo, sans-serif;
            }
            </style>
            <div class="loader-box">
                <h3>{}</h3>
                <p>يرجى الانتظار...</p>
            </div>
            """.format(message),
            unsafe_allow_html=True
        )
    time.sleep(1.2)
    placeholder.empty()

# ==========================================
# 1. نظام الدخول المعزول (Auth Gate)
# ==========================================
def auth_gate():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.title("دخول منصة يقين AI – إصدار الصحافة الاحترافية")

        pwd = st.text_input("مفتاح الوصول:", type="password")

        if st.button("فتح النظام"):
            if pwd == ACCESS_PASSWORD:
                loading_screen("جاري فتح المنصة الصحفية...")
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("مفتاح الوصول غير صحيح")

        st.stop()

# استدعاء بوابة الدخول
auth_gate()

# ==========================================
# 2. محرك الهندسة التحريرية
# ==========================================
def run_samba_writer(text, tone, keyword):
    try:
        client = OpenAI(
            api_key=st.secrets["SAMBANOVA_API_KEY"],
            base_url="https://api.sambanova.ai/v1",
        )

        prompt = f"""
أنت صحفي محترف نخبوّي تكتب وفق معايير الصحافة المؤسسية الصارمة.

المطلوب:
إعادة صياغة النص بأسلوب صحفي احترافي صالح للنشر الورقي والرقمي.

قواعد إلزامية:
- المبني للمجهول لا يتجاوز 10%.
- طول الجملة لا يتجاوز 25 كلمة.
- تنويع بدايات الجمل (ممنوع التكرار المتتالي).
- إدراج عناوين فرعية عند الانتقال بين الزوايا.
- العنوان الرئيسي يبدأ بالكلمة المفتاحية: {keyword}.
- لغة خبرية رصينة، مبني للمعلوم، فاعل واضح.

أسلوب المقال: {tone}
الكلمة المفتاحية: {keyword}

النص الأصلي:
{text[:4500]}
"""

        response = client.chat.completions.create(
            model="Meta-Llama-3.3-70B-Instruct",
            messages=[
                {"role": "system", "content": "أنت كاتب صحفي محترف جداً بلغة عربية رصينة."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            top_p=0.9
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"خطأ تقني في محرك الصياغة: {str(e)}"

# ==========================================
# 3. المصادر الإخبارية
# ==========================================
RSS_SOURCES = {
    "الصحافة الوطنية 🇲🇦": {
        "هسبريس": "https://www.hespress.com/feed",
        "هبة بريس": "https://ar.hibapress.com/feed",
        "العمق المغربي": "https://al3omk.com/feed"
    }
}

# ==========================================
# 4. الواجهة
# ==========================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
html, body, [class*="st-"] {
    font-family: 'Cairo', sans-serif;
    direction: rtl;
    text-align: right;
}
.article-output {
    white-space: pre-wrap;
    background-color: #ffffff;
    padding: 40px;
    border-radius: 20px;
    border: 1px solid #eee;
    line-height: 2.2;
    font-size: 1.2rem;
    text-align: justify;
}
</style>
""", unsafe_allow_html=True)

st.title("يقين AI – منصة الصياغة الصحفية الاحترافية")

if os.path.exists(DB_FILE):
    with open(DB_FILE, "r", encoding="utf-8") as f:
        db = json.load(f)
else:
    db = {"data": {}}

tabs = st.tabs(list(RSS_SOURCES.keys()))

for i, cat in enumerate(RSS_SOURCES.keys()):
    with tabs[i]:
        if st.button("تحديث الأخبار", key=f"up_{i}"):
            loading_screen("جاري جلب الأخبار...")
            all_news = []

            def fetch_feed(name, url):
                try:
                    d = feedparser.parse(url)
                    return [{"title": e.title, "link": e.link, "source": name} for e in d.entries[:10]]
                except:
                    return []

            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as exe:
                futures = [
                    exe.submit(fetch_feed, name, url)
                    for name, url in RSS_SOURCES[cat].items()
                ]
                for f in concurrent.futures.as_completed(futures):
                    all_news.extend(f.result())

            db["data"][cat] = all_news
            with open(DB_FILE, "w", encoding="utf-8") as f:
                json.dump(db, f, ensure_ascii=False)

            st.rerun()

        if cat in db["data"]:
            news = db["data"][cat]
            idx = st.selectbox(
                "اختر الخبر:",
                range(len(news)),
                format_func=lambda x: f"[{news[x]['source']}] {news[x]['title']}"
            )

            tone = st.selectbox("نبرة المقال:", ["تقرير صحفي احترافي", "تحليل استقصائي"])
            keyword = st.text_input("الكلمة المفتاحية:")

            if st.button("صياغة المقال"):
                loading_screen("جاري الصياغة الصحفية...")
                raw = trafilatura.fetch_url(news[idx]["link"])
                txt = trafilatura.extract(raw)

                if txt:
                    final = run_samba_writer(txt, tone, keyword)
                    st.markdown("<div class='article-output'>{}</div>".format(final), unsafe_allow_html=True)
                else:
                    st.error("تعذر استخراج النص من المصدر.")

st.markdown("---")
st.caption("يقين AI | إدارة الماندجر إلياس | إصدار 2026")
