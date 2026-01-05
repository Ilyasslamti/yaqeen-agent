import streamlit as st
import feedparser
import trafilatura
import json
import os
import socket
import concurrent.futures
from openai import OpenAI
from duckduckgo_search import DDGS

# استيراد الترسانة من المكتبة
try:
    from manadger_lib import RSS_DATABASE, get_safe_key, ELITE_PROMPT
except ImportError:
    st.error("❌ خطأ: ملف manadger_lib.py مفقود.")
    st.stop()

# ==========================================
# 0. الإعدادات والتحصين
# ==========================================
ACCESS_PASSWORD = "Manager_Tech_2026"
DB_FILE = "news_db_v27.json"
socket.setdefaulttimeout(40)

st.set_page_config(page_title="الماندجر تك | رادار السيادة", page_icon="🛡️", layout="wide")

# ==========================================
# 1. محرك البحث عن الصور
# ==========================================
def get_related_images(query):
    try:
        with DDGS() as ddgs:
            results = ddgs.images(query, region="wt-wt", safesearch="off", max_results=3)
            return [r['image'] for r in results]
    except: return []

# ==========================================
# 2. محرك الصياغة النخبوية
# ==========================================
def run_samba_writer(text, keyword):
    api_key = get_safe_key()
    if not api_key: return "⚠️ خطأ في المفاتيح."

    try:
        client = OpenAI(api_key=api_key, base_url="https://api.sambanova.ai/v1")
        
        # هندسة البرومبت
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
        
        # الفلتر السيادي: إزالة أي بادئات زائدة مع الحفاظ على العنوان
        clean_article = raw_article.replace("هاشمي بريس:", "").replace("هاشمي بريس :", "").replace("العنوان:", "").strip()
        return clean_article

    except Exception as e: return f"❌ خطأ: {str(e)}"

# ==========================================
# 3. نظام الدخول والحماية
# ==========================================
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown("<h2 style='text-align:center;'>🔐 الماندجر تك | دخول الترسانة</h2>", unsafe_allow_html=True)
    pwd = st.text_input("مفتاح الوصول:", type="password")
    if st.button("فتح النظام"):
        if pwd == ACCESS_PASSWORD:
            st.session_state["authenticated"] = True
            st.rerun()
        else: st.error("المفتاح خاطئ")
    st.stop()

# ==========================================
# 4. التنسيق والواجهة (Premium UI)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
    html, body, [class*="st-"] { font-family: 'Cairo', sans-serif; text-align: right; direction: rtl; }
    .article-output { white-space: pre-wrap; background-color: white; padding: 30px; border-radius: 12px; border: 1px solid #ddd; line-height: 2.1; font-size: 1.2rem; }
    .stButton>button { background: linear-gradient(90deg, #0f172a, #1e3a8a); color: white; border-radius: 10px; font-weight: 700; width: 100%; border: none; height: 3.5rem; }
</style>
""", unsafe_allow_html=True)

st.title("🛡️ الماندجر تك | رادار السيادة الشامل")

# تحميل قاعدة البيانات
if os.path.exists(DB_FILE):
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f: db = json.load(f)
    except: db = {"data": {}}
else: db = {"data": {}}

# ==========================================
# 5. التبويبات والتشغيل
# ==========================================
tabs = st.tabs(list(RSS_DATABASE.keys()))

for i, cat in enumerate(list(RSS_DATABASE.keys())):
    with tabs[i]:
        if st.button(f"🔄 تحديث ترسانة {cat}", key=f"up_{i}"):
            with st.spinner("جاري المسح المتوازي..."):
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
            selected_idx = st.selectbox("اختر الخبر:", range(len(news_list)), format_func=lambda x: f"[{news_list[x]['source']}] {news_list[x]['title']}", key=f"sel_{i}")
            keyword_input = st.text_input("الكلمة المفتاحية (SEO):", key=f"kw_{i}", placeholder="مثال: تطوان، عاجل...")

            if st.button("🚀 صياغة بأسلوب هاشمي بريس", key=f"run_{i}"):
                final_keyword = keyword_input.strip() if keyword_input.strip() != "" else "هاشمي بريس"
                with st.spinner("جاري هندسة المقال..."):
                    raw_data = trafilatura.fetch_url(news_list[selected_idx]['link'])
                    main_text = trafilatura.extract(raw_data)
                    if main_text:
                        article = run_samba_writer(main_text, final_keyword)
                        
                        # تمييز العنوان عن المتن
                        lines = article.split('\n')
                        headline = lines[0]
                        body = "\n".join(lines[1:])
                        
                        st.markdown(f"<h2 style='color: #1e3a8a; text-align: center;'>{headline}</h2>", unsafe_allow_html=True)
                        st.markdown(f"<div class='article-output'>{body}</div>", unsafe_allow_html=True)
                        
                        # جلب الصور بناءً على العنوان
                        st.markdown("### 🖼️ الصور المقترحة")
                        images = get_related_images(headline)
                        if images:
                            cols = st.columns(len(images))
                            for idx, img_url in enumerate(images):
                                with cols[idx]: st.image(img_url, use_container_width=True)
                        
                        st.text_area("نسخة النشر الصافية:", article, height=300)
                    else: st.error("فشل في سحب النص.")
