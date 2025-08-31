from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import (
    openai,
    noise_cancellation,
)
from src.tools.tools import get_wheather, query_information, get_contact_info
load_dotenv(".env")



#from tools import get_wheather
class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="Your name is voxhive a helpful voice AI assistant, use the available tools to answer the queries you dont know.",
                        tools = [
                            get_wheather,
                            query_information,
                            get_contact_info
                            ]
                        )   
    

async def entrypoint(ctx: agents.JobContext):
    session = AgentSession(
        llm=openai.realtime.RealtimeModel(
            voice="coral"
        )
    )
    assistant = Assistant()
    await session.start(
        room=ctx.room,
        agent=assistant,
        room_input_options=RoomInputOptions(
            # For telephony applications, use `BVCTelephony` instead for best results
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )
    await session.generate_reply(
        instructions="Greet the user and offer your assistance in English."
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))