import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import graphviz 
import time
from streamlit_gsheets import GSheetsConnection
# کتابخانه برای استخراج داده‌های سمت کلاینت (IP و User-Agent)
from streamlit_javascript import st_javascript 

# Setup
st.set_page_config(page_title="Psycho-Security Intelligence", layout="wide")

# --- اصلاح خودکار فرمت کلید در حافظه (جلوگیری از ارور PEM) ---
if "connections" in st.secrets and "gsheets" in st.secrets.connections:
    raw_key = st.secrets.connections.gsheets.get("private_key", "")
    if "\\n" in raw_key:
        st.secrets.connections.gsheets["private_key"] = raw_key.replace("\\n", "\n")

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

# --- مدیریت اتصال به Google Sheets ---
conn = None
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.sidebar.error(f"⚠️ Errore Connessione DB: {e}")

def save_nexus_data(data):
    if conn is None: return False
    try:
        new_row = pd.DataFrame([data])
        try:
            existing_data = conn.read(ttl=0) 
            updated_df = pd.concat([existing_data, new_row], ignore_index=True)
        except:
            updated_df = new_row
        conn.update(data=updated_df)
        return True
    except Exception as e:
        st.error(f"Errore Nexus: {e}")
        return False

st.title("🛡️ Sistema di Intelligence Psico-Sicurezza (Protocollo Pre-Crimine Avanzato)")

# --- بخش مبانی نظری و اتصال SEM ---
with st.expander("🧠 Logica del Modello SEM & Intelligence"):
    st.markdown("""
    این سیستم بر اساس مدل **Modellazione di Equazioni Strutturali (SEM)** طراحی شده است. 
    ضرایب وزنی اعمال شده در محاسبات، مستقیماً از بارهای عاملی استخراج شده در تحقیق Alvani حاصل شده‌اند:
    """)
    st.latex(r"Dissociazione \approx (Trauma \times 0.3) + (Attaccamento \times 0.2) + (Alessitimia \times 0.2) + (Bassa Autostima \times 0.3)")
    st.info("💡 ضرایب فوق، وزن هر متغیر مکنون را در ایجاد وضعیت گسست شخصیت (Dissociazione) نشان می‌دهند.")

# --- تابع رسم نمودار مسیر SEM ---
def render_sem_diagram(t, a, al, se, title="Dinamico"):
    dot = graphviz.Digraph(comment=f'Modello SEM {title}')
    dot.attr(rankdir='LR', size='8,5')
    
    dot.node('T', f'Trauma\n({t:.1f})', color='indianred1', style='filled')
    dot.node('A', f'Attaccamento\n({a:.1f})', color='lightblue', style='filled')
    dot.node('AL', f'Alessitimia\n({al:.1f})', color='lightgoldenrod1', style='filled')
    dot.node('SE', f'Autostima\n({se:.1f})', color='palegreen', style='filled')
    dot.node('D', f'DISSOCIAZIONE\n({title})', shape='ellipse', color='mediumpurple1', style='filled')
    
    dot.edge('T', 'D', label='0.3', penwidth=str((t/20)+1))
    dot.edge('A', 'D', label='0.2', penwidth=str((a/20)+1))
    dot.edge('AL', 'D', label='0.2', penwidth=str((al/20)+1))
    dot.edge('SE', 'D', label='0.3', penwidth=str(((100-se)/20)+1))
    
    return dot

# --- توابع محاسباتی ---
def calculate_entropy(rt, base_rt, pattern):
    rt_deviation = abs(rt - base_rt) / (base_rt if base_rt > 0 else 1)
    entropy_score = rt_deviation * 50
    if pattern == "Irregolare": entropy_score += 30
    return min(entropy_score, 100)

def get_comprehensive_risk(t, a, al, se, ls, rt, b_rt, text, hour, dep_vel, nudge_rt, pattern, dev_chg, time_on_page=0):
    latent_base = (t * 0.3 + a * 0.2 + al * 0.2 + (100 - se) * 0.3)
    somatic_words = ["battito", "sudore", "respiro", "nausea"]
    somatic_risk = 20 if any(w in str(text).lower() for w in somatic_words) and al > 70 else 0
    speed_ratio = b_rt / rt if rt > 0 else 1
    baseline_alert = 40 if speed_ratio >= 3 else 0
    circadian_risk = 35 if 2 <= hour <= 5 else 0
    acceleration_risk = 45 if dep_vel >= 3 else 0
    nudge_fail = 30 if nudge_rt < 500 else 0
    entropy = calculate_entropy(rt, b_rt, pattern)
    impulsivity_entropy = 25 if time_on_page < 10 else 0 
    
    diss_trigger = (1200 / max(rt, 1)) * (3.5 if ls >= 3 else 1.0)
    keywords = ["inutile", "fallimento", "sparire", "vuoto", "anagrafe"]
    text_risk = 25 if any(w in str(text).lower() for w in keywords) else 0
    device_risk = 30 if dev_chg else 0
    
    total_score = (latent_base * 0.25) + (diss_trigger * 5) + baseline_alert + circadian_risk + acceleration_risk + nudge_fail + (entropy * 0.2) + text_risk + somatic_risk + impulsivity_entropy + device_risk
    
    if pattern == "Matematico/Fisso" and rt > 800: status = "PURPLE"
    elif total_score > 90 or (ls >= 3 and nudge_fail > 0): status = "RED"
    elif total_score > 75: status = "ORANGE"
    else: status = "GREEN"
    return min(total_score, 100), status

