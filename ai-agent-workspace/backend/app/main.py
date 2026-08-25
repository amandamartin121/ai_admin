"""
FastAPI application factory and main entry point.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import structlog

from app.core.config import settings
from app.database.session import init_db
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.admin import router as admin_router
from app.api.conversations import router as conversations_router
from app.api.chat import router as chat_router
from app.api.agents import router as agents_router
from app.api.files import router as files_router


# Configure structured logging
import logging

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(settings.log_level.upper())),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=False,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown."""
    # Startup
    logger.info("Starting up AI Agent Workspace backend...")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Agent Workspace backend...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="AI Agent Workspace",
        description="A secure multi-user AI chatbot/agent platform",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register routers
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
    app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])
    app.include_router(admin_router, prefix="/api/v1/admin", tags=["Admin"])
    app.include_router(conversations_router, prefix="/api/v1/conversations", tags=["Conversations"])
    app.include_router(chat_router, prefix="/api/v1/chat", tags=["Chat"])
    app.include_router(agents_router, prefix="/api/v1/agents", tags=["Agents"])
    app.include_router(files_router, prefix="/api/v1/files", tags=["Files"])
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(
            f"Unhandled exception: {exc}",
            extra={"path": str(request.url.path), "method": request.method},
        )
        
        if settings.is_production:
            # Don't expose internal errors in production
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "An internal error occurred",
                        "request_id": getattr(request.state, "request_id", "unknown"),
                    }
                },
            )
        else:
            # Show detailed error in development
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": str(exc),
                        "request_id": getattr(request.state, "request_id", "unknown"),
                    }
                },
            )
    
    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "healthy", "environment": settings.environment}
    
    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root():
        return {
            "name": "AI Agent Workspace API",
            "version": "1.0.0",
            "docs": "/docs",
        }
    
    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
    )
