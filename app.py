
import streamlit as st
import feedparser
import trafilatura
import os
import socket
import concurrent.futures
import base64
import time
import re
from openai import OpenAI
from fake_useragent import UserAgent

# ==========================================
# 0.5 نظام العضويات (Supabase Email/Password)
# ==========================================
from datetime import datetime
from zoneinfo import ZoneInfo
try:
    from supabase import create_client
except Exception as _e:
    create_client = None

TZ = ZoneInfo("Africa/Casablanca")

def _need_secrets_msg():
    st.error("❌ لم يتم ضبط مفاتيح Supabase داخل Streamlit Secrets.")
    st.info("""ضع القيم التالية في Streamlit → Settings → Secrets:

SUPABASE_URL = "https://...supabase.co"
SUPABASE_ANON_KEY = "eyJ..."
""")
    st.stop()

def sb_client():
    if create_client is None:
        st.error("❌ مكتبة supabase غير مثبتة. تأكد أن requirements.txt يحتوي على: supabase>=2.3.0")
        st.stop()
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_ANON_KEY")
    if not url or not key:
        _need_secrets_msg()
    return create_client(url, key)

def auth_box():
    st.markdown("### 🔐 تسجيل الدخول")
    tab1, tab2 = st.tabs(["Login", "Create account"])
    sb = sb_client()

    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("دخول", use_container_width=True):
            try:
                res = sb.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state["sb_session"] = res.session.model_dump()
                st.success("✅ تم تسجيل الدخول")
                st.rerun()
            except Exception:
                st.error("❌ بيانات الدخول غير صحيحة")

    with tab2:
        email2 = st.text_input("Email", key="signup_email")
        password2 = st.text_input("Password", type="password", key="signup_password")
        if st.button("إنشاء حساب", use_container_width=True):
            try:
                sb.auth.sign_up({"email": email2, "password": password2})
                st.success("✅ تم إنشاء الحساب. قم بتسجيل الدخول.")
            except Exception:
                st.error("❌ تعذر إنشاء الحساب (ربما البريد مستخدم)")

def require_login():
    if "sb_session" not in st.session_state:
        st.info("هذه المرحلة للأعضاء فقط. سجّل الدخول للمتابعة.")
        auth_box()
        st.stop()

def sb_user_client():
    sb = sb_client()
    sess = st.session_state.get("sb_session")
    if not sess:
        return sb
    sb.auth.set_session(sess["access_token"], sess["refresh_token"])
    return sb

def load_profile(sb):
    user = sb.auth.get_user().user
    prof = sb.table("profiles").select("*").eq("user_id", user.id).single().execute().data
    return user, prof

def reset_daily_if_needed(sb, user, prof):
    today = datetime.now(TZ).date().isoformat()
    if str(prof.get("daily_date")) != today:
        sb.table("profiles").update({"daily_used": 0, "daily_date": today}).eq("user_id", user.id).execute()
        prof["daily_used"] = 0
        prof["daily_date"] = today
    return prof

def can_rewrite(prof):
    if not prof.get("is_active", True):
        return False, "الحساب موقوف."
    if prof.get("plan") == "pro":
        return True, ""
    if int(prof.get("daily_used", 0)) >= int(prof.get("daily_limit", 2)):
        return False, "وصلتي للحد اليومي المجاني (جوج صياغات). خاصك Pro."
    return True, ""

def logout():
    # نمسح جلسة Supabase المحلية فقط
    st.session_state.pop("sb_session", None)
    st.session_state.pop("current_article", None)
    st.session_state.pop("edit_title", None)
    st.session_state.pop("edit_body", None)
    st.session_state.page = "public"
    st.rerun()


