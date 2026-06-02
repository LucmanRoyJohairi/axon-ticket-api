import anthropic
import json
from app.schemas.ticket import TicketCategory, TicketPriority, TicketAnalysisResponse
from typing import get_args

# Initialize Anthropic Client, reads the ANTHROPIC_API_KEY from the env
client = anthropic.Anthropic()


def classify_ticket_content(title: str, description: str):
    '''
    Sends ticket content to Claude 3.5 Haiku and extracts validated structured data.
    Returns a dictionary matching the TicketAnalysisResponse schema.
    '''

    content = f"Analyze this support ticket:\n\nTitle: {title}\nDescription: {description}"

    try:

        # Using .parse() instead of .create() for native Pydantic support
        response = client.messages.parse(
            model="claude-3-5-haiku-20241022",
            max_tokens=300,
            response_format=TicketAnalysisResponse, # ensures that the response format matches are Pydantic Schema
            temperature=0.0,
            messages=[
                {
                    "role": "user", 
                    "content": content
                }
            ]
        )

       # access the data instantly as a validated python dictionary
       # response.output is automatically an instance of TicketAnalysisResponse
        return response.parsed_output.model_dump()

    except Exception as e:
        # Fallback dictionary if the API fails or returns invalid formatting
        print(f"AI Claissification failed: {str(e)}")
        return {
            "category": None,
            "priority": None,
            "summary": "AI processing failed"
        }
