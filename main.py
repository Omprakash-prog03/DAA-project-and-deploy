import uvicorn
from backend.config import settings

if __name__ == "__main__":
    print(f"Starting EV Infrastructure Planning Real-World GIS Application on http://{settings.APP_HOST}:{settings.APP_PORT}...")
    uvicorn.run(
        "backend.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=False
    )
