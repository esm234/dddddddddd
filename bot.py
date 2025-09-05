#!/usr/bin/env python3
"""
Telegram Bot for HTML Question Extraction
بوت تليجرام لاستخراج الأسئلة من ملفات HTML
"""

import os
import json
import logging
import asyncio
import requests
from typing import Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from parse_html import HTMLResultsParser

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', '7936685638:AAEoXoyLbdH6aYpVI6M4WXhCai4_fJ8vs-0')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

# Categories dictionary
CATEGORIES = {
    "1": "التناظر اللفظي",
    "2": "إكمال الجمل", 
    "3": "استيعاب المقروء",
    "4": "الخطأ السياقي",
    "5": "المفردة الشاذة"
}

class QuestionExtractionBot:
    def __init__(self):
        self.user_sessions = {}  # Store user sessions
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command handler"""
        welcome_text = """
🎓 أهلاً بك في بوت استخراج الأسئلة من HTML

📋 هذا البوت يساعدك في استخراج الأسئلة من ملفات HTML أو روابط صفحات النتائج

📤 اختر طريقة الإدخال:
        """
        
        # Create main menu keyboard
        keyboard = [
            [InlineKeyboardButton("📄 إرسال ملف HTML", callback_data="upload_html")],
            [InlineKeyboardButton("🔗 إرسال رابط صفحة النتائج", callback_data="upload_url")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help command handler"""
        help_text = """
🆘 مساعدة البوت:

📤 طرق الإدخال:
1️⃣ إرسال ملف HTML
2️⃣ إرسال رابط صفحة النتائج

📋 خطوات الاستخراج:
1️⃣ اختر طريقة الإدخال
2️⃣ أرسل الملف أو الرابط
3️⃣ اختر نوع القسم من القائمة
4️⃣ احصل على ملف JSON بالأسئلة المستخرجة

📝 الأقسام المدعومة:
• التناظر اللفظي
• إكمال الجمل
• استيعاب المقروء
• الخطأ السياقي
• المفردة الشاذة
        """
        await update.message.reply_text(help_text)
    
    async def handle_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle main menu selection"""
        try:
            query = update.callback_query
            await query.answer()
            
            if query.data == "upload_html":
                await query.edit_message_text(
                    "📄 أرسل ملف HTML الآن\n\n"
                    "يجب أن يكون الملف بصيغة .html"
                )
                # Set user state to expect HTML file
                context.user_data['expecting'] = 'html_file'
                
            elif query.data == "upload_url":
                await query.edit_message_text(
                    "🔗 أرسل رابط صفحة النتائج الآن\n\n"
                    "مثال: https://forms.gle/example"
                )
                # Set user state to expect URL
                context.user_data['expecting'] = 'url'
                
        except Exception as e:
            logger.error(f"Error handling main menu: {e}")
            await query.edit_message_text("❌ حدث خطأ في معالجة الطلب")
    
    async def handle_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle URL input"""
        try:
            user_id = update.effective_user.id
            url = update.message.text.strip()
            
            # Validate URL
            if not url.startswith(('http://', 'https://')):
                await update.message.reply_text("❌ يرجى إرسال رابط صحيح يبدأ بـ http:// أو https://")
                return
            
            # Show processing message
            processing_msg = await update.message.reply_text("⏳ جاري جلب محتوى الصفحة...")
            
            try:
                # Fetch HTML content from URL
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                
                html_content = response.text
                
                # Update processing message
                await processing_msg.edit_text("⏳ تم جلب المحتوى بنجاح! جاري معالجة البيانات...")
                
                # Store HTML content in user session
                self.user_sessions[user_id] = {
                    'html_content': html_content,
                    'source': 'url',
                    'url': url
                }
                
                # Show category selection
                await self.show_category_selection(update, context)
                
            except requests.RequestException as e:
                await processing_msg.edit_text(f"❌ خطأ في جلب المحتوى من الرابط: {str(e)}")
                return
                
        except Exception as e:
            logger.error(f"Error handling URL: {e}")
            await update.message.reply_text("❌ حدث خطأ في معالجة الرابط")
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages (URLs)"""
        if context.user_data.get('expecting') == 'url':
            await self.handle_url(update, context)
        else:
            await update.message.reply_text(
                "❌ يرجى استخدام القائمة الرئيسية أولاً\n"
                "اضغط /start لبدء الاستخدام"
            )
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle HTML file uploads"""
        try:
            user_id = update.effective_user.id
            document = update.message.document
            
            # Check if user is expecting HTML file
            if context.user_data.get('expecting') != 'html_file':
                await update.message.reply_text(
                    "❌ يرجى استخدام القائمة الرئيسية أولاً\n"
                    "اضغط /start لبدء الاستخدام"
                )
                return
            
            # Check if file is HTML
            if not document.file_name.lower().endswith('.html'):
                await update.message.reply_text("❌ يرجى إرسال ملف HTML فقط")
                return
            
            # Download file
            file = await context.bot.get_file(document.file_id)
            file_path = f"temp_{user_id}_{document.file_name}"
            
            await file.download_to_drive(file_path)
            
            # Store file info in user session
            self.user_sessions[user_id] = {
                'file_path': file_path,
                'file_name': document.file_name,
                'source': 'file'
            }
            
            # Clear expecting state
            context.user_data.pop('expecting', None)
            
            # Show category selection
            await self.show_category_selection(update, context)
            
        except Exception as e:
            logger.error(f"Error handling document: {e}")
            await update.message.reply_text("❌ حدث خطأ في معالجة الملف")
    
    async def show_category_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show category selection keyboard"""
        keyboard = []
        for key, value in CATEGORIES.items():
            keyboard.append([InlineKeyboardButton(f"{key}. {value}", callback_data=f"cat_{key}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = """
