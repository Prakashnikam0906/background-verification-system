# run.py
import uvicorn
from app.config.settings import settings

if __name__ == "__main__":
    print(f"\n{'='*55}")
    print(f"  Background Verification System  v{settings.VERSION}")
    print(f"  Mode : {'REAL API (UltraSafe)' if settings.USE_REAL_API else 'MOCK (simulation)'}")
    print(f"  Port : {settings.PORT}")
    print(f"  Docs : http://localhost:{settings.PORT}/docs")
    print(f"{'='*55}\n")

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=True,
    )
    
