import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    DataBaseOperationError,
    DomainException,
    ResourceNotFoundError
)

logger = logging.getLogger(__name__)

def register_exception_handler(app: FastAPI) -> None:

    # 1. Validation Errors (Errores de entrada Pydantic / Query / Path)
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = []

        for err in exc.errors():
            loc = " -> ".join([str(x) for x in err.get("loc", [])])
            msg = err.get("msg", "Invalid data")
            errors.append({"field": loc, "message": msg})

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "error" : "Validation Error",
                "details": errors
            }
        )

    # 2. Authentication Errors
    @app.exception_handler(AuthenticationError)
    async def auth_exception_handler(request: Request, exc: AuthenticationError):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "Faild Authentication", "message": exc.message},
            headers={"WWW-Authenticate": "Bearer"}
        )

    # 3. Authorization Errors
    @app.exception_handler(AuthorizationError)
    async def forbidden_exception_handler(request: Request, exc: AuthorizationError):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"error": "Denieded Access", "message": exc.message}
        )

    # 4. Resource Not Found
    @app.exception_handler(AuthorizationError)
    async def not_found_exption_handler(request: Request, exc: ResourceNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "Not found resource", "message": exc.message}
        )

    # 5. Database Errors (SQLAlchemyError)
    @app.exception_handler(SQLAlchemyError)
    @app.exception_handler(DataBaseOperationError)
    async def database_exception_handler(request: Request, exc: Exception):
        logger.error(f"Database error in {request.method} {request.url.path}: {str(exc)}", exc_info=True)

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Error in database",
                "message": "There was a problem processing the request in storage."
            }
        )

    # 6. Unexpected / Unhandled Errors (500 Internal Server Error)
    @app.exception_handler(Exception)
    async def unexpected_exception_handler(request: Request, exc: Exception):
        logger.critical(f"Unhandled Exception in {request.method} {request.url.path}: {str(exc)}", exc_info=True)

        is_production = getattr(settings, "ENVIROMENT", "production").lower() == "production"
        message = "It must include at least one lowercase letter"

        if not is_production:
            message = f"Debug Info: {str(exc)}"

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "message": message
            }
        )