# --- مدیریت داده‌های ورودی ---
default_vals = st.session_state.selected_user_data if st.session_state.selected_user_data else {
    "trauma": 75, "attachment": 60, "alexithymia": 80, "self_esteem": 30, "base_rt": 1000,
    "loss": 3, "dep": 1, "hour": st.session_state.entry_hour, "rt": 350, "nudge": 2000, "pattern": "Irregolare", "text": "Non capisco cosa provo...", "dev": False
}

# Sidebar
st.sidebar.header("Profilo Psicologico Utente (Fase 1)")
trauma = st.sidebar.slider("Punteggio Trauma (PCL-5)", 0, 100, int(default_vals["trauma"]))
attachment = st.sidebar.slider("Attaccamento Insicuro (ECR-R)", 0, 100, int(default_vals["attachment"]))
alexithymia = st.sidebar.slider("Alessitimia (TAS-20)", 0, 100, int(default_vals["alexithymia"]))
self_esteem = st.sidebar.slider("Autostima (RSES)", 0, 100, int(default_vals["self_esteem"]))
st.sidebar.markdown("---")
st.sidebar.header("Baseline Utente")
base_rt = st.sidebar.number_input("Average RT (ms)", 100, 2000, int(default_vals["base_rt"]))

st.sidebar.markdown("---")
st.sidebar.header("🛰️ Nexus Telemetry")
st.sidebar.text(f"IP: {client_ip}")
st.sidebar.text(f"Entry Hour: {st.session_state.entry_hour}:00")

# Monitoring UI
st.header("Monitoraggio Live & Analisi Entropica")
col_diag, col_input = st.columns([1, 1])

with col_diag:
    st.subheader("📊 Visualizzazione Dinamica SEM")
    st.graphviz_chart(render_sem_diagram(trauma, attachment, alexithymia, self_esteem))

with col_input:
    c1, c2 = st.columns(2)
    with c1:
        loss_streak = st.number_input("Perdite consecutive", 0, 20, int(default_vals["loss"]))
        deposit_velocity = st.number_input("Depositi (30 min)", 0, 10, int(default_vals["dep"]))
    with c2:
        hour_of_day = st.slider("Ora attività", 0, 23, int(default_vals["hour"]))
        rt = st.number_input("RT attuale (ms)", 100, 2000, int(default_vals["rt"]))
    nudge_rt = st.number_input("Nudge Response (ms)", 0, 5000, int(default_vals["nudge"]))
    bet_pattern = st.selectbox("Pattern scommesse", ["Irregolare", "Matematico/Fisso"], index=(0 if default_vals["pattern"] == "Irregolare" else 1))
    chat = st.text_input("Ultimo messaggio", str(default_vals["text"]))
    is_device_changed = st.checkbox("Cambio dispositivo/VPN", value=default_vals["dev"])

current_duration = time.time() - st.session_state.arrival_time
risk_score, status = get_comprehensive_risk(trauma, attachment, alexithymia, self_esteem, loss_streak, rt, base_rt, chat, hour_of_day, deposit_velocity, nudge_rt, bet_pattern, is_device_changed, current_duration)

# ساختار کامل لاگ Nexus
nexus_log = {
    "user_id": f"ALVANI_{int(time.time())}", 
    "date": datetime.now().strftime("%Y-%m-%d"),
    "actual_crime_date": (datetime.now() + pd.Timedelta(days=14)).strftime("%Y-%m-%d"),
    "trauma": trauma, "attachment": attachment, "alexithymia": alexithymia, "self_esteem": self_esteem,
    "loss": loss_streak, "rt": rt, "base_rt": base_rt, "text": chat, "hour": hour_of_day,
    "dep": deposit_velocity, "nudge": nudge_rt, "pattern": bet_pattern, "risk_score": risk_score,
    "ip": str(client_ip), "user_agent": str(user_agent)
}