# ==========================================
# 0. الإعدادات والتهيئة
# ==========================================
st.set_page_config(
    page_title="Yaqeen Press | سيادة الخبر",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

try:
    from manadger_lib import RSS_DATABASE, get_safe_key, ELITE_PROMPT_V2
except ImportError:
    st.error("❌ ملف manadger_lib.py مفقود.")
    st.stop()

ua = UserAgent()
socket.setdefaulttimeout(30)

if 'page' not in st.session_state: st.session_state.page = 'public'

# ==========================================
# 1. التصميم الملكي (مع إصلاح الأيقونات)
# ==========================================
def inject_royal_css():
    # ملاحظة: أي CSS عدواني قد يكسر Streamlit (الـ header/زر السايدبار). لذلك نلتزم بتصميم آمن.
    st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');

:root{
  --bg1:#f6f9ff;
  --bg2:#ffffff;
  --card:#ffffff;
  --card2:#f3f6ff;
  --text:#0b1220;
  --muted:#5a677a;
  --border:rgba(15,23,42,.10);
  --shadow: 0 10px 30px rgba(2,6,23,.08);
  --shadow2: 0 6px 18px rgba(2,6,23,.10);
  --brand:#2563eb;      /* blue */
  --brand2:#7c3aed;     /* violet */
  --brand3:#06b6d4;     /* cyan */
  --ok:#16a34a;
  --warn:#f59e0b;
}

html, body, .stApp{font-family:'Tajawal', sans-serif;}
.stApp{
  background:
    radial-gradient(1100px 600px at 10% 10%, rgba(124,58,237,.10), transparent 60%),
    radial-gradient(900px 500px at 90% 15%, rgba(37,99,235,.12), transparent 55%),
    radial-gradient(800px 500px at 55% 95%, rgba(6,182,212,.10), transparent 55%),
    linear-gradient(180deg, var(--bg1), var(--bg2) 55%);
}

/* Keep Streamlit chrome alive (sidebar toggle lives here) */
[data-testid="stHeader"]{
  background: rgba(246,249,255,.78) !important;
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border);
}
[data-testid="stSidebarCollapsedControl"]{
  display:flex !important;
  visibility:visible !important;
  opacity:1 !important;
}

/* Layout */
.block-container{padding-top:1.1rem; padding-bottom:2.2rem; max-width:1180px;}
body{direction:rtl; text-align:right;}
.stMarkdown, .stCaption, .stText, .stAlert, label{direction:rtl; text-align:right;}

/* Sidebar */
[data-testid="stSidebar"]{
  background: rgba(255,255,255,.86) !important;
  backdrop-filter: blur(10px);
  border-right:1px solid var(--border);
}
[data-testid="stSidebar"] *{direction:rtl; text-align:right;}
[data-testid="stSidebar"] .stButton>button{border-radius:14px!important;}

/* Buttons */
.stButton>button{
  border-radius:16px !important;
  border: 1px solid var(--border) !important;
  box-shadow: 0 1px 0 rgba(2,6,23,.03);
  padding: .70rem 1.0rem !important;
  font-weight: 700 !important;
}
.stButton>button[kind="primary"]{
  background: linear-gradient(135deg, var(--brand), var(--brand2)) !important;
  color:#fff !important;
  border: none !important;
  box-shadow: var(--shadow2);
}
.stButton>button:hover{transform: translateY(-1px);}

/* Inputs / Selects */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] div[data-baseweb="select"] > div{
  border-radius:14px !important;
  border: 1px solid var(--border) !important;
  background: rgba(255,255,255,.92) !important;
}
[data-testid="stNumberInput"] input{
  border-radius:14px !important;
  border: 1px solid var(--border) !important;
}
[data-testid="stTextInput"] input{padding:.65rem .85rem !important;}
[data-testid="stTextArea"] textarea{padding:.75rem .85rem !important;}

