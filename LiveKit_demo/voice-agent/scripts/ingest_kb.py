#!/usr/bin/env python3
"""
Knowledge Base Ingestion Script
Ingests documents into the ChromaDB vector database for the voice agent.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.voice_agent.rag import knowledge_base
from src.voice_agent.config import settings

def main():
    """Main ingestion function"""
    print("🚀 Starting knowledge base ingestion...")

    # Check if knowledge base file exists
    kb_path = Path(settings.knowledge_base_path)
    if not kb_path.exists():
        print(f"❌ Knowledge base file not found: {kb_path}")
        print("Please ensure the knowledge base document exists.")
        return

    try:
        # Ingest the document
        print(f"📖 Ingesting document: {kb_path}")
        num_chunks = knowledge_base.ingest_document(str(kb_path))

        print(f"✅ Successfully ingested {num_chunks} chunks into the knowledge base")

        # Test the search functionality
        print("\n🧪 Testing search functionality...")
        test_query = "What products does the company offer?"
        results = knowledge_base.search(test_query, k=2)

        if results:
            print(f"🔍 Search results for: '{test_query}'")
            for i, result in enumerate(results, 1):
                print(f"\nResult {i}:")
                print(f"Content: {result['content'][:200]}...")
                print(f"Source: {result['metadata']['source']}")
        else:
            print("⚠️  No search results found")

        print("\n🎉 Knowledge base setup complete!")

    except Exception as e:
        print(f"❌ Error during ingestion: {str(e)}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