# ذخیره خودکار
if client_ip and user_agent and conn: save_nexus_data(nexus_log)

st.markdown("---")
st.markdown("### 📋 Executive Summary")
sum_col1, sum_col2, sum_col3 = st.columns(3)
with sum_col1: st.metric("Punteggio di rischio", f"{risk_score:.1f}%")
with sum_col2: st.info(f"**Stato:** {status}")
with sum_col3:
    if status == "RED": st.error("⚠️ Blocco Preventivo")
    elif status == "ORANGE": st.warning("🟠 Intervento Nudge")
    else: st.success("✅ Monitoraggio Normale")

if st.button("🚀 Registra Profilo nel Database Nexus"):
    if save_nexus_data(nexus_log): st.success("Dati inviati!")

# --- بخش تحلیل آفلاین و CSV (بدون حذف) ---
st.markdown("---")
st.subheader("📂 Analisi Offline e Analisi Multi-Soggetto")
uploaded = st.file_uploader("Carica file CSV")

if uploaded:
    df = pd.read_csv(uploaded)
    res_score, res_status = [], []
    for _, row in df.iterrows():
        r, s = get_comprehensive_risk(row["trauma"], row["attachment"], row["alexithymia"], row["self_esteem"], row["loss"], row["rt"], row["base_rt"], row["text"], row["hour"], row["dep"], row["nudge"], row["pattern"], False, 15)
        res_score.append(r); res_status.append(s)
    df["risk_score"], df["status"] = res_score, res_status
    
    selected_rows = st.dataframe(df, on_select="rerun", selection_mode="multi-row", use_container_width=True)
    indices = selected_rows["selection"]["rows"]
    
    if len(indices) > 0:
        st.markdown("### 📊 Executive Summary del Gruppo")
        selected_df = df.iloc[indices].copy()
        g1, g2, g3 = st.columns(3)
        g1.metric("Media Rischio", f"{selected_df['risk_score'].mean():.1f}%")
        g2.metric("Soggetti", len(selected_df))
        g3.bar_chart(selected_df["status"].value_counts())

        # --- تحلیل تشدید ریسک (Aggravamento) ---
        st.markdown("### 🔍 Analisi di Aggravamento")
        if 'user_id' in df.columns and 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            unique_users = df['user_id'].unique()
            agg_data = []
            for uid in unique_users:
                u_hist = df[df['user_id'] == uid].sort_values(by='date')
                if len(u_hist) >= 2:
                    past, now = u_hist.iloc[0], u_hist.iloc[-1]
                    r_past, _ = get_comprehensive_risk(past['trauma'], past['attachment'], past['alexithymia'], past['self_esteem'], past['loss'], past['rt'], past['base_rt'], "", 12, 1, 2000, "Irregolare", False, 15)
                    r_now, s_now = get_comprehensive_risk(now['trauma'], now['attachment'], now['alexithymia'], now['self_esteem'], now['loss'], now['rt'], now['base_rt'], "", 12, 1, 2000, "Irregolare", False, 15)
                    if r_now > r_past: agg_data.append({"User ID": uid, "Rischio (Past)": f"{r_past:.1f}%", "Rischio (Now)": f"{r_now:.1f}%", "Stato": s_now})
            if agg_data: st.table(pd.DataFrame(agg_data))

        st.graphviz_chart(render_sem_diagram(selected_df["trauma"].mean(), selected_df["attachment"].mean(), selected_df["alexithymia"].mean(), selected_df["self_esteem"].mean(), title="Gruppo"))

        # --- نوار زمانی پیش‌بینی جرم (Timeline) ---
        st.markdown("#### ⏳ Predictive Timeline")
        selected_df['event_date'] = pd.to_datetime(selected_df.get('date', datetime.now()))
        selected_df['actual_crime_date'] = selected_df['event_date'] + pd.Timedelta(days=14)
        timeline_df = selected_df[selected_df['status'].str.contains("RED|PURPLE", na=False)].copy()
        if not timeline_df.empty:
            fig_t = px.timeline(timeline_df, x_start="event_date", x_end="actual_crime_date", y="user_id", color="risk_score", color_continuous_scale="Reds")
            st.plotly_chart(fig_t, use_container_width=True)

# Trend & Download
st.session_state.risk_history.append(risk_score)
if len(st.session_state.risk_history) > 20: st.session_state.risk_history.pop(0)
st.subheader("📈 Analisi del trend")
st.line_chart(st.session_state.risk_history)

st.sidebar.markdown("---")
with open(__file__, "r", encoding="utf-8") as f: code_content = f.read()
st.sidebar.download_button(label="📥 Scarica Codice (.py)", data=code_content, file_name="psycho_app.py")
