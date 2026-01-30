import os
import logging
from datetime import datetime
from supabase import acreate_client, AsyncClient
from redis_client import redis_client as cache
from config import config
from typing import List, Dict, Optional
from dotenv import load_dotenv
from fuzzywuzzy import fuzz, process
import re

load_dotenv()

logger = logging.getLogger("Database")
_supabase: AsyncClient = None

async def get_db():
    global _supabase
    if _supabase is None:
        _supabase = await acreate_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    return _supabase

class Database:
    def __init__(self):
        self._supabase = None
    
    async def get_client(self):
        if self._supabase is None:
            self._supabase = await acreate_client(config.SUPABASE_URL, config.SUPABASE_KEY)
        return self._supabase
    
    async def init_tables(self):
        """Initialize database tables"""
        try:
            db = await self.get_client()
            # Test connection with spare_parts table (your existing table)
            await db.table('spare_parts').select('*').limit(1).execute()
            logger.info("✅ Database connection established")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            print("Creating database tables...")
    
    # Enhanced Parts operations with fuzzy search and comprehensive filtering
    async def get_parts(self, search: str = "", category: str = "", brand: str = "", model: str = "", year: int = None, limit: int = 200) -> List[Dict]:
        """Get parts with advanced fuzzy search and comprehensive filtering"""
        try:
            db = await self.get_client()
            query = db.table('spare_parts').select('*')
            
            # Apply filters first - but only if they have values
            if category and category.strip():
                query = query.eq('part_category', category)
            if brand and brand.strip():
                query = query.eq('bike_brand', brand)
            if model and model.strip():
                query = query.eq('bike_model', model)
            if year:
                query = query.lte('year_from', year).gte('year_to', year)
                
            # Get all matching parts for fuzzy search
            result = await query.limit(2000).execute()  # Increased limit to get more parts
            parts = result.data
            
            # Apply fuzzy search if search term provided
            if search and search.strip() and parts:
                parts = await self._fuzzy_search_parts(parts, search)
            
            # Return limited results
            return parts[:limit]
        except Exception as e:
            logger.error(f"❌ Error fetching parts: {e}")
            return []
    
    async def _fuzzy_search_parts(self, parts: List[Dict], search_term: str) -> List[Dict]:
        """Apply fuzzy search to parts list"""
        try:
            search_term = search_term.lower().strip()
            scored_parts = []
            
            for part in parts:
                # Create searchable text from multiple fields
                searchable_text = f"{part.get('part_name', '')} {part.get('bike_brand', '')} {part.get('bike_model', '')} {part.get('part_category', '')} {part.get('description', '')}"
                
                # Calculate fuzzy match scores
                name_score = fuzz.partial_ratio(search_term, part.get('part_name', '').lower())
                brand_score = fuzz.partial_ratio(search_term, part.get('bike_brand', '').lower())
                model_score = fuzz.partial_ratio(search_term, part.get('bike_model', '').lower())
                category_score = fuzz.partial_ratio(search_term, part.get('part_category', '').lower())
                full_text_score = fuzz.partial_ratio(search_term, searchable_text.lower())
                
                # Weight the scores (name and brand are more important)
                final_score = max(
                    name_score * 1.5,      # Part name is most important
                    brand_score * 1.2,     # Brand is important
                    model_score * 1.1,     # Model is important
                    category_score * 1.0,  # Category is relevant
                    full_text_score * 0.8  # Full text search as fallback
                )
                
                # Only include parts with reasonable match (threshold: 60)
                if final_score >= 60:
                    part['_search_score'] = final_score
                    scored_parts.append(part)
            
            # Sort by score (highest first)
            scored_parts.sort(key=lambda x: x['_search_score'], reverse=True)
            
            # Remove the score field before returning
            for part in scored_parts:
                part.pop('_search_score', None)
            
            return scored_parts
            
        except Exception as e:
            logger.error(f"❌ Error in fuzzy search: {e}")
            return parts  # Return original parts if fuzzy search fails
    
    async def get_advanced_filters(self) -> Dict:
        """Get all available filter options"""
        try:
            cache_key = "advanced_filters"
            cached = await cache.get_cache(cache_key)
            if cached:
                import json
                return json.loads(cached)
            
            db = await self.get_client()
            result = await db.table('spare_parts').select('bike_brand, bike_model, part_category, year_from, year_to').execute()
            
            brands = sorted(list(set(row['bike_brand'] for row in result.data if row['bike_brand'])))
            categories = sorted(list(set(row['part_category'] for row in result.data if row['part_category'])))
            
            # Generate all years from year ranges
            all_years = set()
            for row in result.data:
                if row['year_from'] and row['year_to']:
                    for year in range(int(row['year_from']), int(row['year_to']) + 1):
                        all_years.add(year)
            years = sorted(list(all_years), reverse=True)
            
            # Get models grouped by brand
            models_by_brand = {}
            for brand in brands:
                brand_models = sorted(list(set(
                    row['bike_model'] for row in result.data 
                    if row['bike_brand'] == brand and row['bike_model']
                )))
                models_by_brand[brand] = brand_models
            
            filters = {
                'brands': brands,
                'categories': categories,
                'years': years,
                'models_by_brand': models_by_brand
            }
            
            import json
            await cache.set_cache(cache_key, json.dumps(filters), ttl=3600)  # Cache for 1 hour
            return filters
            
        except Exception as e:
            logger.error(f"❌ Error fetching advanced filters: {e}")
            return {'brands': [], 'categories': [], 'years': [], 'models_by_brand': {}}
    
    async def search_suggestions(self, query: str, limit: int = 10) -> List[Dict]:
        """Get search suggestions with fuzzy matching"""
        try:
            if not query or len(query) < 2:
                return []
            
            db = await self.get_client()
            result = await db.table('spare_parts').select('part_name, bike_brand, bike_model, part_category').execute()
            
            # Create suggestion candidates
            suggestions = []
            seen = set()
            
            for row in result.data:
                # Add part names
                part_name = row.get('part_name', '').strip()
                if part_name and part_name.lower() not in seen:
                    suggestions.append({
                        'text': part_name,
                        'type': 'part',
                        'category': row.get('part_category', '')
                    })
                    seen.add(part_name.lower())
                
                # Add brand names
                brand = row.get('bike_brand', '').strip()
                if brand and brand.lower() not in seen:
                    suggestions.append({
                        'text': brand,
                        'type': 'brand',
                        'category': 'Brand'
                    })
                    seen.add(brand.lower())
                
                # Add model names
                model = row.get('bike_model', '').strip()
                if model and model.lower() not in seen:
                    suggestions.append({
                        'text': model,
                        'type': 'model',
                        'category': 'Model'
                    })
                    seen.add(model.lower())
            
            # Use fuzzy matching to find best suggestions
            query_lower = query.lower()
            scored_suggestions = []
            
            for suggestion in suggestions:
                score = fuzz.partial_ratio(query_lower, suggestion['text'].lower())
                if score >= 70:  # Higher threshold for suggestions
                    suggestion['score'] = score
                    scored_suggestions.append(suggestion)
            
            # Sort by score and return top results
            scored_suggestions.sort(key=lambda x: x['score'], reverse=True)
            
            # Remove score field and return
            for suggestion in scored_suggestions:
                suggestion.pop('score', None)
            
            return scored_suggestions[:limit]
            
        except Exception as e:
            logger.error(f"❌ Error getting search suggestions: {e}")
            return []
    
    async def get_part_by_id(self, part_id: int) -> Optional[Dict]:
        """Get specific part by ID"""
        try:
            db = await self.get_client()
            result = await db.table('spare_parts').select('*').eq('id', part_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"❌ Error fetching part by ID: {e}")
            return None
    
    async def get_brands(self):
        """Get all unique brands"""
        cached = await cache.get_cache("brands")
        if cached: 
            import json
            return json.loads(cached)
        
        try:
            db = await self.get_client()
            res = await db.table("spare_parts").select("bike_brand").execute()
            brands = sorted(list({row["bike_brand"] for row in res.data}))
            import json
            await cache.set_cache("brands", json.dumps(brands))
            return brands
        except Exception as e:
            logger.error(f"❌ Error fetching brands: {e}")
            return []

    async def get_models_by_brand(self, brand: str):
        """Get models for a specific brand"""
        key = f"models:{brand}"
        cached = await cache.get_cache(key)
        if cached: 
            import json
            return json.loads(cached)
        
        try:
            db = await self.get_client()
            res = await db.table("spare_parts").select("bike_model").eq("bike_brand", brand).execute()
            models = sorted(list({row["bike_model"] for row in res.data}))
            import json
            await cache.set_cache(key, json.dumps(models))
            return models
        except Exception as e:
            logger.error(f"❌ Error fetching models: {e}")
            return []

    async def get_years(self, brand: str, model: str):
        """Get years for a specific brand and model"""
        key = f"years:{brand}:{model}"
        cached = await cache.get_cache(key)
        if cached: 
            return cached
        
        try:
            db = await self.get_client()
            res = await db.table("spare_parts").select("year_from, year_to").eq("bike_brand", brand).eq("bike_model", model).execute()
            # Generate unique years from all ranges
            all_years = sorted(list({y for r in res.data for y in range(int(r["year_from"]), int(r["year_to"]) + 1)}), reverse=True)
            await cache.set_cache(key, all_years)
            return all_years
        except Exception as e:
            logger.error(f"❌ Error fetching years: {e}")
            return []

    async def get_part_details(self, brand, model, year, part):
        """Get detailed information for a specific part"""
        try:
            db = await self.get_client()
            res = await db.table("spare_parts") \
                .select("*") \
                .eq("bike_brand", brand) \
                .eq("bike_model", model) \
                .eq("part_name", part) \
                .lte("year_from", year) \
                .gte("year_to", year) \
                .limit(1) \
                .execute()
            return res.data[0] if res.data else None
        except Exception as e:
            logger.error(f"❌ Error fetching part details: {e}")
            return None

    async def get_categories_by_model(self, brand, model):
        """Get categories for a specific brand and model"""
        try:
            db = await self.get_client()
            res = await db.table("spare_parts") \
                .select("part_category") \
                .match({"bike_brand": brand, "bike_model": model}) \
                .execute()
            return sorted(list(set([row['part_category'] for row in res.data])))
        except Exception as e:
            logger.error(f"❌ Error fetching categories: {e}")
            return []

    async def get_parts_by_category(self, brand, model, category):
        """Get parts for a specific category"""
        try:
            db = await self.get_client()
            res = await db.table("spare_parts") \
                .select("part_name") \
                .match({"bike_brand": brand, "bike_model": model, "part_category": category}) \
                .execute()
            return sorted(list(set([row['part_name'] for row in res.data])))
        except Exception as e:
            logger.error(f"❌ Error fetching parts by category: {e}")
            return []

    async def get_colors_for_part(self, brand, model, part_name):
        """Get available colors for a specific part"""
        try:
            db = await self.get_client()
            res = await db.table("spare_parts") \
                .select("color") \
                .match({"bike_brand": brand, "bike_model": model, "part_name": part_name}) \
                .execute()
            return [row['color'] for row in res.data if row.get('color')]
        except Exception as e:
            logger.error(f"❌ Error fetching colors: {e}")
            return []

    async def search_all_models(self, query: str):
        """Search for models across all brands"""
        try:
            db = await self.get_client()
            res = await db.table("spare_parts").select("bike_brand, bike_model") \
                .ilike("bike_model", f"%{query}%").execute()
            
            unique = []
            seen = set()
            for row in res.data:
                id_ = f"{row['bike_brand']}:{row['bike_model']}"
                if id_ not in seen:
                    unique.append(row)
                    seen.add(id_)
            return unique[:10]
        except Exception as e:
            logger.error(f"❌ Search Error: {e}")
            return []
    
    # Customer operations (Updated to work with your existing tables)
    async def create_customer(self, telegram_id: int, username: str, first_name: str) -> Dict:
        """Create or update customer"""
        try:
            db = await self.get_client()
            customer_data = {
                'user_id': telegram_id,  # Using user_id to match your existing schema
                'username': username,
                'first_name': first_name
            }
            
            # Check if customer exists
            existing = await db.table('users').select('*').eq('user_id', telegram_id).execute()
            
            if existing.data:
                # Update existing customer
                result = await db.table('users').update(customer_data).eq('user_id', telegram_id).execute()
            else:
                # Insert new customer
                result = await db.table('users').insert(customer_data).execute()
            
            return result.data[0] if result.data else customer_data
        except Exception as e:
            logger.error(f"❌ Error creating/updating customer: {e}")
            return {}
    
    async def get_customer(self, telegram_id: int) -> Optional[Dict]:
        """Get customer by telegram ID"""
        try:
            db = await self.get_client()
            result = await db.table('users').select('*').eq('user_id', telegram_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"❌ Error fetching customer: {e}")
            return None

    async def update_user_profile(self, user_id: int, full_name: str, phone: str, address: str):
        """Update user profile information"""
        try:
            db = await self.get_client()
            await db.table("user_profiles").upsert({
                "user_id": user_id,
                "full_name": full_name,
                "phone": phone,
                "address": address,
                "updated_at": datetime.now().isoformat()
            }, on_conflict="user_id").execute()
            logger.info(f"✅ Profile updated for user {user_id}")
        except Exception as e:
            logger.error(f"❌ Profile Update Error: {e}")
            raise
    
    # Order operations (Updated to work with your existing orders table)
    async def create_order(self, user_id: int, items: List[Dict], total_amount: float, **kwargs) -> Dict:
        """Create new order"""
        try:
            db = await self.get_client()
            order_data = {
                'user_id': user_id,
                'items': items,
                'total_amount': total_amount,
                'status': 'pending',
                'order_id': kwargs.get('order_id', f"ORD-{datetime.now().strftime('%Y%m%d')}-{user_id}"),
                'full_name': kwargs.get('full_name'),
                'phone': kwargs.get('phone'),
                'address': kwargs.get('address')
            }
            
            result = await db.table('orders').insert(order_data).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"❌ Error creating order: {e}")
            return {}
    
    async def get_customer_orders(self, user_id: int) -> List[Dict]:
        """Get customer's orders"""
        try:
            db = await self.get_client()
            result = await db.table('orders').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
            return result.data
        except Exception as e:
            logger.error(f"❌ Error fetching orders: {e}")
            return []
    
    async def update_order_status(self, order_id: int, status: str):
        """Update order status"""
        try:
            db = await self.get_client()
            await db.table('orders').update({'status': status}).eq('id', order_id).execute()
        except Exception as e:
            logger.error(f"❌ Error updating order status: {e}")

    async def get_all_orders(self, status: str = None) -> List[Dict]:
        """Get all orders for admin panel"""
        try:
            db = await self.get_client()
            query = db.table('orders').select('*')
            
            if status:
                query = query.eq('status', status)
                
            result = await query.order('created_at', desc=True).execute()
            return result.data
        except Exception as e:
            logger.error(f"❌ Error fetching all orders: {e}")
            return []
    
    # Cart operations (Updated to work with your existing cart table)
    async def add_to_cart(self, user_id: int, part_name: str, brand: str, model: str, year: int, price: float, color: str = None, quantity: int = 1):
        """Add item to database cart"""
        try:
            db = await self.get_client()
            await db.table("cart").insert({
                "user_id": user_id,
                "part_name": part_name,
                "bike_brand": brand,
                "bike_model": model,
                "year": year,
                "price": price,
                "color": color,
                "quantity": quantity
            }).execute()
        except Exception as e:
            logger.error(f"❌ Error adding to cart: {e}")

    async def get_cart(self, user_id: int):
        """Get user's cart from database"""
        try:
            db = await self.get_client()
            res = await db.table("cart").select("*").eq("user_id", user_id).execute()
            return res.data
        except Exception as e:
            logger.error(f"❌ Error fetching cart: {e}")
            return []

    async def clear_cart(self, user_id: int):
        """Clear user's cart"""
        try:
            db = await self.get_client()
            await db.table("cart").delete().eq("user_id", user_id).execute()
        except Exception as e:
            logger.error(f"❌ Error clearing cart: {e}")

    async def remove_from_cart(self, user_id: int, cart_item_id: int):
        """Remove specific item from cart"""
        try:
            db = await self.get_client()
            await db.table("cart").delete().eq("user_id", user_id).eq("id", cart_item_id).execute()
        except Exception as e:
            logger.error(f"❌ Error removing from cart: {e}")

