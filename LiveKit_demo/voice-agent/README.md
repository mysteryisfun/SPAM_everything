# Voice Agent

A real-time voice agent with RAG capabilities using LiveKit and OpenAI.

## Features

- 🎙️ **Real-time Voice Conversations** - Natural voice interactions
- 🧠 **RAG-Powered Knowledge Base** - GPT embeddings with ChromaDB
- 🔄 **LiveKit Integration** - WebRTC-based audio streaming
- 🤖 **OpenAI Realtime API** - Advanced AI voice processing
- 🌐 **Web Interface** - Simple HTML frontend

## Setup

1. **Install uv** (if not already installed):
   ```bash
   pip install uv
   ```

2. **Clone and setup**:
   ```bash
   cd voice-agent
   uv sync
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Ingest knowledge base**:
   ```bash
   uv run python scripts/ingest_kb.py
   ```

## Usage

### Start the Backend Server
```bash
uv run uvicorn src.voice_agent.main:app --reload
```

### Open the Frontend
Open `frontend/index.html` in your web browser, or serve it with a local server:
```bash
cd frontend
python -m http.server 3000
```
Then visit `http://localhost:3000`

### API Endpoints

- `GET /` - Health check
- `GET /health` - Detailed system status
- `POST /token` - Generate LiveKit access token
- `POST /search` - Search knowledge base
- `POST /start-agent` - Start voice agent
- `POST /stop-agent` - Stop voice agent

## Architecture

### Part 1: Backend Server (✅ Complete)
- FastAPI server with CORS support
- LiveKit token generation
- Environment configuration

### Part 2: RAG System (✅ Complete)
- GPT embeddings with ChromaDB
- Document ingestion and chunking
- Semantic search capabilities
- LangChain tool integration

### Part 3: Voice Agent (🚧 In Progress)
- LiveKit room connection
- OpenAI Realtime API integration
- Audio streaming between services
- RAG tool usage in conversations

### Part 4: Frontend (✅ Complete)
- HTML interface with modern design
- LiveKit JavaScript integration
- Real-time status updates
- Microphone access handling

## Configuration

Required environment variables in `.env`:
```env
OPENAI_API_KEY=your_openai_api_key
LIVEKIT_URL=wss://your-livekit-server.livekit.cloud
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
```

## Development

### Project Structure
```
voice-agent/
├── src/voice_agent/
│   ├── __init__.py
│   ├── main.py          # FastAPI server
│   ├── config.py        # Settings
│   ├── rag.py           # RAG system
│   └── agent.py         # LiveKit agent
├── frontend/
│   └── index.html       # Web interface
├── data/
│   └── knowledge_base.txt
├── scripts/
│   ├── ingest_kb.py     # Document ingestion
│   └── test_rag.py      # RAG testing
└── pyproject.toml       # Dependencies
```

### Testing Components

1. **Test RAG System**:
   ```bash
   uv run python scripts/test_rag.py
   ```

2. **Test API Endpoints**:
   Visit `http://localhost:8000/docs` for interactive API documentation

3. **Test Voice Agent**:
   Use the frontend interface to start conversations

## Troubleshooting

### Common Issues

1. **Import Errors**: Run `uv sync` to install all dependencies
2. **API Key Issues**: Check `.env` file and API key validity
3. **Port Conflicts**: Change port in uvicorn command if 8000 is busy
4. **Microphone Access**: Allow microphone permissions in browser

### Logs
Check console logs for detailed error information and debugging.

## Next Steps

- [ ] Complete OpenAI Realtime API integration
- [ ] Add conversation history
- [ ] Implement conversation analytics
- [ ] Add support for multiple languages
- [ ] Deploy to production environment
