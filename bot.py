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
        
        # Create main menu keyboard
        keyboard = [
            [InlineKeyboardButton("📄 استخراج من HTML", callback_data="extract_html")],
            [InlineKeyboardButton("🔗 دمج ملفات JSON", callback_data="merge_files")],
            [InlineKeyboardButton("❓ مساعدة", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help command handler"""
        help_text = """
🆘 مساعدة البوت:

📄 استخراج من HTML:
1️⃣ أرسل ملف HTML
2️⃣ اختر نوع القسم من القائمة
3️⃣ احصل على ملف JSON بالأسئلة المستخرجة

🔗 دمج ملفات JSON:
1️⃣ أرسل ملفات JSON متعددة
2️⃣ اختر الملفات المراد دمجها
3️⃣ احصل على ملف JSON موحد ومرتب

📝 الأقسام المدعومة:
• التناظر اللفظي
• إكمال الجمل
• استيعاب المقروء
• الخطأ السياقي
• المفردة الشاذة
        """
        await update.message.reply_text(help_text)
    
    async def handle_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle main menu selections"""
        try:
            query = update.callback_query
            await query.answer()
            
            if query.data == "extract_html":
                await query.edit_message_text(
                    "📄 أرسل ملف HTML لبدء الاستخراج",
                    reply_markup=None
                )
            elif query.data == "merge_files":
                await self.start_merge_process(update, context)
            elif query.data == "help":
                await self.help_command(update, context)
                
        except Exception as e:
            logger.error(f"Error handling main menu: {e}")
            await query.edit_message_text("❌ حدث خطأ في معالجة الطلب")
    
    async def start_merge_process(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start the merge files process"""
        user_id = update.effective_user.id
        
        # Initialize merge session
        self.user_sessions[user_id] = {
            'mode': 'merge',
            'files': [],
            'file_paths': []
        }
        
        text = """
🔗 دمج ملفات JSON

📤 أرسل ملفات JSON التي تريد دمجها
📝 يمكنك إرسال عدة ملفات في نفس الوقت

✅ بعد إرسال جميع الملفات، اضغط على "دمج الملفات"
        """
        
        keyboard = [
            [InlineKeyboardButton("✅ دمج الملفات", callback_data="execute_merge")],
            [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_merge")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle file uploads (HTML or JSON)"""
        try:
            user_id = update.effective_user.id
            document = update.message.document
            file_extension = document.file_name.lower().split('.')[-1]
            
            # Check if user is in merge mode
            if user_id in self.user_sessions and self.user_sessions[user_id].get('mode') == 'merge':
                if file_extension == 'json':
                    await self.handle_json_upload(update, context)
                else:
                    await update.message.reply_text("❌ في وضع الدمج، يرجى إرسال ملفات JSON فقط")
                return
            
            # Check if file is HTML for extraction mode
            if file_extension != 'html':
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
                'mode': 'extract'
            }
            
            # Show category selection
            await self.show_category_selection(update, context)
            
        except Exception as e:
            logger.error(f"Error handling document: {e}")
            await update.message.reply_text("❌ حدث خطأ في معالجة الملف")
    
    async def handle_json_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle JSON file uploads for merging"""
        try:
            user_id = update.effective_user.id
            document = update.message.document
            
            # Download file
            file = await context.bot.get_file(document.file_id)
            file_path = f"temp_{user_id}_{document.file_name}"
            
            await file.download_to_drive(file_path)
            
            # Add to merge session
            if user_id in self.user_sessions and self.user_sessions[user_id].get('mode') == 'merge':
                self.user_sessions[user_id]['files'].append(document.file_name)
                self.user_sessions[user_id]['file_paths'].append(file_path)
                
                files_count = len(self.user_sessions[user_id]['files'])
                await update.message.reply_text(
                    f"✅ تم إضافة الملف: {document.file_name}\n"
                    f"📊 إجمالي الملفات: {files_count}"
                )
            else:
                await update.message.reply_text("❌ يرجى البدء بعملية الدمج أولاً")
                
        except Exception as e:
            logger.error(f"Error handling JSON upload: {e}")
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
    
    async def execute_merge(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Execute the merge process"""
        try:
            query = update.callback_query
            await query.answer()
            
            user_id = update.effective_user.id
            
            if user_id not in self.user_sessions or self.user_sessions[user_id].get('mode') != 'merge':
                await query.edit_message_text("❌ لا توجد جلسة دمج نشطة")
                return
            
            files = self.user_sessions[user_id].get('files', [])
            file_paths = self.user_sessions[user_id].get('file_paths', [])
            
            if len(files) < 2:
                await query.edit_message_text("❌ تحتاج إلى ملفين JSON على الأقل للدمج")
                return
            
            # Show processing message
            await query.edit_message_text("⏳ جاري دمج الملفات...")
            
            # Merge files
            merged_questions = await self.merge_json_files(file_paths)
            
            if not merged_questions:
                await query.edit_message_text("❌ فشل في دمج الملفات")
                return
            
            # Generate output filename
            output_filename = f"merged_questions_{len(merged_questions)}_questions.json"
            
            # Save merged questions to JSON
            output_path = f"output_{user_id}_{output_filename}"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(merged_questions, f, ensure_ascii=False, indent=2)
            
            # Send results
            result_text = f"""
✅ تم دمج الملفات بنجاح!

📊 إحصائيات:
• عدد الملفات المدمجة: {len(files)}
• إجمالي الأسئلة: {len(merged_questions)}
• اسم الملف: {output_filename}

📝 الملفات المدمجة:
{chr(10).join([f"• {file}" for file in files])}
            """
            
            await query.edit_message_text(result_text)
            
            # Send merged JSON file
            with open(output_path, 'rb') as f:
                await context.bot.send_document(
                    chat_id=user_id,
                    document=f,
                    filename=output_filename,
                    caption=f"📄 ملف الأسئلة المدمجة - {len(merged_questions)} سؤال"
                )
            
            # Clean up temporary files
            self.cleanup_merge_files(user_id)
            
        except Exception as e:
            logger.error(f"Error executing merge: {e}")
            await query.edit_message_text("❌ حدث خطأ في دمج الملفات")
    
    async def cancel_merge(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel merge process"""
        try:
            query = update.callback_query
            await query.answer()
            
            user_id = update.effective_user.id
            
            if user_id in self.user_sessions and self.user_sessions[user_id].get('mode') == 'merge':
                self.cleanup_merge_files(user_id)
            
            await query.edit_message_text("❌ تم إلغاء عملية الدمج")
            
        except Exception as e:
            logger.error(f"Error canceling merge: {e}")
            await query.edit_message_text("❌ حدث خطأ في إلغاء العملية")
    
    async def merge_json_files(self, file_paths: list) -> list:
        """Merge multiple JSON files and renumber questions"""
        try:
            all_questions = []
            question_number = 1
            
            for file_path in file_paths:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        questions = json.load(f)
                    
                    # Ensure questions is a list
                    if not isinstance(questions, list):
                        questions = [questions] if questions else []
                    
                    # Renumber questions and add to merged list
                    for question in questions:
                        if isinstance(question, dict) and 'question' in question:
                            question_copy = question.copy()
                            question_copy['question_number'] = question_number
                            all_questions.append(question_copy)
                            question_number += 1
                            
                except Exception as e:
                    logger.error(f"Error reading file {file_path}: {e}")
                    continue
            
            return all_questions
            
        except Exception as e:
            logger.error(f"Error merging JSON files: {e}")
            return []
    
    def cleanup_merge_files(self, user_id: int):
        """Clean up merge session files"""
        try:
            if user_id in self.user_sessions and self.user_sessions[user_id].get('mode') == 'merge':
                # Clean up individual files
                for file_path in self.user_sessions[user_id].get('file_paths', []):
                    if os.path.exists(file_path):
                        os.remove(file_path)
                
                # Clean up output file
                files_count = len(self.user_sessions[user_id].get('files', []))
                output_path = f"output_{user_id}_merged_questions_{files_count}_questions.json"
                if os.path.exists(output_path):
                    os.remove(output_path)
                
                del self.user_sessions[user_id]
        except Exception as e:
            logger.error(f"Error cleaning up merge files: {e}")
    
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
    application.add_handler(CallbackQueryHandler(bot.handle_main_menu, pattern="^(extract_html|merge_files|help)$"))
    application.add_handler(CallbackQueryHandler(bot.execute_merge, pattern="^execute_merge$"))
    application.add_handler(CallbackQueryHandler(bot.cancel_merge, pattern="^cancel_merge$"))
    
    # Start the bot
    logger.info("Starting bot...")
    application.run_polling()

if __name__ == "__main__":
    main()
