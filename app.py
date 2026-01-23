st.markdown("""
<style>

/* ===============================
   UI POLISH – SAFE VISUAL UPGRADE
   =============================== */

/* تحسين عام للقراءة */
.stMarkdown, .stTextInput, .stTextArea {
    line-height: 1.9;
    font-size: 0.95rem;
}

/* تحسين الحاويات */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #020617 0%, #020617 100%);
    border-left: 1px solid #1e293b;
}

/* البطاقات */
div[data-testid="stVerticalBlockBorderWrapper"] {
    padding: 1rem;
    transition: all 0.25s ease-in-out;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: #fbbf24;
    box-shadow: 0 0 0 1px rgba(251,191,36,0.15);
}

/* تحسين SelectBox */
div[data-baseweb="select"] {
    background-color: #020617 !important;
    border-radius: 8px;
}
div[data-baseweb="select"] > div {
    border-color: #334155 !important;
}

/* Radio buttons */
div[role="radiogroup"] label {
    background: #020617;
    padding: 6px 10px;
    border-radius: 6px;
    margin-bottom: 6px;
    border: 1px solid #1e293b;
}
div[role="radiogroup"] label:hover {
    border-color: #60a5fa;
}

/* Inputs */
input, textarea {
    background-color: #020617 !important;
    border: 1px solid #334155 !important;
    color: #e5e7eb !important;
    border-radius: 8px !important;
}
input:focus, textarea:focus {
    border-color: #60a5fa !important;
    box-shadow: 0 0 0 1px rgba(96,165,250,0.4);
}

/* تحسين الأزرار */
.stButton>button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 18px rgba(37,99,235,0.35);
}

/* Progress bar */
div[data-testid="stProgress"] > div > div {
    background: linear-gradient(90deg, #fbbf24, #60a5fa);
}

/* Scrollbar (Webkit only) */
::-webkit-scrollbar {
    width: 8px;
}
::-webkit-scrollbar-track {
    background: #020617;
}
::-webkit-scrollbar-thumb {
    background: #334155;
    border-radius: 6px;
}
::-webkit-scrollbar-thumb:hover {
    background: #475569;
}

/* Placeholder المحرر */
.editor-placeholder {
    background: repeating-linear-gradient(
        45deg,
        #020617,
        #020617 10px,
        #020617 20px
    );
}

/* رسائل الحالة */
div[data-testid="stAlert"] {
    border-radius: 10px;
    border: 1px solid #334155;
}

/* تحسين التباعد العام */
.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
}

</style>
""", unsafe_allow_html=True)
