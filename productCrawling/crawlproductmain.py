"""
use module
import os
"""

import asyncio
import uvicorn
import logging
from fastapi import FastAPI, Query
from uuid import uuid4
from typing import Optional, List

from crawl.productcrawl import ProductCrawl, product_crawl
from routers.product import router

app = FastAPI()
app.include_router(router)

context = {'jobs': {}}


@app.get("/")
async def root():
    return {"message": "Hello World111"}


# @app.get(
#     "/start"
# )
# async def start():
#     identifier = str(uuid4())
#     logging.info("start")
#     context['jobs'][identifier] = {}
#
#     asyncio.run_coroutine_threadsafe(product_crawl.parse(identifier, context), loop=asyncio.get_running_loop())
#
#     return {"identifier": identifier}


@app.get(
    "/start/"
)
async def start(q: Optional[List[str]] = Query(None)):
    identifier = str(uuid4())
    logging.info("start")
    context['jobs'][identifier] = {}

    asyncio.run_coroutine_threadsafe(product_crawl.parse(identifier, context, q), loop=asyncio.get_running_loop())

    return {"identifier": identifier}


@app.get(
    "/status/{identifier}"
)
async def get_crawl_status(identifier: str):
    return {"status": context['jobs'].get(identifier, 'job with that identifier is undefined')}


if __name__ == '__main__':
    uvicorn.run("crawlproductmain:app", host="0.0.0.0", port=8000, reload=True)
