from fastapi import FastAPI

app = FastAPI(title="E-Commerce API")


@app.get("/")
async def root():
    return {"message": "Welcome to the E-Commerce API", "status": "success"}
