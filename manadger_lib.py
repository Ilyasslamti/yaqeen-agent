# ==========================================
# manadger_lib.py - مستودع أسلحة الماندجر تك
# الإصدار: V33.0 (البرومبت النووي الشامل)
# ==========================================

import random
import streamlit as st

# 1. نظام تدوير المفاتيح
def get_safe_key():
    try:
        keys = st.secrets["API_KEYS"]
        return random.choice(keys)
    except:
        return None

# 2. برومبت "السيادة الشاملة" (The Masterpiece Prompt)
# تم تصميمه لإنتاج مقالات مهيكلة، قوية لغوياً، وصديقة لمحركات البحث بدقة مليمترية
ELITE_PROMPT = """الدور والصفة:

أنت تعمل بصفتك كبير الاستراتيجيين للمحتوى الرقمي ورئيس تحرير مخضرم في مؤسسة إعلامية ذات ثقل تحريري وتأثير جماهيري واسع.

تمتلك خبرة عميقة في الصحافة الرقمية، السرد الإخباري، تحسين محركات البحث (SEO)، وهندسة انتباه القارئ.

مهمتك هي تحويل النص الخام المُقدَّم إليك إلى عمل صحفي احترافي متكامل، يجمع بين الصياغة الرصينة، الجاذبية البصرية، والجاهزية القصوى لمحركات البحث.

أولاً: الخوارزمية البصرية للتحرير (Visual Flow Engineering)

قاعدة النقطة النهائية الإلزامية:
كل جملة مكتملة المعنى تنتهي بنقطة (.).
بعد كل نقطة، يجب النزول مباشرة إلى سطر جديد.
يمنع منعاً باتاً تكوين فقرات متصلة أو كتل نصية مغلقة.

إدارة التنفس البصري:
حافظ على مساحات بيضاء مريحة للعين.
المقال يجب أن يُقرأ بسهولة على الهاتف قبل الحاسوب.

الترابط الذكي:
استخدم الفواصل (،) لربط الأفكار داخل الجملة الواحدة.
لا تُطِل الجملة بشكل يُضعف وضوحها قبل الوصول للنقطة النهائية.

ثانياً: معايير السيو والدقة اللغوية (SEO & Linguistic Precision)

الكلمة المفتاحية:
استخدم الكلمة المفتاحية {keyword} ومرادفاتها الدلالية بشكل طبيعي وغير متكلف.
يجب أن تظهر في:

العنوان الرئيسي.

المقدمة.

المتن عند الحاجة السياقية.

الخاتمة.

المبني للمعلوم حصراً:
جميع الجمل يجب أن تكون بصيغة المبني للمعلوم مع فاعل واضح.
مثال:

مرفوض: تم اتخاذ القرار.

مقبول: اتخذت الجهات المختصة القرار.

سلامة اللغة:
النص النهائي يجب أن يكون خالياً تماماً من:

الأخطاء الإملائية.

الأخطاء النحوية.

الركاكة الأسلوبية.
نسبة الخطأ المقبولة: صفر بالمائة.

ثالثاً: الهيكل التحريري للمقال (Editorial Structure)

السطر الأول:
عنوان رئيسي (H1) احترافي.
يبدأ إلزامياً بـ {keyword}.
يكون طويلاً نسبياً، مثيراً للاهتمام، ويحمل قيمة خبرية أو تحليلية واضحة دون تهويل.

السطر الثاني:
سطر فارغ بالكامل.

المقدمة:
استهلال قوي يجيب بوضوح عن:
من؟
متى؟
أين؟
لماذا يهم هذا الخبر القارئ؟

المتن:
عرض التفاصيل بشكل متدرج ومنطقي.
كل جملة مستقلة في سطر منفصل بعد النقطة.
لا تكرار، لا حشو، لا خروج عن السياق.

الخاتمة:
قراءة تحليلية أو رؤية استشرافية لما بعد الحدث.
تُظهر عمق الفهم وليس إعادة تلخيص سطحية.

رابعاً: قائمة الممنوعات التحريرية (Strict Prohibitions)

يُمنع منعاً باتاً:

البدء بعبارات من قبيل:

«هاشمي بريس:»

«العنوان:»

استخدام العبارات الإنشائية الضعيفة أو المستهلكة، مثل:

يعتبر

يعد

مما لا شك فيه

الجدير بالذكر

كتابة فقرات طويلة متصلة دون فواصل بصرية.
(قاعدة السطر الجديد بعد كل نقطة غير قابلة للنقاش).

النتيجة المتوقعة:
مقال صحفي نظيف، قوي، قابل للأرشفة، جذاب للقارئ، ومُهيأ لاكتساح نتائج البحث دون التضحية بالقيمة التحريرية.
الكلمة المفتاحية المستهدفة: {keyword}
النص الخام للمعالجة:
"""

