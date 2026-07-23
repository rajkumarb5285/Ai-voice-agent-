# Personal Voice AI Agent 🎙️✦

> A production-ready personal AI companion — ChatGPT Voice Mode + Jarvis + your own memory.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2-4B32C3)](https://langchain-ai.github.io/langgraph/)
[![Next.js](https://img.shields.io/badge/Next.js-14-000000?logo=nextdotjs)](https://nextjs.org)

---

## 🏗️ Architecture

```
User Voice Input
      │
      ▼
Microphone Capture (Browser MediaRecorder)
      │
      ▼
Voice Activity Detection (client-side)
      │
      ▼
Speech-to-Text (OpenAI Whisper / Deepgram)
      │
      ▼
Intent Understanding (LangGraph Intent Classifier)
      │
      ▼
LangGraph Agent System
  ├── Memory Agent          (Redis + PostgreSQL + ChromaDB)
  ├── Research Agent        (Tavily Web Search)
  ├── Planner Agent         (Task Breakdown)
  ├── Coding Agent          (Code Generation + Debug)
  ├── Learning Coach Agent  (Personalized Tutoring)
  ├── Productivity Agent    (Calendar + Tasks)
  ├── Wellness Agent        (Mental Health + Habits)
  ├── Career Coach Agent    (Resume + Interviews)
  └── Email Agent           (Draft + Summarize)
      │
      ▼
Response Synthesis
      │
      ▼
Memory Update (persist new facts)
      │
      ▼
Text-to-Speech (OpenAI TTS / ElevenLabs)
      │
      ▼
Audio Playback (Browser Web Audio API)
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+
- Docker + Docker Compose (recommended)

### 1. Clone & Configure
```bash
git clone https://github.com/yourname/voice-ai-agent
cd voice-ai-agent

# Copy and fill in your API keys
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY (required)
```

### 2a. Docker (recommended)
```bash
docker-compose up --build
```
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 2b. Manual (development)

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Infrastructure (required):**
```bash
# PostgreSQL
docker run -d -e POSTGRES_PASSWORD=secret -e POSTGRES_DB=voice_agent_db -p 5432:5432 postgres:16

# Redis
docker run -d -p 6379:6379 redis:7-alpine

# ChromaDB (optional — will use in-process if unavailable)
docker run -d -p 8001:8000 chromadb/chroma
```

---

## 🔑 Required API Keys

| Key | Required | Purpose |
|-----|----------|---------|
| `OPENAI_API_KEY` | ✅ Yes | LLM (gpt-4o) + Whisper STT + TTS + Embeddings |
| `TAVILY_API_KEY` | ⚡ Recommended | Web search (free tier at tavily.com) |
| `DEEPGRAM_API_KEY` | Optional | Better streaming STT |
| `ELEVENLABS_API_KEY` | Optional | Premium natural voice |
| `GOOGLE_CLIENT_ID/SECRET` | Optional | Gmail + Calendar integration |

---

## ✨ Features

### 🎙️ Voice Pipeline
- Microphone capture via browser MediaRecorder API
- Real-time audio level visualization
- OpenAI Whisper transcription (100+ languages)
- Streaming TTS playback

### 🧠 10 Specialist Agents
| Agent | Capabilities |
|-------|-------------|
| Intent Classifier | Routes requests to right agents |
| Memory Agent | Stores and retrieves all memory types |
| Research Agent | Web search + fact synthesis |
| Planner Agent | Multi-step task planning |
| Coding Agent | Code gen, debug, review |
| Learning Coach | Personalized tutoring, study plans |
| Productivity Agent | Tasks, reminders, day planning |
| Wellness Agent | Mental health, habits, fitness |
| Career Coach | Interviews, resume, skill gaps |
| Email Agent | Draft, summarize, communicate |

### 💾 4-Layer Memory
| Layer | Storage | Purpose |
|-------|---------|---------|
| Short-term | Redis | Current session (24h TTL) |
| Long-term | PostgreSQL | User profile, goals, skills |
| Semantic | ChromaDB | Vector search over all facts |
| Episodic | PostgreSQL | Important life/work events |

### 🖥️ Frontend Pages
- `/` — Auth (login/register)
- `/chat` — Main chat with WebSocket streaming
- `/voice` — Full-screen voice mode with animated orb
- `/memory` — Memory browser with semantic search
- `/tasks` — Task manager (AI + manual tasks)
- `/agents` — Agent activity feed
- `/settings` — Profile, voice, and preferences

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Login + get JWT |
| GET | `/api/auth/me` | Current user |
| POST | `/api/chat/` | Send message (REST) |
| WS | `/api/chat/ws/{id}` | Streaming WebSocket |
| POST | `/api/voice/transcribe` | Audio → Text |
| POST | `/api/voice/synthesize` | Text → Audio |
| GET | `/api/memory/` | List memories |
| POST | `/api/memory/search` | Semantic search |
| GET | `/api/tasks/` | List tasks |
| POST | `/api/tasks/` | Create task |

Full Swagger docs: `http://localhost:8000/docs`

---

## 🐳 Production Deployment

```bash
# Build production images
docker-compose -f docker-compose.yml up -d

# Scale backend workers
docker-compose up --scale backend=3

# Check health
curl http://localhost:8000/health
```

---

## 🛠️ Tech Stack

**Backend:** FastAPI · LangGraph · LangChain · PostgreSQL · Redis · ChromaDB · SQLAlchemy · JWT
**Frontend:** Next.js 14 · TypeScript · TailwindCSS · Zustand · Framer Motion · ShadCN/UI
**AI:** OpenAI GPT-4o · Whisper · TTS · Embeddings · Tavily Search
**Infrastructure:** Docker · Docker Compose · GitHub Actions CI/CD

---

## 📁 Project Structure

```
voice-agent/
├── backend/
│   ├── app/
│   │   ├── agents/          # LangGraph nodes
│   │   ├── api/             # FastAPI routes
│   │   ├── memory/          # 4-layer memory system
│   │   ├── models/          # SQLAlchemy + Pydantic
│   │   ├── services/        # STT, TTS, Auth
│   │   └── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js pages
│   │   ├── components/      # React components
│   │   ├── hooks/           # Custom hooks
│   │   ├── store/           # Zustand state
│   │   └── types/           # TypeScript types
│   └── package.json
├── docker-compose.yml
├── .env.example
└── README.md
```

---

Made with ❤️ using FastAPI, LangGraph, and Next.js
