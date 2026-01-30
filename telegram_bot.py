from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
from config import config
from database import db
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        self.application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup bot command and message handlers"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("shop", self.shop_command))
        self.application.add_handler(CommandHandler("orders", self.orders_command))
        self.application.add_handler(CommandHandler("support", self.support_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command - Enhanced to work with your existing bot"""
        user = update.effective_user
        
        # Create or update customer in database
        await db.create_customer(
            telegram_id=user.id,
            username=user.username or "",
            first_name=user.first_name or ""
        )
        
        # Create web app keyboard with your existing structure
        web_app = WebAppInfo(url=f"{config.WEBHOOK_URL}/webapp")
        keyboard = [
            [KeyboardButton("🛍️ Open Web Shop", web_app=web_app)],
            [InlineKeyboardButton("🛍 Browse by Bike", callback_data="main_browse")],
            [InlineKeyboardButton("🔎 Search Part", switch_inline_query_current_chat="")],
            [InlineKeyboardButton("🛒 View Cart", callback_data="v_cart")],
            [InlineKeyboardButton("📦 Track Order", callback_data="track_order")],
            [InlineKeyboardButton("💬 Support", url="https://t.me/Lakshmi_Motorcycle_spares")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_message = f"""
🏍️ **Welcome to {config.APP_NAME}!**

Hi {user.first_name}! We're your one-stop shop for motorcycle spare parts.

**Choose how you want to shop:**
🛍️ **Web Shop** - Modern web interface with advanced features
🛍 **Browse by Bike** - Traditional bot interface
🔎 **Search Part** - Quick part search
🛒 **View Cart** - Check your items
📦 **Track Order** - Monitor your orders
💬 **Support** - Get help from our team

Click any option to get started!
        """
        
        await update.message.reply_text(
            welcome_message, 
            reply_markup=reply_markup, 
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = f"""
🏍️ **{config.APP_NAME} - Help**

**Available Commands:**
/start - Start the bot and open main menu
/shop - Open the web shop
/orders - View your orders
/support - Contact customer support
/help - Show this help message

**Shopping Options:**
🛍️ **Web Shop** - Full-featured web interface with:
   ✅ Advanced search and filtering
   ✅ Real-time chat support
   ✅ Visual product gallery
   ✅ Easy checkout process

🛍 **Bot Interface** - Traditional Telegram bot with:
   ✅ Browse by bike brand/model
   ✅ Category-wise part selection
   ✅ Quick order placement
   ✅ Order tracking

**Features:**
✅ Real-time parts search across all brands
✅ Live chat support with our team
✅ Secure order tracking
✅ Multiple payment options
✅ Fast delivery across India

Need help? Contact us at @Lakshmi_Motorcycle_spares
        """
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def shop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /shop command"""
        web_app = WebAppInfo(url=f"{config.WEBHOOK_URL}/webapp")
        keyboard = [
            [InlineKeyboardButton("🛍️ Open Web Shop", web_app=web_app)],
            [InlineKeyboardButton("🛍 Browse by Bike", callback_data="main_browse")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🛍️ **Choose your shopping experience:**\n\n"
            "🛍️ **Web Shop** - Modern interface with advanced features\n"
            "🛍 **Browse by Bike** - Traditional bot interface",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def orders_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /orders command"""
        user = update.effective_user
        orders = await db.get_customer_orders(user.id)
        
        if not orders:
            await update.message.reply_text("📋 You haven't placed any orders yet.")
            return
        
        orders_text = "📋 **Your Recent Orders:**\n\n"
        for order in orders[:5]:  # Show last 5 orders
            status_emoji = {
                "pending": "⏳", 
                "confirmed": "✅", 
                "shipped": "🚚", 
                "delivered": "📦", 
                "cancelled": "❌"
            }
            emoji = status_emoji.get(order.get('status', 'pending'), "📋")
            
            orders_text += f"{emoji} **Order #{order.get('order_id', order.get('id'))}**\n"
            orders_text += f"Amount: ₹{order.get('total_amount')}\n"
            orders_text += f"Status: {order.get('status', 'pending').title()}\n"
            
            if order.get('created_at'):
                orders_text += f"Date: {order['created_at'][:10]}\n"
            orders_text += "\n"
        
        await update.message.reply_text(orders_text, parse_mode=ParseMode.MARKDOWN)
    
    async def support_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /support command"""
        support_text = """
📞 **Customer Support**

Our support team is here to help you!

**Contact Methods:**
💬 **Live Chat** - Type your message below
📱 **Direct Chat** - @Lakshmi_Motorcycle_spares
📧 **Email** - support@lakshmimotorcycleparts.com

**Support Hours:**
🕘 Monday - Saturday: 9:00 AM - 7:00 PM
🕘 Sunday: 10:00 AM - 5:00 PM

**Quick Help:**
• Part compatibility questions
• Order status updates
• Payment assistance
• Delivery information
• Technical support

Just type your message and our team will respond shortly!
        """
        await update.message.reply_text(support_text, parse_mode=ParseMode.MARKDOWN)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular text messages (for support chat)"""
        user = update.effective_user
        
        # Save customer message to database
        await db.save_chat_message(
            user_id=user.id,
            message=update.message.text,
            is_customer=True
        )
        
        # Send acknowledgment
        await update.message.reply_text(
            "💬 **Thank you for your message!**\n\n"
            "Our support team will respond shortly.\n\n"
            "For immediate assistance:\n"
            "📱 Call/WhatsApp: +91-XXXXXXXXXX\n"
            "💬 Direct chat: @Lakshmi_Motorcycle_spares",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def send_message_to_user(self, telegram_id: int, message: str, **kwargs):
        """Send message to specific user"""
        try:
            parse_mode = kwargs.get('parse_mode', ParseMode.MARKDOWN)
            reply_markup = kwargs.get('reply_markup')
            
            await self.application.bot.send_message(
                chat_id=telegram_id, 
                text=message,
                parse_mode=parse_mode,
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Failed to send message to {telegram_id}: {e}")
    
    async def send_photo_to_user(self, telegram_id: int, photo, caption: str = "", **kwargs):
        """Send photo to specific user"""
        try:
            parse_mode = kwargs.get('parse_mode', ParseMode.MARKDOWN)
            reply_markup = kwargs.get('reply_markup')
            
            await self.application.bot.send_photo(
                chat_id=telegram_id,
                photo=photo,
                caption=caption,
                parse_mode=parse_mode,
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Failed to send photo to {telegram_id}: {e}")
    
    async def get_file_url(self, file_id: str) -> str:
        """Get file URL from Telegram (for image storage)"""
        try:
            file = await self.application.bot.get_file(file_id)
            return file.file_path
        except Exception as e:
            logger.error(f"Failed to get file URL: {e}")
            return ""
    
    async def upload_image_to_telegram(self, image_path: str, chat_id: int) -> str:
        """Upload image to Telegram and return file_id for storage"""
        try:
            with open(image_path, 'rb') as photo:
                message = await self.application.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo
                )
                return message.photo[-1].file_id  # Return largest photo file_id
        except Exception as e:
            logger.error(f"Failed to upload image: {e}")
            return ""
    
    def run(self):
        """Run the bot"""
        self.application.run_polling()

# Global bot instance
telegram_bot = TelegramBot()

# Helper functions for integration with your existing bot
async def send_admin_notification(order_data: dict, photo_file_id: str = None):
    """Send order notification to admin"""
    admin_id = os.getenv("ADMIN_ID")
    if not admin_id:
        return
    
    try:
        admin_id = int(admin_id)
        
        # Create order notification message
        message = f"""
💰 **NEW ORDER RECEIVED**
━━━━━━━━━━━━━━━

👤 **Customer:** {order_data.get('full_name', 'N/A')}
📞 **Phone:** {order_data.get('phone', 'N/A')}
📍 **Address:** {order_data.get('address', 'N/A')}
━━━━━━━━━━━━━━━

📦 **Items:**
"""
        
        for item in order_data.get('items', []):
            message += f"• {item.get('item')} x{item.get('qty')} - ₹{item.get('price')}\n"
        
        message += f"\n💵 **Total: ₹{order_data.get('total_amount')}**"
        
        # Create admin buttons
        keyboard = [
            [InlineKeyboardButton("✅ Approve Order", callback_data=f"approve_order:{order_data.get('id')}")],
            [InlineKeyboardButton("❌ Reject Order", callback_data=f"reject_order:{order_data.get('id')}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if photo_file_id:
            await telegram_bot.send_photo_to_user(
                telegram_id=admin_id,
                photo=photo_file_id,
                caption=message,
                reply_markup=reply_markup
            )
        else:
            await telegram_bot.send_message_to_user(
                telegram_id=admin_id,
                message=message,
                reply_markup=reply_markup
            )
            
    except Exception as e:
        logger.error(f"Failed to send admin notification: {e}")

async def send_order_confirmation(user_id: int, order_data: dict):
    """Send order confirmation to customer"""
    try:
        message = f"""
🎉 **ORDER CONFIRMED!**
━━━━━━━━━━━━━━━

🆔 **Order ID:** {order_data.get('order_id', order_data.get('id'))}
📅 **Date:** {order_data.get('created_at', 'Today')}
━━━━━━━━━━━━━━━

📦 **Items:**
"""
        
        for item in order_data.get('items', []):
            message += f"• {item.get('item')} x{item.get('qty')}\n"
        
        message += f"""
━━━━━━━━━━━━━━━
💰 **Total Amount:** ₹{order_data.get('total_amount')}
🚚 **Status:** {order_data.get('status', 'Processing')}

Your order is being processed. We'll notify you once it's shipped!

Track your order anytime with /orders command.
"""
        
        await telegram_bot.send_message_to_user(
            telegram_id=user_id,
            message=message
        )
        
    except Exception as e:
        logger.error(f"Failed to send order confirmation: {e}")

async def send_chat_notification(user_id: int, message: str, from_admin: bool = False):
    """Send chat message notification"""
    try:
        if from_admin:
            notification = f"💬 **Support Team:** {message}"
        else:
            notification = f"💬 **New message from customer:** {message}"
        
        # In a real implementation, you'd send this to the appropriate recipient
        # For now, we'll just log it
        logger.info(f"Chat notification: {notification}")
        
    except Exception as e:
        logger.error(f"Failed to send chat notification: {e}")