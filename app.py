"""AI Resume Screener & Feedback — FastAPI app."""
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from extract import ALLOWED_TYPES, extract_text
from llm import screen_resume

load_dotenv()

app = FastAPI(title="AI Resume Screener & Feedback")

# CORS — allow the Next.js dev server (and any origin during the demo).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health():
    return {"status": "ok", "service": "ai-resume-screener"}


@app.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    """Accept a PDF/DOCX resume and return its extracted text."""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Only PDF or DOCX resumes are accepted")
    content = await file.read()
    try:
        text = extract_text(content, file.content_type, file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {"filename": file.filename, "size_bytes": len(content), "text": text}


@app.post("/screen")
async def screen(
    file: UploadFile = File(...),
    job_description: str = Form(...),
):
    """Score a resume against a job description and return structured JSON feedback."""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Only PDF or DOCX resumes are accepted")
    if not job_description.strip():
        raise HTTPException(status_code=422, detail="Job description must not be empty")

    content = await file.read()
    try:
        resume_text = extract_text(content, file.content_type, file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    if not resume_text.strip():
        raise HTTPException(
            status_code=422,
            detail="Could not extract any text from the resume (is it a scanned image?)",
        )

    try:
        result = screen_resume(resume_text, job_description)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:  # noqa: BLE001 — surface a clean error to the client
        raise HTTPException(status_code=502, detail=f"LLM screening failed: {exc}")

    return {"filename": file.filename, **result}