# Global database instance
# Chat operations (Updated to work with your existing chat_messages table)
    async def save_chat_message(self, user_id: int, message: str, is_customer: bool = True) -> Dict:
        """Save chat message"""
        try:
            db_client = await self.get_client()
            message_data = {
                'user_id': user_id,  # Using user_id to match your schema
                'message': message,
                'is_customer': is_customer
            }
            
            result = await db_client.table('chat_messages').insert(message_data).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"❌ Error saving chat message: {e}")
            return {}

    async def get_chat_history(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get chat history for user"""
        try:
            db_client = await self.get_client()
            result = await db_client.table('chat_messages').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(limit).execute()
            return list(reversed(result.data))
        except Exception as e:
            logger.error(f"❌ Error fetching chat history: {e}")
            return []

    async def get_all_chat_sessions(self) -> List[Dict]:
        """Get all chat sessions for admin panel"""
        try:
            db_client = await self.get_client()
            # Get latest message from each user
            result = await db_client.table('chat_messages') \
                .select('user_id, message, created_at') \
                .order('created_at', desc=True) \
                .execute()
            
            # Group by user_id and get the latest message
            sessions = {}
            for msg in result.data:
                user_id = msg['user_id']
                if user_id not in sessions:
                    sessions[user_id] = msg
            
            return list(sessions.values())
        except Exception as e:
            logger.error(f"❌ Error fetching chat sessions: {e}")
            return []

    # Wishlist operations
    async def add_to_wishlist(self, user_id: int, item: Dict):
        """Add item to user's wishlist"""
        try:
            db_client = await self.get_client()
            res = await db_client.table("user_profiles").select("wishlist").eq("user_id", user_id).maybe_single().execute()
            wishlist = res.data['wishlist'] if res and res.data else []
            
            if not any(x['item'] == item['item'] for x in wishlist):
                wishlist.append(item)
                await db_client.table("user_profiles").upsert({"user_id": user_id, "wishlist": wishlist}).execute()
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Error adding to wishlist: {e}")
            return False

    async def get_wishlist(self, user_id: int) -> List[Dict]:
        """Get user's wishlist"""
        try:
            db_client = await self.get_client()
            res = await db_client.table("user_profiles").select("wishlist").eq("user_id", user_id).maybe_single().execute()
            return res.data.get('wishlist', []) if res and res.data else []
        except Exception as e:
            logger.error(f"❌ Error fetching wishlist: {e}")
            return []

    async def remove_from_wishlist(self, user_id: int, index: int):
        """Remove item from wishlist by index"""
        try:
            db_client = await self.get_client()
            res = await db_client.table("user_profiles").select("wishlist").eq("user_id", user_id).single().execute()
            wishlist = res.data['wishlist']
            if 0 <= index < len(wishlist):
                wishlist.pop(index)
                await db_client.table("user_profiles").update({"wishlist": wishlist}).eq("user_id", user_id).execute()
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Error removing from wishlist: {e}")
            return False

# Global database instance
db = Database()

# Legacy functions for compatibility with your existing bot code
async def get_brands():
    return await db.get_brands()

async def get_models_by_brand(brand: str):
    return await db.get_models_by_brand(brand)

async def get_years(brand: str, model: str):
    return await db.get_years(brand, model)

async def get_part_details(brand, model, year, part):
    return await db.get_part_details(brand, model, year, part)

async def get_categories_by_model(brand, model):
    return await db.get_categories_by_model(brand, model)

async def get_parts_by_category(brand, model, category):
    return await db.get_parts_by_category(brand, model, category)

async def get_colors_for_part(brand, model, part_name):
    return await db.get_colors_for_part(brand, model, part_name)

async def search_all_models(query: str):
    return await db.search_all_models(query)

async def add_to_db_cart(user_id, part_name, brand, model, year, price, color=None):
    return await db.add_to_cart(user_id, part_name, brand, model, year, price, color)

async def get_db_cart(user_id):
    return await db.get_cart(user_id)

async def clear_db_cart(user_id):
    return await db.clear_cart(user_id)

async def update_user_profile(user_id: int, full_name: str, phone: str, address: str):
    return await db.update_user_profile(user_id, full_name, phone, address)