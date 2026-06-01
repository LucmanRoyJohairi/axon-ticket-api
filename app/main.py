from fastapi import FastAPI
from app.routes import ticket_router, user_router

# This runs once when the server starts
# Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Axon API",
    description="AI-powered support ticket system",
    version="0.1.0"
)


@app.get("/health")
def health_check():
    return {"status": "ok"}

app.include_router(ticket_router)
app.include_router(user_router)