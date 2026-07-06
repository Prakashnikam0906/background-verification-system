# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.verification import router
from app.config.settings import settings


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="""
## Background Verification System

Orchestrates **16 verification agents** across 3 categories in parallel,
generates intelligent smart reports, and supports selective re-execution
based on user feedback.

### Categories
- **Identity** — Name, DOB, Address, Govt ID, Address History
- **Criminal** — Federal, State, County, Sex Offender, Interpol
- **Financial** — Credit, Fraud, Sanctions, Bankruptcy, PEP, Adverse Media

### Key Features
- Parallel agent execution using asyncio
- Smart report with risk scores and recommendations
- Selective re-execution (only re-runs affected agents)
- CACHED vs FRESH indicators per agent
- Full audit trail and version history
""",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "status":  "running",
        "docs":    "/docs",
        "mode":    "REAL_API" if settings.USE_REAL_API else "MOCK",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}


