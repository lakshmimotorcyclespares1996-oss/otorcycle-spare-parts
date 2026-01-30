import json
import logging
from typing import Dict, Any, Optional
from config import config
import asyncio

logger = logging.getLogger("RedisClient")

class SimpleCache:
    """Simple in-memory cache as fallback when Redis is not available"""
    
    def __init__(self):
        self._cache = {}
        self._connected = False
        
    async def connect(self):
        """Initialize cache"""
        self._connected = True
        logger.info("🟢 Simple cache initialized")
        
    async def disconnect(self):
        """Cleanup cache"""
        self._cache.clear()
        self._connected = False
        logger.info("🔴 Cache disconnected")
        
    async def get_cache(self, key: str) -> Optional[str]:
        """Get cached value"""
        if not self._connected:
            return None
            
        value = self._cache.get(key)
        if value:
            logger.info(f"🟢 Cache hit: {key}")
            return value
        else:
            logger.info(f"🟡 Cache miss: {key}")
            return None
    
    async def set_cache(self, key: str, value: str, ttl: int = 3600):
        """Set cache with expiration (TTL ignored in simple cache)"""
        if not self._connected:
            return
            
        self._cache[key] = value
        logger.info(f"🟡 Cached: {key}")
        
        # Simple cleanup - remove old entries if cache gets too large
        if len(self._cache) > 1000:
            # Remove oldest 100 entries
            keys_to_remove = list(self._cache.keys())[:100]
            for k in keys_to_remove:
                del self._cache[k]
    
    async def delete_cache(self, key: str):
        """Delete cached value"""
        if key in self._cache:
            del self._cache[key]
            logger.info(f"🗑️ Cache deleted: {key}")

class RedisClient:
    """Redis client with fallback to simple cache"""
    
    def __init__(self):
        self.cache = SimpleCache()
        self._use_redis = False
        self.redis_client = None
        
    async def connect(self):
        """Connect to Redis or fallback to simple cache"""
        try:
            # Try to import and connect to Redis
            import redis.asyncio as redis
            
            # Check if we have Redis Cloud URL or separate credentials
            if config.REDIS_URL and config.REDIS_URL != "redis://localhost:6379":
                # Use Redis URL (Redis Cloud format)
                self.redis_client = redis.from_url(
                    config.REDIS_URL,
                    decode_responses=True,
                    socket_timeout=5.0,
                    socket_connect_timeout=5.0,
                    health_check_interval=30,
                    retry_on_timeout=True
                )
                logger.info(f"🔗 Connecting to Redis Cloud: {config.REDIS_URL[:20]}...")
                
            elif config.REDIS_HOST and config.REDIS_PASSWORD:
                # Use separate host/port/password (alternative Redis Cloud format)
                self.redis_client = redis.Redis(
                    host=config.REDIS_HOST,
                    port=int(config.REDIS_PORT),
                    password=config.REDIS_PASSWORD,
                    username=config.REDIS_USERNAME,
                    decode_responses=True,
                    socket_timeout=5.0,
                    socket_connect_timeout=5.0,
                    health_check_interval=30,
                    retry_on_timeout=True,
                    ssl=True,  # Redis Cloud typically uses SSL
                    ssl_cert_reqs=None
                )
                logger.info(f"🔗 Connecting to Redis Cloud: {config.REDIS_HOST}:{config.REDIS_PORT}")
                
            else:
                # Try local Redis
                self.redis_client = redis.Redis(
                    host="localhost",
                    port=6379,
                    decode_responses=True,
                    socket_timeout=2.0,
                    health_check_interval=30
                )
                logger.info("🔗 Connecting to local Redis...")
            
            # Test connection
            await self.redis_client.ping()
            self._use_redis = True
            logger.info("✅ Redis connected successfully!")
            
        except Exception as e:
            logger.warning(f"⚠️ Redis not available, using simple cache: {e}")
            self._use_redis = False
            await self.cache.connect()
    
    async def disconnect(self):
        """Disconnect from Redis or simple cache"""
        if self._use_redis and hasattr(self, 'redis_client'):
            try:
                await self.redis_client.close()
                logger.info("🔴 Redis disconnected")
            except Exception as e:
                logger.error(f"Redis disconnect error: {e}")
        else:
            await self.cache.disconnect()
    
    async def get_cache(self, key: str) -> Optional[str]:
        """Get cached value"""
        try:
            if self._use_redis:
                value = await self.redis_client.get(key)
                if value:
                    logger.info(f"🟢 Redis hit: {key}")
                return value
            else:
                return await self.cache.get_cache(key)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set_cache(self, key: str, value: str, ttl: int = 3600):
        """Set cache with expiration"""
        try:
            if self._use_redis:
                await self.redis_client.setex(key, ttl, value)
                logger.info(f"🟡 Redis cached: {key}")
            else:
                await self.cache.set_cache(key, value, ttl)
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
    
    async def delete_cache(self, key: str):
        """Delete cached value"""
        try:
            if self._use_redis:
                await self.redis_client.delete(key)
                logger.info(f"🗑️ Redis deleted: {key}")
            else:
                await self.cache.delete_cache(key)
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
    
    # Cart functionality (simplified)
    async def add_to_cart(self, user_id: int, part_id: str, quantity: int = 1, **kwargs):
        """Add item to user's cart"""
        try:
            cart_key = f"cart:{user_id}"
            
            # Get existing cart
            cart_data = await self.get_cache(cart_key)
            cart = json.loads(cart_data) if cart_data else {}
            
            # Add/update item
            if part_id in cart:
                cart[part_id]['quantity'] += quantity
            else:
                cart[part_id] = {
                    'part_id': part_id,
                    'quantity': quantity,
                    **kwargs  # Additional part details
                }
            
            # Save cart
            await self.set_cache(cart_key, json.dumps(cart), ttl=86400)  # 24 hours
            logger.info(f"🛒 Added to cart: user {user_id}, part {part_id}")
            
        except Exception as e:
            logger.error(f"Add to cart error: {e}")
    
    async def get_cart(self, user_id: int) -> Dict[str, Any]:
        """Get user's cart"""
        try:
            cart_key = f"cart:{user_id}"
            cart_data = await self.get_cache(cart_key)
            return json.loads(cart_data) if cart_data else {}
        except Exception as e:
            logger.error(f"Get cart error: {e}")
            return {}
    
    async def clear_cart(self, user_id: int):
        """Clear user's cart"""
        try:
            cart_key = f"cart:{user_id}"
            await self.delete_cache(cart_key)
            logger.info(f"🛒 Cart cleared for user {user_id}")
        except Exception as e:
            logger.error(f"Clear cart error: {e}")

# Global instance
redis_client = RedisClient()