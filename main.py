from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.chat_routes import router as chat_router
from app.api.routes.voice_routes import router as voice_router

from app.core.logger import logger


app = FastAPI(
    title="AI Voice Agent"
)


# CORS CONFIGURATION

app.add_middleware(

    CORSMiddleware,

    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500"
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]
)


logger.info(
    "AI Voice Agent Starting..."
)


@app.get("/")
async def root():

    logger.info(
        "Root endpoint accessed"
    )

    return {
        "message": "AI Voice Agent Running"
    }


@app.get("/health")
async def health():

    logger.info(
        "Health endpoint checked"
    )

    return {
        "status": "healthy"
    }


# ROUTES

app.include_router(chat_router)

app.include_router(voice_router)