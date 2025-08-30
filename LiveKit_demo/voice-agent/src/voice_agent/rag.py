"""
RAG (Retrieval-Augmented Generation) module for the Voice Agent
Handles knowledge base ingestion, vector storage, and retrieval using ChromaDB and LangChain.
"""

import os
from pathlib import Path
from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings
from chromadb.errors import NotFoundError
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from langchain.tools import Tool

from .config import settings

class KnowledgeBase:
    """Manages the knowledge base using ChromaDB and GPT embeddings"""

    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=settings.openai_api_key
        )
        self.persist_directory = Path(settings.chroma_persist_directory)
        self.persist_directory.mkdir(exist_ok=True)

        # Initialize ChromaDB client
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.persist_directory)
        )

        # Create or get collection
        self.collection_name = "voice_agent_kb"
        try:
            self.collection = self.chroma_client.get_collection(
                name=self.collection_name
            )
        except NotFoundError:
            self.collection = self.chroma_client.create_collection(
                name=self.collection_name
            )

        # Initialize LangChain Chroma vectorstore
        self.vectorstore = Chroma(
            client=self.chroma_client,
            collection_name=self.collection_name,
            embedding_function=self.embeddings
        )

    def ingest_document(self, file_path: str, chunk_size: int = 1000, chunk_overlap: int = 200):
        """Ingest a document into the knowledge base"""
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")

        # Read the document
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split the document into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )

        chunks = text_splitter.split_text(content)

        # Generate embeddings and store in ChromaDB
        documents = []
        metadatas = []
        ids = []

        for i, chunk in enumerate(chunks):
            documents.append(chunk)
            metadatas.append({
                "source": str(file_path),
                "chunk_id": i,
                "total_chunks": len(chunks)
            })
            ids.append(f"{file_path.stem}_chunk_{i}")

        # Add to vectorstore
        self.vectorstore.add_texts(
            texts=documents,
            metadatas=metadatas,
            ids=ids
        )

        print(f"Successfully ingested {len(chunks)} chunks from {file_path}")
        return len(chunks)

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search the knowledge base for relevant information"""
        docs = self.vectorstore.similarity_search(query, k=k)

        results = []
        for doc in docs:
            results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": getattr(doc, 'score', None)
            })

        return results

    def get_qa_chain(self):
        """Create a QA chain for answering questions"""
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            openai_api_key=settings.openai_api_key
        )

        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": 3}),
            return_source_documents=True
        )

        return qa_chain

    def create_rag_tool(self) -> Tool:
        """Create a LangChain Tool for the knowledge base search"""
        def knowledge_base_search(query: str) -> str:
            """Search the knowledge base for information about the company and products."""
            try:
                results = self.search(query, k=3)
                if not results:
                    return "No relevant information found in the knowledge base."

                # Format the results
                formatted_results = []
                for i, result in enumerate(results, 1):
                    formatted_results.append(f"Result {i}:\n{result['content']}")

                return "\n\n".join(formatted_results)
            except Exception as e:
                return f"Error searching knowledge base: {str(e)}"

        tool = Tool(
            name="knowledge_base_search",
            description="Use this tool to answer questions about the company's history, products, and services. Input should be a clear question or search query.",
            func=knowledge_base_search
        )

        return tool

# Global knowledge base instance
knowledge_base = KnowledgeBase()
