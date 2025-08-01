# main.py
from fastapi import FastAPI
from fastmcp import FastMCP
import asyncio
from contextlib import asynccontextmanager

# MCP Tools
from tools.file_operations import FileOperationsTool
from tools.database_operations import DatabaseTool
from tools.api_client import APIClientTool
from tools.text_processing import TextProcessingTool

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown

app = FastAPI(
    title="MCP Tools API",
    description="FastAPI application exposing MCP tools as REST endpoints",
    version="1.0.0",
    lifespan=lifespan
)

# Initialize FastMCP
fastmcp = FastMCP()

# Register MCP tools
fastmcp.register_tool(FileOperationsTool())
fastmcp.register_tool(DatabaseTool())
fastmcp.register_tool(APIClientTool())
fastmcp.register_tool(TextProcessingTool())

# Mount MCP tools as FastAPI routes
app.mount("/mcp", fastmcp.app)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "MCP FastAPI server is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


# tools/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List
from pydantic import BaseModel

class MCPTool(ABC):
    """Base class for MCP tools"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description"""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool"""
        pass
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema for OpenAPI"""
        pass


# tools/file_operations.py
from .base import MCPTool
from pydantic import BaseModel
from typing import Dict, Any, Optional
import aiofiles
import os

class FileReadRequest(BaseModel):
    file_path: str
    encoding: str = "utf-8"

class FileWriteRequest(BaseModel):
    file_path: str
    content: str
    encoding: str = "utf-8"

class FileListRequest(BaseModel):
    directory_path: str
    include_hidden: bool = False

class FileOperationsTool(MCPTool):
    @property
    def name(self) -> str:
        return "file_operations"
    
    @property
    def description(self) -> str:
        return "File system operations including read, write, and list files"
    
    async def read_file(self, request: FileReadRequest) -> Dict[str, Any]:
        """Read file content"""
        try:
            async with aiofiles.open(request.file_path, 'r', encoding=request.encoding) as f:
                content = await f.read()
            return {"success": True, "content": content}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def write_file(self, request: FileWriteRequest) -> Dict[str, Any]:
        """Write content to file"""
        try:
            os.makedirs(os.path.dirname(request.file_path), exist_ok=True)
            async with aiofiles.open(request.file_path, 'w', encoding=request.encoding) as f:
                await f.write(request.content)
            return {"success": True, "message": f"File written to {request.file_path}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def list_files(self, request: FileListRequest) -> Dict[str, Any]:
        """List files in directory"""
        try:
            files = []
            for item in os.listdir(request.directory_path):
                if not request.include_hidden and item.startswith('.'):
                    continue
                item_path = os.path.join(request.directory_path, item)
                files.append({
                    "name": item,
                    "is_directory": os.path.isdir(item_path),
                    "size": os.path.getsize(item_path) if os.path.isfile(item_path) else None
                })
            return {"success": True, "files": files}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def execute(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute file operation"""
        if operation == "read":
            return await self.read_file(FileReadRequest(**kwargs))
        elif operation == "write":
            return await self.write_file(FileWriteRequest(**kwargs))
        elif operation == "list":
            return await self.list_files(FileListRequest(**kwargs))
        else:
            return {"success": False, "error": f"Unknown operation: {operation}"}
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "read": FileReadRequest.model_json_schema(),
            "write": FileWriteRequest.model_json_schema(),
            "list": FileListRequest.model_json_schema()
        }


# tools/database_operations.py
from .base import MCPTool
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import asyncpg
import json

class DatabaseConfig(BaseModel):
    host: str = "localhost"
    port: int = 5432
    database: str
    username: str
    password: str

class QueryRequest(BaseModel):
    query: str
    params: Optional[List[Any]] = None
    config: DatabaseConfig

class DatabaseTool(MCPTool):
    @property
    def name(self) -> str:
        return "database_operations"
    
    @property
    def description(self) -> str:
        return "PostgreSQL database operations including queries and transactions"
    
    async def execute_query(self, request: QueryRequest) -> Dict[str, Any]:
        """Execute database query"""
        try:
            conn = await asyncpg.connect(
                host=request.config.host,
                port=request.config.port,
                database=request.config.database,
                user=request.config.username,
                password=request.config.password
            )
            
            if request.params:
                result = await conn.fetch(request.query, *request.params)
            else:
                result = await conn.fetch(request.query)
            
            await conn.close()
            
            # Convert to JSON serializable format
            rows = [dict(row) for row in result]
            return {"success": True, "rows": rows, "count": len(rows)}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute database operation"""
        return await self.execute_query(QueryRequest(**kwargs))
    
    def get_schema(self) -> Dict[str, Any]:
        return QueryRequest.model_json_schema()


# tools/api_client.py
from .base import MCPTool
from pydantic import BaseModel
from typing import Dict, Any, Optional
import httpx

class APIRequest(BaseModel):
    url: str
    method: str = "GET"
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, str]] = None
    json_data: Optional[Dict[str, Any]] = None
    timeout: int = 30

