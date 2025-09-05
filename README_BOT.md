# Telegram Bot for HTML Question Extraction
## بوت تليجرام لاستخراج الأسئلة من ملفات HTML

### المميزات
- 📤 استقبال ملفات HTML عبر تليجرام
- 📋 اختيار نوع القسم من قائمة منسدلة
- 🔄 استخراج الأسئلة تلقائياً
- 📄 إرسال النتائج كملف JSON
- 🌐 يعمل على Render

### الأقسام المدعومة
1. التناظر اللفظي
2. إكمال الجمل
3. استيعاب المقروء
4. الخطأ السياقي
5. المفردة الشاذة

### كيفية الاستخدام
1. أرسل `/start` لبدء البوت
2. أرسل ملف HTML
3. اختر نوع القسم من القائمة
4. احصل على ملف JSON بالأسئلة المستخرجة

### التثبيت على Render

#### 1. إعداد المتغيرات البيئية
```
BOT_TOKEN=your_telegram_bot_token
```

#### 2. رفع الملفات
- `bot.py` - ملف البوت الرئيسي
- `parse_html.py` - ملف استخراج الأسئلة
- `requirements_bot.txt` - المكتبات المطلوبة
- `Procfile` - ملف تشغيل Render

#### 3. إعدادات Render
- **Build Command**: `pip install -r requirements_bot.txt`
- **Start Command**: `python bot.py`
- **Environment**: Python 3

### الملفات المطلوبة
```
├── bot.py                 # البوت الرئيسي
├── parse_html.py          # استخراج الأسئلة
├── requirements_bot.txt   # المكتبات
├── Procfile              # ملف Render
└── README_BOT.md         # هذا الملف
```

### الحصول على BOT_TOKEN
1. اذهب إلى [@BotFather](https://t.me/botfather)
2. أرسل `/newbot`
3. اختر اسم للبوت
4. احصل على التوكن
5. ضع التوكن في متغيرات Render

### التشغيل المحلي
```bash
# تثبيت المكتبات
pip install -r requirements_bot.txt

# تشغيل البوت (التوكن مضمن في الكود)
python bot.py

# أو استخدام ملف الاختبار
python test_bot.py
```

### اختبار البوت
البوت جاهز للاختبار! يمكنك:
1. البحث عن البوت على تليجرام
2. إرسال `/start`
3. إرسال ملف HTML
4. اختيار نوع القسم
5. الحصول على ملف JSON
