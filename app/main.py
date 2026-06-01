from fastapi import FastAPI, Depends, Query, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from schemas import Ticket as TicketSchema, TicketListResponse,CreateTicketPayload, UpdateTicketPayload, DeleteTicketResponse
from schemas import UserCreate, UserRequest, UserResponse, Token
from app.database import get_db, engine, Base
from app.models import Ticket as TicketModel
from app.models import User as UserModel
from app.models import *
from app.security import get_current_user
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from security import hash_password, verify_password, create_access_token

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

@app.get("/tickets", response_model=TicketListResponse)
def get_tickets(
    page: int = Query(default=1,ge=1), #default to page 1, must be greater than 1
    page_size: int = Query(default=10, ge=1, le=100), #default to page size of 10, must be greater than 1, max 100
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user) #checks if token is valid during request
):

    # 1. Calculate how many records to skip
    # Page 1 skips 0 rows, Page 2 skips 10 rows, etc.
    skip = (page - 1) * page_size

    # 2. Get the TOTAL count of tickets in the DB
    count_statement = select(func.count()).where(TicketModel.is_deleted == False).select_from(TicketModel)
    total_count = db.execute(count_statement).scalar() or 0


    # 3. Fetch ony the tickets for the current page
    # .limit() restricts the amount, offset() skips the previous pages

    # query statement
    statement = select(TicketModel).where(TicketModel.is_deleted == False).offset(skip).limit(page_size)

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
def get_single_ticket(
    ticket_id: str, 
    db: Session = Depends(get_db), 
    current_user: UserModel = Depends(get_current_user) #checks if token is valid during request
):
    
    statement = select(TicketModel).where(TicketModel.id == ticket_id, TicketModel.is_deleted == False)
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
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user) #checks if token is valid during request
):
    statement = select(TicketModel).where(TicketModel.id == ticket_id, TicketModel.is_deleted == False)
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
def create_ticket(
    payload: CreateTicketPayload,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user) #checks if token is valid during request

):


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


#Soft delete
@app.delete("/tickets/{ticket_id}/archive", response_model=DeleteTicketResponse, status_code=status.HTTP_200_OK)
def delete_ticket(
    ticket_id: str, 
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user) #checks if token is valid during request    
):

    statement = select(TicketModel).where(TicketModel.id == ticket_id, TicketModel.is_deleted == False)
    result = db.execute(statement)
    matching_ticket = result.scalar_one_or_none()

    if matching_ticket is None:
        raise HTTPException(status_code=404, detail="Ticket is not Found")
    

    matching_ticket.is_deleted = True
    # db.delete(matching_ticket) <- I think this is for hard delete?
    db.commit()
    # db.refresh(matching_ticket) <- not needed since we are just returning a message and not retrieving the data again

    return {"message" : f"Ticket `{ticket_id}` has been deleted"}


#restore soft deleted
@app.patch("/tickets/{ticket_id}/restore", response_model=DeleteTicketResponse, status_code=status.HTTP_200_OK)
def restore_ticket(
    ticket_id: str, 
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user) #checks if token is valid during request    
):

    statement = select(TicketModel).where(TicketModel.id == ticket_id, TicketModel.is_deleted == True)
    result = db.execute(statement)
    matching_ticket = result.scalar_one_or_none()

    if matching_ticket is None:
        raise HTTPException(status_code=404, detail="Ticket is not Found")
    

    matching_ticket.is_deleted = False
    # db.delete(matching_ticket) <- I think this is for hard delete?
    db.commit()
    # db.refresh(matching_ticket) <- not needed since we are just returning a message and not retrieving the data again

    return {"message" : f"Ticket `{ticket_id}` has been restored"}


# Registration
@app.post("/auth/register", response_model=UserResponse)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    statement = select(UserModel).where(UserModel.email == payload.email)
    result = db.execute(statement)
    matching_user = result.scalar_one_or_none()

    if matching_user:
        raise HTTPException(status_code=400, detail="email already in use")
    
    hashed = hash_password(payload.password)

    new_user = UserModel(
        email=payload.email,
        hashed_password=hashed,
        full_name=payload.full_name
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@app.post("/auth/login", response_model=Token)
def login_user(payload: OAuth2PasswordRequestForm = Depends() , db: Session = Depends(get_db)):
    # OAuth2 spec uses 'username'. In your app, this maps to the user's email.
    statement = select(UserModel).where(UserModel.email == payload.username)
    result = db.execute(statement)
    matching_user = result.scalar_one_or_none()

    # Mitigate timing attacks by executing a dummy verify if user doesn't exist
    if matching_user is None:
        verify_password(payload.password, "dummy_hash_to_prevent_timing_attacks")
        raise HTTPException(status_code=404, detail="Email or Password is incorrect")

    is_valid = verify_password(payload.password, matching_user.hashed_password)

    if not is_valid:
        raise HTTPException(status_code=404, detail="Email or Password is incorrect")

    # generate access token and return JWT
    # Use stringified user ID for the 'sub' claim for better database longevity
    access_token = create_access_token(data={"sub": str(matching_user.id)})
    return {
        "access_token": access_token,
        "token_type": "bearer", 
    }