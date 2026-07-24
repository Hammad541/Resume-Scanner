# AI Resume Screener & Feedback

> AI & Generative AI Fellowship — Week 2 Project

An AI-powered tool that compares a resume against a job description, scores the
match from **0–100**, flags **missing keywords**, and gives concrete **rewrite
suggestions** — all returned as structured JSON and rendered in a clean UI.

## Features

- 📄 Resume upload (**PDF / DOCX**) with server-side text extraction
- 📝 Job description input (paste)
- 🤖 LLM comparison (Google **Gemini**) returning strict JSON:
  `match_score`, `missing_keywords`, `suggestions`
- 🔁 JSON validation + automatic retry if the model returns prose
- 🎨 Next.js frontend that renders the score, keyword chips, and suggestions

## Tech Stack

| Layer     | Technology                          |
| --------- | ----------------------------------- |
| Frontend  | Next.js (React 19, App Router)      |
| Backend   | FastAPI (Python)                    |
| LLM       | Google Gemini (`gemini-2.0-flash`)  |
| Parsing   | pypdf, python-docx                  |

## Project Structure

```
ai-resume-screener/
├── app.py            # FastAPI app: /screen, /upload, health, CORS
├── extract.py        # PDF/DOCX -> text
├── llm.py            # Gemini call + prompt + JSON validation/retry
├── requirements.txt
├── .env.example      # copy to .env and add your GEMINI_API_KEY
└── frontend/         # Next.js app
    └── app/page.js   # upload form + results UI
```

## Getting Started

### 1. Backend (FastAPI)

```bash
# from the repo root
python -m pip install -r requirements.txt

# create your environment file and add your Gemini key
cp .env.example .env        # then set GEMINI_API_KEY

# run the API on http://localhost:8000
uvicorn app:app --reload
```

Get a free Gemini API key at <https://aistudio.google.com/apikey>.

### 2. Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev                 # http://localhost:3000
```

The frontend calls the backend at `http://localhost:8000` by default. To point
it elsewhere, copy `frontend/.env.local.example` to `frontend/.env.local` and set
`NEXT_PUBLIC_API_URL`.

## API

`POST /screen` — multipart form: `file` (PDF/DOCX) + `job_description` (text).

```json
{
  "filename": "resume.pdf",
  "match_score": 72,
  "missing_keywords": ["Kubernetes", "GraphQL"],
  "suggestions": ["Quantify impact on the payments project with metrics."]
}
```

## Branching Strategy

- `main` — stable, always working
- `dev` — integration branch
- `feature/*` — one branch per task

No direct pushes to `main`; changes land through reviewed pull requests.

## Team Roles

| Member    | Role                               |
| --------- | ---------------------------------- |
| Member 1  | Backend — file upload & extraction |
| Member 2  | Backend — LLM integration & prompt |
| Member 3  | Frontend — Next.js UI              |
| Member 4  | DevOps — env, CORS, .gitignore     |
| Member 5  | Docs, testing & QA                 |

## License

MIT — see [LICENSE](LICENSE).
