import anthropic
from app.config import settings
from pydantic import BaseModel, Field
from typing import List

client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

def test_ai_connectivity(prompt: str):

    system_prompt = (
        "You are a highly skilled engineers with decades of experience"
    )


    content = f"Analyze this user question:\n\nQuestion: {prompt}"

    message = client.messages.create(
        model="claude-haiku-4-5",
        system=system_prompt,
        max_tokens=300,
        tool_choice={"type": "tool", "name": "record_analysis"},
        temperature=0.0,
        messages=[
            {
                "role": "user",
                "content": content
            }
        ]        
    )

    structured_json_string = message.content[0].input
    return structured_json_string
    