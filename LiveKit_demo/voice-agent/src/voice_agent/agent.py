"""
LiveKit Agent for Voice Agent
Handles real-time voice conversations using LiveKit and OpenAI Realtime API.
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any
import aiohttp
from livekit import rtc
from livekit.plugins.openai import realtime

from .config import settings
from .rag import knowledge_base

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceAgent:
    """LiveKit agent that handles voice conversations with RAG capabilities"""

    def __init__(self):
        self.room: Optional[rtc.Room] = None
        self.audio_stream: Optional[rtc.AudioStream] = None
        self.openai_session: Optional[realtime.RealtimeSession] = None
        self.rag_tool = knowledge_base.create_rag_tool()

    async def connect_to_room(self, token: str):
        """Connect to a LiveKit room"""
        try:
            logger.info("Connecting to LiveKit room...")
            self.room = rtc.Room()

            # Set up event handlers
            self.room.on("track_subscribed", self.on_track_subscribed)
            self.room.on("track_unsubscribed", self.on_track_unsubscribed)
            self.room.on("participant_connected", self.on_participant_connected)
            self.room.on("participant_disconnected", self.on_participant_disconnected)

            # Connect to room
            await self.room.connect(settings.livekit_url, token)
            logger.info("Successfully connected to LiveKit room")

            # Publish agent's audio track
            await self.setup_audio_track()

        except Exception as e:
            logger.error(f"Failed to connect to room: {e}")
            raise

    async def setup_audio_track(self):
        """Set up audio track for the agent"""
        try:
            # Create audio source
            audio_source = rtc.AudioSource(sample_rate=24000, num_channels=1)

            # Create and publish audio track
            audio_track = rtc.LocalAudioTrack.create_audio_track("agent_audio", audio_source)
            options = rtc.TrackPublishOptions()
            options.source = rtc.TrackSource.SOURCE_MICROPHONE

            await self.room.local_participant.publish_track(audio_track, options)
            logger.info("Agent audio track published")

            # Store audio source for later use
            self.audio_source = audio_source

        except Exception as e:
            logger.error(f"Failed to setup audio track: {e}")
            raise

    async def setup_openai_session(self):
        """Set up OpenAI Realtime API session"""
        try:
            logger.info("Setting up OpenAI Realtime session...")

            # Create OpenAI realtime session
            self.openai_session = realtime.RealtimeSession(
                api_key=settings.openai_api_key,
                model="gpt-4o-realtime-preview"
            )

            # Configure session
            await self.openai_session.update_session({
                "modalities": ["text", "audio"],
                "instructions": self.get_system_instructions(),
                "voice": "alloy",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500
                },
                "tools": [self.get_rag_tool_definition()]
            })

            # Set up event handlers
            self.openai_session.on("response.audio.delta", self.on_openai_audio_delta)
            self.openai_session.on("response.text.delta", self.on_openai_text_delta)
            self.openai_session.on("response.done", self.on_openai_response_done)
            self.openai_session.on("input_audio_buffer.speech_started", self.on_speech_started)
            self.openai_session.on("input_audio_buffer.speech_stopped", self.on_speech_stopped)

            logger.info("OpenAI Realtime session configured")

        except Exception as e:
            logger.error(f"Failed to setup OpenAI session: {e}")
            raise

    def get_system_instructions(self) -> str:
        """Get system instructions for the OpenAI agent"""
        return """
        You are a knowledgeable voice assistant with access to a specialized knowledge base about our company.

        Your capabilities:
        - Answer questions about the company's history, products, and services
        - Provide information about our technology stack and offerings
        - Help users understand our business and contact information

        When users ask questions that require specific company information, use the knowledge_base_search tool to get accurate, up-to-date information from our knowledge base.

        Be conversational, helpful, and professional. If you don't have specific information in your knowledge base, let the user know and offer to help with what you can.

        Always maintain a friendly and engaging tone during voice conversations.
        """

    def get_rag_tool_definition(self) -> Dict[str, Any]:
        """Get the RAG tool definition for OpenAI"""
        return {
            "type": "function",
            "name": "knowledge_base_search",
            "description": "Search the company knowledge base for specific information about history, products, services, and technology.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to find relevant information in the knowledge base"
                    }
                },
                "required": ["query"]
            }
        }

    def on_track_subscribed(self, track: rtc.Track, publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
        """Handle when a remote track is subscribed"""
        logger.info(f"Track subscribed: {track.kind} from {participant.identity}")

        if track.kind == rtc.TrackKind.KIND_AUDIO:
            # Handle audio track from user
            self.audio_stream = rtc.AudioStream(track)
            self.audio_stream.on("data", self.on_audio_data)

    def on_track_unsubscribed(self, track: rtc.Track, publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
        """Handle when a remote track is unsubscribed"""
        logger.info(f"Track unsubscribed: {track.kind} from {participant.identity}")

    def on_participant_connected(self, participant: rtc.RemoteParticipant):
        """Handle participant connection"""
        logger.info(f"Participant connected: {participant.identity}")

    def on_participant_disconnected(self, participant: rtc.RemoteParticipant):
        """Handle participant disconnection"""
        logger.info(f"Participant disconnected: {participant.identity}")

    def on_audio_data(self, data: rtc.AudioFrame):
        """Handle incoming audio data from user"""
        try:
            if self.openai_session:
                # Send audio data to OpenAI asynchronously
                asyncio.create_task(self._send_audio_to_openai(data))
        except Exception as e:
            logger.error(f"Error processing audio data: {e}")

    async def _send_audio_to_openai(self, data: rtc.AudioFrame):
        """Async helper to send audio to OpenAI"""
        try:
            await self.openai_session.send_audio(data.data)
        except Exception as e:
            logger.error(f"Error sending audio to OpenAI: {e}")

    def on_openai_audio_delta(self, event):
        """Handle audio delta from OpenAI"""
        try:
            if self.audio_source and event.delta:
                # Send audio to LiveKit room asynchronously
                asyncio.create_task(self._send_audio_to_livekit(event.delta))
        except Exception as e:
            logger.error(f"Error handling OpenAI audio delta: {e}")

    async def _send_audio_to_livekit(self, audio_data):
        """Async helper to send audio to LiveKit"""
        try:
            await self.audio_source.capture_frame(audio_data)
        except Exception as e:
            logger.error(f"Error sending audio to LiveKit: {e}")

    def on_openai_text_delta(self, event):
        """Handle text delta from OpenAI"""
        logger.info(f"OpenAI text: {event.delta}")

    def on_openai_response_done(self, event):
        """Handle when OpenAI response is complete"""
        logger.info("OpenAI response completed")

        # Handle tool calls if any
        if hasattr(event, 'response') and hasattr(event.response, 'tool_calls') and event.response.tool_calls:
            asyncio.create_task(self.handle_tool_calls(event.response.tool_calls))

    async def handle_tool_calls(self, tool_calls):
        """Handle tool calls from OpenAI"""
        for tool_call in tool_calls:
            if tool_call.function.name == "knowledge_base_search":
                # Execute RAG search
                query = json.loads(tool_call.function.arguments)["query"]
                result = self.rag_tool.func(query)

                # Send result back to OpenAI
                await self.openai_session.send_tool_result(tool_call.id, result)

    def on_speech_started(self, event):
        """Handle when user starts speaking"""
        logger.info("User started speaking")

    def on_speech_stopped(self, event):
        """Handle when user stops speaking"""
        logger.info("User stopped speaking")

    async def start_conversation(self):
        """Start the conversation loop"""
        try:
            # Connect to OpenAI session
            await self.openai_session.connect()

            logger.info("Voice agent conversation started")

            # Keep the conversation running
            while True:
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Error in conversation loop: {e}")
        finally:
            await self.cleanup()

    async def cleanup(self):
        """Clean up resources"""
        try:
            if self.openai_session:
                await self.openai_session.disconnect()

            if self.room:
                await self.room.disconnect()

            logger.info("Voice agent cleanup completed")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

# Global agent instance
voice_agent = VoiceAgent()