class APIClientTool(MCPTool):
    @property
    def name(self) -> str:
        return "api_client"
    
    @property
    def description(self) -> str:
        return "HTTP API client for making requests to external services"
    
    async def make_request(self, request: APIRequest) -> Dict[str, Any]:
        """Make HTTP request"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=request.method,
                    url=request.url,
                    headers=request.headers,
                    params=request.params,
                    json=request.json_data,
                    timeout=request.timeout
                )
                
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "content": response.text,
                    "json": response.json() if response.headers.get("content-type", "").startswith("application/json") else None
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute API request"""
        return await self.make_request(APIRequest(**kwargs))
    
    def get_schema(self) -> Dict[str, Any]:
        return APIRequest.model_json_schema()


# tools/text_processing.py
from .base import MCPTool
from pydantic import BaseModel
from typing import Dict, Any, List
import re

class TextAnalysisRequest(BaseModel):
    text: str
    operations: List[str] = ["word_count", "char_count", "line_count"]

class TextTransformRequest(BaseModel):
    text: str
    operation: str  # "uppercase", "lowercase", "title", "reverse"

class TextSearchRequest(BaseModel):
    text: str
    pattern: str
    case_sensitive: bool = True

class TextProcessingTool(MCPTool):
    @property
    def name(self) -> str:
        return "text_processing"
    
    @property
    def description(self) -> str:
        return "Text processing operations including analysis, transformation, and search"
    
    async def analyze_text(self, request: TextAnalysisRequest) -> Dict[str, Any]:
        """Analyze text statistics"""
        try:
            results = {}
            
            if "word_count" in request.operations:
                results["word_count"] = len(request.text.split())
            
            if "char_count" in request.operations:
                results["char_count"] = len(request.text)
                results["char_count_no_spaces"] = len(request.text.replace(" ", ""))
            
            if "line_count" in request.operations:
                results["line_count"] = len(request.text.splitlines())
            
            return {"success": True, "analysis": results}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def transform_text(self, request: TextTransformRequest) -> Dict[str, Any]:
        """Transform text"""
        try:
            if request.operation == "uppercase":
                result = request.text.upper()
            elif request.operation == "lowercase":
                result = request.text.lower()
            elif request.operation == "title":
                result = request.text.title()
            elif request.operation == "reverse":
                result = request.text[::-1]
            else:
                return {"success": False, "error": f"Unknown operation: {request.operation}"}
            
            return {"success": True, "transformed_text": result}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def search_text(self, request: TextSearchRequest) -> Dict[str, Any]:
        """Search text for patterns"""
        try:
            flags = 0 if request.case_sensitive else re.IGNORECASE
            matches = re.finditer(request.pattern, request.text, flags)
            
            results = []
            for match in matches:
                results.append({
                    "match": match.group(),
                    "start": match.start(),
                    "end": match.end()
                })
            
            return {"success": True, "matches": results, "count": len(results)}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def execute(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute text processing operation"""
        if operation == "analyze":
            return await self.analyze_text(TextAnalysisRequest(**kwargs))
        elif operation == "transform":
            return await self.transform_text(TextTransformRequest(**kwargs))
        elif operation == "search":
            return await self.search_text(TextSearchRequest(**kwargs))
        else:
            return {"success": False, "error": f"Unknown operation: {operation}"}
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "analyze": TextAnalysisRequest.model_json_schema(),
            "transform": TextTransformRequest.model_json_schema(),
            "search": TextSearchRequest.model_json_schema()
        }


# requirements.txt
fastapi==0.104.1
fastmcp==0.1.0
uvicorn[standard]==0.24.0
pydantic==2.5.0
aiofiles==23.2.1
asyncpg==0.29.0
httpx==0.25.2
python-multipart==0.0.6


# config.py
from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    app_name: str = "MCP FastAPI Server"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database settings
    db_host: Optional[str] = None
    db_port: int = 5432
    db_name: Optional[str] = None
    db_user: Optional[str] = None
    db_password: Optional[str] = None
    
    class Config:
        env_file = ".env"

settings = Settings()


# .env (example)
APP_NAME=MCP FastAPI Server
DEBUG=true
HOST=0.0.0.0
PORT=8000

DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database
DB_USER=your_username
DB_PASSWORD=your_password


# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=true
    volumes:
      - .:/app
    depends_on:
      - postgres
    
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: mcpdb
      POSTGRES_USER: mcpuser
      POSTGRES_PASSWORD: mcppass
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:


# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


# README.md
# FastAPI MCP Application

A FastAPI application that implements Model Context Protocol (MCP) tools and exposes them as REST API endpoints with Swagger documentation.

## Features

- **File Operations**: Read, write, and list files
- **Database Operations**: PostgreSQL query execution
- **API Client**: HTTP requests to external services  
- **Text Processing**: Text analysis, transformation, and search
- **Swagger Documentation**: Auto-generated API docs at `/docs`
- **Health Check**: Status endpoint at `/health`

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Development
uvicorn main:app --reload

# Production
python main.py
```

## Docker

```bash
docker-compose up -d
```

## API Endpoints

- `GET /health` - Health check
- `GET /docs` - Swagger documentation  
- `POST /mcp/file_operations` - File operations
- `POST /mcp/database_operations` - Database queries
- `POST /mcp/api_client` - HTTP requests
- `POST /mcp/text_processing` - Text processing

## Configuration

Set environment variables in `.env` file or export them directly.
