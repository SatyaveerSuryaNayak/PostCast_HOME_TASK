# Portcast Home Task

This is a REST API that lets you fetch paragraphs from an external source, store them, search through them, and get dictionary definitions for the most common words. It's built with FastAPI, PostgreSQL, Redis, and Celery.

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Local Development Setup](#local-development-setup)
- [Docker Compose Setup](#docker-compose-setup)
- [Code Structure](#code-structure)
- [Database Design](#database-design)
- [API Endpoints](#api-endpoints)
- [How It Works](#how-it-works)
- [Caching Strategy](#caching-strategy)
- [Search Implementation & Enhancements](#search-implementation--enhancements)
- [Running Tests](#running-tests)

## Features

- **Fetch Endpoint**: Fetches a paragraph from an external API and saves it to the database
- **Search Endpoint**: Search through stored paragraphs using AND or OR operators
- **Dictionary Endpoint**: Shows definitions for the top 10 most frequent words found in all paragraphs, with smart caching to avoid hitting the dictionary API too often
- **Background Jobs**: When you fetch a new paragraph, a background job automatically updates the dictionary cache
- **Caching**: Uses Redis to cache dictionary definitions and word frequencies, so repeated requests are super fast

## Quick Start

### Using Docker Compose (Recommended)

This is the easiest way to get everything up and running:

```bash
# Start everything (PostgreSQL, Redis, API, Celery worker)
docker compose up --build -d

# Check if everything is running
docker compose ps

# See what the API is doing
docker compose logs -f api

# Open the API docs in your browser
open http://localhost:8000/docs
```

That's it! The API will be running at `http://localhost:8000` and you can check out the Swagger docs at `/docs`.

### Stop Services

```bash
docker compose down
```

## Local Development Setup

If you want to run everything on your machine without Docker, here's how to do it:

### Prerequisites

- Python 3.10 or higher
- PostgreSQL running locally (or use Docker for just DB/Redis)
- Redis running locally (or use Docker for just Redis)

### Step-by-Step Setup

1. **Clone and navigate to the project**
   ```bash
   cd portcast_home_task
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up PostgreSQL**
   
   If you have PostgreSQL installed locally:
   ```bash
   # Start PostgreSQL (macOS with Homebrew)
   brew services start postgresql
   
   # Create the database
   createdb paragraphs_db
   ```
   
   Or use Docker for just the database:
   ```bash
   docker run -d -p 5432:5432 \
     -e POSTGRES_USER=postgres \
     -e POSTGRES_PASSWORD=postgres \
     -e POSTGRES_DB=paragraphs_db \
     --name paragraph_db \
     postgres:15-alpine
   ```

5. **Set up Redis**
   
   If you have Redis installed locally:
   ```bash
   # Start Redis (macOS with Homebrew)
   brew services start redis
   ```
   
   Or use Docker for just Redis:
   ```bash
   docker run -d -p 6379:6379 --name paragraph_redis redis:7-alpine
   ```

6. **Create environment file**
   
   Create a `.env` file in the project root:
   ```bash
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/paragraphs_db
   METAPHORPSUM_URL=http://metaphorpsum.com/paragraphs/1/50
   DICTIONARY_API_URL=https://api.dictionaryapi.dev/api/v2/entries/en
   REDIS_URL=redis://localhost:6379/0
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_DB=0
   CELERY_BROKER_URL=redis://localhost:6379/0
   CELERY_RESULT_BACKEND=redis://localhost:6379/0
   ```

7. **Start the API**
   ```bash
   source venv/bin/activate
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

8. **Start Celery Worker** (in a separate terminal)
   ```bash
   source venv/bin/activate
   celery -A app.core.celery_app worker --loglevel=info
   ```

9. **Access the API**
   - API: http://localhost:8000
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Using Helper Scripts

There are a couple of helper scripts to make this easier:

```bash
# Start the API
./start_local.sh

# Start the Celery worker (in a separate terminal)
./start_celery.sh
```

## Docker Compose Setup

The `docker-compose.yml` file sets up everything you need - database, cache, API, and background workers:

### Services

1. **PostgreSQL Database** (`db`)
   - Port: 5432
   - Database: `paragraphs_db`
   - User: `postgres` / Password: `postgres`
   - Persistent volume for data

2. **Redis** (`redis`)
   - Port: 6379
   - Used for caching and Celery message broker
   - Persistent volume for data

3. **FastAPI Application** (`api`)
   - Port: 8000
   - Auto-reload enabled for development
   - Depends on `db` and `redis` being healthy

4. **Celery Worker** (`celery-worker`)
   - Processes background tasks
   - Updates dictionary cache asynchronously
   - Depends on `db` and `redis` being healthy

### Environment Variables

All services are configured via environment variables in `docker-compose.yml`. The API service uses:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`, `REDIS_HOST`, `REDIS_PORT`: Redis configuration
- `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`: Celery configuration
- External API URLs for fetching paragraphs and definitions

### Health Checks

All services have health checks set up:
- Database: Checks if PostgreSQL is ready
- Redis: Pings Redis to make sure it's up
- The API waits for the database and Redis to be ready before it starts

## Code Structure

The code is organized in a clean, layered way that makes it easy to understand and work with:

```
portcast_home_task/
├── app/
│   ├── main.py                    # FastAPI app entry point, startup events
│   ├── config.py                  # Configuration management (Pydantic Settings)
│   │
│   ├── core/                      # Core infrastructure
│   │   ├── database.py           
│   │   ├── cache.py              # Redis cache wrapper
│   │   └── celery_app.py         # Celery application configuration
│   │
│   ├── models/                    # Database models 
│   │   └── paragraph.py          # Paragraph model
│   │
│   ├── schemas/                   # Request/Response schemas (Pydantic)
│   │   └── paragraph.py          # API schemas for validation
│   │
│   ├── repositories/              # Data access layer
│   │   └── paragraph_repository.py  # Database operations
│   │
│   ├── services/                  # Business logic layer
│   │   ├── paragraph_service.py  # Paragraph business logic
│   │   └── dictionary_service.py  # Dictionary logic with caching
│   │
│   ├── routes/                     # API endpoints
│   │   ├── health.py             # Health check endpoint
│   │   ├── paragraphs.py         # /fetch, /search endpoints
│   │   └── dictionary.py         # /dictionary endpoint
│   │
│   └── tasks/                     # Celery background tasks
│       └── dictionary_tasks.py   # Dictionary cache update tasks
│
├── tests/                         # Test suite
│   ├── conftest.py               # Pytest fixtures
│   ├── unit/                     # Unit tests
│   └── integration/              # Integration tests
│
├── docker-compose.yml             # Docker Compose configuration (all services)
├── docker-compose.local.yml       # Local dev services (DB + Redis only)
├── Dockerfile                     # Application Docker image
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

### Architecture Layers

```
┌─────────────────────────────────────┐
│         API Layer (Routes)          │  FastAPI endpoints
│  /fetch, /search, /dictionary       │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Service Layer                  │  Business logic
│  ParagraphService, DictionaryService│
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│    Repository Layer                  │  Data access
│  ParagraphRepository                 │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Database Layer                  │  PostgreSQL
│  SQLAlchemy ORM                      │
└──────────────────────────────────────┘
```

### Key Design Principles

1. **Separation of Concerns**: Each part of the code does one thing and does it well
2. **Dependency Injection**: We pass dependencies in rather than creating them inside, which makes testing easier
3. **Repository Pattern**: Database operations are abstracted away, so we could swap databases if needed
4. **Service Layer**: Business logic lives here, separate from the API routes and database code
5. **Fail-Fast**: If the database isn't available when the app starts, it crashes immediately instead of failing later

## Database Design

### Schema

The database uses a simple, efficient schema:

**Table: `paragraphs`**

| Column      | Type          | Constraints           | Description                    |
|-------------|---------------|-----------------------|--------------------------------|
| `id`        | INTEGER       | PRIMARY KEY, INDEX    | Auto-incrementing unique ID    |
| `content`   | TEXT          | NOT NULL, INDEX       | The paragraph text content     |
| `created_at`| TIMESTAMP     | NOT NULL, DEFAULT NOW| When the paragraph was stored  |

### SQLAlchemy Model

```python
class Paragraph(Base):
    __tablename__ = "paragraphs"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

### Design Decisions

- **TEXT type for content**: Paragraphs can be pretty long, so we use TEXT instead of VARCHAR
- **Indexed content column**: There's an index on the content column 
- **Timezone-aware timestamps**: The `created_at` field uses timezone-aware timestamps so we don't have timezone issues
- **Simple schema**: We kept it simple - just the basics. Can always add more fields later if needed

### Indexes

- Primary key index on `id` (automatic)
- Index on `content` column

## API Endpoints

### 1. POST /fetch

Fetches a paragraph from an external API and stores it in the database.

**Request:**
```bash
curl -X POST http://localhost:8000/fetch
```

**Response (201 Created):**
```json
{
  "id": 1,
  "content": "The paragraph text content here...",
  "created_at": "2025-11-21T10:30:00Z"
}
```

**How it works:**
```
┌─────────┐    1. HTTP GET      ┌──────────────┐
│ Client  │ ──────────────────> │ External API │
│         │                     │ (metaphorpsum)│
└────┬────┘                     └──────┬───────┘
     │                                  │
     │                                  │ 2. Paragraph text
     │                                  │
     │ 3. POST /fetch                   │
     ▼                                  ▼
┌─────────────────────────────────────────────┐
│         FastAPI Application                 │
│  ┌──────────────────────────────────────┐   │
│  │  ParagraphService                   │   │
│  │  1. Fetch from external API         │   │
│  │  2. Store in PostgreSQL             │   │
│  │  3. Trigger Celery task (async)      │   │
│  └──────────────────────────────────────┘   │
└────┬───────────────────────────────────────┘
     │
     │ 4. Store paragraph
     ▼
┌─────────────┐         ┌──────────────┐
│ PostgreSQL  │         │   Redis      │
│  (Storage)  │         │ (Task Queue) │
└─────────────┘         └──────┬──────┘
                                │
                                │ 5. Background task
                                ▼
                         ┌──────────────┐
                         │ Celery Worker│
                         │ (Updates cache)│
                         └──────────────┘
```

**How it works:**
- We fetch the paragraph from the external API using async HTTP client (httpx.AsyncClient)
- We save it to the database using async database operations
- We trigger a Celery task to update the dictionary cache in the background (doesn't block the response)
- If Celery or Redis is down, the request still works fine - we just skip the cache update

### 2. POST /search

Searches through stored paragraphs using AND or OR operators.

**Request:**
```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "words": ["one", "two", "three"],
    "operator": "or"
  }'
```

**Response (200 OK):**
```json
{
  "paragraphs": [
    {
      "id": 1,
      "content": "Paragraph containing one of the words...",
      "created_at": "2025-11-21T10:30:00Z"
    },
    {
      "id": 3,
      "content": "Another paragraph with two...",
      "created_at": "2025-11-21T10:35:00Z"
    }
  ],
  "total_count": 2
}
```

**Parameters:**
- `words` (array, required): List of words to search for
- `operator` (string, required): Either `"and"` or `"or"`
  - `"or"`: Returns paragraphs containing **at least one** of the words
  - `"and"`: Returns paragraphs containing **all** of the words

**How it works:**
```
┌─────────┐    1. POST /search
│ Client  │ ──────────────────>
│         │    {words: ["one", "two"], operator: "or"}
└─────────┘
     │
     │
     ▼
┌─────────────────────────────────────┐
│      FastAPI /search endpoint      │
└──────────────┬─────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│    ParagraphService.search()       │
│  - Validates operator               │
│  - Calls repository                 │
└──────────────┬─────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  ParagraphRepository.search()        │
│  - Sanitizes input (removes special │
│    characters like backslash)       │
│  - Builds SQL query with regex      │
│  - Uses AND/OR based on operator     │
└──────────────┬─────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│         PostgreSQL Query            │
│  SELECT * FROM paragraphs           │
│  WHERE content ~* '\yone\y'         │
│     OR content ~* '\ytwo\y'         │
│  (Regex with word boundaries for     │
│   exact word matching)              │
└──────────────┬─────────────────────┘
               │
               │ 2. Matching paragraphs
               ▼
┌─────────┐
│ Client  │ <─── 3. JSON response
└─────────┘
```

**How it works:**
- Uses PostgreSQL's regex operator (`~*`) with word boundaries (`\y`) to match exact words
- Case-insensitive - "One", "ONE", and "one" all match the same
- Input sanitization - automatically removes special characters like backslashes that could break the regex
- Database-level filtering - the database does the filtering, we don't load all paragraphs into memory
- Works fine for small to medium datasets (up to around 100K paragraphs)
- For really large datasets, see the [Search Enhancements](#search-implementation--enhancements) section

**What this means:**
- **Exact word matching**: If you search for "one", it only matches "one", not "none" or "someone"
- **Case doesn't matter**: "One", "ONE", "one" - all the same
- **Safe input**: Special characters get cleaned up automatically so the regex doesn't break
- **Efficient**: The database does the heavy lifting, not your Python code

### 3. GET /dictionary

Returns definitions for the top 10 most frequent words in all stored paragraphs.

**Request:**
```bash
curl http://localhost:8000/dictionary
```

**Response (200 OK):**
```json
{
  "words": [
    {
      "word": "the",
      "definitions": [
        "Used to refer to a specific person or thing.",
        "Used to point forward to a following qualifying clause."
      ],
      "phonetic": "/ðə/"
    },
    {
      "word": "and",
      "definitions": [
        "Used to connect words of the same part of speech.",
        "Used to introduce an additional comment or interjection."
      ],
      "phonetic": "/ænd/"
    }
  ]
}
```

**How it works:**
See the [Caching Strategy](#caching-strategy) section for detailed flow.

## How It Works

### Application Startup Flow

```
1. FastAPI app starts
   │
   ├─> Load configuration from .env
   │
   ├─> Create SQLAlchemy engine (connection pool)
   │
   ├─> Startup event triggered
   │   │
   │   ├─> Test database connection
   │   │   └─> FAIL: App crashes (fail-fast)
   │   │   └─> SUCCESS: Continue
   │   │
   │   └─> Create database tables (if not exist)
   │
   └─> Application ready
       └─> Accept HTTP requests
```

### Request Flow Example: /fetch

```
Client Request
    │
    ▼
FastAPI Router (routes/paragraphs.py)
    │
    ├─> Validate request
    │
    ├─> Get database session (dependency injection)
    │
    ▼
ParagraphService.fetch_and_store_paragraph() (async)
    │
    ├─> HTTP GET to external API (metaphorpsum.com) using httpx.AsyncClient
    │   └─> Get paragraph text
    │
    ├─> Call ParagraphRepository.create() (async)
    │   └─> INSERT INTO paragraphs
    │   └─> Return saved paragraph
    │
    ├─> Trigger Celery task (non-blocking, runs in background)
    │   └─> update_dictionary_cache.delay(paragraph_id)
    │
    └─> Return paragraph to client
```

### Background Task Flow: Dictionary Cache Update

```
/fetch endpoint triggers Celery task
    │
    ▼
Celery Worker receives task (runs async function with asyncio.run)
    │
    ├─> Get all paragraphs from database (async)
    │
    ├─> Extract words, calculate frequencies for top 10 words
    │
    ├─> For each top word:
    │   ├─> Check Redis cache for definition
    │   ├─> If miss: Fetch from dictionary API (async, parallel requests)
    │   └─> Store definition in cache (24 hour TTL)
    │
    ├─> Cache word frequencies (30 min TTL)
    │
    └─> Cache final result (1 hour TTL)
```

## Caching Strategy

The dictionary endpoint uses a multi-level caching setup to avoid hitting the dictionary API and database too often.

### Cache Levels

```
Level 3: Final Result Cache (Fastest)
    │
    │ Cache Key: "top_words_definitions:10"
    │ TTL: 1 hour
    │ Contains: Complete response with all word definitions
    │
    └─> If hit: Return immediately (no DB/API calls)
        If miss: Check Level 1

Level 1: Word Frequencies Cache
    │
    │ Cache Key: "word_frequencies:all"
    │ TTL: 30 minutes
    │ Contains: All word frequencies from database
    │
    └─> If hit: Use cached frequencies, check Level 2
        If miss: Query database, cache result, check Level 2

Level 2: Individual Word Definition Cache
    │
    │ Cache Key: "word_definition:{word}"
    │ TTL: 24 hours
    │ Contains: Definition for a single word
    │
    └─> For each word:
        If hit: Use cached definition
        If miss: Fetch from dictionary API, cache it
```

### Flow Diagram

```
GET /dictionary Request
    │
    ▼
┌─────────────────────────────────────┐
│  DictionaryService.get_top_words()  │
└──────────────┬──────────────────────┘
               │
               ▼
    ┌──────────────────────┐
    │ Redis Available?     │
    └───┬──────────────┬───┘
        │ Yes          │ No
        ▼              ▼
┌───────────────┐  ┌──────────────────────┐
│ Check Level 3 │  │ Direct DB Query     │
│ Cache         │  │ (No caching)        │
└───┬───────────┘  └──────────────────────┘
    │
    │ Hit? ──Yes──> Return immediately
    │
    │ No
    ▼
┌──────────────────────┐
│ Check Level 1 Cache  │
│ (Word Frequencies)   │
└───┬──────────────────┘
    │
    │ Hit? ──Yes──> Use cached frequencies
    │
    │ No
    ▼
┌──────────────────────┐
│ Query Database       │
│ Calculate frequencies│
└───┬──────────────────┘
    │
    │ Cache frequencies (Level 1)
    │
    ▼
┌──────────────────────┐
│ For each top word:   │
│                      │
│ Check Level 2 Cache  │
│ (Individual word)    │
└───┬──────────────────┘
    │
    │ Hit? ──Yes──> Use cached definition
    │
    │ No
    ▼
┌──────────────────────┐
│ Fetch from Dictionary│
│ API                  │
└───┬──────────────────┘
    │
    │ Cache definition (Level 2)
    │
    ▼
┌──────────────────────┐
│ Build final result   │
│ Cache Level 3        │
└───┬──────────────────┘
    │
    ▼
Return to client
```

### Benefits

1. **Fast**: If the final result is cached, it returns almost instantly
2. **Saves API calls**: Word definitions are cached for 24 hours, so we don't keep asking the dictionary API
3. **Resilient**: If Redis is down, it just falls back to querying the database directly
4. **Efficient**: Background jobs update the cache automatically when new paragraphs are added

### Cache TTLs

- **Level 3 (Final Result)**: 1 hour - Balance between freshness and performance
- **Level 1 (Frequencies)**: 30 minutes - Word frequencies change as new paragraphs are added
- **Level 2 (Definitions)**: 24 hours - Word definitions rarely change

### Background Job Integration

When a new paragraph is fetched via `/fetch`:
1. Paragraph is stored in database
2. Celery task is triggered asynchronously
3. Worker recalculates word frequencies
4. Updates all three cache levels
5. Next `/dictionary` request benefits from fresh cache

This way the cache stays fresh without slowing down the API response.

## Search Implementation & Enhancements

### Current Implementation

Right now, we're using PostgreSQL's regex operator (`~*`) with word boundaries to match exact words:

```sql
-- OR operator example
SELECT * FROM paragraphs 
WHERE content ~* '\yword1\y' 
   OR content ~* '\yword2\y';

-- AND operator example
SELECT * FROM paragraphs 
WHERE content ~* '\yword1\y' 
  AND content ~* '\yword2\y';
```

**Key Features:**
- **Exact word matching**: Uses word boundaries (`\y`) - "one" matches only "one", not "none" or "someone"
- **Case-insensitive**: `~*` operator handles case-insensitive matching
- **Input sanitization**: Automatically removes special characters (backslash, asterisk, etc.) to prevent regex errors
- **Database-level filtering**: Filters at database level, doesn't load all paragraphs (scalable)
- **SQLite fallback**: For tests, falls back to Python-side filtering

**Pros:**
- Matches exact words only (no false matches on substrings)
- Case-insensitive
- Database does the filtering (works well for medium-sized datasets)
- Input sanitization prevents regex errors
- Works fine for small to medium datasets (under 100K paragraphs)
- No extra infrastructure needed

**Cons:**
- Gets slower with really large datasets (over 1M paragraphs)
- Regex can be slower than full-text search for complex queries
- Limited features (no fuzzy matching, no ranking, etc.)
- For really large scale, Elasticsearch would be a better choice

### Enhancement: Elasticsearch Integration

If you're dealing with large datasets in production, **Elasticsearch** would be a big improvement:

#### Why Elasticsearch?

1. **Full-Text Search Engine**: Built specifically for searching text content
2. **Inverted Index**: Much faster than SQL pattern matching
3. **Advanced Features**:
   - Fuzzy matching (typo tolerance)
   - Relevance scoring and ranking
   - Phrase matching
   - Boolean queries
   - Highlighting
4. **Scalability**: Handles millions of documents efficiently
5. **Real-time Updates**: Near-instant indexing of new content

#### Proposed Architecture

```
┌─────────┐
│ Client  │
└────┬────┘
     │ POST /search
     ▼
┌─────────────────────────────────────┐
│      FastAPI /search endpoint       │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   SearchService (New)               │
│   - Check if Elasticsearch available│
│   - Fallback to PostgreSQL if not  │
└──────────────┬──────────────────────┘
               │
     ┌─────────┴─────────┐
     │                    │
     ▼                    ▼
┌─────────────┐    ┌──────────────┐
│Elasticsearch│    │  PostgreSQL   │
│  (Primary)  │    │  (Fallback)  │
└─────────────┘    └──────────────┘
```

#### Implementation Approach

1. **Dual Strategy**: Try Elasticsearch first, fallback to PostgreSQL
2. **Indexing**: When paragraphs are stored, also index them in Elasticsearch
3. **Query Translation**: Convert search request to Elasticsearch query DSL
4. **Graceful Degradation**: If Elasticsearch is down, use PostgreSQL

#### Example Elasticsearch Query

```json
{
  "query": {
    "bool": {
      "should": [
        { "match": { "content": "word1" } },
        { "match": { "content": "word2" } }
      ],
      "minimum_should_match": 1
    }
  },
  "highlight": {
    "fields": {
      "content": {}
    }
  }
}
```

#### Benefits Over Current Implementation

- **10-100x faster** for large datasets
- **Better relevance** with scoring algorithms
- **Typo tolerance** with fuzzy matching
- **Highlighting** of matched terms
- **Faceted search** capabilities (filter by date, etc.)

#### When to Use Elasticsearch

- **Current**: Good for < 100K paragraphs, simple use cases
- **Elasticsearch**: Recommended for > 100K paragraphs, production scale, advanced search needs

The current PostgreSQL setup works fine for this assignment, but if you need to scale to production with lots of data, Elasticsearch would be the way to go.

## Running Tests

### Run All Tests

```bash
# Using Docker
docker compose exec api pytest

# Or locally (with virtual environment activated)
pytest
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html
```

Coverage report will be generated in `htmlcov/index.html`.

### Run Specific Test Suites

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Specific test file
pytest tests/unit/test_paragraph_repository.py
```

### Test Structure

- **Unit Tests**: Test individual pieces of code in isolation, with dependencies mocked
- **Integration Tests**: Test the API endpoints end-to-end with a test database

## Technology Stack

- **FastAPI**: Modern, fast web framework with automatic API documentation
- **Uvicorn**: ASGI server to run the FastAPI application
- **PostgreSQL**: Robust relational database with excellent text search capabilities
- **SQLAlchemy**: ORM for database operations (using async version with asyncpg)
- **asyncpg**: PostgreSQL async driver for high-performance database operations
- **Redis**: In-memory cache and Celery message broker
- **Celery**: Distributed task queue for background jobs
- **Pydantic**: Type-safe data validation and settings management
- **httpx**: Modern async HTTP client for external API calls
- **pytest**: Testing framework with async support (pytest-asyncio)

---

**Note**: The readme table of content is asked by ai assitant to write as it makes it beautiful.


THANKS:
SATYAVEER NAYAK
