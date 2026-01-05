import streamlit as st
import feedparser
import trafilatura
from openai import OpenAI
import concurrent.futures
import json
import os
import socket
from datetime import datetime

# ==========================================
# 0. الإعدادات والتحصين البرمجي (الماندجر V22.0)
# ==========================================
SYSTEM_VERSION = "V22.0_HUMAN_WRITER"
ACCESS_PASSWORD = "Manager_Tech_2026"
DB_FILE = "news_db_v22.json"

st.set_page_config(page_title="يقين AI |وكيل الدكاء الاصطناعي يقين الصحفي ", page_icon="✍️", layout="wide")
socket.setdefaulttimeout(40)

# ==========================================
# 1. محرك الهندسة اللغوية "البشرية" (The Human-Like Engine)
# ==========================================
def run_samba_writer(text, tone, keyword):
    try:
        client = OpenAI(
            api_key=st.secrets["SAMBANOVA_API_KEY"],
            base_url="https://api.sambanova.ai/v1",
        )
        
        # برومبت مطول جداً لوصف الأسلوب الصحفي البشري السلس
        prompt = f"""
        بصفتك رئيس تحرير صحفي متمرس، أعد صياغة النص التالي ليكون مقالاً صحفياً احترافياً يبدو وكأنه كُتب بيد بشرية بارعة.
        
        الكلمة المفتاحية المستهدفة: {keyword}
        
        الدليل التحريري الصارم (قواعد الماندجر إلياس):
        1. **الأسلوب البشري السلس:** ابتعد عن المفردات العربية القديمة أو الصعبة. استخدم لغة الصحافة العربية الحديثة (لغة بي بي سي عربي، والجزيرة نت، وهسبريس). يجب أن يكون النص منساباً، سهلاً، وواضحاً للقارئ العادي دون فقدان الرصانة.
        2. **قوة "الفاعل":** التزم بأن يكون أكثر من 90% من النص "مبني للمعلوم". (قل: كشفت الهيئة، أعلن المصدر، أكدت التقارير) بدلاً من (يُذكر، تَم الكشف، قيل). نريد نصاً حيوياً ونشطاً.
        3. **توزيع العناوين:** إذا كان المقال طويلاً، استخدم عناوين فرعية جذابة (H2) في أماكن منطقية لراحة العين، لكن باعتدال (عنوان فرعي كل 3 أو 4 فقرات).
        4. **التنفس اللغوي (الفواصل):** لا تستخدم النقاط بكثرة لتقطيع الكلام. استخدم الفواصل (،) وحروف العطف بذكاء لربط الأفكار في جمل طويلة النفس ومريحة في القراءة، مما يمنح المقال "دسامة" فكرية وتدفقاً بشرياً.
        5. **الروابط اللغوية العصرية:** استخدم روابط سلسة (وفي هذا الصدد، ومن جهة أخرى، وفي سياق ذي صلة، وبناءً على هذه التطورات، ولعل المثير للاهتمام هو..).
        6. **منع التكرار (Zero Redundancy):** ادمج المعلومات المتشابهة واحذف الحشو. المقال يجب أن يطور فكرته في كل سطر جديد دون العودة للوراء.
        7. **هندسة السيو (SEO):** عنوان المقال يجب أن يكون جذاباً جداً وبشرياً (ليس آلياً) ويبدأ بالكلمة المفتاحية ({keyword}).
        8. **تنبيه نهائي:** ممنوع استخدام رموز Markdown مثل النجوم (**) أو الهاشتاغ (##) داخل النص. المقال يجب أن يكون نصياً صافياً وجاهزاً للنشر المباشر.

        الأسلوب المطلوب: {tone}. الكلمة المفتاحية: {keyword}.
        النص الأصلي للمعالجة:
        {text[:4500]}
        """

        response = client.chat.completions.create(
            model='Meta-Llama-3.3-70B-Instruct', 
            messages=[
                {"role": "system", "content": "أنت صحفي محترف تكتب بلغة عربية سلسة وعصرية بعيداً عن التعقيد."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6, # رفع الحرارة لزيادة "الانسيابية البشرية"
            top_p=0.9
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"عذراً إلياس، حدث خطأ في محرك SambaNova: {str(e)}"

# ==========================================
# 2. نظام الدخول والحماية
# ==========================================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown("<h2 style='text-align:center;'>🔐 دخول منصة يقين AI - الإصدار البشري</h2>", unsafe_allow_html=True)
    pwd = st.text_input("مفتاح الوصول:", type="password")
    if st.button("فتح النظام"):
        if pwd == ACCESS_PASSWORD:
            st.session_state["authenticated"] = True
            st.rerun()
        else: st.error("المفتاح غير صحيح")
    st.stop()

# ==========================================
# 3. المصادر والجرائد (58 مصدراً - خط أحمر + إضافات)
# ==========================================
RSS_SOURCES = {
    "الصحافة الوطنية 🇲🇦": {
        "هسبريس": "https://www.hespress.com/feed", "شوف تيفي": "https://chouftv.ma/feed",
        "العمق المغربي": "https://al3omk.com/feed", "زنقة 20": "https://www.rue20.com/feed",
        "هبة بريس": "https://ar.hibapress.com/feed", "اليوم 24": "https://alyaoum24.com/feed",
        "كود": "https://www.goud.ma/feed", "Le360": "https://ar.le360.ma/rss",
        "فبراير": "https://www.febrayer.com/feed", "آشكاين": "https://achkayen.com/feed",
        "الجريدة 24": "https://aljarida24.ma/feed", "لكم": "https://lakome2.com/feed",
        "عبر": "https://aabbir.com/feed", "سفيركم": "https://safir24.com/feed",
        "باناصا": "https://banassa.com/feed", "الأيام 24": "https://www.alayam24.com/feed",
        "برلمان.كوم": "https://www.barlamane.com/feed", "تليكسبريس": "https://telexpresse.com/feed",
        "الصباح": "https://assabah.ma/feed", "الأحداث المغربية": "https://ahdath.info/feed",
        "مدار 21 (جديد)": "https://madar21.com/feed", "كيوسك أنفو (جديد)": "https://kiosqueinfo.ma/feed"
    },
    "أخبار الشمال والجهات 🌊": {
        "شمال بوست": "https://chamalpost.net/feed", "بريس تطوان": "https://presstetouan.com/feed",
        "طنجة 24": "https://tanja24.com/feed", "تطوان بريس": "https://tetouanpress.ma/feed",
        "طنجة نيوز": "https://tanjanews.com/feed", "كاب 24": "https://cap24.tv/feed",
        "صدى تطوان": "https://sadatetouan.com/feed", "أكادير 24": "https://agadir24.info/feed",
        "مراكش الآن": "https://www.marrakechalaan.com/feed", "ناظور سيتي": "https://www.nadorcity.com/rss/",
        "دوزيم": "https://2m.ma/ar/news/rss.xml", "ماب إكسبريس": "https://www.mapexpress.ma/ar/feed/",
        "الجهة 24": "https://aljahia24.ma/feed", "فاس نيوز": "https://fesnews.media/feed",
        "ريف بوست": "https://rifpost.com/feed", "تطوان نيوز (جديد)": "https://tetouannews.com/feed"
    },
    "دولية واقتصاد 🌍": {
        "سكاي نيوز": "https://www.skynewsarabia.com/rss/v1/middle-east.xml",
        "الجزيرة": "https://www.aljazeera.net/alritem/rss/rss.xml",
        "فرانس 24": "https://www.france24.com/ar/rss",
        "BBC عربي": "https://www.bbc.com/arabic/index.xml",
        "اقتصادكم": "https://www.economistcom.ma/feed",
        "انفستنغ": "https://sa.investing.com/rss/news.rss",
        "العربية": "https://www.alarabiya.net/.mrss/ar/last-24-hours.xml",
        "RT عربي": "https://arabic.rt.com/rss/",
        "الشرق للأخبار (جديد)": "https://asharq.com/feed/"
    },
    "رياضة وفن ⚽": {
        "البطولة": "https://www.elbotola.com/rss", "هسبريس رياضة": "https://hesport.com/feed",
        "المنتخب": "https://almountakhab.com/rss", "لالة مولاتي": "https://www.lallamoulati.ma/feed/",
        "سلطانة": "https://soltana.ma/feed", "غالية": "https://ghalia.ma/feed",
        "هاي كورة": "https://hihi2.com/feed", "في الجول": "https://www.filgoal.com/rss",
        "كووورة (جديد)": "https://www.kooora.com/rss.xml"
    }
}

# ==========================================
# 4. الواجهة والتنسيق (Premium UI)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
    html, body, [class*="st-"] { font-family: 'Cairo', sans-serif; text-align: right; direction: rtl; }
    .article-output { white-space: pre-wrap; background-color: #ffffff; padding: 40px; border-radius: 20px; border: 1px solid #eee; line-height: 2.3; font-size: 1.3rem; text-align: justify; box-shadow: 0 10px 30px rgba(0,0,0,0.05); }
    .stButton>button { background: linear-gradient(90deg, #1e3a8a, #3b82f6); color: white; height: 3.8rem; border-radius: 12px; font-weight: 900; width: 100%; border: none; }
</style>
""", unsafe_allow_html=True)

st.title("🦅 يقين AI | وكيل الدكاء الاصطناعي يقين الصحفي  V2.0")

if os.path.exists(DB_FILE):
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f: db = json.load(f)
    except: db = {"data": {}}
else: db = {"data": {}}

tabs = st.tabs(list(RSS_SOURCES.keys()))
for i, cat in enumerate(list(RSS_SOURCES.keys())):
    with tabs[i]:
        if st.button(f"🔄 تحديث شامل لـ {cat}", key=f"up_{i}"):
            with st.spinner("جاري جلب المصادر الـ 58..."):
                all_news = []
                def fetch_t(n, u):
                    try:
                        d = feedparser.parse(u)
                        return [{"title": e.title, "link": e.link, "source": n} for e in d.entries[:10]]
                    except: return []
                with concurrent.futures.ThreadPoolExecutor(max_workers=30) as exec:
                    futures = [exec.submit(fetch_t, name, url) for name, url in RSS_SOURCES[cat].items()]
                    for f in concurrent.futures.as_completed(futures): all_news.extend(f.result())
                db["data"][cat] = all_news
                with open(DB_FILE, 'w', encoding='utf-8') as f: json.dump(db, f, ensure_ascii=False)
            st.rerun()

        if cat in db["data"] and db["data"][cat]:
            news_list = db["data"][cat]
            choice = st.selectbox("اختر الخبر الأساسي للمقال:", range(len(news_list)), format_func=lambda x: f"[{news_list[x]['source']}] {news_list[x]['title']}", key=f"sel_{i}")
            c1, c2 = st.columns(2)
            with c1: tone = st.selectbox("نبرة المقال:", ["تقرير صحفي سلس", "تحقيق بشري معمق"], key=f"tn_{i}")
            with c2: keyword = st.text_input("الكلمة المفتاحية (SEO):", key=f"kw_{i}")

            if st.button("🚀 صياغة المقال الآن", key=f"run_{i}"):
                with st.spinner("جاري الكتابة بنَفَس صحفي بشري..."):
                    raw = trafilatura.fetch_url(news_list[choice]['link'])
                    txt = trafilatura.extract(raw)
                    if txt:
                        final = run_samba_writer(txt, tone, keyword)
                        st.markdown("### ✅ المقال النهائي (أسلوب بشري)")
                        st.markdown(f"<div class='article-output'>{final}</div>", unsafe_allow_html=True)
                        st.text_area("للنسخ المباشر:", final, height=500)
                    else: st.error("المصدر يرفض السحب.")
        else: st.info("اضغط تحديث لتفعيل المصادر.")

st.markdown("---")
st.caption("يقين V22.0 - إدارة الماندجر إلياس - أسلوب بشري سلس 2026")
