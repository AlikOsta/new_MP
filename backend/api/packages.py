from fastapi import APIRouter, Depends, HTTPException
from typing import List
from core.database import get_database
from models.package import Package, PackageCreate, Payment, PaymentCreate

router = APIRouter(prefix="/api/packages", tags=["packages"])

@router.get("/", response_model=List[Package])
async def get_packages(db=Depends(get_database)):
    cursor = db.packages.find({"is_active": True})
    return [Package(**doc) async for doc in cursor]

@router.post("/", response_model=Package)
async def create_package(package: PackageCreate, db=Depends(get_database)):
    package_dict = package.model_dump()
    result = await db.packages.insert_one(package_dict)
    created_package = await db.packages.find_one({"_id": result.inserted_id})
    return Package(**created_package)

@router.post("/payments", response_model=Payment)
async def create_payment(payment: PaymentCreate, user_id: str, db=Depends(get_database)):
    # Get package details
    package = await db.packages.find_one({"_id": payment.package_id})
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    
    payment_dict = payment.model_dump()
    payment_dict["user_id"] = user_id
    payment_dict["amount"] = package["price"]
    payment_dict["currency_id"] = package["currency_id"]
    
    result = await db.payments.insert_one(payment_dict)
    created_payment = await db.payments.find_one({"_id": result.inserted_id})
    return Payment(**created_payment)

@router.get("/payments/{payment_id}", response_model=Payment)
async def get_payment(payment_id: str, db=Depends(get_database)):
    payment = await db.payments.find_one({"_id": payment_id})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return Payment(**payment)

@router.put("/payments/{payment_id}/complete")
async def complete_payment(
    payment_id: str,
    telegram_charge_id: str,
    provider_charge_id: str,
    db=Depends(get_database)
):
    result = await db.payments.update_one(
        {"_id": payment_id},
        {"$set": {
            "status": "completed",
            "telegram_payment_charge_id": telegram_charge_id,
            "provider_payment_charge_id": provider_charge_id
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Update post status to active
    payment = await db.payments.find_one({"_id": payment_id})
    await db.posts.update_one(
        {"_id": payment["post_id"]},
        {"$set": {"status": 3, "is_premium": True}}  # Active status
    )
    
    return {"message": "Payment completed successfully"}