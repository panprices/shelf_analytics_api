import os

import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware


from app.routers import (
    auth,
    performance,
    availability,
    data,
    overview,
    content,
    matching,
    groups,
    stock,
    price,
)

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

app.include_router(auth.router)
app.include_router(performance.router)
app.include_router(availability.router)
app.include_router(data.router)
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
