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
# 0. إعدادات النظام والهوية (النسخة النهائية)
# ==========================================
SYSTEM_VERSION = "V14.0_FINAL_SEO" 
st.set_page_config(page_title="وكيل يقين الصحفي - Manadger Tech", page_icon="🗞️", layout="wide")
socket.setdefaulttimeout(20) 
DB_FILE = "news_db_v14.json"

# ==========================================
# 1. نظام التنظيف الذكي (3 صباحاً)
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
# 2. القائمة العملاقة للمصادر (45+ مصدر)
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
        "برلمان.كوم": "https://www.barlamane.com/feed",
        "الصباح": "https://assabah.ma/feed",
        "الأحداث المغربية": "https://ahdath.info/feed",
        "تليكسبريس": "https://telexpresse.com/feed",
        "Le360": "https://ar.le360.ma/rss",
        "فبراير": "https://www.febrayer.com/feed",
        "آشكاين": "https://achkayen.com/feed",
        "الجريدة 24": "https://aljarida24.ma/feed",
        "لكم": "https://lakome2.com/feed",
        "عبر": "https://aabbir.com/feed",
        "سفيركم": "https://safir24.com/feed",
        "باناصا": "https://banassa.com/feed"
    },
    "أخبار الشمال والجهات 🌊": {
        "شمال بوست": "https://chamalpost.net/feed",
        "بريس تطوان": "https://presstetouan.com/feed",
        "طنجة 24": "https://tanja24.com/feed",
        "تطوان بريس": "https://tetouanpress.ma/feed",
        "طنجة نيوز": "https://tanjanews.com/feed",
        "كاب 24": "https://cap24.tv/feed",
        "صدى تطوان": "https://sadatetouan.com/feed",
        "أكادير 24": "https://agadir24.info/feed",
        "مراكش الآن": "https://www.marrakechalaan.com/feed",
        "الجهة 24": "https://aljahia24.ma/feed"
    },
    "أخبار دولية واقتصاد 🌍": {
        "سكاي نيوز عربية": "https://www.skynewsarabia.com/rss/v1/middle-east.xml",
        "الجزيرة نت": "https://www.aljazeera.net/alritem/rss/rss.xml",
        "فرانس 24": "https://www.france24.com/ar/rss",
        "BBC عربي": "https://www.bbc.com/arabic/index.xml",
        "اقتصادكم": "https://www.economistcom.ma/feed",
        "المصدر ميديا": "https://almasdar.ma/feed",
        "انفستنغ": "https://sa.investing.com/rss/news.rss"
    },
    "فن، مشاهير ورياضة ⚽": {
        "البطولة": "https://www.elbotola.com/rss",
        "هسبريس رياضة": "https://hesport.com/feed",
        "المنتخب": "https://almountakhab.com/rss",
        "لالة مولاتي": "https://www.lallamoulati.ma/feed/",
        "سلطانة": "https://soltana.ma/feed",
        "غالية": "https://ghalia.ma/feed",
        "هاي كورة": "https://hihi2.com/feed"
    }
}

