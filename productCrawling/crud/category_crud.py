from typing import List, Optional
from common.database.dbmanager import DatabaseManager
from models.product import ProductBase
from common.consts import PRODUCT


async def get_products(db: DatabaseManager) -> List[ProductBase]:
    categories: List[ProductBase] = []
    rows = db.find(PRODUCT, {})

    if rows:
        for row in rows:
            categories.append(ProductBase(**row))

    return categories