📋 اختر نوع القسم:

1️⃣ التناظر اللفظي
2️⃣ إكمال الجمل
3️⃣ استيعاب المقروء
4️⃣ الخطأ السياقي
5️⃣ المفردة الشاذة
        """
        
        await update.message.reply_text(text, reply_markup=reply_markup)
    
    async def handle_category_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle category selection"""
        try:
            query = update.callback_query
            await query.answer()
            
            user_id = update.effective_user.id
            category_key = query.data.split('_')[1]
            category = CATEGORIES[category_key]
            
            if user_id not in self.user_sessions:
                await query.edit_message_text("❌ انتهت صلاحية الجلسة. يرجى إرسال الملف مرة أخرى")
                return
            
            # Show processing message
            await query.edit_message_text("⏳ جاري معالجة الملف...")
            
            # Process the file or URL content
            file_info = self.user_sessions[user_id]
            
            # Create new parser instance for each file to avoid merging
            parser = HTMLResultsParser()
            
            if file_info['source'] == 'url':
                # Process HTML content from URL
                html_content = file_info['html_content']
                questions = parser.parse_html_content_from_string(html_content, category)
                file_name = "results_from_url.html"
            else:
                # Process HTML file
                file_path = file_info['file_path']
                file_name = file_info['file_name']
                questions = parser.parse_html_file(file_path, category)
            
            if not questions:
                await query.edit_message_text("❌ لم يتم العثور على أسئلة في الملف")
                return
            
            # Generate output filename
            output_filename = file_name.replace('.html', '.json')
            
            # Save questions to JSON
            output_path = f"output_{user_id}_{output_filename}"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(questions, f, ensure_ascii=False, indent=2)
            
            # Send results
            result_text = f"""
✅ تم استخراج الأسئلة بنجاح!

📊 إحصائيات:
• عدد الأسئلة: {len(questions)}
• نوع القسم: {category}
• اسم الملف: {output_filename}
            """
            
            await query.edit_message_text(result_text)
            
            # Send JSON file
            with open(output_path, 'rb') as f:
                await context.bot.send_document(
                    chat_id=user_id,
                    document=f,
                    filename=output_filename,
                    caption=f"📄 ملف الأسئلة المستخرجة - {category}"
                )
            
            # Clean up temporary files
            self.cleanup_files(user_id)
            
        except Exception as e:
            logger.error(f"Error processing category selection: {e}")
            await query.edit_message_text("❌ حدث خطأ في معالجة الملف")
    
    def cleanup_files(self, user_id: int):
        """Clean up temporary files"""
        try:
            if user_id in self.user_sessions:
                file_info = self.user_sessions[user_id]
                
                # Only clean up file if it was uploaded (not from URL)
                if file_info['source'] == 'file' and 'file_path' in file_info:
                    file_path = file_info['file_path']
                    if os.path.exists(file_path):
                        os.remove(file_path)
                
                # Clean up output file
                if file_info['source'] == 'url':
                    output_filename = "results_from_url.json"
                else:
                    output_filename = file_info['file_name'].replace('.html', '.json')
                
                output_path = f"output_{user_id}_{output_filename}"
                if os.path.exists(output_path):
                    os.remove(output_path)
                
                del self.user_sessions[user_id]
        except Exception as e:
            logger.error(f"Error cleaning up files: {e}")

async def main():
    """Main function to run the bot"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not found in environment variables")
        return
    
    # Create bot instance
    bot = QuestionExtractionBot()
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(MessageHandler(filters.Document.ALL, bot.handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_text_message))
    application.add_handler(CallbackQueryHandler(bot.handle_main_menu, pattern="^(upload_html|upload_url)$"))
    application.add_handler(CallbackQueryHandler(bot.handle_category_selection, pattern="^cat_"))
    
    # Get port from environment variable (Render sets this)
    port = int(os.getenv('PORT', 8000))
    
    # Start the bot
    logger.info(f"Starting bot on port {port}...")
    
    # For Render deployment, we need to run both polling and a web server
    # This creates a simple web server that Render can detect
    from aiohttp import web
    
    async def health_check(request):
        return web.Response(text="Bot is running", status=200)
    
    # Create web app for health checks
    web_app = web.Application()
    web_app.router.add_get('/', health_check)
    web_app.router.add_get('/health', health_check)
    
    # Start web server
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    # Start bot polling
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    # Keep running
    try:
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
