# Project "Know-It-All" - Information and Reference

This document contains important information and summaries from the LiveKit documentation and the provided example code. It will serve as a technical reference for building our voice agent.

---

## 1. Core Concepts from LiveKit Agents Documentation

- **LiveKit Agents Framework:** A Python framework for building real-time voice and video AI agents.
- **Key Components:**
    - **Agent:** The main class that defines the AI's logic, instructions, and tools.
    - **AgentSession:** Manages the entire real-time pipeline, integrating Speech-to-Text (STT), Large Language Model (LLM), and Text-to-Speech (TTS) services.
    - **Room:** The virtual space where the agent and users interact. Audio and data are exchanged within a room.
    - **Worker:** The process that runs the agent. It can be run locally for development (`dev` mode) or deployed to the cloud.
- **Environment Setup:**
    - **Python:** Requires Python 3.9 or higher.
    - **Package Manager:** `uv` is the recommended tool for managing the environment and dependencies.
    - **API Keys:** We need API keys for LiveKit Cloud and our chosen AI providers (OpenAI, etc.). These should be stored in a `.env` file.
- **Real-time Pipeline (STT-LLM-TTS):**
    1.  **STT (Speech-to-Text):** Transcribes the user's speech into text in real-time.
    2.  **LLM (Large Language Model):** Processes the transcribed text, decides on a response, and determines if a tool needs to be used.
    3.  **TTS (Text-to-Speech):** Converts the LLM's text response back into audible speech.
- **Frontend Integration:**
    - A web or mobile application connects to the same LiveKit room as the agent.
    - The frontend uses the LiveKit SDK (e.g., `livekit-client` for JavaScript) to handle the connection, capture microphone audio, and play back the agent's audio.

---

## 2. Insights from the Example Code (`/ex` directory)

The provided example demonstrates a multi-agent system with a FastAPI backend and a vanilla JavaScript frontend.

### `server.py` (Backend)

- **Framework:** Uses **FastAPI** to create the web server.
- **WebSocket Communication:**
    - Establishes a WebSocket endpoint at `/ws/{session_id}`.
    - This is the primary channel for real-time communication between the frontend and the agent.
- **`RealtimeWebSocketManager`:**
    - A class to manage active agent sessions and their corresponding WebSocket connections.
    - When a new client connects, it instantiates a `RealtimeRunner` with a starting agent (`triage_agent` in the example).
- **Audio Handling:**
    - The server receives audio from the frontend as a JSON message containing an array of 16-bit integers.
    - It packs this integer array into raw bytes (`struct.pack`) before forwarding it to the LiveKit agent session.
- **Event Handling:**
    - It asynchronously listens for events from the `RealtimeSession` (e.g., `audio`, `tool_start`, `history_updated`).
    - These events are serialized into JSON and sent back to the frontend over the WebSocket.
    - Audio data from the agent is Base64 encoded before being sent to the frontend.
- **Static Files:** Serves the `index.html` and `app.js` files from a `static` directory.

### `agent.py` (Agent Logic)

- **Multiple Agents:** Defines several `RealtimeAgent` instances, each with a specific role:
    - `triage_agent`: The initial agent that determines the user's intent.
    - `faq_agent`: An agent specialized in answering FAQs.
    - `seat_booking_agent`: An agent for handling seat updates.
- **Function Tools (`@function_tool`):**
    - Demonstrates how to define Python functions as tools that the LLM can decide to call.
    - Examples: `faq_lookup_tool`, `update_seat`, `get_weather`.
- **Agent Handoff:**
    - Shows how one agent can "handoff" the conversation to another, more specialized agent. The `triage_agent` can delegate tasks to the `faq_agent` or `seat_booking_agent`.

### `static/app.js` (Frontend)

- **Audio Capture:**
    - Uses `navigator.mediaDevices.getUserMedia` to access the user's microphone.
    - It specifically requests a `sampleRate` of 24000 Hz to match the agent's expected input.
    - A `ScriptProcessorNode` is used to capture audio data in chunks.
- **Audio Processing:**
    - The captured audio (Float32) is converted to a 16-bit integer array (`Int16Array`).
    - This array is sent to the backend via the WebSocket as a JSON object: `{ type: 'audio', data: [...] }`.
