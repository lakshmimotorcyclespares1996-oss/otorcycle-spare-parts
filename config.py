import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Telegram Bot Settings
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")  # Match your existing env var name
    
    # Supabase Settings - handle both local and Vercel environment variables
    SUPABASE_URL = (
        os.getenv("SUPABASE_URL") or 
        os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    )
    SUPABASE_KEY = (
        os.getenv("SUPABASE_KEY") or 
        os.getenv("SUPABASE_ANON_KEY") or
        os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY") or
        os.getenv("SUPABASE_PUBLISHABLE_KEY")
    )
    
    # Redis Settings - Support both local and cloud Redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Redis Cloud specific settings (if using separate host/port/password)
    REDIS_HOST = os.getenv("REDIS_HOST")
    REDIS_PORT = os.getenv("REDIS_PORT", "6379")
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
    REDIS_USERNAME = os.getenv("REDIS_USERNAME", "default")
    
    # App Settings
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL", "http://localhost:8000")
    
    # Server Settings
    APP_NAME = "Lakshmi MotorCycle Parts"
    APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT = int(os.getenv("APP_PORT", "8000"))
    
    # Admin Settings
    ADMIN_ID = os.getenv("ADMIN_ID")
    OWNER_UPI_ID = os.getenv("OWNER_UPI_ID")
    
    # Redis Channels
    CHAT_CHANNEL = "chat_messages"
    ORDER_CHANNEL = "order_updates"
    PARTS_CHANNEL = "parts_updates"

# Create global config instance
config = Config()

# Validation and debug info
print(f"🔧 Config loaded:")
print(f"  - Supabase URL: {config.SUPABASE_URL}")
print(f"  - Supabase Key: {'✅ Set' if config.SUPABASE_KEY else '❌ Missing'}")
print(f"  - Telegram Token: {'✅ Set' if config.TELEGRAM_BOT_TOKEN else '❌ Missing'}")

if not config.TELEGRAM_BOT_TOKEN:
    print("⚠️  Warning: TELEGRAM_TOKEN not found in environment variables")

if not config.SUPABASE_URL or not config.SUPABASE_KEY:
    print("⚠️  Warning: Supabase credentials not found in environment variables")