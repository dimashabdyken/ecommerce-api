from fastapi import FastAPI

from app.api.endpoints import auth, cart, payments, products

app = FastAPI(title="E-Commerce API")

# Include routers
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(payments.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to E-Commerce API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
