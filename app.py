def rewrite_seo_architect(text, tone, keyword):
    if not client: return "خطأ في الاتصال"
    
    prompt = f"""
    أنت رئيس تحرير جريدة مشهورة وخبير في تحسين محركات البحث (SEO). 
    حول النص "الجامد" التالي إلى مقال صحفي "نابض بالحياة" يثير حماس القراء.
    
    الكلمة المفتاحية: {keyword}
    
    القواعد الذهبية (التزام صارم):
    1. العنوان: صغ عنواناً "انفجارياً" يحبس الأنفاس، يتضمن الكلمة المفتاحية، ويعد القارئ بكشف أسرار. (بدون رموز Markdown).
    2. الأسلوب القصصي: لا تسرد حقائق فقط، بل اصنع قصة. استخدم أفعالاً قوية (يفجر، يكشف، يزلزل، يقود).
    3. كلمات الانتقال الذكية: نوع في روابط الجمل (بالموازاة مع ذلك، وفي غمرة هذا النجاح، ولم يقف الأمر عند هذا الحد، بل تجاوزه إلى..).
    4. معايير Yoast SEO: 
       - جمل قصيرة ورشيقة.
       - مبني للمعلوم (اجعل الفنانين هم الأبطال في الجمل).
       - الكلمة المفتاحية في أول المقال وفي العناوين الفرعية.
    5. التنسيق: عناوين فرعية مثيرة بدون رموز.
    
    الأسلوب: {tone}. الكلمة المفتاحية: {keyword}.
    النص الأصلي: {text}
    """
    try:
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile", 
            temperature=0.6 # رفع الحرارة قليلاً لزيادة الإبداع اللغوي
        )
        return res.choices[0].message.content
    except Exception as e: return str(e)                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error("❌ المفتاح غير صحيح")
        return False
    return True

# ==========================================
# 2. محرك الصياغة الهندسي (SEO ARCHITECT)
# ==========================================
try:
    if "GROQ_API_KEY" in st.secrets:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    else:
        client = None
except:
    client = None

def rewrite_seo_architect(text, tone, keyword):
    if not client: 
        return "خطأ: تأكد من إضافة مفتاح API في Secrets باسم GROQ_API_KEY"
    
    # تحسين الـ Prompt لمنع الكلمات الواصفة مثل "مغناطيسياً"
    prompt = f"""
    بصفتك خبير محتوى رقمي ومتخصص في Yoast SEO، أعد صياغة النص التالي لتحويله إلى مقال صحفي احترافي متكامل.
    الكلمة المفتاحية المستهدفة: {keyword}
    
    الخطة الهندسية للمقال:
    1. العنوان الرئيسي: صغ عنواناً قوياً ومثيراً للاهتمام يتصدر نتائج البحث ويبدأ بالكلمة المفتاحية. 
       (مهم: لا تكتب كلمات واصفة مثل 'مغناطيسياً' أو 'جذاب' في العنوان، فقط صغ العنوان بأسلوب قوي).
    2. المقدمة: فقرة افتتاحية مكثفة تحتوي الكلمة المفتاحية وتلخص الحدث بقوة.
    3. العناوين الفرعية: قسّم المقال بعناوين نصية واضحة في أسطر مستقلة بدون رموز Markdown.
    4. معايير Yoast SEO للقراءة: 
       - استخدم كلمات انتقال بكثافة (علاوة على ذلك، ومن جهة أخرى، وفي سياق متصل).
       - الجمل قصيرة جداً (أقل من 18 كلمة لكل جملة).
       - استخدم المبني للمعلوم (Active Voice) وتجنب 'تم' وأخواتها.
       - الفقرات قصيرة (3 أسطر بحد أقصى).
    
    الأسلوب المطلوب: {tone}.
    النص الأصلي للمعالجة:
    {text[:3800]}
    """
    try:
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile", 
            temperature=0.4
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"خطأ تقني: {str(e)}"

# ==========================================
# 3. تشغيل السكربت بعد التحقق
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

    st.markdown("<div style='text-align: center; background: #1e3a8a; color: white; padding: 1rem; border-radius: 10px; margin-bottom: 2rem;'><h1>وكيل يقين الصحفي - خبير SEO</h1></div>", unsafe_allow_html=True)

    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            db = json.load(f)
    else:
        db = {"data": {}}

    tabs = st.tabs(list(RSS_SOURCES.keys()))
    for i, cat in enumerate(list(RSS_SOURCES.keys())):
        with tabs[i]:
            if st.button(f"🔄 تحديث {cat}", key=f"up_{i}"):
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
                    with open(DB_FILE, 'w', encoding='utf-8') as f:
                        json.dump(db, f, ensure_ascii=False)
                st.rerun()

            if cat in db["data"] and db["data"][cat]:
                news_list = db["data"][cat]
                choice = st.selectbox("اختر المقال:", range(len(news_list)), format_func=lambda x: f"[{news_list[x]['source']}] {news_list[x]['title']}", key=f"sel_{i}")
                
                c1, c2 = st.columns(2)
                with c1:
                    tone = st.selectbox("الأسلوب:", ["تحقيق صحفي رصين", "تقرير إخباري سريع", "تحليل تفاعلي"], key=f"tn_{i}")
                with c2:
                    keyword = st.text_input("الكلمة المفتاحية المستهدفة (SEO):", key=f"kw_{i}")

                if st.button("🚀 توليد مقال احترافي متصدر", key=f"run_{i}"):
                    with st.status("🏗️ جاري بناء المقال وفق معايير Yoast SEO...", expanded=True):
                        raw = trafilatura.fetch_url(news_list[choice]['link'])
                        txt = trafilatura.extract(raw)
                        if txt:
                            final_content = rewrite_seo_architect(txt, tone, keyword)
                            st.markdown("### ✅ المقال النهائي المنسق")
                            st.markdown(f"<div class='article-output'>{final_content}</div>", unsafe_allow_html=True)
                            st.text_area("نسخة النشر المباشر:", final_content, height=450)
                        else:
                            st.error("المصدر يمنع السحب التلقائي.")
            else:
                st.info("اضغط تحديث لجلب البيانات.")

    st.markdown("---")
    st.markdown("<p style='text-align:center; color:#666;'>وكيل يقين الصحفي V16.1 - تطوير وحلول الماندجر</p>", unsafe_allow_html=True)
