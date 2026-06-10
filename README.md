AegisAI: Intelligent Incident Router & SRE Copilot
AegisAI is an automated incident diagnostic and remediation platform designed for Site Reliability Engineers (SREs). It leverages local LLM inference (via Ollama) and a FastAPI backend to ingest system logs, perform automated root cause analysis (RCA), and provide interactive chat-based remediation support.

🚀 Key Features
Live Incident Diagnosis: Paste logs to get automated anomaly detection and root cause insights.

AI Copilot: A chat-based assistant that guides engineers through remediation steps.

Incident History: Tracks all previous diagnostics per user.

Admin Dashboard: Role-based access control with telemetry overview for team leads.

🛠 Prerequisites
Before running the application, ensure you have the following installed:

Python 3.10+

Ollama (Required for local AI processing)

⚙️ Setup Guide
1. Install & Setup Ollama
AegisAI uses Llama 3 for intelligent diagnostics.

Install:

Bash
curl -fsSL https://ollama.com/install.sh | sh
Pull Model:

Bash
ollama pull llama3
Keep the Ollama service running in the background.

2. Clone and Prepare Environment
Bash
# Clone the repository
git clone https://github.com/amanmukati09/incident-router-hackathon.git
cd incident-router-hackathon

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
if any more installations required then install them as per errors #tip
3. Run the Application
You will need two terminal windows open in the project root.

Terminal 1 (Backend):

Bash
source venv/bin/activate
python backend/app.py
Terminal 2 (Frontend):

Bash
source venv/bin/activate
python frontend/app.py
🔐 Administration & Bootstrapping
AegisAI supports multi-user roles (User/Admin). To bootstrap your instance:

Navigate to the Login/Register page.

Register your first account. The first user registered in a clean database is automatically granted Admin privileges.

Admin Credentials:

Email: admin@gmail.com
Password: Admin##2002## (or any secure password you prefer for the first account).

📂 Project Structure
Plaintext
/
├── backend/
│   ├── app.py          # FastAPI server & API Endpoints
│   ├── models.py       # SQLAlchemy database schemas
│   ├── auth.py         # JWT security & role management
│   └── agents/         # AI logic (Monitor, Diagnosis, Remediation, Chat)
├── frontend/
│   └── app.py          # Gradio UI & State Management
├── requirements.txt    # Python dependencies
└── README.md
⚠️ Troubleshooting
Backend Timeout (500 Error): If the AI takes too long to respond, check that your Ollama service is running (ollama list) and that you have sufficient RAM available.

404 on API Generate: Ensure you have run ollama pull llama3 successfully.

Database Lock: If you see database schema errors after major code changes, simply delete the local app.db file and restart the backend to trigger a fresh migration.