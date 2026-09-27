"""Anthropic chat provider."""

import os
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name('.env'))

__all__ = ['generate_response']


def generate_response(message: str, history: list[dict]) -> str:
    """Generate a reply using prior turns and the current user message.

    History excludes the current message and is left unchanged.
    Raises TimeoutError on timeout and RuntimeError on API failure.
    """
    api_key = os.getenv('ANTHROPIC_API_KEY', '').strip()
    if not api_key or api_key == 'your-api-key-here':
        raise RuntimeError('Set ANTHROPIC_API_KEY in backend/.env and restart the backend.')

    messages = [{'role': turn['role'], 'content': turn['content']} for turn in history]
    messages.append({'role': 'user', 'content': message})

    try:
        # Disable automatic retries to keep failures within the UI's wait time.
        with anthropic.Anthropic(api_key=api_key, timeout=60.0, max_retries=0) as client:
            response = client.messages.create(
                model='claude-sonnet-4-5',
                max_tokens=1024,
                messages=messages,
            )
    except anthropic.APITimeoutError:
        raise TimeoutError('The AI service took too long to respond.') from None
    except anthropic.APIError:
        raise RuntimeError('The AI service could not complete the request. Please try again.') from None

    text = '\n'.join(block.text for block in response.content if block.type == 'text')
    if not text.strip():
        raise RuntimeError('The AI service returned no text. Please try again.')
    return text
