from livekit.agents.llm import function_tool
from rag import query_rag,setup_rag
import httpx
@function_tool
async def get_wheather(city: str)->str:
    """Get wheather of a city"""
    return f"the wheather of {city} is sunny"

@function_tool(description="Use this tool to query information about the company from the vector database")
async def query_information(query:str)->str:
    """Query information about the company from the vector database"""
    file_path="C:/Users/ujwal/OneDrive/Documents/GitHub/SPAM_everything/LiveKit_demo/voice-agent/knowledge/rag_file.txt"
    vector_db=setup_rag(file_path,"./chroma_db")
    docs =await query_rag(query,vector_db)
    return "\n".join([doc.page_content for doc in docs]) if docs else "No relevant information found."

@function_tool(description="use this tool to get contact informatio of people")
async def get_contact_info(name:str)->str:
    """Get contact information of a person
    args:
    name: name of the person with first letter capitalized eg:John, Ujwal
    returns:
    contact information of the person in a string
"""
    url = "http://localhost:5678/webhook-test/4be28cc1-5fe6-48ee-bc36-7ec162b48e90"
    payload = {"name":name}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            json_data=response.json()
            return "\n".join([f"{key}: {value}" for key, value in json_data.items()])
        except httpx.RequestError as e:
            return f"Error: {e}"
        except httpx.HTTPError as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Error: {e}"