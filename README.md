# 🧩 Blue Learn: AI-Powered Micro-Learning Platform

Blue Learn is a modern micro-learning platform that transforms any subject into structured, interactive "puzzle" lessons. Built with **FastAPI** and **React**, it delivers intelligent, bite-sized learning experiences powered by Google Gemini AI.

---

## ✨ Key Features

- 🎯 **Intelligent Curriculum Design** — AI agents build comprehensive, non-linear learning paths for any topic
- 🧩 **Puzzle-Style Learning** — Break down complex subjects into manageable micro-lessons
- ✍️ **On-Demand Content** — Each concept generated as high-quality Markdown lesson
- 🤖 **Contextual AI Coach** — Smart assistant that adapts to your learning progress
- 📈 **Mastery Tracking** — Visual progress indicators with persistent state management
- 🚀 **Zero-Build Frontend** — Lightweight React via CDN for instant deployment

## 🛠️ Tech Stack

- **Backend:** FastAPI (Python 3.12+)
- **Frontend:** React 18 (CDN-based SPA)
- **Database:** SQLite with SQLAlchemy ORM
- **AI Engine:** Google Gemini Pro/Flash via LangChain
- **Styling:** Custom CSS with modern glassmorphism design

## 📂 Project Structure

```text
blue_learn/
├── app/                    # 🧠 Core Application
│   ├── api/                # REST API endpoints
│   ├── services/           # AI agents & business logic
│   ├── config.py           # Configuration management
│   ├── database.py         # DB session handling
│   ├── models.py           # SQLAlchemy models
│   └── main.py             # FastAPI application
├── static/                 # 🎨 Frontend Assets
│   ├── css/                # Styling
│   ├── js/                 # React components
│   │   ├── components/     # UI components
│   │   └── app.jsx         # Main React app
│   └── index.html          # Entry point
├── backend/                # 💾 Database storage
├── scripts/                # 🔧 Utility scripts
├── main.py                 # 🚀 Application entry point
├── requirements.txt        # 📦 Python dependencies
└── .env.example            # ⚙️ Environment template
```

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Google Gemini API Key ([Get one free](https://aistudio.google.com/))

### Installation

```bash
# Clone the repository
git clone https://github.com/amirhosseinzolfi/blue_learn.git
cd blue_learn

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your Google Gemini API key:
```env
GOOGLE_API_KEY=your_actual_api_key_here
GENERATOR_MODEL_NAME=gemini-1.5-flash
MAIN_MODEL_NAME=gemini-1.5-flash
COACH_MODEL_NAME=gemini-1.5-flash
DATABASE_URL=sqlite:///./backend/learning_app.db
```

### Run the Application

```bash
uvicorn main:app --reload --port 8083
```

Open your browser and navigate to: **http://localhost:8083**

## 📖 Usage

1. **Discover** — Enter any subject you want to learn
2. **Consult** — Chat with AI to refine your learning goals
3. **Build** — Generate a custom course outline
4. **Learn** — Click puzzle pieces to generate and study lessons
5. **Master** — Mark lessons complete and track your progress

## 🎯 API Endpoints

- `GET /` — Frontend application
- `POST /api/chat` — AI chat interactions
- `POST /api/courses` — Course generation
- `GET /api/courses/{id}` — Get course details
- `POST /api/items/{id}/content` — Generate lesson content
- `GET /api/profile` — User profile & progress

## 🔧 Development

### Project Architecture

- **Modular Design:** Clean separation between API, services, and data layers
- **AI Agents:** Specialized agents for course generation and coaching
- **State Management:** SQLAlchemy models with progress tracking
- **CDN React:** No build step required, pure ESM modules

### Running in Development Mode

```bash
uvicorn main:app --reload --port 8083
```

The `--reload` flag enables hot-reloading during development.

## 📝 License

MIT License - feel free to use this project for learning and development.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## 📧 Contact

Built with ❤️ by Amir Hossein Zolfi

- GitHub: [@amirhosseinzolfi](https://github.com/amirhosseinzolfi)
- Project: [Blue Learn](https://github.com/amirhosseinzolfi/blue_learn)

---

*Empowering lifelong learners with AI-driven micro-education.*
