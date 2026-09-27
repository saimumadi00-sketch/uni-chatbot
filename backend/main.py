from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from llm_provider import generate_response

app = FastAPI(title='Simple Chat')
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173', 'http://127.0.0.1:5173'],
    allow_methods=['POST'],
    allow_headers=['Content-Type'],
)


class Message(BaseModel):
    role: Literal['user', 'assistant']
    content: str = Field(min_length=1)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    history: list[Message] = Field(default_factory=list)

    @field_validator('message')
    @classmethod
    def reject_blank_message(cls, value: str) -> str:
        if not value.strip():
            raise ValueError('Message cannot be blank.')
        return value.strip()


class ChatResponse(BaseModel):
    response: str


@app.post('/chat', response_model=ChatResponse)
def chat(body: ChatRequest):
    # A sync route runs in FastAPI's thread pool, allowing blocking providers.
    history = [message.model_dump() for message in body.history]
    try:
        text = generate_response(body.message, history)
    except NotImplementedError:
        raise HTTPException(503, 'The chat provider is not configured yet.') from None
    except TimeoutError:
        raise HTTPException(504, 'The response took too long. Please try again.') from None
    except Exception:
        raise HTTPException(502, 'Could not generate a response. Please try again.') from None

    if not isinstance(text, str) or not text.strip():
        raise HTTPException(502, 'The chat provider returned an invalid response. Please try again.')
    return ChatResponse(response=text)
