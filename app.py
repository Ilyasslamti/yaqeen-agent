import streamlit as st
import feedparser
import trafilatura
import json
import os
import socket
import concurrent.futures
from openai import OpenAI
from duckduckgo_search import DDGS

# استيراد الترسانة والمنطق البرمجي من مكتبة الماندجر
try:
    from manadger_lib import RSS_DATABASE, get_safe_key, ELITE_PROMPT
except ImportError:
    st.error("❌ خطأ: لم يتم العثور على ملف manadger_lib.py في نفس المجلد.")
    st.stop()

# ==========================================
# 0. الإعدادات والتحصين (Manager Tech V27.7)
# ==========================================
ACCESS_PASSWORD = "Manager_Tech_2026"
DB_FILE = "news_db_v27.json"
socket.setdefaulttimeout(40)

st.set_page_config(
    page_title="الماندجر تك | رادار السيادة الشامل",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 1. محرك البحث عن الصور (Image Finder)
# ==========================================
def get_related_images(query):
    try:
        with DDGS() as ddgs:
            results = ddgs.images(query, region="wt-wt", safesearch="off", max_results=3)
            return [r['image'] for r in results]
    except:
        return []

# ==========================================
# 2. محرك الصياغة النخبوية (SambaNova Core)
# ==========================================
def run_samba_writer(text, keyword):
    api_key = get_safe_key()
    if not api_key:
        return "⚠️ خطأ: لم يتم العثور على مفاتيح API في Secrets الكلاود."

    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.sambanova.ai/v1",
        )
        
        # هندسة البرومبت: حقن النص والكلمة المفتاحية
        formatted_prompt = ELITE_PROMPT.format(keyword=keyword) + f"\n\nالمحتوى الخام:\n{text[:4500]}"
        
        response = client.chat.completions.create(
            model='Meta-Llama-3.3-70B-Instruct', 
            messages=[
                {"role": "system", "content": "محرر صحفي نخبوي - الماندجر تك"},
                {"role": "user", "content": formatted_prompt}
            ],
            temperature=0.4,
            top_p=0.9
        )
        
        raw_article = response.choices[0].message.content
        
        # --- الفلتر السيادي: إزالة "هاشمي بريس:" من بداية المقال ---
        clean_article = raw_article.replace("هاشمي بريس:", "").replace("هاشمي بريس :", "").strip()
        return clean_article

    except Exception as e:
        return f"❌ خطأ تقني في المحرك: {str(e)}"

# ==========================================
# 3. نظام الدخول والحماية
# ==========================================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown("<h2 style='text-align:center;'>🔐 نظام السيادة المعلوماتية | الماندجر تك</h2>", unsafe_allow_html=True)
    pwd = st.text_input("مفتاح الوصول القيادي:", type="password")
    if st.button("فتح الترسانة"):
        if pwd == ACCESS_PASSWORD:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("المفتاح غير صحيح")
    st.stop()

# ==========================================
# 4. التنسيق والجمالية (Premium UI)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
    html, body, [class*="st-"] { font-family: 'Cairo', sans-serif; text-align: right; direction: rtl; }
    .article-output { white-space: pre-wrap; background-color: #ffffff; padding: 35px; border-radius: 15px; border: 1px solid #e2e8f0; line-height: 2.2; font-size: 1.25rem; text-align: justify; color: #1e293b; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
    .stButton>button { background: linear-gradient(90deg, #0f172a, #1e3a8a); color: white; height: 3.8rem; border-radius: 12px; font-weight: 700; width: 100%; border: none; transition: 0.3s; }
    .stButton>button:hover { opacity: 0.9; transform: scale(1.01); }
</style>
""", unsafe_allow_html=True)

st.title("🛡️ الماندجر تك | الرادار الصحفي الشامل")
st.caption("الإصدار V27.7 - إدارة هاشمي بريس بـ 200 مصدر و26 محركاً دواراً")

# تحميل قاعدة البيانات المحلية
if os.path.exists(DB_FILE):
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f: db = json.load(f)
    except: db = {"data": {}}
else: db = {"data": {}}

# ==========================================
# 5. التبويبات والتشغيل الميداني
# ==========================================
tabs = st.tabs(list(RSS_DATABASE.keys()))

for i, cat in enumerate(list(RSS_DATABASE.keys())):
    with tabs[i]:
        if st.button(f"🔄 تحديث شامل لـ {cat}", key=f"up_{i}"):
            with st.spinner(f"جاري مسح المصادر..."):
                all_news = []
                def fetch_task(name, url):
                    try:
                        feed = feedparser.parse(url)
                        return [{"title": e.title, "link": e.link, "source": name} for e in feed.entries[:10]]
                    except: return []
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
                    futures = [executor.submit(fetch_task, n, u) for n, u in RSS_DATABASE[cat].items()]
                    for f in concurrent.futures.as_completed(futures):
                        all_news.extend(f.result())
                
                db["data"][cat] = all_news
                with open(DB_FILE, 'w', encoding='utf-8') as f:
                    json.dump(db, f, ensure_ascii=False)
            st.rerun()

        if cat in db["data"] and db["data"][cat]:
            news_list = db["data"][cat]
            selected_idx = st.selectbox(
                "اختر الخبر الخام لمباشرة المعالجة:", 
                range(len(news_list)), 
                format_func=lambda x: f"[{news_list[x]['source']}] {news_list[x]['title']}",
                key=f"sel_{i}"
            )
            
            keyword_input = st.text_input("الكلمة المفتاحية للعنوان (SEO) - اختياري:", key=f"kw_{i}", placeholder="مثال: تطوان، اقتصاد، عاجل...")

            if st.button("🚀 هندسة وصياغة بأسلوب هاشمي بريس", key=f"run_{i}"):
                final_keyword = keyword_input.strip() if keyword_input.strip() != "" else "هاشمي بريس"
                
                with st.spinner("الماندجر يحلل المحتوى ويطبق معايير النخبة..."):
                    raw_data = trafilatura.fetch_url(news_list[selected_idx]['link'])
                    main_text = trafilatura.extract(raw_data)
                    
                    if main_text:
                        article = run_samba_writer(main_text, final_keyword)
                        
                        st.markdown("### ✅ المقال الاستراتيجي الجاهز")
                        st.markdown(f"<div class='article-output'>{article}</div>", unsafe_allow_html=True)
                        
                        new_title = article.split('\n')[0]
                        st.markdown("---")
                        st.markdown("### 🖼️ الصور المقترحة للمقال")
                        images = get_related_images(new_title)
                        if images:
                            cols = st.columns(len(images))
                            for idx, img_url in enumerate(images):
                                with cols[idx]:
                                    st.image(img_url, use_container_width=True, caption=f"خيار {idx+1}")
                        
                        st.text_area("نسخة النشر الصافية:", article, height=350)
                    else:
                        st.error("فشل في استخلاص النص.")
        else:
            st.info("اضغط على 'تحديث شامل' لتفعيل الرادار.")

st.sidebar.title("🛠️ لوحة تحكم الماندجر")
st.sidebar.success("الحالة: متصل بـ 26 مفتاحاً")
if st.sidebar.button("تسجيل الخروج"):
    st.session_state["authenticated"] = False
    st.rerun()
