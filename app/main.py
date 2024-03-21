import json
import os

import uvicorn
from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware
import structlog

from app.logging import config_structlog


from app.routers import (
    auth,
    performance,
    availability,
    brand_products,
    retailer_offers,
    overview,
    content,
    matching,
    groups,
    stock,
    price,
)

config_structlog()
logger = structlog.get_logger()

app = FastAPI(
    title="Panprices - Digital Shelf Analytics Solution API",
    version="0.1 Wow much Alpha Very incipient",
    description="""
        This API is used to deliver data to the dashboard used by producers to track their products in the market. It 
        returns valuable overview insights as well as the ability to analyze particular products and observe how they
        are doing. 
    """,
)

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# @app.middleware("http")
# async def canonical_line_logger(request: Request, call_next):
#     # !Important: always catch exceptions since a request should never fail
#     # because of logging.

#     try:
#         request_body_json = await request.json() if request.body else None
#     except json.JSONDecodeError:
#         # No need to care if the request body format is incorrect:
#         request_body_json = None
#     except Exception as e:
#         logger.error("Logging error", error=e)

#     try:
#         logger.info(
#             "Request received",
#             http_method=request.method,
#             http_path=request.url.path,
#             http_request_headers=request.headers,
#             http_request_body=request_body_json,
#         )
#     except Exception as e:
#         logger.error(f"Canonical line logging failed!", error=e)

#     response = await call_next(request)
#     return response


app.include_router(auth.router)
app.include_router(performance.router)
app.include_router(availability.router)
app.include_router(brand_products.router)
app.include_router(retailer_offers.router)
app.include_router(overview.router)
app.include_router(content.router)
app.include_router(matching.router)
app.include_router(groups.router)
app.include_router(stock.router)
app.include_router(price.router)


if __name__ == "__main__":
    port = os.getenv("PORT")
    if not port:
        port = 8080
    uvicorn.run(app, host="0.0.0.0", port=8080)
