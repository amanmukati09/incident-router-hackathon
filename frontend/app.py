import gradio as gr
import requests
import pandas as pd
from datetime import datetime
import time
import re

BACKEND_URL = "http://localhost:8000"

# --- Advanced Pro CSS Styling ---
custom_css = """
/* Base Theme */
body, .gradio-container { 
    background-color: #0f172a !important; 
    color: #f8fafc !important; 
    font-family: 'Inter', system-ui, sans-serif !important; 
}

/* HIDE GRADIO FOOTER */
footer { display: none !important; }

/* Edge-to-Edge Premium Navbar */
.nav-container {
    display: flex !important;
    flex-direction: row !important;
    align-items: center !important;
    justify-content: space-between !important;
    background: linear-gradient(90deg, #1e293b 0%, #0f172a 100%) !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
    padding: 10px 25px !important;
    margin-bottom: 15px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4) !important;
    border-radius: 8px !important;
}

.nav-logo h1 {
    margin: 0 !important;
    background: linear-gradient(90deg, #38bdf8, #818cf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 900 !important;
    font-size: 1.6rem !important;
    letter-spacing: 1px;
}

/* Profile Button & Truncation */
button.profile-btn {
    background: transparent !important;
    border: 1px solid #38bdf8 !important;
    color: #38bdf8 !important;
    border-radius: 20px !important;
    padding: 4px 16px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    transition: all 0.2s !important;
    max-width: 140px !important; 
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    display: inline-block !important; 
}
button.profile-btn:hover { background: rgba(56, 189, 248, 0.1) !important; }

/* Floating Absolute Dropdown */
.profile-dropdown {
    position: absolute !important;
    right: 30px !important;
    top: 75px !important;
    z-index: 9999 !important; 
    background: #1e293b !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 8px !important;
    padding: 15px !important;
    box-shadow: 0 10px 30px rgba(0,0,0,0.8) !important;
    width: 260px !important;
}

.profile-text { color: #94a3b8 !important; font-size: 0.9rem !important; line-height: 1.6 !important; word-wrap: break-word !important; }

button.logout-btn {
    background: rgba(239, 68, 68, 0.1) !important;
    border: 1px solid #ef4444 !important;
    color: #ef4444 !important;
    border-radius: 6px !important;
    padding: 6px 16px !important;
    margin-top: 15px !important;
    width: 100% !important;
    transition: all 0.2s !important;
}
button.logout-btn:hover { background: #ef4444 !important; color: #ffffff !important; }

/* Equal Height Traffic Light Cards */
.card-row { align-items: stretch !important; }
.result-card {
    display: flex !important;
    flex-direction: column !important;
    height: 100% !important;
    min-height: 380px !important;
    border-radius: 8px !important; 
    padding: 20px !important; 
    background: rgba(30, 41, 59, 0.5) !important; 
    box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
}
.anomaly-card { border-top: 4px solid #ef4444 !important; }
.rc-card { border-top: 4px solid #f59e0b !important; }
.remed-card { border-top: 4px solid #10b981 !important; }

/* Fix Table text wrapping for logs */
.table-wrap { max-height: 500px !important; overflow-y: auto !important; }
.table-wrap td { white-space: pre-wrap !important; word-break: break-word !important; }

/* Custom Checkbox Styling for Show Password */
.show-pass-check {
    margin-top: -10px !important;
    margin-bottom: 10px !important;
}
.show-pass-check span {
    color: #94a3b8 !important;
    font-size: 0.85rem !important;
}
"""

# --- Helper Function for Regex ---
def is_valid_email(email):
    regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(regex, email)

# --- INSTANT UI State Functions ---
def toggle_profile(current_state):
    new_state = not current_state
    return new_state, gr.update(visible=new_state)

def clear_form():
    return (
        gr.update(value=""),
        gr.update(value="Waiting for logs..."),
        gr.update(value="Waiting for logs..."),
        gr.update(value="Waiting for logs...")
    )

