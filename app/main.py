import os
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from starlette.staticfiles import StaticFiles

from app.api.routes import router as questions_router
from app.config import settings
from app.schemas.question import HealthResponse

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="REST API for Automatic Question Generation from Educational Materials using Generative AI (Google Gemini / OpenAI).",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for web and mobile frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 Routes
app.include_router(questions_router, prefix=settings.API_V1_STR)

# Mount frontend static assets
if os.path.exists("frontend"):
    app.mount("/static", StaticFiles(directory="frontend"), name="static")


# Custom Validation Error Handler to match PRD specific error response requirements
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    first_error = errors[0] if errors else {}
    loc = first_error.get("loc", [])
    msg = str(first_error.get("msg", "Invalid request parameters"))

    field = loc[-1] if loc else "field"

    # Match PRD specified validation error messages
    if "number_of_questions" in loc:
        detail_msg = "Number of questions must be between 1 and 50"
    elif "question_type" in loc:
        detail_msg = "Invalid question type. Allowed values are 'mcq', 'short_answer', 'true_false'"
    elif "difficulty" in loc:
        detail_msg = "Invalid difficulty level. Allowed values are 'easy', 'medium', 'hard'"
    elif "text" in loc and ("empty" in msg.lower() or "too short" in msg.lower()):
        detail_msg = "Educational material cannot be empty"
    else:
        detail_msg = f"Validation error on '{field}': {msg}"

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": detail_msg},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.get(
    "/",
    response_model=HealthResponse,
    tags=["General"],
    summary="Root Endpoint",
    description="Returns interactive web app for browser requests, or health check for API clients"
)
async def root(request: Request):
    """
    Root endpoint: serves frontend UI to browsers, and JSON health check to API callers.
    """
    accept = request.headers.get("accept", "")
    if accept.startswith("text/html") and os.path.exists("frontend/index.html"):
        return FileResponse("frontend/index.html", media_type="text/html")
    return HealthResponse(
        message="EduQuestion AI API is running",
        status="healthy",
        version=settings.PROJECT_VERSION
    )


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["General"],
    summary="Service Health Status"
)
async def health_check():
    """
    Health check endpoint for monitoring systems.
    """
    return HealthResponse(
        message="EduQuestion AI is healthy and operational",
        status="healthy",
        version=settings.PROJECT_VERSION
    )

@app.get("/ui", response_class=HTMLResponse, tags=["Interactive UI"])
@app.get("/demo", response_class=HTMLResponse, tags=["Interactive UI"])
async def interactive_demo():
    """
    Serves the modern EduQuestion AI interactive frontend interface.
    """
    if os.path.exists("frontend/index.html"):
        return FileResponse("frontend/index.html", media_type="text/html")
    return HTMLResponse("<h3>EduQuestion AI frontend not found</h3>")
