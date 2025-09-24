# Deep Research Pipeline 🔎🧠

A multi-agent research assistant that takes a user query, plans searches,  
executes them, synthesizes findings into a long markdown report,  
and sends the report via email.

---

## ✨ Features
- 🗺️ Planner Agent → generates a set of search queries
- 🌐 Search Agent → performs web searches + summarizes results
- ✍️ Writer Agent → creates a 1000+ word detailed markdown report
- 📧 Email Agent → sends the final report via SendGrid
- 🎛️ Research Manager → orchestrates the full pipeline
- 🖥️ Gradio UI → simple front-end for entering queries

---

## 🛠️ Setup

1. Clone the repo:
   git clone https://github.com/YOUR-USER/Agentic_AI.git
   cd Agentic_AI/IdeaMiner

2. Install dependencies:
   pip install -r requirements.txt

3. Configure environment variables (.env):
   OPENAI_API_KEY=sk-...
   SENDGRID_API_KEY=SG....

4. Run the Gradio app:
   python deep_research.py

---

## 🚀 Usage
- Enter a topic in the text box (e.g., “Future of renewable energy storage”).
- Watch status updates as the agents plan → search → write → email.
- Final output:
  - Long-form markdown report
  - Report automatically emailed to configured address

---

## 📂 Project Structure
deep_research/
│── deep_research.py        # Gradio UI
│── research_manager.py     # Orchestrator
│── planner_agent.py        # Plans searches
│── search_agent.py         # Runs searches
│── writer_agent.py         # Writes report
│── email_agent.py          # Sends report via SendGrid
│── README.md