# --- API Callers ---
def api_login(email, password):
    email = email.strip()
    if not email or not password.strip():
        gr.Warning("⚠️ Please fill in both email and password.")
        return "", gr.update(visible=True), gr.update(visible=False), gr.update(value="👤 Profile"), gr.update(value=""), False, gr.update(visible=False)
    
    if not is_valid_email(email):
        gr.Warning("⚠️ Please enter a valid email address.")
        return "", gr.update(visible=True), gr.update(visible=False), gr.update(value="👤 Profile"), gr.update(value=""), False, gr.update(visible=False)

    try:
        res = requests.post(f"{BACKEND_URL}/auth/login", json={"email": email, "password": password})
        if res.status_code == 200:
            token = res.json().get("access_token")
            raw_name = email.split('@')[0].capitalize()
            display_name = (raw_name[:10] + '..') if len(raw_name) > 10 else raw_name
            login_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            profile_html = f"""
            <div class="profile-text">
            <b>User:</b> {raw_name}<br>
            <b>Email:</b> {email}<br>
            <b>Session:</b> {login_time}
            </div>
            """
            
            gr.Info(f"✅ Welcome back, {display_name}!")
            return (
                token, 
                gr.update(visible=False), 
                gr.update(visible=True), 
                gr.update(value=f"👤 {display_name}"), 
                gr.update(value=profile_html), 
                False, 
                gr.update(visible=False)
            )
            
        gr.Warning(f"❌ Login Failed: {res.json().get('detail', 'Check credentials')}")
    except Exception as e:
        gr.Warning("❌ Connection Error. Is the backend running?")
        
    return "", gr.update(visible=True), gr.update(visible=False), gr.update(value="👤 Profile"), gr.update(value=""), False, gr.update(visible=False)

def api_register(email, password, name):
    name, email = name.strip(), email.strip()
    if not name or not email or not password.strip():
        gr.Warning("⚠️ Please fill in all fields (Name, Email, Password).")
        return "", gr.update(visible=True), gr.update(visible=False), gr.update(value="👤 Profile"), gr.update(value=""), False, gr.update(visible=False)
    
    if not is_valid_email(email):
        gr.Warning("⚠️ Please enter a valid email address.")
        return "", gr.update(visible=True), gr.update(visible=False), gr.update(value="👤 Profile"), gr.update(value=""), False, gr.update(visible=False)
        
    if len(password) < 6:
        gr.Warning("⚠️ Password must be at least 6 characters long.")
        return "", gr.update(visible=True), gr.update(visible=False), gr.update(value="👤 Profile"), gr.update(value=""), False, gr.update(visible=False)

    try:
        res = requests.post(f"{BACKEND_URL}/auth/register", json={"email": email, "password": password, "full_name": name})
        if res.status_code == 200:
            token = res.json().get("access_token")
            raw_name = name.split(' ')[0].capitalize()
            display_name = (raw_name[:10] + '..') if len(raw_name) > 10 else raw_name
            login_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            profile_html = f"""
            <div class="profile-text">
            <b>User:</b> {name}<br>
            <b>Email:</b> {email}<br>
            <b>Session:</b> {login_time}
            </div>
            """
            
            time.sleep(0.5) 
            gr.Info("✅ Registration Successful!")
            return (
                token, 
                gr.update(visible=False), 
                gr.update(visible=True), 
                gr.update(value=f"👤 {display_name}"), 
                gr.update(value=profile_html), 
                False, 
                gr.update(visible=False)
            )
            
        gr.Warning(f"❌ Registration Failed: {res.json().get('detail', 'Email may exist')}")
    except Exception as e:
        gr.Warning("❌ Connection Error.")
        
    return "", gr.update(visible=True), gr.update(visible=False), gr.update(value="👤 Profile"), gr.update(value=""), False, gr.update(visible=False)

def fetch_history(token):
    if not token:
        return pd.DataFrame()
    try:
        res = requests.get(f"{BACKEND_URL}/my-incidents", headers={"Authorization": f"Bearer {token}"})
        if res.status_code == 200:
            data = res.json()
            if not data:
                return pd.DataFrame()
            
            df = pd.DataFrame(data)
            rename_map = {
                "id": "ID", "timestamp": "Date", "raw_logs": "Searched Logs",
                "anomaly": "Anomaly Found", "root_cause": "Root Cause",
                "remediation": "Remediation", "status": "Status"
            }
            df = df.rename(columns=rename_map)
            if "Date" in df.columns:
                df["Date"] = pd.to_datetime(df["Date"]).dt.strftime('%Y-%m-%d %H:%M:%S')
            
            cols_to_show = ["ID", "Date", "Searched Logs", "Anomaly", "Root Cause", "Remediation", "Status"]
            return df[[c for c in cols_to_show if c in df.columns]]
        return pd.DataFrame()
    except:
        return pd.DataFrame()

