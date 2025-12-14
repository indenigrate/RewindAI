from langchain_google_genai import ChatGoogleGenerativeAI
from app.config.settings import MODEL_NAME, REQUEST_TIMEOUT
import os

def get_llm():
    return ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        api_key=os.getenv("GOOGLE_API_KEY"),
        request_timeout=REQUEST_TIMEOUT,
    )
