"""
Packages router - handles package operations
"""
from fastapi import APIRouter, HTTPException, Request
from database import db
from datetime import datetime, timedelta
import uuid

router = APIRouter(prefix="/api/packages", tags=["packages"])

@router.get("/")
async def get_packages():
    """Get all active packages"""
    results = await db.fetchall("SELECT * FROM packages WHERE is_active = 1 ORDER BY sort_order ASC")
    
    # Parse features from pipe-separated strings
    for package in results:
        if package.get("features_ru"):
            package["features_ru"] = package["features_ru"].split("|")
        if package.get("features_ua"):
            package["features_ua"] = package["features_ua"].split("|")
    
    return results

@router.get("/{package_id}")
async def get_package(package_id: str):
    """Get a specific package by ID"""
    package = await db.fetchone("SELECT * FROM packages WHERE id = ? AND is_active = 1", [package_id])
    
    if not package:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Package not found")
    
    # Parse features
    if package.get("features_ru"):
        package["features_ru"] = package["features_ru"].split("|")
    if package.get("features_ua"):
        package["features_ua"] = package["features_ua"].split("|")
    
    return package

@router.post("/purchase")
async def purchase_package(request: Request):
    """Purchase a package (initiate payment)"""
    data = await request.json()
    user_id = data.get("user_id")
    package_id = data.get("package_id")
    
    if not user_id or not package_id:
        raise HTTPException(status_code=400, detail="user_id and package_id are required")
    
    # Get package info
    package = await db.fetchone("SELECT * FROM packages WHERE id = ? AND is_active = 1", [package_id])
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    
    # Create user_package record with pending status
    user_package_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()
    expires_at = (datetime.now() + timedelta(days=package["duration_days"])).isoformat()
    
    await db.execute("""
        INSERT INTO user_packages 
        (id, user_id, package_id, purchased_at, expires_at, is_active, payment_status, amount, currency_code, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        user_package_id, user_id, package_id, created_at, expires_at, 
        0, "pending", package["price"], "RUB", created_at
    ])
    
    return {
        "user_package_id": user_package_id,
        "package_id": package_id,
        "amount": package["price"],
        "currency": "RUB",
        "status": "pending"
    }

@router.post("/confirm-payment")
async def confirm_payment(request: Request):
    """Confirm payment from Telegram Bot"""
    data = await request.json()
    
    user_id = data.get("user_id")
    package_id = data.get("package_id")
    telegram_charge_id = data.get("telegram_charge_id")
    provider_charge_id = data.get("provider_charge_id")
    amount = data.get("amount")
    currency = data.get("currency")
    payload = data.get("payload")
    
    if not all([user_id, package_id, telegram_charge_id]):
        raise HTTPException(status_code=400, detail="Missing required payment data")
    
    try:
        # Find pending payment
        user_package = await db.fetchone("""
            SELECT * FROM user_packages 
            WHERE user_id = ? AND package_id = ? AND payment_status = 'pending'
            ORDER BY created_at DESC
            LIMIT 1
        """, [user_id, package_id])
        
        if not user_package:
            # Create new user_package if not exists
            package = await db.fetchone("SELECT * FROM packages WHERE id = ?", [package_id])
            if not package:
                raise HTTPException(status_code=404, detail="Package not found")
            
            user_package_id = str(uuid.uuid4())
            created_at = datetime.now().isoformat()
            expires_at = (datetime.now() + timedelta(days=package["duration_days"])).isoformat()
            
            await db.execute("""
                INSERT INTO user_packages 
                (id, user_id, package_id, purchased_at, expires_at, is_active, payment_status, 
                telegram_charge_id, provider_charge_id, amount, currency_code, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                user_package_id, user_id, package_id, created_at, expires_at, 
                1, "completed", telegram_charge_id, provider_charge_id, amount, currency, created_at
            ])
        else:
            # Update existing pending payment
            await db.execute("""
                UPDATE user_packages 
                SET payment_status = 'completed', 
                    is_active = 1,
                    telegram_charge_id = ?,
                    provider_charge_id = ?,
                    amount = ?,
                    currency_code = ?
                WHERE id = ?
            """, [telegram_charge_id, provider_charge_id, amount, currency, user_package["id"]])
        
        return {
            "success": True,
            "message": "Payment confirmed successfully",
            "package_id": package_id,
            "user_id": user_id
        }
        
    except Exception as e:
        print(f"Error confirming payment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to confirm payment")

@router.get("/user/{user_id}")
async def get_user_packages(user_id: str):
    """Get all packages purchased by user"""
    packages = await db.fetchall("""
        SELECT up.*, p.name_ru, p.name_ua, p.package_type, p.features_ru, p.features_ua
        FROM user_packages up
        JOIN packages p ON up.package_id = p.id
        WHERE up.user_id = ? AND up.is_active = 1 AND up.payment_status = 'completed'
        ORDER BY up.created_at DESC
    """, [user_id])
    
    # Parse features
    for package in packages:
        if package.get("features_ru"):
            package["features_ru"] = package["features_ru"].split("|")
        if package.get("features_ua"):
            package["features_ua"] = package["features_ua"].split("|")
    
    return packages