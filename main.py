from fastapi import FastAPI
from datetime import datetime
import uvicorn

app = FastAPI(title="Backend API", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "Backend API is running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "backend-api"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
