# your_name Site Agent 👤🤖

A personal AI-powered chatbot that represents **your_name** online.  
It loads profile details (summary + LinkedIn PDF), answers questions faithfully,  
and can log unknown questions or capture user contact details via tools.

---

## ✨ Features
- ✅ Acts as a virtual your_name, answering career-related queries
- ✅ Uses OpenAI function calling for two tools:
  - record_user_details → logs email + notes
  - record_unknown_question → captures unanswered queries
- ✅ Push notifications via Pushover
- ✅ Runs in-browser via a Gradio ChatInterface

---

## 🛠️ Setup

1. Clone the repo:
   git clone https://github.com/YOUR-USER/Agentic_AI.git
   cd Agentic_AI/Chatbot

2. Install dependencies:
   pip install -r requirements.txt

3. Create .env file:
   OPENAI_API_KEY=sk-...
   PUSHOVER_TOKEN=...
   PUSHOVER_USER=...

4. Add supporting files:
   - me/summary.txt
   - me/linkedin.pdf

5. Run the app:
   personally_you.py

---

## 🚀 Usage
- Open the Gradio UI (it will auto-launch in browser).
- Chat with the AI as if you are speaking to your_name.
- If you provide an email, it will be recorded.
- Unknown questions are logged automatically.

---



