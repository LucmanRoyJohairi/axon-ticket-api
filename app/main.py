from fastapi import FastAPI, Depends, Query, HTTPException
from pydantic import BaseModel
from schemas import Ticket as TicketSchema, TicketListResponse,CreateTicketPayload, UpdateTicketPayload
from app.database import get_db, engine, Base
from app.models import Ticket as TicketModel
from app.models import *
from sqlalchemy import select, func
from sqlalchemy.orm import Session

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


@app.get("/tickets/{ticket_id}", response_model=TicketSchema)
def get_single_ticket(ticket_id: str, db: Session = Depends(get_db)):
    
    statement = select(TicketModel).where(TicketModel.id == ticket_id)
    result = db.execute(statement)
    ticket = result.scalar_one_or_none()

    #raise an exception if ticket is not found
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return ticket


@app.patch("/tickets/{ticket_id}", response_model=TicketSchema)
def update_single_ticket(
    ticket_id: str,
    payload: UpdateTicketPayload,
    db: Session = Depends(get_db)
):
    statement = select(TicketModel).where(TicketModel.id == ticket_id)
    result = db.execute(statement)
    matching_ticket = result.scalar_one_or_none()

     # 1. Print a specific attribute to your terminal console
    # if matching_ticket:
    #     print("DATABASE FOUND TICKET:", matching_ticket.title) # <--- Check your terminal!
    # else:
    #     print("DATABASE RETURNED NONE")

    if matching_ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    #this creates a python dictionary i.e. {"status":in_progress, "priority":"low"}
    update_data = payload.model_dump(exclude_unset=True)

    # we use a loop here so that we don't have to manually assign or update the properties in the dictionary
    for key, value in update_data.items():
        setattr(matching_ticket, key, value)



    # Save changes to the DB and refreshes the object
    db.commit()
    db.refresh(matching_ticket)

    return matching_ticket


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