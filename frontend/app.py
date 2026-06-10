import gradio as gr
import requests
import pandas as pd

BACKEND_URL = "http://localhost:8000"

# --- API Callers ---

def api_login(email, password):
    try:
        res = requests.post(f"{BACKEND_URL}/auth/login", json={"email": email, "password": password})
        if res.status_code == 200:
            token = res.json().get("access_token")
            return token, gr.update(visible=False), gr.update(visible=True), "✅ Login Successful!"
        return "", gr.update(visible=True), gr.update(visible=False), f"❌ Login Failed: {res.json().get('detail')}"
    except Exception as e:
        return "", gr.update(visible=True), gr.update(visible=False), f"❌ Connection Error: {str(e)}"

def api_register(email, password, name):
    try:
        res = requests.post(f"{BACKEND_URL}/auth/register", json={"email": email, "password": password, "full_name": name})
        if res.status_code == 200:
            token = res.json().get("access_token")
            return token, gr.update(visible=False), gr.update(visible=True), "✅ Registration Successful!"
        return "", gr.update(visible=True), gr.update(visible=False), f"❌ Registration Failed: {res.json().get('detail')}"
    except Exception as e:
        return "", gr.update(visible=True), gr.update(visible=False), f"❌ Connection Error: {str(e)}"

def fetch_history(token):
    if not token:
        return pd.DataFrame(columns=["ID", "Timestamp", "Description", "Status"])
    try:
        res = requests.get(f"{BACKEND_URL}/my-incidents", headers={"Authorization": f"Bearer {token}"})
        if res.status_code == 200:
            data = res.json()
            if not data:
                return pd.DataFrame(columns=["ID", "Timestamp", "Description", "Status"])
            return pd.DataFrame(data)[["id", "timestamp", "anomaly_description", "status"]]
        return pd.DataFrame(columns=["ID", "Timestamp", "Description", "Status"])
    except:
        return pd.DataFrame(columns=["ID", "Timestamp", "Description", "Status"])

def diagnose_logs(logs_text, token):
    if not token:
        return "❌ Please log in first.", gr.update()
    if not logs_text.strip():
        return "⚠️ Please enter some logs.", gr.update()
    
    try:
        # Split logs by newline into a list
        log_lines = [line.strip() for line in logs_text.split('\n') if line.strip()]
        
        res = requests.post(
            f"{BACKEND_URL}/diagnose", 
            json={"logs": log_lines},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if res.status_code == 200:
            data = res.json()
            if not data.get("anomaly_detected", True):
                return "✅ No anomalies detected in the provided logs.", fetch_history(token)
            
            output = f"""
### 🔴 ANOMALY DETECTED
**Type:** {data.get('anomaly', {}).get('anomaly_type')} | **Severity:** {data.get('anomaly', {}).get('severity')}
**Description:** {data.get('anomaly', {}).get('description')}

---
### 🔍 ROOT CAUSE ANALYSIS
**Root Cause:** {data.get('root_cause', {}).get('root_cause')}
**Confidence:** {data.get('root_cause', {}).get('confidence', 0):.1%}

---
### ⚙️ REMEDIATION PLAN
**Immediate Actions:** {', '.join(data.get('remediation', {}).get('immediate_actions', []))}
**Recovery Time:** {data.get('remediation', {}).get('estimated_recovery_time', 'N/A')}
            """
            return output, fetch_history(token)
        return f"❌ Error: {res.text}", gr.update()
    except Exception as e:
        return f"❌ Connection Error: {str(e)}", gr.update()

# --- UI Layout ---

custom_css = """
body { background-color: #0f172a !important; color: #e2e8f0 !important; }
"""

with gr.Blocks(title="AGENTS_026", css=custom_css, theme=gr.themes.Monochrome()) as demo:
    
    # State variable to hold the JWT token
    session_token = gr.State("")
    
    gr.Markdown("# 🛡️ AGENTS_026: Intelligent Incident Diagnostics Platform")
    auth_msg = gr.Markdown("")

    # === AUTHENTICATION VIEW ===
    with gr.Column(visible=True) as auth_view:
        with gr.Tab("Login"):
            log_email = gr.Textbox(label="Email", placeholder="test@example.com")
            log_pass = gr.Textbox(label="Password", type="password")
            login_btn = gr.Button("Login 🚀", variant="primary")
            
        with gr.Tab("Register"):
            reg_name = gr.Textbox(label="Full Name", placeholder="John Doe")
            reg_email = gr.Textbox(label="Email", placeholder="test2@example.com")
            reg_pass = gr.Textbox(label="Password", type="password")
            register_btn = gr.Button("Sign Up 📝")

    # === MAIN APP VIEW (Hidden until logged in) ===
    with gr.Column(visible=False) as app_view:
        with gr.Tabs():
            with gr.Tab("Live Diagnosis"):
                with gr.Row():
                    with gr.Column(scale=2):
                        logs_input = gr.Textbox(
                            label="Paste System Logs (One per line)", 
                            lines=10, 
                            placeholder="[ERROR] nginx worker crashed\n[WARNING] memory: 90%\n[ERROR] cpu: 95%"
                        )
                        diagnose_btn = gr.Button("Analyze Incident ⚡", variant="primary")
                        
                        gr.Examples(
                            examples=[
                                "[ERROR] nginx worker crashed\n[WARNING] memory: 90%\n[ERROR] cpu: 95%",
                                "[INFO] database pool active\n[CRITICAL] connection timeout\n[CRITICAL] query failed"
                            ],
                            inputs=logs_input
                        )
                    
                    with gr.Column(scale=3):
                        results_output = gr.Markdown("Waiting for logs... ⏳")

            with gr.Tab("My Incident History"):
                refresh_btn = gr.Button("Refresh History 🔄", size="sm")
                history_table = gr.Dataframe(interactive=False)
                
        logout_btn = gr.Button("Logout 🔒", size="sm")

    # --- Event Wiring ---
    
    # Login Flow: Attempt Login -> Hide Auth View -> Show App View -> Fetch History
    login_btn.click(
        fn=api_login, inputs=[log_email, log_pass], outputs=[session_token, auth_view, app_view, auth_msg]
    ).then(
        fn=fetch_history, inputs=[session_token], outputs=[history_table]
    )
    
    # Register Flow
    register_btn.click(
        fn=api_register, inputs=[reg_email, reg_pass, reg_name], outputs=[session_token, auth_view, app_view, auth_msg]
    ).then(
        fn=fetch_history, inputs=[session_token], outputs=[history_table]
    )
    
    # Diagnosis Flow
    diagnose_btn.click(
        fn=diagnose_logs, inputs=[logs_input, session_token], outputs=[results_output, history_table]
    )
    
    # Refresh History
    refresh_btn.click(
        fn=fetch_history, inputs=[session_token], outputs=[history_table]
    )
    
    # Logout Flow
    logout_btn.click(
        fn=lambda: ("", gr.update(visible=True), gr.update(visible=False), "Logged out successfully."),
        inputs=[], outputs=[session_token, auth_view, app_view, auth_msg]
    )

if __name__ == "__main__":
    demo.launch(share=True, server_name="0.0.0.0", server_port=7860)