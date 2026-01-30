from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from contextlib import asynccontextmanager
from datetime import datetime
import asyncio
import json
from typing import Dict, List, Optional
import uvicorn
import threading
import os

from config import config
from database import db
from redis_client import redis_client
from models import *

# Import Telegram bot
import sys
sys.path.append('.')

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await redis_client.connect()
    await db.init_tables()
    print(f"🚀 {config.APP_NAME} started successfully!")
    yield
    # Shutdown
    await redis_client.disconnect()
    print("👋 Shutting down...")

app = FastAPI(title=config.APP_NAME, lifespan=lifespan)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Web App Routes
@app.get("/webapp", response_class=HTMLResponse)
async def webapp(request: Request):
    """Main web app page"""
    return templates.TemplateResponse("webapp.html", {
        "request": request,
        "app_name": config.APP_NAME
    })

# Add favicon endpoint to fix 404
@app.get("/favicon.ico")
async def favicon():
    """Return favicon"""
    return {"message": "No favicon"}

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now()}

@app.get("/test-images", response_class=HTMLResponse)
async def test_images_page(request: Request):
    """Test page for image debugging"""
    with open("test_browser_debug.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

# API Routes - Essential web app functionality
@app.get("/api/parts")
async def get_parts(
    search: str = "", 
    category: str = "", 
    brand: str = "", 
    model: str = "", 
    year: int = None,
    limit: int = 200
):
    """Get parts with search and filtering"""
    parts = await db.get_parts(
        search=search, 
        category=category, 
        brand=brand, 
        model=model, 
        year=year,
        limit=limit
    )
    
    # Transform to match web app expectations
    transformed_parts = []
    for part in parts:
        # Use web_image_url for web app display - check if it exists and is not empty
        web_image_url = part.get("web_image_url")
        if not web_image_url or web_image_url.strip() == "":
            # Fallback to category-specific placeholder
            category = part.get("part_category", "").lower()
            placeholder_images = {
                "body panels": "https://via.placeholder.com/400x300/6f42c1/ffffff?text=Body+Panels",
                "petrol tank": "https://via.placeholder.com/400x300/28a745/ffffff?text=Petrol+Tank",
                "suspension": "https://via.placeholder.com/400x300/fd7e14/ffffff?text=Suspension",
                "body parts": "https://via.placeholder.com/400x300/6f42c1/ffffff?text=Body+Parts",
                "transmission": "https://via.placeholder.com/400x300/e83e8c/ffffff?text=Transmission",
                "electrical": "https://via.placeholder.com/400x300/ffc107/000000?text=Electrical",
                "engine": "https://via.placeholder.com/400x300/28a745/ffffff?text=Engine",
                "lights": "https://via.placeholder.com/400x300/17a2b8/ffffff?text=Lights",
                "fuel system": "https://via.placeholder.com/400x300/dc3545/ffffff?text=Fuel+System",
                "wheels": "https://via.placeholder.com/400x300/343a40/ffffff?text=Wheels",
                "engine parts": "https://via.placeholder.com/400x300/28a745/ffffff?text=Engine+Parts",
                "brake system": "https://via.placeholder.com/400x300/dc3545/ffffff?text=Brake+System",
                "exhaust system": "https://via.placeholder.com/400x300/dc3545/ffffff?text=Exhaust+System"
            }
            web_image_url = placeholder_images.get(category, 
                "https://via.placeholder.com/400x300/6c757d/ffffff?text=Motorcycle+Part")
        else:
            # Clean up the URL if it has extra spaces
            web_image_url = web_image_url.strip()
        
        transformed_parts.append({
            "id": part.get("id"),
            "name": part.get("part_name"),
            "description": part.get("description", ""),
            "category": part.get("part_category"),
            "price": float(part.get("price", 0)),
            "stock": int(part.get("stock_qty", 0)),
            "image_url": web_image_url,
            "part_number": part.get("part_number", ""),
            "brand": part.get("bike_brand"),
            "model": part.get("bike_model"),
            "year_from": part.get("year_from"),
            "year_to": part.get("year_to"),
            "color": part.get("color"),
            "compatible_models": [f"{part.get('bike_brand')} {part.get('bike_model')}"]
        })
    
    return {"parts": transformed_parts}

@app.get("/api/filters")
async def get_filters():
    """Get all available filter options"""
    filters = await db.get_advanced_filters()
    return filters

@app.get("/api/brands")
async def get_brands_api():
    """Get all available brands"""
    brands = await db.get_brands()
    return {"brands": brands}

@app.get("/api/models/{brand}")
async def get_models_api(brand: str):
    """Get models for a specific brand"""
    models = await db.get_models_by_brand(brand)
    return {"models": models}

@app.get("/api/years/{brand}/{model}")
async def get_years_api(brand: str, model: str):
    """Get years for a specific brand and model"""
    years = await db.get_years(brand, model)
    return {"years": years}

@app.get("/api/categories/{brand}/{model}")
async def get_categories_api(brand: str, model: str):
    """Get categories for a specific brand and model"""
    categories = await db.get_categories_by_model(brand, model)
    return {"categories": categories}

@app.get("/api/years")
async def get_all_years_api():
    """Get all available years"""
    try:
        db_client = await db.get_client()
        result = await db_client.table('spare_parts').select('year_from, year_to').execute()
        
        all_years = set()
        for row in result.data:
            if row['year_from'] and row['year_to']:
                for year in range(int(row['year_from']), int(row['year_to']) + 1):
                    all_years.add(year)
        
        years = sorted(list(all_years), reverse=True)
        return {"years": years}
    except Exception as e:
        print(f"Error fetching years: {e}")
        return {"years": []}

@app.post("/api/cart/add")
async def add_to_cart(request: Request):
    """Add item to cart with Redis caching"""
    data = await request.json()
    user_id = data.get("user_id")
    part_id = data.get("part_id")
    quantity = data.get("quantity", 1)
    
    # Get part details
    part_details = await db.get_part_by_id(part_id)
    if not part_details:
        raise HTTPException(status_code=404, detail="Part not found")
    
    # Add to Redis cart
    await redis_client.add_to_cart(
        user_id=user_id,
        part_id=part_id,
        quantity=quantity,
        part_name=part_details.get("part_name"),
        brand=part_details.get("bike_brand"),
        model=part_details.get("bike_model"),
        price=part_details.get("price"),
        image_url=part_details.get("web_image_url")
    )
    
    return {"success": True, "message": "Item added to cart"}

@app.get("/api/cart/{user_id}")
async def get_cart_api(user_id: int):
    """Get user's cart from Redis"""
    cart = await redis_client.get_cart(user_id)
    
    # Convert cart format for web app
    cart_items = []
    for part_id, item in cart.items():
        cart_items.append({
            "id": item.get("part_id"),
            "name": item.get("part_name"),
            "brand": item.get("brand"),
            "model": item.get("model"),
            "price": item.get("price"),
            "cart_quantity": item.get("quantity"),
            "image_url": item.get("image_url")
        })
    
    return {"cart": cart_items}

@app.post("/api/orders")
async def create_order_api(request: Request):
    """Create new order"""
    data = await request.json()
    user_id = data.get("user_id")
    delivery_address = data.get("delivery_address")
    phone = data.get("phone")
    notes = data.get("notes", "")
    
    # Get cart items from Redis
    cart = await redis_client.get_cart(user_id)
    if not cart:
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    # Calculate total and prepare items
    items = []
    total_amount = 0
    
    for part_id, item in cart.items():
        item_total = float(item.get("price", 0)) * int(item.get("quantity", 1))
        total_amount += item_total
        
        items.append({
            "item": item.get("part_name"),
            "qty": item.get("quantity"),
            "brand": item.get("brand"),
            "model": item.get("model"),
            "price": item.get("price")
        })
    
    # Create order
    order = await db.create_order(
        user_id=user_id,
        items=items,
        total_amount=total_amount,
        address=delivery_address,
        phone=phone,
        full_name=data.get("full_name", "Customer")
    )
    
    # Clear cart after successful order
    await redis_client.clear_cart(user_id)
    
    return {"success": True, "order": order}

@app.get("/api/orders/{user_id}")
async def get_user_orders_api(user_id: int):
    """Get user's orders"""
    orders = await db.get_customer_orders(user_id)
    return {"orders": orders}

@app.get("/api/profile/{user_id}")
async def get_user_profile_api(user_id: int):
    """Get user profile"""
    try:
        db_client = await db.get_client()
        
        try:
            result = await db_client.table('user_profiles').select('user_id, full_name, phone, address, created_at').eq('user_id', user_id).execute()
            
            if result.data:
                profile = result.data[0]
                profile['email'] = ''  # Add empty email field
                return profile
            else:
                raise HTTPException(status_code=404, detail="Profile not found")
        except Exception as table_error:
            print(f"⚠️ Profile table error: {table_error}")
            raise HTTPException(status_code=404, detail="Profile not found")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch profile")

@app.post("/api/profile")
async def save_user_profile_api(request: Request):
    """Save user profile"""
    try:
        data = await request.json()
        user_id = data.get("user_id")
        full_name = data.get("full_name")
        phone = data.get("phone")
        address = data.get("address")
        
        if not all([user_id, full_name, phone, address]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        db_client = await db.get_client()
        
        try:
            profile_data = {
                'user_id': user_id,
                'full_name': full_name,
                'phone': phone,
                'address': address
            }
            
            result = await db_client.table('user_profiles').upsert(profile_data, on_conflict='user_id').execute()
            print(f"✅ Profile saved for user {user_id}")
            
            return {"success": True, "message": "Profile saved successfully"}
            
        except Exception as table_error:
            print(f"⚠️ Profile table error: {table_error}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(table_error)}")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error saving profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to save profile")

# Telegram webhook (for production)
@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Handle Telegram webhook"""
    return {"status": "ok"}

if __name__ == "__main__":
    print("🚀 Starting web app only (Telegram bot disabled to avoid conflicts)")
    
    # Start FastAPI server
    uvicorn.run(
        "main:app",
        host=config.APP_HOST,
        port=config.APP_PORT,
        reload=True
    )