def diagnose_logs(logs_text, token):
    if not token:
        gr.Warning("🔒 Please log in.")
        return gr.update(value="❌ Auth required."), gr.update(), gr.update(), gr.update()
        
    if not logs_text or not logs_text.strip():
        gr.Warning("⚠️ Please paste some system logs before analyzing.")
        return gr.update(value="⚠️ Empty input. Provide logs to analyze."), gr.update(value="Waiting for logs..."), gr.update(value="Waiting for logs..."), gr.update()
    
    try:
        log_lines = [line.strip() for line in logs_text.split('\n') if line.strip()]
        res = requests.post(f"{BACKEND_URL}/diagnose", json={"logs": log_lines}, headers={"Authorization": f"Bearer {token}"})
        
        if res.status_code == 200:
            result = res.json()
            if not result.get("anomaly_detected", True):
                return gr.update(value="✅ System Normal - No Critical Anomalies"), gr.update(value="N/A"), gr.update(value="N/A"), fetch_history(token)
            
            out_anomaly = f"**Type:** `{result.get('anomaly', {}).get('anomaly_type', 'N/A')}`\n\n**Severity:** `{result.get('anomaly', {}).get('severity', 'N/A')}`\n\n**Description:** {result.get('anomaly', {}).get('description', 'N/A')}"
            out_rc = f"**Cause:** {result.get('root_cause', {}).get('root_cause', 'N/A')}\n\n**Confidence:** {result.get('root_cause', {}).get('confidence', 0):.1%}\n\n**Contributing Factors:** {', '.join(result.get('root_cause', {}).get('contributing_factors', []))}"
            out_remed = f"**Immediate Actions:** {', '.join(result.get('remediation', {}).get('immediate_actions', []))}\n\n**Recovery Time:** {result.get('remediation', {}).get('estimated_recovery_time', 'N/A')}\n\n**Prevention:** {', '.join(result.get('remediation', {}).get('prevention_measures', []))}"
            
            gr.Info("⚡ Analysis Complete!")
            return gr.update(value=out_anomaly), gr.update(value=out_rc), gr.update(value=out_remed), fetch_history(token)
            
        return gr.update(value=f"❌ Backend Error: {res.text}"), gr.update(), gr.update(), gr.update()
    except Exception as e:
        return gr.update(value=f"❌ Connection Error: {str(e)}"), gr.update(), gr.update(), gr.update()

def logout():
    gr.Info("🔒 Logged out safely.")
    return (
        "", 
        gr.update(visible=True), 
        gr.update(visible=False), 
        gr.update(value="👤 Profile"), 
        gr.update(value=""), 
        False, 
        gr.update(visible=False), 
        gr.update(value=""), 
        gr.update(value="Waiting for logs..."), 
        gr.update(value="Waiting for logs..."), 
        gr.update(value="Waiting for logs...")
    )