- **Audio Playback:**
    - When an `audio` event is received from the server, the Base64 encoded audio is decoded.
    - The Web Audio API (`AudioContext`, `createBufferSource`) is used to play the audio.
    - It implements an audio queue to ensure that incoming audio chunks are played sequentially without interrupting each other.
- **UI Updates:**
    - Dynamically updates the conversation history, event stream, and tool usage panels based on messages received from the server.

### `static/index.html` (Frontend UI)

- **Structure:** A simple, clean HTML structure with three main panels:
    1.  **Conversation:** Displays the chat between the user and the agent.
    2.  **Event stream:** Shows the raw JSON events from the agent for debugging.
    3.  **Tools & Handoffs:** Visualizes when the agent uses a tool or hands off to another agent.
- **Controls:** Includes a "Connect" button to start/stop the session and a "Mute" button to control the microphone.

---

This information provides a solid foundation for our project. We have a clear understanding of the architecture, the key technologies, and the data flow between the frontend, backend, and AI services.

---

## 3. Code Architecture for Our "Know-It-All" Agent

Based on the plan and the example code, here is a blueprint for the code we will write.

### **Backend (`/backend`)**

This is the core of our application, running the FastAPI server and the LiveKit agent.

-   **`main.py`**:
    -   **Purpose**: The main entry point for our backend. It will run the FastAPI server.
    -   **Key Features**:
        -   A FastAPI app instance.
        -   An HTTP endpoint (e.g., `/get-livekit-token`) that the frontend can call to get a temporary access token for a LiveKit room.
        -   A WebSocket endpoint (e.g., `/ws`) where the frontend will connect to stream user audio and receive agent audio and events. This will be simpler than the example's `RealtimeWebSocketManager` since we are starting with a single agent.
        -   It will import and run the agent logic from `agent.py`.

-   **`agent.py`**:
    -   **Purpose**: To define the logic and personality of our AI agent.
    -   **Key Features**:
        -   A class `KnowItAllAgent` that inherits from `livekit.agents.Agent`.
        -   It will be initialized with a system prompt (e.g., "You are a helpful assistant with access to a special knowledge base...").
        -   It will define and use a `Tool` for our RAG functionality. This tool will be created using `langchain` and will be linked to the search function in `rag.py`.

-   **`rag.py`**:
    -   **Purpose**: To manage the Retrieval-Augmented Generation (RAG) functionality. This is the agent's "memory".
    -   **Key Features**:
        -   A function to load the text from `data/knowledge.txt`.
        -   A function to split the document into chunks, generate embeddings (using `sentence-transformers`), and store them in a **ChromaDB** vector store. This is the "ingestion" process.
        -   A search function that takes a user's query, searches the ChromaDB vector store for relevant information, and returns it. This function will be the core of our LangChain `Tool`.

### **Frontend (`/frontend`)**

A simple, clean web interface for the user to interact with the agent. We will adapt the code from the `/ex/static` directory.

-   **`index.html`**:
    -   **Purpose**: The main UI of our application.
    -   **Key Features**:
        -   A single "Start Conversation" button.
        -   A status display to show states like "Connecting...", "Listening...", "Agent Speaking...".
        -   A simple area to display the conversation transcript (optional, but good for debugging).

-   **`app.js`**:
    -   **Purpose**: The client-side logic that powers the user interface.
    -   **Key Features**:
        -   **Connection Flow**:
            1.  On "Start" click, it will call our backend's `/get-livekit-token` endpoint.
            2.  It will use this token to connect to the LiveKit room using the LiveKit JavaScript SDK.
            3.  It will also connect to our backend's `/ws` WebSocket endpoint.
        -   **Audio Handling**:
            -   It will use `navigator.mediaDevices.getUserMedia` to capture microphone audio.
            -   Crucially, it will process the raw audio, convert it from Float32 format to a 16-bit integer array, and send it to our backend via the WebSocket.
            -   It will receive Base64 encoded audio from the backend, decode it, and play it using the Web Audio API.

### **Data (`/data`)**

-   **`knowledge.txt`**:
    -   **Purpose**: A simple text file containing the specialized information we want our agent to know. This is the source for our RAG tool. We will populate this with some sample facts.

