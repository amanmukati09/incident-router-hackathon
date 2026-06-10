import gradio as gr
import requests
import pandas as pd
import time

BACKEND_URL = "http://localhost:8000"

# --- Advanced CSS Styling ---
custom_css = """
body, .gradio-container { background-color: #0f172a !important; color: #f8fafc !important; font-family: 'Inter', sans-serif !important; }

/* Perfect Navbar */
.nav-container {
    display: flex !important;
    flex-direction: row !important;
    align-items: center !important;
    justify-content: space-between !important;
    background: rgba(30, 41, 59, 0.8) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 12px !important;
    padding: 12px 25px !important;
    margin-bottom: 20px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2) !important;
}
.nav-logo h1 {
    margin: 0 !important;
    background: linear-gradient(90deg, #38bdf8, #818cf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800 !important;
    font-size: 1.6rem !important;
}
.nav-user-area {
    display: flex !important;
    align-items: center !important;
    gap: 15px !important;
}
.nav-user-area p { margin: 0 !important; color: #e2e8f0 !important; font-weight: 500 !important; white-space: nowrap !important; }

/* Custom Logout Button */
button.logout-btn {
    background: transparent !important;
    border: 1px solid #ef4444 !important;
    color: #ef4444 !important;
    border-radius: 6px !important;
    padding: 4px 12px !important;
    transition: all 0.2s !important;
    box-shadow: none !important;
}
button.logout-btn:hover { background: #ef4444 !important; color: #ffffff !important; }

/* Distinct Result Cards */
.result-card {
    background: rgba(30, 41, 59, 0.6) !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
    border-radius: 12px !important;
    padding: 20px !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
}

/* Fix Table text wrapping for logs */
.table-wrap td { white-space: pre-wrap !important; word-break: break-word !important; min-width: 200px !important; }
"""

# --- API Callers ---
def api_login(email, password):
    try:
        res = requests.post(f"{BACKEND_URL}/auth/login", json={"email": email, "password": password})
        if res.status_code == 200:
            token = res.json().get("access_token")
            user_display = res.json().get("email", email)
            gr.Info("✅ Login Successful!")
            return token, gr.update(visible=False), gr.update(visible=True), f"👤 {user_display}"
        gr.Warning("❌ Login Failed.")
        return "", gr.update(visible=True), gr.update(visible=False), ""
    except:
        gr.Warning("❌ Connection Error.")
        return "", gr.update(visible=True), gr.update(visible=False), ""

def api_register(email, password, name):
    try:
        res = requests.post(f"{BACKEND_URL}/auth/register", json={"email": email, "password": password, "full_name": name})
        if res.status_code == 200:
            token = res.json().get("access_token")
            user_display = res.json().get("email", email)
            # Short sleep to let backend DB commit finish before frontend fetches history
            time.sleep(0.5) 
            gr.Info("✅ Registration Successful!")
            return token, gr.update(visible=False), gr.update(visible=True), f"👤 {user_display}"
        gr.Warning("❌ Registration Failed. Email may exist.")
        return "", gr.update(visible=True), gr.update(visible=False), ""
    except:
        gr.Warning("❌ Connection Error.")
        return "", gr.update(visible=True), gr.update(visible=False), ""

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
                "id": "ID", 
                "timestamp": "Date", 
                "raw_logs": "Searched Logs",
                "anomaly": "Anomaly Found", 
                "root_cause": "Root Cause",
                "remediation": "Remediation",
                "status": "Status"
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
        return "❌ Auth required.", "", "", gr.update()
    if not logs_text.strip():
        gr.Warning("⚠️ Please enter logs.")
        return "⚠️ Empty input.", "", "", gr.update()
    
    try:
        log_lines = [line.strip() for line in logs_text.split('\n') if line.strip()]
        res = requests.post(f"{BACKEND_URL}/diagnose", json={"logs": log_lines}, headers={"Authorization": f"Bearer {token}"})
        
        if res.status_code == 200:
            result = res.json()
            if not result.get("anomaly_detected", True):
                return "✅ No anomalies detected.", "N/A", "N/A", fetch_history(token)
            
            # SPLIT INTO 3 SEPARATE BLOCKS
            out_anomaly = f"**Type:** `{result.get('anomaly', {}).get('anomaly_type', 'N/A')}`\n**Severity:** `{result.get('anomaly', {}).get('severity', 'N/A')}`\n**Description:** {result.get('anomaly', {}).get('description', 'N/A')}"
            out_rc = f"**Cause:** {result.get('root_cause', {}).get('root_cause', 'N/A')}\n**Confidence:** {result.get('root_cause', {}).get('confidence', 0):.1%}\n**Contributing Factors:** {', '.join(result.get('root_cause', {}).get('contributing_factors', []))}"
            out_remed = f"**Immediate Actions:** {', '.join(result.get('remediation', {}).get('immediate_actions', []))}\n**Recovery Time:** {result.get('remediation', {}).get('estimated_recovery_time', 'N/A')}\n**Prevention:** {', '.join(result.get('remediation', {}).get('prevention_measures', []))}"
            
            gr.Info("⚡ Analysis Complete!")
            return out_anomaly, out_rc, out_remed, fetch_history(token)
            
        return f"❌ Backend Error: {res.text}", "", "", gr.update()
    except Exception as e:
        return f"❌ Connection Error: {str(e)}", "", "", gr.update()