# 3. ترسانة الـ 200 مصدر (لم يتم المساس بها)
RSS_DATABASE = {
    "الصحافة السيادية والوطنية": {
        "هاشمي بريس": "https://hashemipress.com/feed/",
        "هسبريس": "https://www.hespress.com/feed",
        "وكالة المغرب العربي": "https://www.mapnews.ma/ar/rss.xml",
        "لوسيت أنفو": "https://ar.lesiteinfo.com/feed",
        "زنقة 20": "https://www.rue20.com/feed",
        "هبة بريس": "https://ar.hibapress.com/feed",
        "كود": "https://www.goud.ma/feed",
        "اليوم 24": "https://alyaoum24.com/feed",
        "العمق المغربي": "https://al3omk.com/feed",
        "مدار 21": "https://madar21.com/feed",
        "برلمان.كوم": "https://www.barlamane.com/feed",
        "تليكسبريس": "https://telexpresse.com/feed",
        "آشكاين": "https://achkayen.com/feed",
        "فبراير": "https://www.febrayer.com/feed",
        "الجريدة 24": "https://aljarida24.ma/feed",
        "لكم": "https://lakome2.com/feed",
        "سفيركم": "https://safir24.com/feed",
        "بناصا": "https://banassa.com/feed",
        "منارة": "https://www.menara.ma/ar/rss",
        "الصحراء المغربية": "https://assahra.ma/rss",
        "بيان اليوم": "https://bayanealyaoume.press.ma/feed",
        "الاتحاد الاشتراكي": "https://alittihad.press.ma/feed",
        "رسالة الأمة": "https://الرسالة.ma/feed",
        "بلادنا 24": "https://www.beladna24.ma/feed",
        "آذار": "https://aaddar.com/feed",
        "مشاهد": "https://mashahed.info/feed",
        "دوزيم": "https://2m.ma/ar/news/rss.xml",
        "ميد راديو": "https://medradio.ma/feed",
        "لوديسك": "https://ledesk.ma/ar/feed",
        "عبر": "https://aabbir.com/feed",
        "صوت المغرب": "https://saoutalmaghrib.ma/feed",
        "مغرب أنباء": "https://maghrebanbaa.ma/feed",
        "أكادير 24": "https://agadir24.info/feed",
        "كشـ 24": "https://kech24.com/feed",
        "الأيام 24": "https://www.alayam24.com/feed",
        "نون بريس": "https://www.noonpresse.com/feed",
        "سياسي": "https://www.siyasi.com/feed",
        "الأسبوع": "https://alaousboue.ma/feed",
        "أنفاس": "https://anfasspress.com/feed",
        "فلاش بريس": "https://www.flashpresse.ma/feed",
        "آخر خبر": "https://akharkhabar.ma/feed",
        "ماب تيفي": "https://maptv.ma/feed",
        "الجريدة العربية": "https://aljaridaalarabia.ma/feed",
        "حقائق 24": "https://hakaek24.com/feed",
        "المغرب 24": "https://almaghrib24.com/feed",
        "الأنباء": "https://anbaa.ma/feed",
        "الأخبار": "https://alakhbar.press.ma/feed",
        "المجلة": "https://almajalla.com/feed",
        "كازاوي": "https://casaoui.ma/feed",
        "بديل": "https://badil.info/feed",
        "أغورا": "https://agora.ma/feed",
        "المصدر": "https://almasdar.ma/feed",
        "الأول": "https://alaoual.com/feed",
        "مراكش بوست": "https://marrakechpost.com/feed",
        "طنجة الأدبية": "https://aladabia.net/feed",
        "الحدث 24": "https://alhadath24.ma/feed",
        "مغرب تايمز": "https://maghrebtimes.ma/feed"
    },
    "رادار الشمال والريف": {
        "بريس تطوان": "https://presstetouan.com/feed",
        "طنجة 24": "https://tanja24.com/feed",
        "شمال بوست": "https://chamalpost.net/feed",
        "طنجة نيوز": "https://tanjanews.com/feed",
        "صدى تطوان": "https://sadatetouan.com/feed",
        "تطوان بريس": "https://tetouanpress.ma/feed",
        "العرائش نيوز": "https://larachenews.com/feed",
        "دليل الريف": "https://www.dalil-rif.com/rss.xml",
        "ريف بوست": "https://rifpost.com/feed",
        "طنجة أنتر": "https://tanjainter.com/feed",
        "وزان بريس": "https://ouazzanepress.com/feed",
        "شفشاون بريس": "https://chefchaouenpress.com/feed",
        "تطوان نيوز": "https://tetouannews.com/feed",
        "العرائش 24": "https://larache24.com/feed",
        "أصداء تطوان": "https://asdaetetouan.com/feed",
        "منبر تطوان": "https://minbartetouan.com/feed",
        "خبايا نيوز": "https://khabayanews.com/feed",
        "ريف ديا": "https://rifdia.com/feed",
        "أصوات الدريوش": "https://driouchvoices.com/feed",
        "ميضار برس": "https://midarpress.com/feed",
        "زايو سيتي": "https://zaiocity.net/feed",
        "أخبار الريف": "https://akhbararif.com/feed",
        "الحسيمة سيتي": "https://alkhocimacity.com/feed",
        "ألتريس بريس": "https://altrespress.com/feed",
        "راديو تطوان": "https://radiotetouan.ma/feed",
        "عرائش سيتي": "https://larachecity.ma/feed",
        "القصر نيوز": "https://ksarnews.com/feed",
        "طنجة نيوز 24": "https://tanjanews24.com/feed",
        "سبتة بريس": "https://ceutapress.com/feed",
        "الريف 24": "https://rif24.com/feed",
        "ناظور 24": "https://nador24.com/feed",
        "الحسيمة 24": "https://alhoceima24.com/feed",
        "كاب تطوان": "https://captetouan.com/feed",
        "مارتيل بريس": "https://martilpress.com/feed",
        "المضيق تيفي": "https://mdiqtv.ma/feed",
        "الفنيدق 24": "https://fnideq24.com/feed",
        "شمالي": "https://chamaly.ma/feed",
        "طنجة الكبرى": "https://tanjakobra.com/feed",
        "تطوان بلوس": "https://tetouanplus.com/feed",
        "ريف سيتي": "https://rifcity.ma/feed",
        "طنجة بريس": "https://tangerpress.com/feed",
        "أخبار تطوان": "https://akhbartetouan.com/feed",
        "العرائش أنفو": "https://laracheinfo.com/feed",
        "القصر الكبير": "https://ksarkebir.com/feed",
        "وزان 24": "https://ouazzane24.com/feed",
        "شفشاون 24": "https://chefchaouen24.com/feed",
        "الريف بريس": "https://rifpress.ma/feed",
        "ناظور أوبزيرفر": "https://nadorobserver.com/feed",
        "تطوان اليوم": "https://tetouantoday.com/feed"
    },
    "الجهات والشرق والجنوب": {
        "وجدة سيتي": "https://www.oujdacity.net/feed",
        "مراكش الآن": "https://www.marrakechalaan.com/feed",
        "الداخلة نيوز": "https://dakhlanews.com/feed",
        "الصحراء زووم": "https://www.sahrazoom.com/feed",
        "سوس 24": "https://sous24.com/feed",
        "فاس نيوز": "https://fesnews.media/feed",
        "ناظور سيتي": "https://www.nadorcity.com/rss/",
        "تارودانت نيوز": "https://taroudant-news.com/feed",
        "صوت أكادير": "https://saoutagadir.ma/feed",
        "اشتوكة بريس": "https://chtoukapress.com/feed",
        "مكناس بريس": "https://meknespress.com/feed",
        "الجهة 24": "https://aljahia24.ma/feed",
        "وجدة بريس": "https://oujdapress.com/feed",
        "بركان سيتي": "https://berkanecity.com/feed",
        "ناظور برس": "https://nadorpress.com/feed",
        "تيزنيت 24": "https://tiznit24.com/feed",
        "كلميم نيوز": "https://glimimnews.com/feed",
        "الداخلة 24": "https://dakhla24.com/feed",
        "العيون أونلاين": "https://elaiunonline.com/feed",
        "كازا بريس": "https://casapress.com/feed",
        "سلا نيوز": "https://salanews.ma/feed",
        "قنيطرة سيتي": "https://kenitracity.net/feed",
        "آسفي كود": "https://saficod.ma/feed",
        "الجديدة 24": "https://eljadida24.com/feed",
        "سطات أونلاين": "https://settatonline.com/feed",
        "بني ملال أونلاين": "https://benimellalonline.com/feed",
        "خريبكة أونلاين": "https://khouribgaonline.com/feed",
        "آسفي 24": "https://safi24.ma/feed",
        "تارودانت بريس": "https://taroudantpress.ma/feed",
        "العيون 24": "https://laayoune24.com/feed",
        "الداخلة مباشر": "https://dakhlamobachir.net/feed",
        "زاكورة بريس": "https://zagorapress.com/feed",
        "تنغير نيوز": "https://tinghirnews.com/feed",
        "ورزازات أونلاين": "https://ouarzazateonline.com/feed",
        "الراشيدية 24": "https://errachidia24.com/feed",
        "ميدلت بريس": "https://mideltpress.com/feed",
        "خنيفرة أونلاين": "https://khenifraonline.com/feed",
        "تازة نيوز": "https://tazanews.com/feed",
        "تاونات نت": "https://taounatenet.ma/feed",
        "جرسيف 24": "https://guercif24.com/feed",
        "بركان نيوز": "https://berkanenews.com/feed",
        "جرادة نيوز": "https://jeradanews.com/feed",
        "فجيج نيوز": "https://figuignews.com/feed",
        "السمارة نيوز": "https://smara-news.com/feed",
        "بوجدور 24": "https://boujdour24.com/feed",
        "طانطان 24": "https://tantan24.com/feed",
        "سيدي إفني 24": "https://sidiifni24.com/feed",
        "أكادير تيفي": "https://agadirtv.ma/feed"
    },
    "رياضة واقتصاد ودولية": {
        "هسبريس رياضة": "https://hesport.com/feed",
        "البطولة": "https://www.elbotola.com/rss",
        "المنتخب": "https://almountakhab.com/rss",
        "اقتصادكم": "https://www.ecoactu.ma/ar/feed/",
        "سكاي نيوز": "https://www.skynewsarabia.com/rss/v1/middle-east.xml",
        "الجزيرة": "https://www.aljazeera.net/alritem/rss/rss.xml",
        "فرانس 24": "https://www.france24.com/ar/rss",
        "العربية": "https://www.alarabiya.net/.mrss/ar/last-24-hours.xml",
        "360 سبورت": "https://ar.sport.le360.ma/rss",
        "بورس نيوز": "https://boursenews.ma/feed",
        "ميديا 24": "https://www.medias24.com/ar/feed/",
        "رويترز": "https://www.reutersagency.com/feed/",
        "بي بي سي": "https://www.bbc.com/arabic/index.xml",
        "الشرق": "https://asharq.com/feed/",
        "CNBC عربية": "https://www.cnbcarabia.com/rss.xml",
        "كووورة": "https://www.kooora.com/rss.xml",
        "هاي كورة": "https://hihi2.com/feed",
        "في الجول": "https://www.filgoal.com/rss",
        "هبة سبور": "https://hibasport.com/feed",
        "شوف سبور": "https://choufsport.com/feed",
        "كورة بريس": "https://koorapress.com/feed",
        "الأخبار الاقتصادية": "https://economie.ma/feed",
        "المال": "https://almal.ma/feed",
        "تشالنج": "https://challenge.ma/feed",
        "ليكونوميست": "https://www.leconomiste.com/rss.xml",
        "راديو مارس": "https://radiomars.ma/feed",
        "أصوات": "https://aswat.ma/feed",
        "القدس العربي": "https://www.alquds.co.uk/feed",
        "عربي 21": "https://arabi21.com/rss",
        "روسيا اليوم": "https://arabic.rt.com/rss",
        "الحرة": "https://www.alhurra.com/rss",
        "اندبندنت": "https://www.independentarabia.com/rss",
        "دويتشه فيله": "https://rss.dw.com/xml/rss-ar-all",
        "رأي اليوم": "https://www.raialyoum.com/feed",
        "CNN بالعربية": "https://arabic.cnn.com/rss",
        "يورونيوز": "https://arabic.euronews.com/rss",
        "سبوتنيك": "https://sputnikarabic.ae/export/rss2/archive/index.xml"
    }
}
