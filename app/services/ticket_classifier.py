import anthropic
import json
from app.schemas.ticket import TicketCategory, TicketPriority, TicketAnalysisResponse
from typing import get_args
from app.config import settings 

# Initialize Anthropic Client, reads the ANTHROPIC_API_KEY from the env
client = anthropic.Anthropic(api_key=settings.anthropic_api_key)


def classify_ticket_content(title: str, description: str):
    '''
    Sends ticket content to Claude 3.5 Haiku and extracts validated structured data.
    Returns a dictionary matching the TicketAnalysisResponse schema.
    '''

    # System prompt for setting the persona and context
    system_prompt = (
        "You are an expert, highly efficient IT Support triage assistant. "
        "Your task is to analyze incoming support tickets and classify them accurately. "
        "Focus on the underlying technical issue to determine the correct category "
        "and urgency level based on impact."
    )

    content = f"Analyze this support ticket:\n\nTitle: {title}\nDescription: {description}"
    #is called instruction wrapping.
    try:

        # Using .parse() instead of .create() for native Pydantic support
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=300,
            system=system_prompt,
            # Force Claude to respond using your Pydantic schema structure
            # also called structured output (the Pydantic schema) via tool calling
            tools=[{
                "name": "ticket_analysis",
                "description": "Analyze the ticket and return structured data",
                "input_schema": TicketAnalysisResponse.model_json_schema() # Your Pydantic model
            }],
            tool_choice={"type": "tool", "name": "ticket_analysis"}, # Forces the tool output
            temperature=0.0,
            messages=[
                {
                    "role": "user", 
                    "content": content
                }
            ]
        )

       # Grab the tool use block from the content array
        tool_use_block = response.content[0]

        # Extract the raw JSON dictionary arguments from it
        structured_data = tool_use_block.input

        # Pass the data back into your Pydantic model to fully validate it
        return TicketAnalysisResponse(**structured_data).model_dump()

    except Exception as e:
        # Fallback dictionary if the API fails or returns invalid formatting
        print(f"AI Claissification failed: {str(e)}")
        return {
            "ai_category": None,
            "ai_priority": None,
            "ai_summary": "AI processing failed"
        }
