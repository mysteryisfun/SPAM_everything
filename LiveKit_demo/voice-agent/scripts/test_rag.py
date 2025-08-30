#!/usr/bin/env python3
"""
Test script for the RAG knowledge base functionality
"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.voice_agent.rag import knowledge_base

def test_rag():
    """Test the RAG functionality"""
    print("🧪 Testing RAG Knowledge Base...")

    # Test search
    test_queries = [
        "What is the company history?",
        "What products do they offer?",
        "What technology stack do they use?",
        "How can I contact them?"
    ]

    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        results = knowledge_base.search(query, k=2)

        if results:
            for i, result in enumerate(results, 1):
                print(f"  Result {i}: {result['content'][:100]}...")
        else:
            print("  No results found")

    # Test the RAG tool
    print("\n🔧 Testing RAG Tool...")
    rag_tool = knowledge_base.create_rag_tool()

    test_tool_query = "Tell me about the company's products"
    print(f"Tool Query: {test_tool_query}")
    tool_result = rag_tool.func(test_tool_query)
    print(f"Tool Result: {tool_result[:200]}...")

    print("\n✅ RAG tests completed!")

if __name__ == "__main__":
    test_rag()
