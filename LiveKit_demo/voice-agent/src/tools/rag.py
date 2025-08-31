from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from dotenv import load_dotenv
load_dotenv()
def load_text(file_path:str)->str:
    with open(file_path,'r', encoding='utf-8') as f:
        return f.read()
def setup_rag(text_file_path:str, persist_directry:str="./chroma_db"):
    
    if os.path.exists(persist_directry):
        embeddings= OpenAIEmbeddings(model="text-embedding-3-small")
        vector_store = Chroma(persist_directory=persist_directry, embedding_function=embeddings)
        print("using the existing vector store")
    else:
        text = load_text(text_file_path)

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        documnets = [Document(page_content = chunk) for chunk in splitter.split_text(text)]
        print(documnets)
        print(len(documnets))
        print(documnets[0])

        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        vector_store = Chroma.from_documents(documnets, embeddings, persist_directory=persist_directry)
    return vector_store
async def query_rag(query:str, vector_store:Chroma):
    docs = vector_store.similarity_search(query, k=2)
    return docs
if __name__ == "__main__":
    vector_store=setup_rag("C:/Users/ujwal/OneDrive/Documents/GitHub/SPAM_everything/LiveKit_demo/voice-agent/knowledge/rag_file.txt")
    text = "whats the name of the company"
    return_text=query_rag(text,vector_store)
    print(return_text)