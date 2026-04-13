# 🏋️ FitGenie — Multi-Agent Personalized Fitness Coaching System

> A production-ready AI coaching system powered by 5 specialized agents that dynamically generate personalized workout and diet plans.

🌐 **Live Demo:** https://fitgenier.up.railway.app  
🔧 **API Docs:** https://fitgenie.up.railway.app/docs

---

## 🎯 What Makes This Different

Most fitness apps give you a static plan. FitGenie uses a **multi-agent architecture** where specialized AI agents collaborate, negotiate conflicts, and adapt to your data every day.

| Traditional App | FitGenie |
|---|---|
| Static plan | Dynamic daily adaptation |
| Single LLM call | 5 specialized agents |
| No memory | Training history + trend analysis |
| No conflict handling | Orchestrator arbitration |
| Hallucinated exercises | Real ExerciseDB API via Tool Use |

---

## 🧠 System Architecture

```
User Input
│
▼
┌─────────────────────┐
│    Orchestrator      │  ← Conflict arbitration & mode decision
│  normal/conservative │    (aggressive when plateau detected)
│     /aggressive      │
└──────┬──────────────┘
│
┌──────┼────────────────────────────────┐
▼      ▼           ▼         ▼          ▼
Tracker  Analyst   Coach    Diet      Mental
Agent    Agent     Agent    Agent     Agent
│         │
│         └── ExerciseDB API (Tool Use)
│
└── Plateau Detection (rule-based)
│
▼
Memory Layer
(SQLite + Vector Store)
```

### Agent Responsibilities

| Agent | Role | Key Design Decision |
|---|---|---|
| **Tracker** | Collects daily user data | API mode vs CLI mode auto-detection |
| **Analyst** | Detects plateau, analyzes trends | Rule-based plateau (< 0.2kg/7days) + LLM for narrative |
| **Orchestrator** | Arbitrates conflicts between agents | plateau + tired → conservative (protect adherence over progress) |
| **Coach** | Generates workout plan | Tool Use: queries real ExerciseDB, LLM selects from real exercises |
| **Diet** | Calculates nutrition targets | Mifflin-St Jeor BMR → TDEE → deficit, prompt-enforced calorie constraints |
| **Mental** | Generates motivational message | Rule-based style selection, LLM for natural language output |

---

## ⚡ Core Design Decisions

### 1. Orchestrator Conflict Arbitration
When agents disagree, the Orchestrator resolves it:

plateau detected + mood == "tired" → conservative mode
(protect long-term adherence over short-term progress)
plateau detected + mood != "tired" → aggressive mode
(break plateau with increased deficit/intensity)
no plateau → normal mode

### 2. Tool Use in Coach Agent
Coach Agent calls ExerciseDB API to fetch real exercises before generating a plan. LLM can only **select and combine** from real exercises — it cannot invent movements.

```python
# Two-step process:
# Step 1: LLM decides which muscle group to train
muscle_group = _decide_muscle_group(client, history_context)

# Step 2: Tool fetches real exercises from database
exercises = get_exercises_by_muscle(muscle_group)

# Step 3: LLM selects from REAL exercises only
plan = generate_plan(client, exercises)
```

### 3. LLM vs Rule-based Decision Split

Plateau detection    → rule-based  (fast, reliable, no token cost)
Trend narrative      → LLM         (natural language)
Style decision       → rule-based  (consistent behavior)
Message generation   → LLM         (flexible, personalized)
BMR/TDEE calculation → formula     (scientifically grounded)

### 4. Prompt Constraint Engineering
Diet Agent forces calorie output to match system-calculated targets:
```python
prompt = f"""
【必须遵守，不得修改】
今日目标热量：{target} kcal
第一行必须是：今日目标热量：{target} kcal
"""
```
Solved LLM training bias overriding system-calculated values.

---

## 🛠 Tech Stack

**Backend**
- Python + FastAPI
- LangGraph (multi-agent orchestration)
- SQLite (local) / PostgreSQL (production)
- JWT authentication
- Hunyuan LLM (via OpenAI-compatible API)
- ExerciseDB API (Tool Use)

**Frontend**
- Vue 3 + TypeScript + Vite
- Element Plus
- Pinia (state management)
- Axios

**Infrastructure**
- Docker + Railway
- PostgreSQL (Railway managed)

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 20+
- Hunyuan API Key ([get here](https://console.cloud.tencent.com/hunyuan/api-key))
- ExerciseDB API Key ([get here](https://rapidapi.com/justin-WFnsXH_t6/api/exercisedb))

### Backend Setup

```bash
git clone https://github.com/chqwater/fitgenie.git
cd fitgenie

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env
cp .env.example .env
# Fill in your API keys

uvicorn api.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Environment Variables

```env
HUNYUAN_API_KEY=your_key
RAPIDAPI_KEY=your_key
SECRET_KEY=random_string_for_jwt
DATABASE_URL=postgresql://... (optional, defaults to SQLite)
```

---

## 📁 Project Structure
```
fitgenie/
├── api/                    # FastAPI application
│   ├── main.py             # App entry + CORS
│   ├── auth.py             # JWT auth
│   ├── schemas.py          # Pydantic models
│   └── routes/
│       ├── daily.py        # Checkin + history endpoints
│       └── profile.py      # User profile endpoints
├── agents/                 # AI agents
│   ├── tracker.py          # Data collection
│   ├── analyst.py          # Trend analysis + plateau detection
│   ├── coach.py            # Workout plan (with Tool Use)
│   ├── diet.py             # Nutrition planning
│   └── mental.py           # Motivational messaging
├── memory/
│   └── store.py            # SQLite + PostgreSQL data layer
├── tools/
│   └── exercise_db.py      # ExerciseDB API wrapper + fallback
├── utils/
│   └── formatter.py        # JSON parsing + display formatting
├── graph.py                # LangGraph orchestration
├── state.py                # Shared state definition
└── frontend/               # Vue 3 frontend
```

---

## 🎬 Demo Flow

1. Register → profile saved to PostgreSQL
2. Daily check-in → Tracker collects data
3. Analyst detects plateau → Orchestrator decides mode
4. Coach fetches real exercises via ExerciseDB API
5. Diet calculates TDEE-based calorie targets
6. Mental generates personalized motivation
7. Results displayed in Vue frontend

---

## 👨‍💻 Author

Built by **陈浩泉**  
© 2026 FitGenie
