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
# 0. إعدادات الهوية (إصدار الصحافة الاحترافية)
# ==========================================
SYSTEM_VERSION = "V24.0_ELITE_JOURNALISM"
ACCESS_PASSWORD = "Manager_Tech_2026"
DB_FILE = "news_db_v24.json"

st.set_page_config(page_title="يقين AI | الصحافة الاحترافية", page_icon="✒️", layout="wide")
socket.setdefaulttimeout(40)

# ==========================================
# 1. محرك الهندسة التحريرية (The Journalist Engine)
# ==========================================
def run_samba_writer(text, tone, keyword):
    try:
        client = OpenAI(
            api_key=st.secrets["SAMBANOVA_API_KEY"],
            base_url="https://api.sambanova.ai/v1",
        )
        
       برومت الصياغة الصحفية النخبوية المنضبطة (نسخة مُصحَّحة تقنيًا)

المهمة:
أعد صياغة النص بأسلوب صحفي احترافي نخبوّي، صالح للنشر في جريدة ورقية ومواقع إخبارية كبرى، مع الالتزام الصارم بالقواعد التالية دون أي اجتهاد خارجها:

1. النفس التحريري المتوازن

اكتب بجمل مركبة ومترابطة، لكن دون إفراط.

الحد الأقصى لطول الجملة: 25 كلمة.

امزج بين الجمل الطويلة والمتوسطة لتفادي الإرهاق القرائي.

يُمنع تكديس أكثر من 3 أفكار داخل الجملة الواحدة.

2. منع المبني للمجهول (قاعدة صارمة)

يجب ألا تتجاوز نسبة المبني للمجهول 10% كحد أقصى.

كل جملة خبرية يجب أن تحتوي على فاعل واضح وصريح.

استخدم أفعالًا مباشرة مثل:
شهدت، أطلقت، باشرت، نظمت، انخرطت، بادر، عملت، أكدت، وسعت، جددت.

يُمنع استعمال صيغ مثل: تم، جرى، يتم، تم تسجيل، تم تنظيم، تم الإعلان.

3. تنويع بدايات الجمل (قاعدة إلزامية)

يُمنع بدء أكثر من جملتين متتاليتين بنفس الكلمة أو التركيب.

نوّع بدايات الجمل بين:

ظرف زمان

ظرف مكان

فعل مباشر

جملة وصفية

تركيب سياقي (وفي هذا السياق، بالتوازي مع ذلك، من جهة أخرى…)

4. بنية الفقرة الصحفية

كل فقرة يجب أن تتكون من فكرة واحدة مكتملة.

تبدأ الفقرة بمدخل قوي واضح، وتُدعَّم بتفاصيل دقيقة دون حشو.

يمنع الانتقال بين أفكار غير مترابطة داخل نفس الفقرة.

5. اللغة الصحفية الحديثة

استخدم تعابير مهنية من قبيل:
وفي هذا السياق، فور وقوع الواقعة، حسب معطيات أولية، بالتوازي مع ذلك، وأسفر هذا الإجراء عن، ويعيد هذا المعطى إلى الواجهة.

6. العنوان الرئيسي (Headline – إجباري)

يبدأ بالكلمة المفتاحية {keyword}.

يكون طويلاً ووصفيًا ويعكس جوهر الحدث بدقة.

مثال:
{keyword} تعزز المخزون الجهوي من الدم وتوسع دائرة المشاركة المجتمعية

7. العناوين الفرعية (H2 – إلزامية)

يجب إدراج عناوين فرعية نصية فقط عند كل انتقال زاوية.

الحد الأدنى: 3 عناوين فرعية إذا كان النص طويلاً.

أمثلة:
انخراط السلطات المحلية
الأهداف الصحية للحملة
توسيع نطاق التبرع عبر المحطات المتنقلة

8. نظافة النص

يمنع منعًا باتًا استعمال:
النجوم، الهاشتاغات، الإيموجي، الأقواس البرمجية، أو أي رموز.

النص يجب أن يكون صالحًا للطباعة في جريدة ورقية دون أي تعديل.

9. منع المقدمات الآلية

لا تستخدم عبارات مثل:
"إليك المقال"، "فيما يلي"، "هذه الصياغة".

ابدأ مباشرة بالعنوان ثم المتن الصحفي.
أسلوب الصياغة: {tone}  
الكلمة المفتاحية: {keyword}