/* Make email/password feel natural */
input[type="password"], input[type="email"]{direction:ltr; text-align:left;}
/* Headlines cards */
.yq-card{
  background: rgba(255,255,255,.92);
  border: 1px solid var(--border);
  border-radius: 18px;
  box-shadow: var(--shadow);
  padding: 16px 16px;
}
.yq-chip{
  display:inline-flex;
  align-items:center;
  gap:.45rem;
  padding:.35rem .65rem;
  border-radius:999px;
  border:1px solid var(--border);
  background: rgba(243,246,255,.75);
  font-weight:700;
  color: var(--text);
}
.yq-chip small{color:var(--muted); font-weight:700;}
.yq-hero{
  border-radius: 26px;
  padding: 28px 22px;
  border: 1px solid var(--border);
  background:
    radial-gradient(900px 400px at 20% 20%, rgba(124,58,237,.18), transparent 60%),
    radial-gradient(800px 380px at 85% 30%, rgba(37,99,235,.18), transparent 55%),
    linear-gradient(180deg, rgba(255,255,255,.92), rgba(255,255,255,.78));
  box-shadow: var(--shadow);
}
.yq-hero h1{
  margin:0;
  font-size: 2.1rem;
  line-height: 1.2;
  letter-spacing: -0.3px;
}
.yq-hero p{
  margin:.55rem 0 0 0;
  color: var(--muted);
  font-size: 1.05rem;
  line-height: 1.8;
}
.yq-kpis{
  display:flex;
  flex-wrap:wrap;
  gap:.6rem;
  margin-top: 14px;
}
.yq-kpi{
  background: rgba(255,255,255,.85);
  border:1px solid var(--border);
  border-radius: 16px;
  padding: 10px 12px;
  min-width: 170px;
}
.yq-kpi b{display:block; font-size:1.15rem;}
.yq-kpi span{color:var(--muted); font-weight:700;}

hr{border:0; height:1px; background: var(--border); margin: 1rem 0;}

