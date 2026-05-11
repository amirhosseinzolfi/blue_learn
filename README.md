# 🧩 Blue Learn: AI-Powered Micro-Learning

Blue Learn is a modern, streamlined micro-learning platform that transforms any subject into a structured, interactive "puzzle" of bite-sized lessons. Built with **FastAPI** and **React**, it's designed for efficiency with **zero Node.js dependencies**.

---

## ✨ Key Features

- 🎯 **Intelligent Curriculum Design:** AI agents build comprehensive, non-linear learning paths for any topic.
- 🧩 **Puzzle-Style Learning:** Break down complex subjects into manageable, micro-sized "puzzles".
- ✍️ **On-Demand Content:** Each concept is generated as a concise, high-quality Markdown lesson.
- 🤖 **Contextual AI Coach:** A smart assistant that knows exactly what you're studying and helps you master it.
- 📈 **Mastery Tracking:** Visual progress indicators and persistent state management.
- 🚀 **Zero-Build Frontend:** Lightweight React implementation using CDNs for instant deployment.

## 🛠️ Tech Stack

- **Backend:** FastAPI (Python 3.12+)
- **Frontend:** React (Standalone SPA, CDN-based)
- **Database:** SQLite with SQLAlchemy ORM
- **AI Engine:** Google Gemini Pro/Flash via LangChain & LangGraph
- **Styling:** Custom CSS with Glassmorphism aesthetics

## 📂 Project Structure

```text
blue_learn/
├── static/              # 🎨 Frontend Assets (HTML, CSS, JS/JSX)
│   ├── index.html       # Main Entry Point (CDN React)
│   ├── js/              # React Components & Logic
│   └── css/             # Modern UI Styling
├── agents.py            # 🧠 AI Logic & LangChain Workflows
├── main.py              # 🔌 FastAPI Routes & API Endpoints
├── models.py            # 📊 Database Schemas
├── database.py          # 💾 DB Connection & Session Management
├── requirements.txt     # 📦 Python Dependencies
└── .env.example         # ⚙️ Template for Environment Variables
```

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.12 or higher
- A Google Gemini API Key ([Get one here](https://aistudio.google.com/))

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/amirhosseinzolfi/blue_learn.git
cd blue_learn

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
Copy `.env.example` to `.env` and add your API key:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
GENERATOR_MODEL_NAME=gemini-1.5-flash
```

### 4. Run the Application
```bash
uvicorn main:app --reload --port 8082
```
Access the app at: `http://localhost:8082`

## 📖 Usage
1. **Discover:** Enter any subject you want to learn.
2. **Consult:** Chat with the AI to refine your learning goals.
3. **Build:** Generate a custom-tailored course outline.
4. **Learn:** Click on any "puzzle piece" to generate and study micro-content.
5. **Master:** Mark lessons as complete and track your journey!

---

*Built with ❤️ for lifelong learners.*
