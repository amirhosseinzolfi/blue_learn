# AI Puzzle Learning Platform

A streamlined, AI-powered micro-learning platform built with FastAPI and React. This version is optimized for simplicity, requiring **zero Node.js dependencies**.

## Features
- **Comprehensive Outline Generation:** Automatically creates a detailed learning path for any subject.
- **Puzzle-Style Learning:** Learn concepts in a non-linear, bite-sized "puzzle" format.
- **Micro-Courses:** Each concept is generated as a concise, readable article.
- **Progress Tracking:** Visual progress bars and completed item tracking.
- **AI Agents:** Powered by Google Gemini via LangChain and LangGraph.

## Tech Stack
- **Backend:** FastAPI (Python 3.12+)
- **Frontend:** React (Loaded via CDN, zero build step)
- **Database:** SQLite (SQLAlchemy)
- **AI:** Google Gemini API

## Project Structure
```text
blue_learn/
├── static/              # Frontend files
│   └── index.html       # Standalone React SPA (CDN based)
├── main.py              # FastAPI application & route definitions
├── agents.py            # AI Logic (Outline & Content generation)
├── models.py            # Database schemas
├── database.py          # Database connection setup
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (API Keys)
└── .venv/               # Python virtual environment
```

## How to Run

1. **Setup Environment:**
   Ensure you have a `.env` file in the root directory with your Google API Key:
   ```env
   GOOGLE_API_KEY=your_actual_key_here
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the App:**
   ```bash
   uvicorn main:app --reload --port 8082
   ```

4. **Open in Browser:**
   Navigate to [http://localhost:8082](http://localhost:8082)

## Usage
1. Enter a subject (e.g., "Deep Learning" or "Photography").
2. Click **Create Course** to generate a custom outline.
3. Use **Generate Micro Course** to dive into random topics or click specific parts of the "Puzzle".
4. Mark topics as finished to track your mastery.
