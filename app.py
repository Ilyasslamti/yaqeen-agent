
import streamlit as st
import feedparser
import trafilatura
import os
import socket
import concurrent.futures
import base64
import time
from openai import OpenAI
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

# ==========================================
# 0. الإعدادات الأساسية
# ==========================================
st.set_page_config(
    page_title="Yaqeen Press | سيادة الخبر",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

try:
    from manadger_lib import RSS_DATABASE, get_safe_key, ELITE_PROMPT
except ImportError:
    st.error("❌ ملف manadger_lib.py مفقود.")
    st.stop()

ua = UserAgent()
socket.setdefaulttimeout(30)

if 'page' not in st.session_state: st.session_state.page = 'login'

# ==========================================
# 1. التصميم الملكي المحسن
# ==========================================
def inject_royal_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;600;700;800&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Almarai:wght@300;400;700;800&display=swap');
        
        /* === إعدادات أساسية === */
        html, body, [class*="css"], div, h1, h2, h3, h4, p, span, button, input, textarea, select, option {
            font-family: 'Tajawal', 'Almarai', sans-serif !important;
            direction: rtl;
        }
        
        .stApp {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
            background-attachment: fixed;
            min-height: 100vh;
        }
        
        /* === إخفاء عناصر Streamlit الافتراضية === */
        header, footer { 
            visibility: hidden; 
            height: 0 !important;
        }
        
        /* === تحسين القوائم المنسدلة === */
        div[data-baseweb="select"] {
            border-radius: 12px !important;
            border: 1px solid #334155 !important;
            background: #1e293b !important;
        }
        
        div[data-baseweb="select"] span, li[role="option"] span {
            white-space: normal !important;
            overflow: visible !important;
            text-overflow: clip !important;
            line-height: 1.6 !important;
            height: auto !important;
            padding: 8px 12px !important;
            color: #e2e8f0 !important;
        }
        
        li[role="option"] {
            border-bottom: 1px solid #334155 !important;
            padding: 12px 16px !important;
            height: auto !important;
            min-height: 60px;
            background: #1e293b !important;
            transition: all 0.2s ease !important;
        }
        
        li[role="option"]:hover {
            background: #2d3748 !important;
            transform: translateX(-5px);
        }
        
        /* === تصميم الهيدر المحسن === */
        .royal-header {
            background: linear-gradient(90deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.95) 100%);
            border-bottom: 3px solid linear-gradient(90deg, #fbbf24 0%, #f59e0b 100%);
            padding: 25px 40px;
            margin: -1rem -1rem 30px -1rem;
            backdrop-filter: blur(15px);
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 15px 40px -15px rgba(0, 0, 0, 0.6);
            position: relative;
            overflow: hidden;
        }
        
        .royal-header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #fbbf24 0%, #f59e0b 100%);
        }
        
        .brand-container {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .brand-logo {
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
            color: #0f172a;
            box-shadow: 0 5px 15px rgba(251, 191, 36, 0.3);
        }
        
        .brand-title {
            color: white;
            font-size: 2.2rem;
            font-weight: 800;
            background: linear-gradient(90deg, #f8fafc 0%, #cbd5e1 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
        }
        
        .brand-subtitle {
            color: #94a3b8;
            font-size: 1rem;
            font-weight: 500;
            margin-top: 5px;
            letter-spacing: 1px;
        }
        
        .status-container {
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            gap: 10px;
        }
        
        .live-badge {
            background: linear-gradient(90deg, #ef4444 0%, #dc2626 100%);
            color: white;
            padding: 8px 20px;
            border-radius: 25px;
            font-size: 0.85rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 4px 15px rgba(239, 68, 68, 0.3);
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { box-shadow: 0 4px 15px rgba(239, 68, 68, 0.3); }
            50% { box-shadow: 0 4px 25px rgba(239, 68, 68, 0.5); }
            100% { box-shadow: 0 4px 15px rgba(239, 68, 68, 0.3); }
        }
        
        .date-display {
            color: #cbd5e1;
            font-weight: 600;
            font-size: 1rem;
            background: rgba(30, 41, 59, 0.7);
            padding: 8px 20px;
            border-radius: 20px;
            border: 1px solid #334155;
        }
        
        /* === تحسين البطاقات === */
        div[data-testid="stExpander"], 
        div[data-testid="stVerticalBlockBorderWrapper"],
        .stContainer {
            background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
            border: 1px solid #334155;
            border-radius: 16px;
            padding: 20px;
