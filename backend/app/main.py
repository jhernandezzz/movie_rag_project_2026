from fastapi import FastAPI

app = FastAPI(title="CinemaRAG API")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "CinemaRAG"}

@app.get("/")
async def root():
    return {"message": "Welcome to CinemaRAG API"}