# ==========================================
# 3. CSS (واجهة الماندجر الاحترافية)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
    html, body, [class*="st-"] { font-family: 'Cairo', sans-serif; text-align: right; }
    .brand-header {
        text-align: center; background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        color: white; padding: 2rem; border-radius: 15px; margin-bottom: 2rem; border-bottom: 5px solid #3b82f6;
    }
    .article-output {
        white-space: pre-wrap; background-color: #ffffff; color: #111; padding: 30px; 
        border-radius: 12px; border: 1px solid #cfd8dc; line-height: 2; font-size: 1.15rem;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }
    .stButton>button { background: #1e3a8a; color: white; border-radius: 10px; height: 3.5rem; width: 100%; font-weight: bold; font-size: 18px; border: none; }
    .stButton>button:hover { background: #3b82f6; border: none; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. محرك الصياغة الذكي (يقين SEO Engine)
# ==========================================
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except: client = None

def rewrite_mega_pro(text, tone, instr):
    if not client: return "خطأ: يرجى إعداد مفتاح GROQ في ملف الأسرار (Secrets)"
    
    prompt = f"""
    أنت خبير صياغة عناوين ومحتوى رقمي متصدر (SEO Specialist). حوّل النص التالي إلى مقال صحفي احترافي.
    
    1. هندسة العنوان (الأولوية القصوى):
       - صغ عنواناً نصياً (بدون رموز نهائياً) يكون "مغناطيسياً" ويحفز على النقر بشكل كبير.
       - ضع الكلمة المفتاحية المستهدفة في بداية العنوان.
       - استخدم أسلوب العناوين المتصدرة (مثال: 'قرار مفاجئ يغير..', 'كل ما تريد معرفته عن..', 'تحذير عاجل بخصوص..').

    2. القيود الفنية واللغوية للمقال (Yoast SEO):
       - ممنوع استخدام رموز Markdown نهائياً (لا تستخدم ## أو ** أو * أو -).
       - التنسيق: العناوين الفرعية نصية واضحة في أسطر مستقلة.
       - الجمل قصيرة جداً (لا تتجاوز 18 كلمة لكل جملة).
       - استخدم "المبني للمعلوم" (Active Voice) وتجنب "المبني للمجهول".
       - الفقرات قصيرة جداً (3 أسطر بحد أقصى).
       - استخدم كلمات انتقال قوية (بالإضافة إلى، من جهة أخرى، وفي ذات السياق).

    الأسلوب: {tone}. الكلمة المفتاحية المستهدفة: {instr}.
    
    النص الأصلي:
    {text[:3800]}
    """
    
    try:
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile", temperature=0.4
        )
        return res.choices[0].message.content
    except Exception as e: return f"خطأ تقني: {str(e)}"

# ==========================================
# 5. الواجهة والمنطق (يقين الصحفي)
# ==========================================
st.markdown("<div class='brand-header'><h1>وكيل يقين الصحفي</h1><p>من مجموعة منادجر للتطوير وحلول الويب</p></div>", unsafe_allow_html=True)

def fetch_items(name, url):
    try:
        d = feedparser.parse(url)
        return [{"title": e.title, "link": e.link, "source": name} for e in d.entries[:10]]
    except: return []

if os.path.exists(DB_FILE):
    with open(DB_FILE, 'r', encoding='utf-8') as f: db = json.load(f)
else: db = {"data": {}}

tabs = st.tabs(list(RSS_SOURCES.keys()))
for i, cat in enumerate(list(RSS_SOURCES.keys())):
    with tabs[i]:
        col_up, col_sel = st.columns([1, 4])
        with col_up:
            if st.button(f"🔄 تحديث {cat}", key=f"btn_{i}"):
                with st.spinner("جاري مسح المصادر..."):
                    all_news = []
                    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as exec:
                        futures = [exec.submit(fetch_items, n, u) for n, u in RSS_SOURCES[cat].items()]
                        for f in concurrent.futures.as_completed(futures): all_news.extend(f.result())
                    db["data"][cat] = all_news
                    with open(DB_FILE, 'w', encoding='utf-8') as f: json.dump(db, f, ensure_ascii=False)
                st.rerun()

        if cat in db["data"] and db["data"][cat]:
            news = db["data"][cat]
            choice = st.selectbox("اختر المقال المراد إعادة صياغته:", range(len(news)), format_func=lambda x: f"[{news[x]['source']}] {news[x]['title']}", key=f"sb_{i}")
            
            c1, c2 = st.columns(2)
            with c1: tone = st.selectbox("نبرة المقال:", ["تقرير إخباري رصين", "تحليل صحفي عميق", "تغطية تفاعلية سريعة"], key=f"tn_{i}")
            with c2: instr = st.text_input("الكلمة المفتاحية المستهدفة (SEO):", key=f"kw_{i}")

            if st.button("🚀 هندسة وصياغة المقال", key=f"go_{i}"):
                with st.status("🏗️ جاري معالجة العنوان والمحتوى بمعايير SEO...", expanded=True):
                    raw = trafilatura.fetch_url(news[choice]['link'])
                    txt = trafilatura.extract(raw)
                    if txt:
                        final = rewrite_mega_pro(txt, tone, instr)
                        st.markdown("### ✅ المقال النهائي المنسق")
                        st.markdown(f"<div class='article-output'>{final}</div>", unsafe_allow_html=True)
                        st.text_area("نسخة النسخ المباشر لووردبريس:", final, height=400)
                    else: st.error("عذراً، هذا المصدر يمنع سحب المحتوى حالياً.")
        else:
            st.info("اضغط على زر التحديث لجلب آخر المقالات.")

st.markdown("---")
st.markdown("<p style='text-align:center; color:#666;'>وكيل يقين الصحفي - إصدار V14.0 - تطوير وحلول الماندجر</p>", unsafe_allow_html=True)
