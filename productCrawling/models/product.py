from typing import Optional

from bson import ObjectId
from datetime import datetime
from fastapi.openapi.models import Schema

from models.rwmodel import RWModel, BaseModel
from pydantic import Field


class PyObjectId(ObjectId):

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError('Invalid objectid')
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type='string')


class ProductBase(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id")
    name: str = Field(...)
    nid: str = None
    paths: str = None
    n_cid: str = None
    cid: str = None
    cname: str = None
    imageUrl: str = None
    title: str = None
    price: str = None
    option: dict = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "name": "Jane Doe",
                "paths": "jdoe@example.com",
            }
        }
