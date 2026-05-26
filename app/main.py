import uuid
from datetime import datetime
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from schemas import Ticket as TicketSchema, TicketListResponse,CreateTicketPayload
from utils import STATUS_LABEL, PRIORITY_LABEL, CATEGORY_LABEL
from app.database import get_db, engine, Base
from app.models import Ticket as TicketModel
from app.models import *

# This runs once when the server starts
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Axon API",
    description="AI-powered support ticket system",
    version="0.1.0"
)


@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/tickets", response_model=TicketListResponse)
def get_tickets():
     # return a dictionary that matches the model structure
    return {
        "tickets": [
            {
                "id": "tkt-123",
                "title": "Fix login button",
                "status": "open",  # Fixed: Must match 'open' string literal constraint
                "priority": "high",  # Fixed: Added missing required field
                "category": "bug",  # Fixed: Added missing required field
                "description": "Button is unclickable on mobile",
                # AI Worker Fields (must be provided, can be None)
                "ai_summary": None,  # Fixed: Added missing required field
                "ai_category": None,  # Fixed: Added missing required field
                "ai_priority": None,  # Fixed: Added missing required field
                "ai_processed": False,
                "ai_processed": False,


                "creator_id": "usr-99",
                "assignee_id": None,  # Fixed: Added missing required field
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
        ],
        "total": 1,
        "page": 1,
        "page_size": 10
    } 

# TODO: make a route for ADD Tickets, store in an actual model, will probably need to use an ORM


@app.post("/tickets", response_model=TicketSchema)
def create_ticket(payload: CreateTicketPayload, db: Session = Depends(get_db)):
    # new_ticket = {
    #       # Fields from Postman
    #     "title": payload.title,
    #     "description": payload.description,
    #     "priority": payload.priority,
    #     "category": payload.category,
        
    #     "ai_summary": None,
    #     "ai_category": None,
    #     "ai_priority": None,
    #     "assignee_id": None, 
        
    #     # System-generated fields
    #     "id": str(uuid.uuid4()),
    #     "status": "open",
    #     "creator_id": "usr-123",
    #     "ai_processed": False,
    #     "created_at": datetime.now(),
    #     "updated_at": datetime.now(),
    # }


    new_ticket = TicketModel(
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        category=payload.category,
        creator_id="usr-123" 
        # Everything else (ID, status, timestamps, AI fields) 
        # is handled by the Model defaults or is Nullable.
    )

    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)


    return new_ticket