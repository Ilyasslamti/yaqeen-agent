
import streamlit as st
import feedparser
import trafilatura
import os
import socket
import concurrent.futures
import base64
import time
import re
import math
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
    st.markdown("""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');

      :root{
        --bg:#f6f8fb;
        --panel:#ffffff;
        --card:#ffffff;
        --card2:#f3f6fb;
        --muted:#64748b;
        --text:#0f172a;
        --border:rgba(255,255,255,.90);
        --brand:#1d4ed8;
        --brand2:#2563eb;
        --gold:#f59e0b;
        --danger:#ef4444;
        --ok:#16a34a;
      }
html, body, .stApp { font-family:'Tajawal', sans-serif; }
      /* لا تفرض الخط على كل span/div حتى لا تتكسر أيقونات Streamlit */
      h1,h2,h3,h4,h5,h6,p,label,button,input,textarea{ font-family:'Tajawal', sans-serif !important; direction:rtl; }

      /* خلفية مثل dashboards الوكالات */
      .stApp{
        background:
          radial-gradient(1200px 600px at 10% 0%, rgba(37,99,235,.10), transparent 60%),
          radial-gradient(900px 500px at 90% 20%, rgba(245,158,11,.08), transparent 55%),
          linear-gradient(180deg, var(--bg) 0%, var(--panel) 100%);
        color:var(--text);
      }

      /* إخفاء الهيدر الافتراضي */
      header[data-testid="stHeader"]{ background: transparent; }
      footer { visibility:hidden; }

      /* الحاوية الرئيسية */
      section.main > div { padding-top: 1.2rem; }

      /* Sidebar */
      [data-testid="stSidebar"]{
        background: rgba(255,255,255,.92);
        border-right: 1px solid var(--border);
        backdrop-filter: blur(10px);
      }
      [data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3{
        color: var(--text) !important;
      }

      /* Inputs */
      .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div{
        background: rgba(255,255,255,.95) !important;
        border: 1px solid var(--border) !important;
        color: var(--text) !important;
        border-radius: 14px !important;
      }
      .stTextArea textarea { line-height: 1.9; }

      /* Buttons */
      .stButton>button{
        background: linear-gradient(90deg, var(--brand) 0%, var(--brand2) 100%) !important;
        border: 1px solid rgba(59,130,246,.35) !important;
        color: white !important;
        border-radius: 14px !important;
        height: 3.1rem;
        font-weight: 800;
        letter-spacing: .2px;
        box-shadow: 0 10px 26px rgba(37,99,235,.18);
      }
      .stButton>button:hover{ transform: translateY(-1px); filter: brightness(1.05); }
      .stButton>button:active{ transform: translateY(0px); }

      /* Cards / containers */
      div[data-testid="stVerticalBlockBorderWrapper"]{
        background: rgba(255,255,255,.92);
        border: 1px solid var(--border);
        border-radius: 18px;
        box-shadow: 0 20px 60px rgba(0,0,0,.25);
      }
      div[data-testid="stExpander"]{
        background: rgba(255,255,255,.92);
        border: 1px solid var(--border);
        border-radius: 18px;
      }

      /* Select dropdown wrapping fix */
      div[data-baseweb="select"] span{ white-space: normal !important; }

      /* Metric-like badges */
      .badge{
        display:inline-flex; align-items:center; gap:8px;
        padding:6px 10px; border-radius: 999px;
        border:1px solid var(--border);
        background: rgba(255,255,255,.90);
        color: var(--text);
        font-size:.78rem; font-weight:800;
      }
      .badge-dot{ width:8px; height:8px; border-radius:999px; background: var(--ok); box-shadow:0 0 0 4px rgba(34,197,94,.15); }

      /* Header */
      .newsroom-header{
        display:flex; justify-content:space-between; align-items:center;
        padding: 18px 18px;
        border:1px solid var(--border);
        border-radius: 20px;
        background: rgba(255,255,255,.92);
        backdrop-filter: blur(14px);
        box-shadow: 0 30px 70px rgba(0,0,0,.25);
        margin-bottom: 18px;
      }
      .brand{
        display:flex; align-items:center; gap:12px;
      }
      .brand-title{ font-size:1.25rem; font-weight: 900; color: var(--text); }
      .brand-sub{ font-size:.82rem; color: var(--muted); font-weight:700; margin-top:2px; }
      .live-pill{
        display:inline-flex; align-items:center; gap:8px;
        padding:6px 12px; border-radius: 999px;
        background: rgba(239,68,68,.14);
        border: 1px solid rgba(239,68,68,.35);
        color: #fecaca;
        font-size:.78rem; font-weight:900;
      }
      .live-dot{
        width:8px; height:8px; border-radius:999px; background: var(--danger);
        box-shadow: 0 0 0 4px rgba(239,68,68,.18);
      }

      /* News card */
      .news-card{
        border:1px solid var(--border);
        background: rgba(255,255,255,.90);
        border-radius: 18px;
        padding: 14px 14px;
        margin-bottom: 10px;
      }
      .news-title{
        color: var(--text);
        font-weight: 900;
        line-height: 1.5;
        font-size: 1.02rem;
        margin: 0 0 6px 0;
      }
      .news-meta{
        color: var(--muted);
        font-size: .78rem;
        display:flex; justify-content:space-between; gap:10px; flex-wrap:wrap;
      }
      a{ color:#93c5fd; text-decoration:none; font-weight:800; }
      a:hover{ text-decoration:underline; }

      /* Login card center */
      .login-wrap{
        max-width: 420px;
        margin: 6vh auto 0 auto;
        padding: 24px;
        border-radius: 22px;
        background: rgba(255,255,255,.92);
        border:1px solid var(--border);
        box-shadow: 0 40px 90px rgba(0,0,0,.30);
      }
      .login-title{
        text-align:center;
        font-size: 1.25rem;
        font-weight: 900;
        color: var(--text);
        margin-bottom: 10px;
      }
      .login-sub{
        text-align:center;
        color: var(--muted);
        font-weight: 700;
        font-size: .85rem;
        margin-bottom: 18px;
      }

      /* Mobile */
      @media (max-width: 900px){
        .newsroom-header{ flex-direction: column; align-items: flex-start; gap: 10px; }
      }
    </style>
    """, unsafe_allow_html=True)