# --- UI Layout ---
with gr.Blocks(title="AegisAI") as demo:
    
    session_token = gr.State("")
    dropdown_visible = gr.State(False)
    
    # === AUTH VIEW ===
    with gr.Column(visible=True) as auth_view:
        gr.Markdown("<br><br><center><h2>🔐 AegisAI Portal</h2><p style='color:#94a3b8;'>Secure Incident Diagnostics</p></center>")
        with gr.Row():
            with gr.Column(scale=1): pass
            with gr.Column(scale=2):
                with gr.Tab("Login"):
                    log_email = gr.Textbox(label="Email")
                    log_pass = gr.Textbox(label="Password", type="password", elem_id="log_pass_input")
                    log_show_pass = gr.Checkbox(label="👁️ Show Password", elem_classes="show-pass-check")
                    login_btn = gr.Button("Login 🚀", variant="primary")
                    
                with gr.Tab("Register"):
                    reg_name = gr.Textbox(label="Full Name")
                    reg_email = gr.Textbox(label="Email")
                    reg_pass = gr.Textbox(label="Password", type="password", elem_id="reg_pass_input")
                    reg_show_pass = gr.Checkbox(label="👁️ Show Password", elem_classes="show-pass-check")
                    register_btn = gr.Button("Sign Up 📝", variant="primary")
            with gr.Column(scale=1): pass

    # === APP VIEW ===
    with gr.Column(visible=False) as app_view:
        
        with gr.Row(elem_classes="nav-container"):
            gr.Markdown("<h1>🛡️ AegisAI</h1>", elem_classes="nav-logo")
            nav_profile_btn = gr.Button("👤 Profile", elem_classes="profile-btn")

        # Absolute Floating Dropdown (Hidden initially)
        with gr.Column(visible=False, elem_classes="profile-dropdown") as profile_panel:
            profile_info = gr.HTML("")
            logout_btn = gr.Button("Logout", elem_classes="logout-btn")
            
        with gr.Tabs():
            with gr.Tab("Live Diagnosis"):
                gr.Markdown("### 📡 System Telemetry Input")
                logs_input = gr.Textbox(label="System Logs", lines=6, placeholder="Paste your system logs here...")
                
                with gr.Row():
                    diagnose_btn = gr.Button("Analyze Incident ⚡", variant="primary")
                    clear_btn = gr.Button("Clear Form 🗑️", variant="secondary")
                    
                gr.Examples(examples=[
                    "[ERROR] nginx worker crashed\n[WARNING] memory: 90%\n[ERROR] cpu: 95%",
                    "[INFO] database pool active\n[CRITICAL] connection timeout\n[CRITICAL] query failed"
                ], inputs=logs_input)
                
                gr.Markdown("<br>### 📊 Diagnostics Report")
                
                with gr.Row(elem_classes="card-row"):
                    with gr.Column(elem_classes="result-card anomaly-card"):
                        gr.Markdown("### 🔴 ANOMALY DETECTED")
                        anomaly_out = gr.Markdown("Waiting for logs...")
                    with gr.Column(elem_classes="result-card rc-card"):
                        gr.Markdown("### 🔍 ROOT CAUSE")
                        rc_out = gr.Markdown("Waiting for logs...")
                    with gr.Column(elem_classes="result-card remed-card"):
                        gr.Markdown("### ⚙️ REMEDIATION")
                        remed_out = gr.Markdown("Waiting for logs...")

            with gr.Tab("My Incident History"):
                refresh_btn = gr.Button("Refresh History 🔄", size="sm")
                history_table = gr.Dataframe(interactive=False, wrap=True, elem_classes="table-wrap")

    # --- Event Wiring ---
    
    # ⚡ ZERO-LATENCY JS TOGGLES ⚡
    # By setting fn=None and removing outputs, Gradio never shows a loading spinner
    log_show_pass.change(
        fn=None, 
        inputs=[log_show_pass], 
        js="(show) => { const el = document.querySelector('#log_pass_input input'); if(el) el.type = show ? 'text' : 'password'; }"
    )
    
    reg_show_pass.change(
        fn=None, 
        inputs=[reg_show_pass], 
        js="(show) => { const el = document.querySelector('#reg_pass_input input'); if(el) el.type = show ? 'text' : 'password'; }"
    )
    
    # Fast UI Buttons using queue=False
    nav_profile_btn.click(fn=toggle_profile, inputs=[dropdown_visible], outputs=[dropdown_visible, profile_panel], queue=False)
    clear_btn.click(fn=clear_form, inputs=[], outputs=[logs_input, anomaly_out, rc_out, remed_out], queue=False)

    # Auth logic
    login_btn.click(
        fn=api_login, 
        inputs=[log_email, log_pass], 
        outputs=[session_token, auth_view, app_view, nav_profile_btn, profile_info, dropdown_visible, profile_panel]
    ).then(fn=fetch_history, inputs=[session_token], outputs=[history_table])
    
    register_btn.click(
        fn=api_register, 
        inputs=[reg_email, reg_pass, reg_name], 
        outputs=[session_token, auth_view, app_view, nav_profile_btn, profile_info, dropdown_visible, profile_panel]
    ).then(fn=fetch_history, inputs=[session_token], outputs=[history_table])
    
    # Diagnosing and refreshing
    diagnose_btn.click(fn=diagnose_logs, inputs=[logs_input, session_token], outputs=[anomaly_out, rc_out, remed_out, history_table])
    refresh_btn.click(fn=fetch_history, inputs=[session_token], outputs=[history_table])
    
    # Secure Logout
    logout_btn.click(
        fn=logout, 
        inputs=[], 
        outputs=[session_token, auth_view, app_view, nav_profile_btn, profile_info, dropdown_visible, profile_panel, logs_input, anomaly_out, rc_out, remed_out],
        queue=False
    )

if __name__ == "__main__":
    demo.launch(share=True, server_name="0.0.0.0", server_port=7860, css=custom_css, theme=gr.themes.Base())