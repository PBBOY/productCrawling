import logging
from typing import List
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT
from fastapi import APIRouter, Depends, HTTPException
from common.database.dbmanager import db, DatabaseManager
from common.consts import PRODUCT
from models.product import ProductBase
from crud.category_crud import get_products
from crawl.categorycrawl import CategoryCrawl


router = APIRouter(
    prefix="/products",
    tags=["products"],
    responses={404: {"description": "Not found"}}
)


@router.get(
    "/",
    response_model=List[ProductBase]
)
async def get_category_items():
    categories = await get_products(db)
    return categories


@router.get(
    "/{nid}",
    response_model=ProductBase
)
async def get_category_by_nid(nid: str):
    _query = db.find_query('nid', nid)
    row = db.find_one(PRODUCT, _query)

    if row:
        return ProductBase(**row)