def logout():
    gr.Info("🔒 Logged out.")
    return "", gr.update(visible=True), gr.update(visible=False), ""

# --- UI Layout ---
with gr.Blocks(title="AegisAI", css=custom_css, theme=gr.themes.Base()) as demo:
    session_token = gr.State("")
    
    # === AUTH VIEW ===
    with gr.Column(visible=True) as auth_view:
        gr.Markdown("<center><h2>🔐 AegisAI Portal</h2><p style='color:#94a3b8;'>Secure Incident Diagnostics</p></center>")
        with gr.Tab("Login"):
            log_email = gr.Textbox(label="Email")
            log_pass = gr.Textbox(label="Password", type="password")
            login_btn = gr.Button("Login 🚀", variant="primary")
        with gr.Tab("Register"):
            reg_name = gr.Textbox(label="Full Name")
            reg_email = gr.Textbox(label="Email")
            reg_pass = gr.Textbox(label="Password", type="password")
            register_btn = gr.Button("Sign Up 📝", variant="primary")

    # === APP VIEW ===
    with gr.Column(visible=False) as app_view:
        
        # Perfected Navbar
        with gr.Row(elem_classes="nav-container"):
            gr.Markdown("<h1>🛡️ AegisAI</h1>", elem_classes="nav-logo")
            with gr.Row(elem_classes="nav-user-area"):
                nav_user_display = gr.Markdown("")
                logout_btn = gr.Button("Logout", elem_classes="logout-btn")
            
        with gr.Tabs():
            with gr.Tab("Live Diagnosis"):
                with gr.Row():
                    with gr.Column(scale=1):
                        logs_input = gr.Textbox(label="System Logs", lines=10, placeholder="Paste logs here...")
                        diagnose_btn = gr.Button("Analyze Incident ⚡", variant="primary")
                        gr.Examples(examples=[
                            "[ERROR] nginx worker crashed\n[WARNING] memory: 90%\n[ERROR] cpu: 95%",
                            "[INFO] database pool active\n[CRITICAL] connection timeout\n[CRITICAL] query failed"
                        ], inputs=logs_input)
                    
                    # 3 Distinct Action Cards
                    with gr.Column(scale=1):
                        with gr.Group(elem_classes="result-card"):
                            gr.Markdown("### 🔴 ANOMALY DETECTED")
                            anomaly_out = gr.Markdown("Waiting for logs...")
                        with gr.Group(elem_classes="result-card"):
                            gr.Markdown("### 🔍 ROOT CAUSE")
                            rc_out = gr.Markdown("Waiting for logs...")
                        with gr.Group(elem_classes="result-card"):
                            gr.Markdown("### ⚙️ REMEDIATION")
                            remed_out = gr.Markdown("Waiting for logs...")

            with gr.Tab("My Incident History"):
                refresh_btn = gr.Button("Refresh History 🔄", size="sm")
                history_table = gr.Dataframe(interactive=False, wrap=True, elem_classes="table-wrap")

    # --- Event Wiring ---
    login_btn.click(fn=api_login, inputs=[log_email, log_pass], outputs=[session_token, auth_view, app_view, nav_user_display]).then(
        fn=fetch_history, inputs=[session_token], outputs=[history_table]
    )
    
    register_btn.click(fn=api_register, inputs=[reg_email, reg_pass, reg_name], outputs=[session_token, auth_view, app_view, nav_user_display]).then(
        fn=fetch_history, inputs=[session_token], outputs=[history_table]
    )
    
    diagnose_btn.click(fn=diagnose_logs, inputs=[logs_input, session_token], outputs=[anomaly_out, rc_out, remed_out, history_table])
    refresh_btn.click(fn=fetch_history, inputs=[session_token], outputs=[history_table])
    logout_btn.click(fn=logout, inputs=[], outputs=[session_token, auth_view, app_view, nav_user_display])

if __name__ == "__main__":
    demo.launch(share=True, server_name="0.0.0.0", server_port=7860)