النص الأصلي المراد إعادة صياغته:
{text[:4500]}
"""

        response = client.chat.completions.create(
            model='Meta-Llama-3.3-70B-Instruct', 
            messages=[
                {"role": "system", "content": "أنت كاتب صحفي محترف جداً تكتب بلغة عربية انسيابية ودسمة."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            top_p=0.9
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"خطأ تقني في الاتصال بمحرك SambaNova: {str(e)}"

# ==========================================
# 2. نظام الدخول والحماية
# ==========================================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown("<h2 style='text-align:center;'>🔐 دخول منصة يقين AI - إصدار الصحافة الاحترافية</h2>", unsafe_allow_html=True)
    pwd = st.text_input("مفتاح الوصول:", type="password")
    if st.button("فتح النظام"):
        if pwd == ACCESS_PASSWORD:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("المفتاح غير صحيح")
    st.stop()

# ==========================================
# 3. المصادر والجرائد (65 مصدراً - خط أحمر)
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
        "ناظور سيتي": "https://www.nadorcity.com/rss/",
        "دوزيم": "https://2m.ma/ar/news/rss.xml",
        "ماب إكسبريس": "https://www.mapexpress.ma/ar/feed/",
        "الجهة 24": "https://aljahia24.ma/feed",
        "فاس نيوز": "https://fesnews.media/feed",
        "ريف بوست": "https://rifpost.com/feed",
        "تطوان نيوز": "https://tetouannews.com/feed",
        "تارودانت نيوز": "https://taroudant-news.com/feed",
        "وجدة سيتي": "https://www.oujdacity.net/feed"
    },
    "دولية واقتصاد 🌍": {
        "سكاي نيوز": "https://www.skynewsarabia.com/rss/v1/middle-east.xml",
        "الجزيرة": "https://www.aljazeera.net/alritem/rss/rss.xml",
        "فرانس 24": "https://www.france24.com/ar/rss",
        "BBC عربي": "https://www.bbc.com/arabic/index.xml",
        "اقتصادكم": "https://www.economistcom.ma/feed",
        "انفستنغ": "https://sa.investing.com/rss/news.rss",
        "العربية": "https://www.alarabiya.net/.mrss/ar/last-24-hours.xml",
        "الشرق للأخبار": "https://asharq.com/feed/",
        "CNBC عربية": "https://www.cnbcarabia.com/rss.xml",
        "فرانس برس": "https://www.afp.com/ar/news/feed",
        "رويترز": "https://www.reutersagency.com/feed/"
    },
    "رياضة وفن ⚽": {
        "البطولة": "https://www.elbotola.com/rss",
        "هسبريس رياضة": "https://hesport.com/feed",
        "المنتخب": "https://almountakhab.com/rss",
        "لالة مولاتي": "https://www.lallamoulati.ma/feed/",
        "سلطانة": "https://soltana.ma/feed",
        "غالية": "https://ghalia.ma/feed",
        "هاي كورة": "https://hihi2.com/feed",
        "في الجول": "https://www.filgoal.com/rss",
        "كووورة": "https://www.kooora.com/rss.xml",
        "360 سبورت": "https://ar.sport.le360.ma/rss"
    }
}

# ==========================================
# 4. الواجهة والتنسيق (Premium UI)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
    html, body, [class*="st-"] { font-family: 'Cairo', sans-serif; text-align: right; direction: rtl; }
    .article-output { white-space: pre-wrap; background-color: #ffffff; padding: 40px; border-radius: 20px; border: 1px solid #eee; line-height: 2.3; font-size: 1.35rem; text-align: justify; box-shadow: 0 10px 30px rgba(0,0,0,0.05); }
    .stButton>button { background: linear-gradient(90deg, #1e3a8a, #3b82f6); color: white; height: 3.8rem; border-radius: 12px; font-weight: 900; width: 100%; border: none; }
</style>
""", unsafe_allow_html=True)

st.title("✒️ يقين AI | إصدار الصحافة الاحترافية V24.0")

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
        if st.button(f"🔄 تحديث شامل (65 مصدراً) لـ {cat}", key=f"up_{i}"):
            with st.spinner("جاري استحضار الترسانة الإعلامية..."):
                all_news = []

                def fetch_t(n, u):
                    try:
                        d = feedparser.parse(u)
                        return [{"title": e.title, "link": e.link, "source": n} for e in d.entries[:10]]
                    except:
                        return []

                with concurrent.futures.ThreadPoolExecutor(max_workers=35) as exec:
                    futures = [exec.submit(fetch_t, name, url) for name, url in RSS_SOURCES[cat].items()]
                    for f in concurrent.futures.as_completed(futures):
                        all_news.extend(f.result())

                db["data"][cat] = all_news
                with open(DB_FILE, 'w', encoding='utf-8') as f:
                    json.dump(db, f, ensure_ascii=False)
            st.rerun()

        if cat in db["data"] and db["data"][cat]:
            news_list = db["data"][cat]
            choice = st.selectbox(
                "اختر الخبر الأساسي:",
                range(len(news_list)),
                format_func=lambda x: f"[{news_list[x]['source']}] {news_list[x]['title']}",
                key=f"sel_{i}"
            )
            c1, c2 = st.columns(2)
            with c1:
                tone = st.selectbox(
                    "نبرة المقال:",
                    ["تقرير صحفي احترافي (أسلوب الماندجر)", "تحليل استقصائي رصين"],
                    key=f"tn_{i}"
                )
            with c2:
                keyword = st.text_input("الكلمة المفتاحية (SEO):", key=f"kw_{i}")

            if st.button("🚀 صياغة المقال الاستراتيجي", key=f"run_{i}"):
                with st.spinner("جاري الكتابة بنَفَس صحفي بشري..."):
                    raw = trafilatura.fetch_url(news_list[choice]['link'])
                    txt = trafilatura.extract(raw)
                    if txt:
                        final = run_samba_writer(txt, tone, keyword)
                        st.markdown("### ✅ المقال النهائي (أسلوب الصحافة النخبوية)")
                        st.markdown(f"<div class='article-output'>{final}</div>", unsafe_allow_html=True)
                        st.text_area("نسخة النشر المباشر:", final, height=500)
                    else:
                        st.error("المصدر يرفض السحب.")
        else:
            st.info("اضغط تحديث لتفعيل المصادر.")

st.markdown("---")
st.caption("يقين V24.0 - إدارة الماندجر إلياس - 65 مصدراً - أسلوب صحفي نخبوي 2026")
