import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from core.database import get_database
from models.category import SuperRubric, SubRubric, City, Currency
from models.category import SuperRubricCreate, SubRubricCreate, CityCreate, CurrencyCreate

router = APIRouter(prefix="/api/categories", tags=["categories"])

# Super Rubrics
@router.get("/super-rubrics", response_model=List[SuperRubric])
async def get_super_rubrics(db=Depends(get_database)):
    cursor = db.super_rubrics.find({"is_active": True})
    return [SuperRubric(**doc) async for doc in cursor]

@router.post("/super-rubrics", response_model=SuperRubric)
async def create_super_rubric(rubric: SuperRubricCreate, db=Depends(get_database)):
    rubric_dict = rubric.model_dump()
    result = await db.super_rubrics.insert_one(rubric_dict)
    created_rubric = await db.super_rubrics.find_one({"_id": result.inserted_id})
    return SuperRubric(**created_rubric)

# Sub Rubrics
@router.get("/sub-rubrics", response_model=List[SubRubric])
async def get_sub_rubrics(super_rubric_id: str = None, db=Depends(get_database)):
    query = {"is_active": True}
    if super_rubric_id:
        query["super_rubric_id"] = super_rubric_id
    
    cursor = db.sub_rubrics.find(query)
    return [SubRubric(**doc) async for doc in cursor]

@router.post("/sub-rubrics", response_model=SubRubric)
async def create_sub_rubric(rubric: SubRubricCreate, db=Depends(get_database)):
    rubric_dict = rubric.model_dump()
    result = await db.sub_rubrics.insert_one(rubric_dict)
    created_rubric = await db.sub_rubrics.find_one({"_id": result.inserted_id})
    return SubRubric(**created_rubric)

# Cities
@router.get("/cities", response_model=List[City])
async def get_cities(db=Depends(get_database)):
    cursor = db.cities.find({"is_active": True})
    return [City(**doc) async for doc in cursor]

@router.post("/cities", response_model=City)
async def create_city(city: CityCreate, db=Depends(get_database)):
    city_dict = city.model_dump()
    result = await db.cities.insert_one(city_dict)
    created_city = await db.cities.find_one({"_id": result.inserted_id})
    return City(**created_city)

# Currencies
@router.get("/currencies", response_model=List[Currency])
async def get_currencies(db=Depends(get_database)):
    cursor = db.currencies.find({"is_active": True})
    return [Currency(**doc) async for doc in cursor]

@router.post("/currencies", response_model=Currency)
async def create_currency(currency: CurrencyCreate, db=Depends(get_database)):
    currency_dict = currency.model_dump()
    result = await db.currencies.insert_one(currency_dict)
    created_currency = await db.currencies.find_one({"_id": result.inserted_id})
    return Currency(**created_currency)