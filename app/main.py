import uuid
from datetime import datetime
from fastapi import FastAPI, Depends, Query
from pydantic import BaseModel
from schemas import Ticket as TicketSchema, TicketListResponse,CreateTicketPayload
from utils import STATUS_LABEL, PRIORITY_LABEL, CATEGORY_LABEL
from app.database import get_db, engine, Base
from app.models import Ticket as TicketModel
from app.models import *
from sqlalchemy import select, func

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
def get_tickets(
    page: int = Query(default=1,ge=1), #default to page 1, must be greater than 1
    page_size: int = Query(default=10, ge=1, le=100), #default to page size of 10, must be greater than 1, max 100
    db: Session = Depends(get_db)
):

    # 1. Calculate how many records to skip
    # Page 1 skips 0 rows, Page 2 skips 10 rows, etc.
    skip = (page - 1) * page_size

    # 2. Get the TOTAL count of tickets in the DB
    count_statement = select(func.count()).select_from(TicketModel)
    total_count = db.execute(count_statement).scalar() or 0


    # 3. Fetch ony the tickets for the current page
    # .limit() restricts the amount, offset() skips the previous pages

    # query statement
    statement = select(TicketModel).offset(skip).limit(page_size)

    result = db.execute(statement)

    ticket_list = result.scalars().all()

    # 4. return dictionary matching TicketListResponse structure
    return {
        "tickets": ticket_list,
        "total": total_count,
        "page": page,
        "page_size": page_size
    }



# TODO: make a route for ADD Tickets, store in an actual model, will probably need to use an ORM


@app.post("/tickets", response_model=TicketSchema)
def create_ticket(payload: CreateTicketPayload, db: Session = Depends(get_db)):


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