inject_royal_css()

# ==========================================
# 2. المنطق البرمجي
# ==========================================

def render_header():
    date_now = time.strftime("%d-%m-%Y • %H:%M")
    html = f"""
    <div class="newsroom-header">
        <div class="brand">
            <div style="font-size:1.35rem;">🦅</div>
            <div>
                <div class="brand-title">يقين بريس</div>
                <div class="brand-sub">Newsroom Console • سيادة الخبر</div>
            </div>
        </div>
        <div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap; justify-content:flex-end;">
            <div class="live-pill"><span class="live-dot"></span> LIVE</div>
            <div class="badge"><span class="badge-dot"></span>{date_now}</div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

@st.cache_data(ttl=900, show_spinner=False)
def scan_news_sector(category, sources, per_source_limit:int=10):
    items = []
    def fetch(name, url):
        try:
            feed = feedparser.parse(url, agent=ua.random)
            if not feed.entries: return []
            return [{
                "title": e.title, "link": e.link, "source": name,
                "published": e.get('published', '')[:16]
            } for e in feed.entries[:per_source_limit]]
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

        st.divider()
        selected_cat = st.radio("الأقسام", list(RSS_DATABASE.keys()), label_visibility="collapsed")

        per_source_limit = st.slider("عدد الأخبار لكل مصدر", min_value=3, max_value=30, value=10, step=1,
                                     help="يزيد عدد العناوين المسحوبة من كل RSS. كلما زاد العدد زاد وقت المسح.")


        total_sources = len(RSS_DATABASE.get(selected_cat, {}))
        st.markdown(
            f"""<div style="display:flex; gap:8px; flex-wrap:wrap;">
                    <span class="badge">📌 مصادر: {total_sources}</span>
                    <span class="badge">🧭 TTL: 15 دقيقة</span>
                 </div>""",
            unsafe_allow_html=True
        )

        st.divider()
        search_query = st.text_input("بحث داخل العناوين", "", placeholder="مثال: وزارة الصحة، برشلونة...")

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🔄 تحديث", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        with col_b:
            st.write("")

    st.markdown(f"<h4 style='border-right: 4px solid #fbbf24; padding-right: 10px; color:white !important;'>🗞️ {selected_cat} — العناوين فقط</h4>", unsafe_allow_html=True)

    with st.spinner("جاري المسح..."):
        news_list = scan_news_sector(selected_cat, RSS_DATABASE[selected_cat], per_source_limit)

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

        # عرض بسيط للعناوين فقط

        # --- عرض العناوين مع Pagination (لمنع قطع النتائج) ---
        page_size = st.selectbox("عدد العناوين في الصفحة", [20, 50, 100, 200, 400], index=1)
        total_items = len(news_list)
        total_pages = max(1, math.ceil(total_items / page_size))
        page = st.number_input("الصفحة", min_value=1, max_value=total_pages, value=1, step=1)
        start = (page - 1) * page_size
        end = start + page_size

        st.caption(f"عرض {min(end, total_items)} / {total_items} — صفحة {page} من {total_pages}")

        for item in news_list[start:end]:
            st.markdown(
                f"""<div class="news-card" style="padding:14px;">
                        <div class="news-title" style="font-size:1.02rem;">{item.get('title','')}</div>
                        <div class="news-meta">
                            <span>المصدر: <b>{item.get('source','')}</b></span>
                            <span>{item.get('published','')}</span>
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
    
    with st.sidebar:
        # شعار
        if os.path.exists("logo.png"):
            col_l, col_c, col_r = st.columns([1, 2, 1])
            with col_c:
                st.image("logo.png", width=120)
        else:
            st.markdown("<h2 style='text-align:center; margin:0;'>🦅</h2>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align:center; margin-top:0;'>Yaqeen Press</h3>", unsafe_allow_html=True)

        st.markdown(" ")

        st.markdown("### 🎛️ غرفة التحكم")
        selected_cat = st.radio("الأقسام", list(RSS_DATABASE.keys()), label_visibility="collapsed")

        per_source_limit = st.slider("عدد الأخبار لكل مصدر", min_value=3, max_value=30, value=10, step=1,
                                     help="يزيد عدد العناوين المسحوبة من كل RSS. كلما زاد العدد زاد وقت المسح.")


        # إحصاءات سريعة
        total_sources = len(RSS_DATABASE.get(selected_cat, {}))
        st.markdown(
            f"""<div style="display:flex; gap:8px; flex-wrap:wrap;">
                    <span class="badge">📌 مصادر: {total_sources}</span>
                    <span class="badge">🧭 TTL: 15 دقيقة</span>
                 </div>""",
            unsafe_allow_html=True
        )

        st.divider()

        keyword_input = st.text_input("الكلمة المفتاحية (SEO)", "يقين بريس")

        # حالة العضوية (Plan + Daily quota)
        try:
            plan = profile.get("plan","free")
            used = int(profile.get("daily_used",0))
            limit = int(profile.get("daily_limit",2))
            st.markdown(
                f"""<div style="display:flex; gap:8px; flex-wrap:wrap; margin-top:6px;">
                        <span class="badge">👤 {user.email}</span>
                        <span class="badge">💼 Plan: {plan}</span>
                        <span class="badge">⚡ اليوم: {used}/{limit}</span>
                     </div>""",
                unsafe_allow_html=True
            )
        except Exception:
            pass

        search_query = st.text_input("بحث داخل العناوين", "", placeholder="مثال: وزارة الصحة، برشلونة...")

        st.divider()

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🔄 تحديث", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        with col_b:
            if st.button("🚪 Logout", use_container_width=True):
                logout()

    st.markdown(f"<h4 style='border-right: 4px solid #fbbf24; padding-right: 10px; color:white !important;'>📡 {selected_cat}</h4>", unsafe_allow_html=True)
    
    with st.spinner("جاري المسح..."):
        news_list = scan_news_sector(selected_cat, RSS_DATABASE[selected_cat], per_source_limit)

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
                f"""<div class="news-card">
                        <div class="news-title">{target_news['title']}</div>
                        <div class="news-meta">
                            <span>المصدر: <b>{target_news['source']}</b></span>
                            <span>{target_news['published']}</span>
                        </div>
                        <div style="margin-top:8px;">
                            <a href="{target_news['link']}" target="_blank">🔗 فتح المصدر الأصلي</a>
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

            with st.expander("🧾 قائمة الأخبار (للاطلاع السريع)", expanded=False):
                for k, item in list(news_map.items())[:20]:
                    st.markdown(
                        f"""<div class="news-card" style="padding:12px; margin-bottom:8px;">
                                <div class="news-title" style="font-size:.95rem;">{item['title']}</div>
                                <div class="news-meta">
                                    <span>{item['source']}</span>
                                    <span>{item['published']}</span>
                                </div>
                                <div style="margin-top:6px;">
                                    <a href="{item['link']}" target="_blank">فتح</a>
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
