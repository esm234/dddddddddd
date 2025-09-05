#!/usr/bin/env python3
"""
Telegram Bot for HTML Question Extraction
بوت تليجرام لاستخراج الأسئلة من ملفات HTML
"""

import os
import json
import logging
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

📋 هذا البوت يساعدك في استخراج الأسئلة من ملفات HTML وحفظها في ملفات JSON

📤 أرسل ملف HTML لبدء الاستخراج
        """
        await update.message.reply_text(welcome_text)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help command handler"""
        help_text = """
🆘 مساعدة البوت:

1️⃣ أرسل ملف HTML
2️⃣ اختر نوع القسم من القائمة
3️⃣ احصل على ملف JSON بالأسئلة المستخرجة

📝 الأقسام المدعومة:
• التناظر اللفظي
• إكمال الجمل
• استيعاب المقروء
• الخطأ السياقي
• المفردة الشاذة
        """
        await update.message.reply_text(help_text)
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle HTML file uploads"""
        try:
            user_id = update.effective_user.id
            document = update.message.document
            
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
                'file_name': document.file_name
            }
            
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
            
            # Process the file
            file_info = self.user_sessions[user_id]
            file_path = file_info['file_path']
            file_name = file_info['file_name']
            
            # Create new parser instance for each file to avoid merging
            parser = HTMLResultsParser()
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
                file_path = self.user_sessions[user_id]['file_path']
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                output_path = f"output_{user_id}_{self.user_sessions[user_id]['file_name'].replace('.html', '.json')}"
                if os.path.exists(output_path):
                    os.remove(output_path)
                
                del self.user_sessions[user_id]
        except Exception as e:
            logger.error(f"Error cleaning up files: {e}")

def main():
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
    application.add_handler(CallbackQueryHandler(bot.handle_category_selection, pattern="^cat_"))
    
    # Start the bot
    logger.info("Starting bot...")
    application.run_polling()

if __name__ == "__main__":
    main()