@media (max-width: 760px){
  .block-container{padding-left:1rem; padding-right:1rem;}
  .yq-hero{padding: 18px 14px;}
  .yq-hero h1{font-size:1.65rem;}
  .yq-kpi{min-width: 140px;}
}
</style>""", unsafe_allow_html=True)

inject_royal_css()

# ==========================================
# 2. المنطق البرمجي
# ==========================================

def render_header():
    date_now = time.strftime("%d-%m-%Y • %H:%M")
    html = f'''
    <div class="ny-header" dir="rtl">
      <div class="ny-header-row">
        <div class="ny-brand">
          <span class="ny-mark"></span>
          <div>
            <div class="ny-title">يقين بريس</div>
            <div class="ny-sub">Newsroom Console • سيادة الخبر</div>
          </div>
        </div>
        <div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap;">
          <span class="ny-pill"><span class="ny-dot"></span> LIVE</span>
          <span class="ny-badge">🕒 {date_now}</span>
        </div>
      </div>
    </div>
    '''
    st.markdown(html, unsafe_allow_html=True)

@st.cache_data(ttl=900, show_spinner=False)
def scan_news_sector(category, sources, per_source=10):
    items = []
    def fetch(name, url):
        try:
            feed = feedparser.parse(url, agent=ua.random)
            if not feed.entries: return []
            return [{
                "title": e.title, "link": e.link, "source": name,
                "published": e.get('published', '')[:16]
            } for e in feed.entries[:per_source]]
        except: return []

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
        futures = {ex.submit(fetch, n, u): n for n, u in sources.items()}
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res: items.extend(res)
    return items

def smart_editor_ai(link, keyword):
    try:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.markdown("📡 **جاري سحب البيانات...**")
        progress_bar.progress(20)
        
        downloaded = trafilatura.fetch_url(link)
        if not downloaded: raise Exception("المصدر محمي")
        
        progress_bar.progress(50)
        raw = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
        if not raw: raise Exception("المحتوى فارغ")

        # trafilatura يرجّع نصاً نظيفاً؛ نقصّه فقط لتفادي تجاوز حدود السياق
        clean_text = raw.strip()[:5500]
        
        progress_bar.progress(80)
        status_text.markdown("🧠 **المعالج الذكي يعمل...**")
        
        api_key = get_safe_key()
        if not api_key: raise Exception("مفتاح API مفقود")
        
        client = OpenAI(api_key=api_key, base_url="https://api.sambanova.ai/v1")
        response = client.chat.completions.create(
            model='Meta-Llama-3.3-70B-Instruct',
            messages=[
                {"role": "system", "content": "أنت محرر صحفي مخضرم. التزم بإخراج منسق وثابت وفق TITLE/BODY فقط، بدون أي إضافات."},
                {"role": "user", "content": ELITE_PROMPT_V2.format(keyword=keyword) + f"\n\nالنص:\n{clean_text}"}
            ],
            temperature=0.3
        )
        
        progress_bar.progress(100)
        time.sleep(0.5)
        progress_bar.empty()
        status_text.empty()
        return response.choices[0].message.content, None
    except Exception as e:
        return None, str(e)

# ==========================================
# 3. واجهة المستخدم
# ==========================================


if st.session_state.page == 'public':
    render_header()


    # =============================
    # Landing Hero (واجهة هبوط احترافية)
    # =============================
    st.markdown(
        """
        <div class="yq-hero">
          <div class="yq-chip">🛰️ <small>Yaqeen Press</small> <span style="opacity:.65">|</span> <small>Newsroom Console</small></div>
          <h1>السيادة على الخبر… بسرعة غرفة أخبار عالمية</h1>
          <p>
            لوحة تحكم صحفية تجمع العناوين من مصادر متعددة، ثم تمنحك إعادة صياغة احترافية عند تسجيل الدخول.
            <b>كزائر</b> تشاهد العناوين فقط. <b>كعضو</b> تحصل على الاستخلاص والتحرير والتصدير.
          </p>
          <div class="yq-kpis">
            <div class="yq-kpi"><b>عرض عام</b><span>عناوين فقط للزوار</span></div>
            <div class="yq-kpi"><b>Free</b><span>جوج صياغات / اليوم</span></div>
            <div class="yq-kpi"><b>Pro</b><span>صياغة مفتوحة</span></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("")
    # =============================
    # شريط التحكم الرئيسي (ظاهر دائماً حتى لو أُخفيت القائمة الجانبية)
    # =============================
    if "selected_cat" not in st.session_state:
        st.session_state["selected_cat"] = list(RSS_DATABASE.keys())[0] if RSS_DATABASE else ""

    with st.container():
        c1, c2, c3, c4 = st.columns([2.2, 1.2, 1.2, 1.4])
        with c1:
            st.selectbox("القسم", list(RSS_DATABASE.keys()), key="selected_cat")
        with c2:
            st.slider("لكل مصدر", 3, 30, int(st.session_state.get("entries_per_source", 10)), 1, key="entries_per_source")
        with c3:
            st.selectbox("في الصفحة", [20, 50, 100, 200], index=[20,50,100,200].index(int(st.session_state.get("headlines_per_page", 50))) if int(st.session_state.get("headlines_per_page", 50)) in [20,50,100,200] else 1, key="headlines_per_page")
        with c4:
            st.text_input("بحث", "", key="search_query", placeholder="اكتب كلمة مفتاحية…")

    selected_cat = st.session_state.get("selected_cat", "")
    search_query = st.session_state.get("search_query", "")

    with st.sidebar:
        if os.path.exists("logo.png"):
            col_l, col_c, col_r = st.columns([1, 2, 1])
            with col_c:
                st.image("logo.png", width=120)
        else:
            st.markdown("<h2 style='text-align:center; margin:0;'>🦅</h2>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align:center; margin-top:0;'>Yaqeen Press</h3>", unsafe_allow_html=True)

        st.markdown(" ")
        st.markdown("### 👀 وضع الزائر")
        st.caption("يمكنك الاطلاع على العناوين فقط. للمعالجة والتحرير يلزم تسجيل الدخول.")

        # ملاحظة: اختيار القسم/الفلاتر سيكون في أعلى الصفحة (وليس فقط في السايدبار)
        # لأن السايدبار قد يُخفى على الهاتف.

        if "sb_session" in st.session_state:
            if st.button("➡️ دخول لغرفة التحرير", use_container_width=True):
                st.session_state.page = "newsroom"
                st.rerun()
            if st.button("🚪 Logout", use_container_width=True):
                logout()
        else:
            if st.button("🔐 Login / Create account", use_container_width=True, type="primary"):
                st.session_state.page = "newsroom"
                st.rerun()

        total_sources = len(RSS_DATABASE.get(st.session_state.get("selected_cat",""), {}))
        st.markdown(
            f"""<div style="display:flex; gap:8px; flex-wrap:wrap;">
                    <span class="badge">📌 مصادر: {total_sources}</span>
                    <span class="badge">🧭 TTL: 15 دقيقة</span>
                 </div>""",
            unsafe_allow_html=True
        )

        st.divider()
        if st.button("🔄 تحديث", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    st.markdown(f"<div class='ny-badge' style='margin:10px 0 14px 0;'>🗞️ {selected_cat} — العناوين فقط</div>", unsafe_allow_html=True)

    with st.spinner("جاري المسح..."):
        news_list = scan_news_sector(selected_cat, RSS_DATABASE[selected_cat], per_source=st.session_state.get('entries_per_source', 10))

    if search_query:
        q = search_query.strip().lower()
        news_list = [n for n in news_list if q in (n.get('title','').lower() + ' ' + n.get('source','').lower())]

    if news_list:
        st.markdown(
            f"""<div style="display:flex; gap:10px; flex-wrap:wrap; margin-bottom:10px;">
                    <span class="badge">🗞️ نتائج: {len(news_list)}</span>
                    <span class="badge">🧩 قسم: {selected_cat}</span>
                 </div>""",
            unsafe_allow_html=True
        )

        # عرض بسيط للعناوين فقط (مع صفحات)
        per_page = int(st.session_state.get("headlines_per_page", 50))
        total = len(news_list)
        pages = max(1, (total + per_page - 1) // per_page)
        page = st.number_input("الصفحة", min_value=1, max_value=pages, value=1, step=1, key="public_page")
        start_i = (page - 1) * per_page
        end_i = start_i + per_page

        for item in news_list[start_i:end_i]:
            st.markdown(
                f"""<div class="ny-card" dir="rtl">
                        <div class="ny-h">{item.get('title','')}</div>
                        <div class="ny-meta">
                            <span class="ny-badge">المصدر: {item.get('source','')}</span>
                            <span class="ny-badge">{item.get('published','')}</span>
                        </div>
                     </div>""",
                unsafe_allow_html=True
            )
    else:
        st.warning("لا توجد أخبار")

elif st.session_state.page == 'newsroom':
    render_header()

    # 🔒 غرفة التحرير للأعضاء فقط
    require_login()
    sb = sb_user_client()
    try:
        user, profile = load_profile(sb)
        profile = reset_daily_if_needed(sb, user, profile)
    except Exception as e:
        st.error("❌ تعذر جلب بيانات العضوية من Supabase. تأكد من إنشاء الجداول والسياسات (RLS) بشكل صحيح.")
        st.stop()
    
    # =============================
    # شريط تحكم غرفة التحرير (ظاهر دائماً)
    # =============================
    if "newsroom_cat" not in st.session_state:
        st.session_state["newsroom_cat"] = st.session_state.get("selected_cat") or (list(RSS_DATABASE.keys())[0] if RSS_DATABASE else "")
    if "newsroom_per_source" not in st.session_state:
        st.session_state["newsroom_per_source"] = 10

    top1, top2, top3, top4 = st.columns([2.2, 1.2, 1.2, 1.4])
    with top1:
        st.selectbox("القسم", list(RSS_DATABASE.keys()), key="newsroom_cat")
    with top2:
        st.slider("لكل مصدر", 3, 30, int(st.session_state.get("newsroom_per_source", 10)), 1, key="newsroom_per_source")
    with top3:
        keyword_input = st.text_input("كلمة SEO", "يقين بريس", key="newsroom_keyword")
    with top4:
        search_query = st.text_input("بحث", "", key="newsroom_search", placeholder="وزارة، ريال، لقاح…")

    selected_cat = st.session_state.get("newsroom_cat", "")

    # Sidebar: حساب + أزرار فقط (بدون عناصر حرجة تختفي على الهاتف)
    with st.sidebar:
        if os.path.exists("logo.png"):
            col_l, col_c, col_r = st.columns([1, 2, 1])
            with col_c:
                st.image("logo.png", width=120)
        else:
            st.markdown("<h2 style='text-align:center; margin:0;'>🦅</h2>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align:center; margin-top:0;'>Yaqeen Press</h3>", unsafe_allow_html=True)

        st.markdown("### 👤 الحساب")
        plan = profile.get("plan","free")
        used = int(profile.get("daily_used",0))
        limit = int(profile.get("daily_limit",2))
        st.markdown(
            f"""<div style="display:flex; gap:8px; flex-wrap:wrap;">
                    <span class="ny-badge">{user.email}</span>
                    <span class="ny-badge">Plan: {plan}</span>
                    <span class="ny-badge">اليوم: {used}/{limit}</span>
                 </div>""",
            unsafe_allow_html=True
        )

        total_sources = len(RSS_DATABASE.get(selected_cat, {}))
        st.markdown(
            f"""<div style="display:flex; gap:8px; flex-wrap:wrap; margin-top:8px;">
                    <span class="ny-badge">📌 مصادر: {total_sources}</span>
                    <span class="ny-badge">🧭 TTL: 15 دقيقة</span>
                 </div>""",
            unsafe_allow_html=True
        )

        st.divider()
        if st.button("🔄 تحديث", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        if st.button("🚪 Logout", use_container_width=True):
            logout()

    st.markdown(f"<div class='ny-badge' style='margin:10px 0 14px 0;'>📡 {selected_cat}</div>", unsafe_allow_html=True)
    
    with st.spinner("جاري المسح..."):
        news_list = scan_news_sector(selected_cat, RSS_DATABASE[selected_cat], per_source=int(st.session_state.get('newsroom_per_source', 10)))

    # فلترة حسب البحث
    if 'search_query' in locals() and search_query:
        q = search_query.strip().lower()
        news_list = [n for n in news_list if q in (n.get('title','').lower() + ' ' + n.get('source','').lower())]


    if news_list:
        col_list, col_editor = st.columns([1, 1.5], gap="medium")
        news_map = {f"{item['title']} — {item['source']}": item for item in news_list}
        
        with col_list:
            st.markdown(
                f"""<div style="display:flex; gap:10px; flex-wrap:wrap; margin-bottom:8px;">
                        <span class="badge">🗞️ نتائج: {len(news_list)}</span>
                        <span class="badge">🧩 قسم: {selected_cat}</span>
                     </div>""",
                unsafe_allow_html=True
            )

            selected_title = st.selectbox("اختر خبراً للتحرير", list(news_map.keys()), label_visibility="collapsed")
            target_news = news_map[selected_title]

            # بطاقة الخبر المحدد
            st.markdown(
                f"""<div class="ny-card" dir="rtl">
                        <div class="ny-h">{target_news['title']}</div>
                        <div class="ny-meta">
                            <span class="ny-badge">المصدر: {target_news['source']}</span>
                            <span class="ny-badge">{target_news['published']}</span>
                            <span class="ny-badge"><a href="{target_news['link']}" target="_blank">فتح المصدر</a></span>
                        </div>
                     </div>""",
                unsafe_allow_html=True
            )

            
            ok, msg = can_rewrite(profile)
            if not ok:
                st.error(msg)
            else:
                if st.button("⚡ تحرير الخبر الآن", use_container_width=True, type="primary"):
                    content, error = smart_editor_ai(target_news['link'], keyword_input)
                    if error:
                        st.error(f"❌ {error}")
                    else:
                        st.session_state['current_article'] = content
                        # خصم 1 من الحصة اليومية للحساب المجاني بعد نجاح الصياغة
                        try:
                            if profile.get("plan") != "pro":
                                new_used = int(profile.get("daily_used", 0)) + 1
                                sb.table("profiles").update({"daily_used": new_used}).eq("user_id", user.id).execute()
                                profile["daily_used"] = new_used
                            sb.table("usage_logs").insert({"user_id": user.id, "action": "rewrite"}).execute()
                        except Exception:
                            pass

            with st.expander("🧾 عناوين سريعة", expanded=False):
                for k, item in list(news_map.items())[:20]:
                    st.markdown(
                        f"""<div class="ny-card" dir="rtl" style="padding:12px; margin-bottom:8px;">
                                <div class="ny-h" style="font-size:.95rem;">{item['title']}</div>
                                <div class="ny-meta">
                                    <span class="ny-badge">{item['source']}</span>
                                    <span class="ny-badge">{item['published']}</span>
                                    <span class="ny-badge"><a href="{item['link']}" target="_blank">فتح</a></span>
                                </div>
                             </div>""",
                        unsafe_allow_html=True
                    )

        with col_editor:
            st.markdown("#### 📝 المحرر")
            
            if 'current_article' in st.session_state:
                raw_txt = st.session_state['current_article']

                def parse_ai_output(txt: str):
                    # Expected format:
                    # TITLE: ...
                    # BODY:
                    # ...
                    title = ""
                    body = ""
                    m = re.search(r"^\s*TITLE\s*:\s*(.+?)\s*$", txt, flags=re.MULTILINE)
                    if m:
                        title = m.group(1).strip()
                    m2 = re.search(r"^\s*BODY\s*:\s*$", txt, flags=re.MULTILINE)
                    if m2:
                        body = txt[m2.end():].strip()
                    if not title:
                        # fallback: first non-empty line
                        lines = [l.strip() for l in txt.splitlines() if l.strip()]
                        title = lines[0] if lines else ""
                        body = "\n".join(lines[1:]) if len(lines) > 1 else ""
                    return title, body

                final_title, final_body = parse_ai_output(raw_txt)

                with st.container(border=True):
                    tab_edit, tab_preview, tab_export = st.tabs(["✍️ تحرير", "👁️ معاينة", "⬇️ تصدير"])

                    with tab_edit:
                        st.session_state["edit_title"] = st.session_state.get("edit_title", final_title)
                        st.session_state["edit_body"] = st.session_state.get("edit_body", final_body)

                        st.text_input("العنوان", key="edit_title")
                        st.text_area("المقال", key="edit_body", height=520)

                        st.markdown(
                            """<div style="display:flex; gap:10px; flex-wrap:wrap; margin-top:6px;">
                                    <span class="badge">✅ جاهز للنشر</span>
                                    <span class="badge">🧠 إخراج مهيكل: TITLE/BODY</span>
                                 </div>""",
                            unsafe_allow_html=True
                        )

                    with tab_preview:
                        st.markdown(f"### {st.session_state.get('edit_title','')}")
                        st.write(st.session_state.get("edit_body",""))

                    with tab_export:
                        title_out = st.session_state.get("edit_title","").strip()
                        body_out = st.session_state.get("edit_body","").strip()

                        md = f"# {title_out}\\n\\n{body_out}\\n"
                        txt = f"{title_out}\\n\\n{body_out}\\n"
                        st.download_button(
                            "⬇️ تنزيل Markdown",
                            data=md.encode("utf-8"),
                            file_name="article.md",
                            mime="text/markdown",
                            use_container_width=True
                        )
                        st.download_button(
                            "⬇️ تنزيل TXT",
                            data=txt.encode("utf-8"),
                            file_name="article.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
                        st.code(md, language="markdown")
            else:
                st.markdown("<div style='text-align:center; padding:40px; color:#64748b; border:2px dashed #334155; border-radius:10px;'>اختر خبراً لبدء المعالجة</div>", unsafe_allow_html=True)
    else:
        st.warning("لا توجد أخبار")