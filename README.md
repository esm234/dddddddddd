# Google Forms Quiz Scrapers

مجموعة من السكريبتات لاستخراج الأسئلة والإجابات الصحيحة من نماذج Google Forms (الاختبارات).

## التثبيت

```bash
# تثبيت المكتبات المطلوبة
pip install -r requirements.txt

# تثبيت متصفحات Playwright
playwright install
```

## السكريبتات المتاحة

### 1. `scrape_form.py` - السكريبت الكامل
يأخذ رابط النموذج ويقوم بالعملية كاملة من البداية للنهاية.

```bash
python scrape_form.py --url "رابط_النموذج" --output "النتائج.json" --headless true
```

### 2. `parse_results.py` - محلل صفحة النتائج
يأخذ رابط صفحة النتائج مباشرة ويستخرج الأسئلة والإجابات.

```bash
python parse_results.py --url "رابط_صفحة_النتائج" --output "النتائج.json" --headless true
```

### 3. `parse_html.py` - محلل HTML
يأخذ ملف HTML محفوظ ويستخرج الأسئلة والإجابات.

```bash
python parse_html.py --html "ملف.html" --output "النتائج.json"
```

## الاستخدام الموصى به

### الطريقة الأولى: مع رابط صفحة النتائج
```bash
# احفظ صفحة النتائج كـ HTML
# ثم استخدم:
python parse_html.py --html "results.html" --output "quiz_results.json"
```

### الطريقة الثانية: مع رابط صفحة النتائج مباشرة
```bash
python parse_results.py --url "https://docs.google.com/forms/d/e/..." --output "quiz_results.json" --headless false
```

## تنسيق الإخراج

```json
[
  {
    "question_number": 1,
    "question": "غابة : أسد",
    "type": "اختيار",
    "choices": ["عش : عصفور", "سفينة : قبطان", "نهر : رمل", "طائرة : مسافر"],
    "answer": "عش : عصفور",
    "exam": "الاختبار الأول (التناظر اللفظي) (البنك الثاني)",
    "category": ""
  }
]
```

## ملاحظات

- السكريبتات مصممة للعمل مع نماذج Google Forms باللغة العربية
- تتعامل مع أسئلة الاختيار من متعدد (radio buttons)
- `parse_html.py` لا يحتاج Playwright - أسرع للاستخدام
- `parse_results.py` يحتاج Playwright للوصول للصفحة
- `scrape_form.py` يقوم بالعملية كاملة من البداية
