from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.endpoints import auth, cart, payments, products, users

app = FastAPI(title="E-Commerce API")

# Automatically collect request/latency/status metrics and expose /metrics.
Instrumentator(should_instrument_requests_inprogress=True).instrument(app).expose(app)

# Include routers
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(payments.router)
app.include_router(users.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to E-Commerce API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
