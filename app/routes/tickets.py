from fastapi import APIRouter
from fastapi import Depends, Query, HTTPException, status
from schemas import Ticket as TicketSchema, TicketListResponse,CreateTicketPayload, UpdateTicketPayload, DeleteTicketResponse, TestAIConnectivityPayload
from app.database import get_db
from app.models import Ticket as TicketModel
from app.models import User as UserModel
from app.models import *
from app.security import get_current_user
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from services.ticket_classifier import classify_ticket_content
from services.test_service import test_ai_connectivity

router = APIRouter(
    prefix="/tickets",
    tags=["tickets"]
)

@router.post("/test-ai")
def test_ai_endpoint(payload: TestAIConnectivityPayload):
    response = test_ai_connectivity(payload.prompt)
    
    return response

@router.get("", response_model=TicketListResponse)
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


@router.get("/{ticket_id}", response_model=TicketSchema)
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


@router.patch("/{ticket_id}", response_model=TicketSchema)
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


@router.post("", response_model=TicketSchema)
def create_ticket(
    payload: CreateTicketPayload,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user) #checks if token is valid during request

):
    
    # Run Ticket Data through Claude 3.5 Haiku
    classified_result = classify_ticket_content(payload.title, payload.description)
    
    # Determine if the classification actually succeeded
    is_success = classified_result.get("ai_category") is not None

    new_ticket = TicketModel(
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        category=payload.category,
        creator_id="usr-123", 

         # Store specific AI-generated analysis fields
        ai_summary=classified_result.get("ai_summary"),
        ai_category=classified_result.get("ai_category"),
        ai_priority=classified_result.get("ai_priority"),
        ai_processed=is_success

        # Everything else (ID, status, timestamps, AI fields) 
        # is handled by the Model defaults or is Nullable.
    )

    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)


    return new_ticket


#Soft delete
@router.delete("/{ticket_id}/archive", response_model=DeleteTicketResponse, status_code=status.HTTP_200_OK)
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
@router.patch("/{ticket_id}/restore", response_model=DeleteTicketResponse, status_code=status.HTTP_200_OK)
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

