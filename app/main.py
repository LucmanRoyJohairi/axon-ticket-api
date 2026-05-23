from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="Axon API",
    description="AI-powered support ticket system",
    version="0.1.0"
)




@app.get("/health")
def health_check():
    return {"status": "ok"}

# @app.get("/tickets")
# def get_tickets(){
#     return 
# }