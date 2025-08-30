from livekit.agents.llm import function_tool
from rag import query_rag,setup_rag
@function_tool
async def get_wheather(city: str)->str:
    """Get wheather of a city"""
    return f"the wheather of {city} is sunny"

@function_tool
async def query_information(query:str)->str:
    """Query information about the company from the vector database"""
    file_path="C:/Users/ujwal/OneDrive/Documents/GitHub/SPAM_everything/LiveKit_demo/voice-agent/knowledge/rag_file.txt"
    vector_db=setup_rag(file_path,"./chroma_db")
    docs =await query_rag(query,vector_db)
    return "\n".join([doc.page_content for doc in docs]) if docs else "No relevant information found."