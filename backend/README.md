# Project Ligma Backend

## 🏗 Architecture Overview

The backend is built with FastAPI and organized into several key components:

```
backend/
├── agents/             # Agent system components
│   ├── orchestrator.py # Main agent coordination
│   ├── tools/         # Custom LangChain tools
│   └── prompts/       # Agent system prompts
├── pipelines/         # Data processing pipelines
│   ├── generate_knowledge_graph.py
│   └── process_documents.py
├── models/           # Data models and schemas
├── services/         # External service integrations
├── utils/           # Helper utilities
└── main.py         # Application entry point
```

## 🔧 Core Components

### 1. Agent System (`/agents`)
- **Orchestrator**: Manages agent execution and streaming
- **Tools**: Custom LangChain tools for various data sources
- **Prompts**: System prompts for agent behavior

### 2. Data Processing (`/pipelines`)
- Knowledge graph generation pipeline
- Document processing and chunking
- Vector store integration

### 3. External Services (`/services`)
- Semantic Scholar integration
- News API client
- YouTube data processing
- Web search capabilities

## 🚀 Setup and Installation

### Prerequisites
- Python 3.10+
- PostgreSQL (for vector store)
- uv package manager (recommended)

### Installation Steps

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

2. Install dependencies with uv:
```bash
uv pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. Start the server:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 📚 API Documentation

### Agent Endpoints

#### POST /agents/stream
Streams agent thoughts and actions in real-time.

Request:
```json
{
  "prompt": "Research quantum computing advances in 2024"
}
```

Response (streaming):
```json
{
  "type": "thought",
  "content": "I should start by checking recent academic papers..."
}
```

#### POST /agents/invoke
Non-streaming version of agent execution.

### Knowledge Graph Endpoints

#### POST /graph/generate
Generates a new knowledge graph from input query.

#### GET /graph/{uuid}
Retrieves an existing knowledge graph.

## 🔧 Configuration

### Environment Variables

Required environment variables in `.env`:

```bash
# API Keys
ANTHROPIC_API_KEY=your_anthropic_key
SEMANTIC_SCHOLAR_API_KEY=your_semantic_scholar_key
NEWS_API_KEY=your_news_api_key
YOUTUBE_API_KEY=your_youtube_key
SERP_API_KEY=your_serp_api_key

# Database
POSTGRES_URL=postgresql://user:password@localhost:5432/dbname

# Application Settings
DEBUG=True
LOG_LEVEL=INFO
MAX_TOKENS=1000
CHUNK_SIZE=500
```

## 🧪 Testing

Run tests with pytest:
```bash
pytest tests/
```

## 🔍 Debugging

Enable debug logging in `.env`:
```bash
DEBUG=True
LOG_LEVEL=DEBUG
```

View logs:
```bash
tail -f logs/app.log
```

## 🛠 Development Guidelines

1. **Code Style**
   - Follow PEP 8
   - Use type hints
   - Document all functions and classes

2. **Error Handling**
   - Use custom exceptions
   - Implement proper error responses
   - Log errors appropriately

3. **Testing**
   - Write unit tests for new features
   - Maintain test coverage
   - Mock external services

4. **Performance**
   - Use async/await for I/O operations
   - Implement caching where appropriate
   - Monitor memory usage

## 🔄 Pipeline Workflows

### Knowledge Graph Generation

1. Query Processing
2. Data Collection
3. Document Processing
4. Graph Construction
5. Vector Store Integration

### Document Processing

1. Text Extraction
2. Chunking
3. Embedding Generation
4. Vector Store Storage

## 📊 Monitoring and Metrics

- Request latency
- Token usage
- Error rates
- Pipeline performance

## 🔒 Security Considerations

1. API Authentication
2. Rate Limiting
3. Input Validation
4. Secure Storage of Credentials

## 🚧 Known Issues and Limitations

1. Rate limits on external APIs
2. Memory usage with large graphs
3. Processing time for complex queries

## 📈 Future Improvements

1. Implement caching layer
2. Add more data sources
3. Optimize graph generation
4. Enhance error recovery
5. Add more sophisticated monitoring
