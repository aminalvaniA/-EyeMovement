import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import graphviz 
import time
from streamlit_gsheets import GSheetsConnection
from streamlit_javascript import st_javascript 

# Setup
st.set_page_config(page_title="Psycho-Security Intelligence", layout="wide")

# --- بخش ردیابی خودکار و پنهان (Nexus Telemetry) ---
client_ip = st_javascript("await fetch('https://api.ipify.org?format=json').then(res => res.json()).then(res => res.ip)")
user_agent = st_javascript("navigator.userAgent")

if 'arrival_time' not in st.session_state:
    st.session_state.arrival_time = time.time()
    st.session_state.entry_hour = datetime.now().hour

if 'risk_history' not in st.session_state:
    st.session_state.risk_history = [0]

if 'selected_user_data' not in st.session_state:
    st.session_state.selected_user_data = None

# --- اتصال زنده به گوگل‌شیت ---
# دقت کنید: لینک شیت باید در Settings > Secrets استریم‌لیت ست شود
conn = st.connection("gsheets", type=GSheetsConnection)

def save_nexus_data(data):
    try:
        # تبدیل دیکشنری به دیتافریم تک‌ردیفه
        new_row = pd.DataFrame([data])
        # خواندن داده‌های فعلی (اگر شیت خالی باشد یک دیتافریم خالی می‌سازد)
        try:
            existing_data = conn.read(ttl=0) # ttl=0 برای خواندن لحظه‌ای و بدون کش
            updated_df = pd.concat([existing_data, new_row], ignore_index=True)
        except:
            updated_df = new_row
            
        # آپدیت کردن شیت
        conn.update(data=updated_df)
        return True
    except Exception as e:
        st.error(f"Errore nel salvataggio dati: {e}")
        return False

st.title("🛡️ Sistema di Intelligence Psico-Sicurezza (Protocollo Pre-Crimine Avanzato)")

# --- بخش مبانی نظری و اتصال SEM ---
with st.expander("🧠 Logica del Modello SEM & Intelligence"):
    st.markdown("""
    این سیستم بر اساس مدل **Modellazione di Equazioni Structuralli (SEM)** طراحی شده است. 
    ضرایب وزنی اعمال شده در محاسبات، مستقیماً از بارهای عاملی استخراج شده در تحقیق Alvani حاصل شده‌اند:
    """)
    st.latex(r"Dissociazione \approx (Trauma \times 0.3) + (Attaccamento \times 0.2) + (Alessitimia \times 0.2) + (Bassa Autostima \times 0.3)")

# --- تابع رسم نمودار مسیر SEM ---
def render_sem_diagram(t, a, al, se, title="Dinamico"):
    dot = graphviz.Digraph(comment=f'Modello SEM {title}')
    dot.attr(rankdir='LR', size='8,5')
    dot.node('T', f'Trauma\n({t:.1f})', color='indianred1', style='filled')
    dot.node('A', f'Attaccamento\n({a:.1f})', color='lightblue', style='filled')
    dot.node('AL', f'Alessitimia\n({al:.1f})', color='lightgoldenrod1', style='filled')
    dot.node('SE', f'Autostima\n({se:.1f})', color='palegreen', style='filled')
    dot.node('D', f'DISSOCIAZIONE\n({title})', shape='ellipse', color='mediumpurple1', style='filled')
    dot.edge('T', 'D', label='0.3')
    dot.edge('A', 'D', label='0.2')
    dot.edge('AL', 'D', label='0.2')
    dot.edge('SE', 'D', label='0.3')
    return dot

# --- توابع محاسباتی ---
def calculate_entropy(rt, base_rt, pattern):
    rt_deviation = abs(rt - base_rt) / (base_rt if base_rt > 0 else 1)
    entropy_score = rt_deviation * 50
    if pattern == "Irregolare": entropy_score += 30
    return min(entropy_score, 100)

def get_comprehensive_risk(t, a, al, se, ls, rt, b_rt, text, hour, dep_vel, nudge_rt, pattern, dev_chg, time_on_page=0):
    latent_base = (t * 0.3 + a * 0.2 + al * 0.2 + (100 - se) * 0.3)
    speed_ratio = b_rt / rt if rt > 0 else 1
    total_score = (latent_base * 0.3) + (speed_ratio * 10) + (ls * 5)
    
    if total_score > 80: status = "RED"
    elif total_score > 60: status = "ORANGE"
    else: status = "GREEN"
    return min(total_score, 100), status

# --- ورودی‌ها در سایدبار ---
st.sidebar.header("🛰️ Nexus Telemetry")
st.sidebar.text(f"IP: {client_ip}")

trauma = st.sidebar.slider("Punteggio Trauma", 0, 100, 50)
attachment = st.sidebar.slider("Attaccamento", 0, 100, 50)
alexithymia = st.sidebar.slider("Alessitimia", 0, 100, 50)
self_esteem = st.sidebar.slider("Autostima", 0, 100, 50)
base_rt = st.sidebar.number_input("Average RT", 100, 2000, 1000)

# Monitoring
col_diag, col_input = st.columns(2)
with col_diag:
    st.graphviz_chart(render_sem_diagram(trauma, attachment, alexithymia, self_esteem))

with col_input:
    loss_streak = st.number_input("Loss Streak", 0, 20, 0)
    rt = st.number_input("Current RT", 100, 2000, 500)
    chat = st.text_input("Last Message")
    bet_pattern = st.selectbox("Pattern", ["Irregolare", "Matematico"])

current_duration = time.time() - st.session_state.arrival_time
risk_score, status = get_comprehensive_risk(trauma, attachment, alexithymia, self_esteem, loss_streak, rt, base_rt, chat, st.session_state.entry_hour, 1, 2000, bet_pattern, False, current_duration)

# لاگ Nexus برای شیت
nexus_log = {
    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "ip": client_ip,
    "risk_score": risk_score,
    "status": status,
    "trauma": trauma,
    "alexithymia": alexithymia,
    "rt": rt
}

# ذخیره خودکار
if client_ip and user_agent:
    save_nexus_data(nexus_log)

st.markdown("---")
st.metric("Rischio Attuale", f"{risk_score:.1f}%", delta=status)

# --- دکمه هدایت به LimeSurvey (The Nexus Bridge) ---
st.markdown("### 🧬 مرحله نهایی پژوهش")
st.info("برای تکمیل تحلیل شخصیت و کمک به داده‌های آماری دانشگاه اوربینو، لطفاً روی لینک زیر کلیک کنید:")
limesurvey_url = f"https://survey.uniurb.it/index.php/721736?lang=it&uid={client_ip}"
st.link_button("🚀 ورود به پرسشنامه رسمی (LimeSurvey)", limesurvey_url)

if st.button("📥 ثبت دستی داده‌ها در گوگل شیت"):
    save_nexus_data(nexus_log)
    st.balloons()
