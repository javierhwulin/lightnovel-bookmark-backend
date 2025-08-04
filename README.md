# Light Novel Bookmarks Backend API

A personal portal to organize, search, and manage your light novels. Track where you left off, rate and comment on novels, and discover new tales through automated web scraping from NovelUpdates.

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/your-repo/lightnovel-bookmarks-backend)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 🚀 Features

### Novel Management
- **Create, read, update, and delete** light novels with comprehensive metadata
- **Chapter management** with support for decimal numbering (1, 1.5, 2.1)
- **Genre tagging** and status tracking (ongoing, completed, hiatus, dropped)
- **Cover image and source URL** support

### Web Scraping Integration
- **NovelUpdates.com integration** for automatic novel import
- **Fast preview mode** to verify novel information before importing
- **Background processing** for large novels with hundreds of chapters
- **Cloudflare bypass** using cloudscraper for reliable data extraction

### API Features
- **RESTful API design** with comprehensive OpenAPI documentation
- **Type-safe validation** using Pydantic models with constraints
- **Structured error handling** with detailed error codes and messages
- **CORS support** for frontend integration
- **Environment-based configuration** for development and production

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [API Documentation](#-api-documentation)
- [Configuration](#-configuration)
- [Development](#-development)
- [API Endpoints](#-api-endpoints)
- [Data Models](#-data-models)
- [Error Handling](#-error-handling)
- [Contributing](#-contributing)

## 🏃 Quick Start

### Prerequisites
- Python 3.12 or higher
- `uv` package manager (recommended) or `pip`

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-repo/lightnovel-bookmarks-backend.git
   cd lightnovel-bookmarks-backend
   ```

2. **Install dependencies**
   ```bash
   # Using uv (recommended)
   uv sync

   # Or using pip
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your preferred settings
   ```

4. **Run the application**
   ```bash
   # Using uv
   uv run uvicorn app.main:app --reload

   # Or using Python directly
   python -m uvicorn app.main:app --reload
   ```

5. **Access the API**
   - API: http://localhost:8000
   - Interactive Docs: http://localhost:8000/docs
   - Alternative Docs: http://localhost:8000/redoc

## 📚 API Documentation

### Interactive Documentation
The API provides comprehensive interactive documentation:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI Spec**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

### Quick API Overview
```bash
# Get API information
curl http://localhost:8000/api

# Health check
curl http://localhost:8000/health

# List all novels
curl http://localhost:8000/api/novels

# Preview a novel from NovelUpdates
curl -X POST http://localhost:8000/api/scraper/preview \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.novelupdates.com/series/overlord-ln/"}'
```

## ⚙️ Configuration

### Environment Variables
Copy `.env.example` to `.env` and configure:

```env
# Application
APP_TITLE="Light Novel Bookmarks API"
APP_VERSION="1.0.0"
APP_DEBUG=false
APP_ENVIRONMENT="development"

# Database
DATABASE_URL="sqlite:///light_novels.db"
DATABASE_ECHO=false

# CORS
CORS_ORIGINS="http://localhost:3000,http://localhost:8080"

# Scraper
SCRAPER_DELAY=6
SCRAPER_TIMEOUT=30
```

### Configuration Sections
- **App Settings**: Title, version, debug mode, environment
- **Database**: Connection URL, logging, pool settings
- **CORS**: Origins, credentials, methods, headers
- **Scraper**: Request delays, timeouts, user agent

## 🛠️ Development

### Project Structure
```
app/
├── api/           # API route definitions
├── core/          # Core utilities, config, exceptions
├── db/            # Database configuration
├── models/        # SQLAlchemy models
├── schemas/       # Pydantic schemas
└── services/      # Business logic layer
```

### Architecture Principles
- **Domain-Driven Design (DDD)** with clear separation of concerns
- **Hexagonal Architecture** with ports and adapters pattern
- **Functional programming** preferred over class hierarchies
- **RORO pattern** (Receive Object, Return Object) for services

### Running Tests
```bash
# Using uv
uv run pytest

# Or using Python
python -m pytest
```

### Code Quality
```bash
# Format code
uv run ruff format

# Lint code
uv run ruff check

# Type checking
uv run mypy app/
```

## 🌐 API Endpoints

### Novels API (`/api/novels`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/novels` | List all novels |
| `POST` | `/novels` | Create a new novel |
| `GET` | `/novels/{id}` | Get novel by ID |
| `PATCH` | `/novels/{id}` | Update novel |
| `DELETE` | `/novels/{id}` | Delete novel |

### Chapters API (`/api/novels/{novel_id}/chapters`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/chapters` | List novel chapters |
| `POST` | `/chapters` | Create new chapter |
| `GET` | `/chapters/{id}` | Get chapter by ID |
| `PATCH` | `/chapters/{id}` | Update chapter |
| `DELETE` | `/chapters/{id}` | Delete chapter |

### Scraper API (`/api/scraper`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/preview` | Preview novel without importing |
| `POST` | `/import` | Import novel and chapters |
| `POST` | `/update/{id}` | Update novel with new chapters |
| `POST` | `/import-background` | Background import for large novels |

### System API
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | API information |
| `GET` | `/health` | Health check |
| `GET` | `/api` | Detailed API capabilities |

## 📊 Data Models

### Novel Model
```json
{
  "id": 1,
  "title": "That Time I Got Reincarnated as a Slime",
  "author": "Fuse & 伏瀬",
  "description": "Novel description...",
  "status": "ongoing",
  "genres": ["Fantasy", "Adventure", "Comedy"],
  "cover_url": "https://example.com/cover.jpg",
  "source_url": "https://www.novelupdates.com/series/...",
  "total_chapters": 355,
  "total_volumes": 0,
  "content_type": "chapters",
  "raw_status": "355 Chapters (Completed)"
}
```

### Chapter Model
```json
{
  "id": 1,
  "novel_id": 1,
  "number": 1.5,
  "title": "Chapter 1.5: Side Story",
  "source_url": "https://translator.com/chapter-1-5"
}
```

## 🚨 Error Handling

### Error Response Format
```json
{
  "error": {
    "code": "NOVEL_NOT_FOUND",
    "message": "Novel with ID 123 not found",
    "details": {
      "novel_id": 123
    }

  }
}
```

### Common Error Codes
- `NOVEL_NOT_FOUND` (404): Novel doesn't exist
- `CHAPTER_NOT_FOUND` (404): Chapter doesn't exist
- `DUPLICATE_NOVEL` (409): Novel already exists
- `DUPLICATE_CHAPTER` (409): Chapter number already exists
- `SCRAPING_FAILED` (400): Web scraping error
- `INVALID_URL` (400): Invalid NovelUpdates URL
- `VALIDATION_ERROR` (422): Request validation failed

## 🔧 Production Deployment

### Docker
```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN pip install uv && uv sync --frozen
EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Configuration
```env
APP_ENVIRONMENT="production"
APP_DEBUG=false
DATABASE_URL="postgresql://user:pass@db:5432/lightnovel_bookmarks"
CORS_ORIGINS="https://yourdomain.com"
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow the existing code style and architecture patterns
- Add tests for new features
- Update documentation for API changes
- Use type hints throughout
- Follow the DDD and hexagonal architecture principles

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the excellent web framework
- [NovelUpdates](https://www.novelupdates.com/) for providing novel information
- [SQLAlchemy](https://www.sqlalchemy.org/) for robust database operations
- [Pydantic](https://pydantic.dev/) for data validation
- [Cloudscraper](https://github.com/VeNoMouS/cloudscraper) for Cloudflare bypass

---

**Built with ❤️ for light novel enthusiasts**
