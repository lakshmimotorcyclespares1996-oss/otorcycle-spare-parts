from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class Part(BaseModel):
    id: Optional[int] = None
    name: str
    description: str
    category: str
    price: float
    stock: int
    image_url: Optional[str] = None
    part_number: str
    brand: str
    compatible_models: List[str] = []

class Customer(BaseModel):
    id: Optional[int] = None
    telegram_id: int
    username: Optional[str] = None
    first_name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    created_at: Optional[datetime] = None

class CartItem(BaseModel):
    part_id: int
    quantity: int
    price: float

class Order(BaseModel):
    id: Optional[int] = None
    customer_id: int
    items: List[Dict[str, Any]]
    total_amount: float
    status: str = "pending"
    delivery_address: Optional[str] = None
    phone: Optional[str] = None
    created_at: Optional[datetime] = None

class ChatMessage(BaseModel):
    id: Optional[int] = None
    customer_id: int
    message: str
    is_customer: bool = True
    created_at: Optional[datetime] = None

class SearchRequest(BaseModel):
    query: Optional[str] = ""
    category: Optional[str] = ""
    min_price: Optional[float] = None
    max_price: Optional[float] = None

class OrderRequest(BaseModel):
    items: List[CartItem]
    delivery_address: str
    phone: str
    notes: Optional[str] = None