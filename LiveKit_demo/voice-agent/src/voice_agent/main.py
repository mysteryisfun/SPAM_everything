"""
Voice Agent Backend Server
FastAPI application serving as the central hub for the voice agent system.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio
import logging
import os
from dotenv import load_dotenv
from livekit import api

from .config import settings
from .rag import knowledge_base
from .agent import voice_agent

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Voice Agent API",
    description="Real-time voice agent with RAG capabilities",
    version="0.1.0"
)

# Configure CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    query: str
    k: int = 5

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Voice Agent API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    kb_status = "ready" if knowledge_base.collection.count() > 0 else "empty"

    return {
        "status": "healthy",
        "services": {
            "openai": bool(settings.openai_api_key),
            "livekit": bool(settings.livekit_api_key and settings.livekit_api_secret),
            "knowledge_base": kb_status,
            "chroma_db": f"{knowledge_base.collection.count()} documents"
        }
    }

@app.post("/token")
async def get_token(room_name: str = "voice-room", participant_name: str = "user"):
    """Generate LiveKit access token for frontend"""
    try:
        token = api.AccessToken(settings.livekit_api_key, settings.livekit_api_secret) \
            .with_identity(participant_name) \
            .with_name(participant_name) \
            .with_grants(api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
            ))

        jwt_token = token.to_jwt()
        return {
            "token": jwt_token,
            "url": settings.livekit_url,
            "room": room_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate token: {str(e)}")

@app.post("/search")
async def search_knowledge_base(request: SearchRequest):
    """Search the knowledge base"""
    try:
        results = knowledge_base.search(request.query, request.k)
        return {
            "query": request.query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/start-agent")
async def start_agent(room_name: str = "voice-room"):
    """Start the voice agent in a LiveKit room"""
    try:
        # Generate token for the agent
        token = api.AccessToken(settings.livekit_api_key, settings.livekit_api_secret) \
            .with_identity("voice-agent") \
            .with_name("Voice Agent") \
            .with_grants(api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
            ))

        agent_token = token.to_jwt()

        # Start agent in background
        asyncio.create_task(run_agent(agent_token))

        return {
            "status": "starting",
            "room": room_name,
            "message": "Voice agent is connecting to the room"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start agent: {str(e)}")

@app.post("/stop-agent")
async def stop_agent():
    """Stop the voice agent"""
    try:
        await voice_agent.cleanup()
        return {"status": "stopped", "message": "Voice agent has been stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop agent: {str(e)}")

async def run_agent(token: str):
    """Run the voice agent (background task)"""
    try:
        # Connect to room
        await voice_agent.connect_to_room(token)

        # Setup OpenAI session
        await voice_agent.setup_openai_session()

        # Start conversation
        await voice_agent.start_conversation()

    except Exception as e:
        logger.error(f"Agent error: {e}")
    finally:
        await voice_agent.cleanup()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
