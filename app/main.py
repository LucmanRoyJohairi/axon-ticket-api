from fastapi import FastAPI, Request
from app.routes import ticket_router, user_router
from contextlib import asynccontextmanager
from sentence_transformers import SentenceTransformer
from app.schemas.ticket import EmbeddingRequest

# This runs once when the server starts
# Base.metadata.create_all(bind=engine)


# Use lifespan to load the model once when the server starts up
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.embedding_model = SentenceTransformer("BAAI/bge-small-en-v1.5") #current modern lightweight model
    yield
    # resources clean up automatically here when the server stops


app = FastAPI(
    title="Axon API",
    description="AI-powered support ticket system",
    version="0.1.0",
    lifespan=lifespan
)


@app.get("/health")
def health_check():
    return {"status": "ok"}

app.include_router(ticket_router)
app.include_router(user_router)


# test route
@app.post("/embed")
async def generate_embeddings(payload: EmbeddingRequest, request: Request):
    # access the model via request object context safely
    model = request.app.state.embedding_model
    embedding = model.encode([payload.text])
    return {"embedding": embedding.tolist()}