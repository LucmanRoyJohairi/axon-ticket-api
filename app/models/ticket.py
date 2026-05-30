import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base #absolute import 🤓

class Ticket(Base):

    __tablename__ = "tickets"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String,  server_default=text("true"), default="open")
    priority: Mapped[str | None] = mapped_column(String, nullable=True)
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    
    ai_summary: Mapped[str | None] = mapped_column(String, nullable=True)
    ai_category: Mapped[str | None] = mapped_column(String, nullable=True)
    ai_priority: Mapped[str | None] = mapped_column(String, nullable=True)
    ai_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    
    creator_id: Mapped[str] = mapped_column(String)
    assignee_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False) #for soft delete
