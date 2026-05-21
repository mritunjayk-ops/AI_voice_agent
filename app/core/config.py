import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
GROQ_AGENT_MODEL = os.getenv(
    "GROQ_AGENT_MODEL",
    "llama-3.3-70b-versatile"
)
