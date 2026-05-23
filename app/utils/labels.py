from typing import Dict
from app.schemas.ticket import TicketStatus, TicketPriority, TicketCategory

STATUS_LABEL: Dict[TicketStatus, str] = {
    "open": "Open",
    "in_progress": "In Progress",
    "resolved": "Resolved",
    "closed": "Closed",
}

PRIORITY_LABEL: Dict[TicketPriority, str] = {
    "low": "Low",
    "medium": "Medium",
    "high": "High",
    "critical": "Critical",
}

CATEGORY_LABEL: Dict[TicketCategory, str] = {
    "bug": "Bug",
    "feature": "Feature",
    "billing": "Billing",
    "support": "Support",
    "other": "Other",
}