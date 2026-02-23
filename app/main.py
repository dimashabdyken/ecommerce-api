from fastapi import FastAPI

from app.api.endpoints import auth

app = FastAPI(title="E-Commerce API")

# Include routers
app.include_router(auth.router)


@app.get("/")
async def root():
    return {"message": "Welcome to the E-Commerce API", "status": "success"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
