from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import select

from .database import AS_OF, Base, SessionLocal, engine
from .models import Customer
from .routes import analytics, customers, orders, shipments, tickets
from .seed import seed


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if db.scalar(select(Customer).limit(1)) is None:
            seed(db)
    yield


app = FastAPI(
    title="Nova Orders API",
    version="1.0.0",
    description="NovaCommerce orders, customers, shipments and support tickets.",
    lifespan=lifespan,
    # operationId = function name, so generated MCP tools get readable names.
    generate_unique_id_function=lambda route: route.name,
)


def error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


@app.exception_handler(HTTPException)
async def http_error(_: Request, exc: HTTPException):
    return error(exc.status_code, "not_found" if exc.status_code == 404 else "http_error", str(exc.detail))


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError):
    return error(422, "validation_error", "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors()))


@app.get("/health", tags=["health"], summary="Health check")
def health():
    return {"status": "ok", "service": "nova-orders", "as_of": AS_OF}


for r in (orders, customers, shipments, tickets, analytics):
    app.include_router(r.router)
