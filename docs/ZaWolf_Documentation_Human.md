# ZaWolf — الدليل الشامل لتوثيق بنية وهندسة المشروع (النسخة البشرية)
## ZaWolf Medical Document Processing & OCR System
**تاريخ التحديث الأخير:** سبتمبر 2026  
**بيئة التشغيل:** Local / On-Premise (Windows - Python 3.11.9)  
**المسار الأساسي للمشروع:** `E:\ZaWolf_project`

---

## 1. نظرة عامة على المشروع (Project Overview)

### ما هو مشروع ZaWolf؟
مشروع **ZaWolf** هو نظام برمجي متكامل ومحلي (Local / On-Premise) مصمم لمعالجة وأرشفة ورقمنة المستندات الطبية غير المتجانسة (Heterogeneous Medical Documents). 

يهدف النظام إلى أخذ أي ملف طبي، بأي صيغة كانت (PDF بنوعيه، صور مطبوعة أو بخط اليد، ملفات Word، أو ملفات Excel/CSV)، وتحليله واستخراج محتواه بدقة، ثم تنظيف وتوحيد البيانات عبر نموذج لغوي محلي (Local LLM)، ثم التحقق التام من صحة البيانات المعمارية عبر Pydantic، ومن ثم تخزينها داخل قاعدة بيانات علائقية SQL Server بصورة مترابطة ومتسقة وبأعلى معايير الأمان (Transactional Integrity).

### الهدف الأساسي (Core Objective)
توفير مسار موحد (Unified Ingestion Pipeline) للمستشفيات والعيادات الطبية يمكنه:
1. العمل محلياً 100% دون إرسال بيانات المرضى الحساسة لأي خدمات سحابية خارجية (Data Privacy & Compliance).
2. التعرف الآلي على صيغة ونوع الملف دون الحاجة لتحديد يدوي من المستخدم.
3. التمييز الذكي بين مستندات PDF الرقمية (Digital) والممسوحة ضوئياً (Scanned).
4. توجيه الصور لنماذج التعرف الضوئي المناسبة (OCR: مطبوع عبر PaddleOCR، وبخط اليد عبر رؤية حاسوبية متقدمة Qwen2.5-VL).
5. استخراج البيانات المنظمة وفق 19 كياناً طبياً (المرضى، الأطباء، الأدوية، الفواتير، التحاليل...).
6. منع الهلوسة الطبية (Hallucination Prevention) بواسطة حواجز أمان صارمة (Extraction Guards).
7. الحفظ الآمن في قاعدة بيانات Microsoft SQL Server مع ميزة التراجع الكامل (Rollback) في حال حدوث أي خطأ.

---

## 2. المعمارية الهندسية للنظام (System Architecture)

يعتمد المشروع على هندسة برمجية خطية ومحكمة ومقسمة إلى طبقات منفصلة (Modular Layered Architecture):

```
                     ┌─────────────────────────┐
                     │    ملف طبي من أي نوع     │
                     └────────────┬────────────┘
                                  │
                                  ▼
                     ┌─────────────────────────┐
                     │   كشف امتداد ونوع الملف  │ (File Detector)
                     └────────────┬────────────┘
                                  │
                                  ▼
                     ┌─────────────────────────┐
                     │    موجه المسارات العام   │ (Ingestion Router)
                     └──────┬─────┬─────┬─────┬┘
                            │     │     │     │
         ┌──────────────────┘     │     │     └──────────────────┐
         ▼                        ▼     ▼                        ▼
  ┌──────────────┐          ┌──────────────┐               ┌──────────────┐
  │  ملفات PDF   │          │  ملفات Word  │               │ Excel / CSV  │
  └──────┬───────┘          └──────┬───────┘               └──────┬───────┘
         │                         │                              │
 ┌───────┴────────┐                │ Direct Text                  │ Direct Data
 ▼                ▼                │                              │
[Digital PDF] [Scanned PDF]        │                              ▼
 direct text    render pages       │                     ┌──────────────────┐
     │          to images          │                     │ Structured Data  │
     │                │            │                     │  DataFrames      │
     │                ▼            │                     │  (ملخص الجداول)  │
     │         ┌──────────────┐    │                     └──────────────────┘
     │         │ الصور والرؤية│◄───┘ (Image Branch)
     │         └──────┬───────┘
     │                │
     │                ▼
     │         ┌──────────────┐
     │         │ موجه الـ OCR │ (OCR Router)
     │         └──────┬───────┘
     │                ├────────────────────────┐
     │                ▼                        ▼
     │         [PaddleOCR Engine]    [Qwen2.5-VL Handwriting]
     │         (نصوص عربية مطبوعة)   (نصوص خط اليد الطبية)
     │                │                        │
     └────────────────┼────────────────────────┘
                      │
                      ▼
               ┌──────────────┐
               │  النص الموحد │ (Raw Extracted Text)
               └──────┬───────┘
                      │
                      ▼
               ┌──────────────┐
               │  Local LLM   │ (Ollama - Qwen3 / Format: JSON)
               │  تنظيم البيانات│ قواعد طبية صارمة تمنع التخمين
               └──────┬───────┘
                      │
                      ▼
               ┌──────────────┐
               │ حارس الاستخراج│ (Extraction Guard)
               │ منع الهلوسة  │ عزل جداول الروشتات ومنع تسريب الكيانات
               └──────┬───────┘
                      │
                      ▼
               ┌──────────────┐
               │ فحص Pydantic │ (Data Validator)
               │ مطابقة الأنواع│ التحقق من بنية البيانات وتوافق الحقول
               └──────┬───────┘
                      │
                      ▼
               ┌──────────────┐
               │ تخريج العلاقات│ (Relation Resolver)
               │ DatabaseMapper ربط الـ Foreign Keys للمرضى والفروع
               └──────┬───────┘
                      │
                      ▼
               ┌──────────────┐
               │  SQL Server  │ (ZaWolfDB)
               │ عملية ذرية واحدة│ Save with Atomic Transaction / Rollback
               └──────────────┘
```

---

## 3. القواعد المعمارية الثابتة (Architectural Invariants)

1. **اكتشاف الملفات بالقواعد:** لا يتم تخمين نوع الملف عشوائياً، بل يتم الاعتماد على الامتداد الفعلي وفحص الترويسة.
2. **عزل المهام (Separation of Concerns):** المعالجات (Processors) تستخرج فقط البيانات، والـ OCR يقرأ الصور، والـ LLM ينظمها، وقاعدة البيانات هي الوحيدة التي تنشئ وتدير المفاتيح (IDs).
3. **لا OCR لملفات Word و Excel:** هذه الملفات تحتوي على بيانات ونصوص مباشرة فلا يتم إهدار موارد الجهاز في تحويلها لصور وقراءتها بالـ OCR.
4. **توحيد مسار Scanned PDF مع الصور:** صفحات الـ PDF الممسوحة ضوئياً تتحول إلى صور وتدخل فوراً مسار الصور نفسه (Image/OCR Branch) دون اختراع بنية منفصلة.
5. **النموذج اللغوي لا يخترع بيانات:** يُحظر على الـ LLM اختراع أسماء مرضى، أدوية، تواريخ، أو معرفات قاعدة بيانات غير موجودة في النص الأصلي.
6. **معاملة قاعدة بيانات ذرية (Atomic Transaction):** كل مستند يتم حفظه في قاعدة البيانات يفتح اتصالاً واحداً ومؤشراً واحداً (Cursor)، ويتم حفظ كل الجداول الـ 19 في معاملة واحدة؛ إن فشل أي جدول يتم التراجع كلياً (Rollback) لمنع أي بيانات يتيمة.

---

## 4. الهيكل الكامل للمجلدات والملفات (Folder & File Structure)

```text
E:\ZaWolf_project
│
├── config/                                 # مجلد الإعدادات العامة للمشروع
│   ├── __init__.py                         # تعريف الحزمة
│   └── settings.py                         # المسارات والحدود القصوى للذاكرة والامتدادات المدعومة
│
├── data/                                   # مجلد بيانات التشغيل
│   ├── input/                              # المستندات المدخلة للاختبار والمعالجة
│   ├── processed/                          # المخرجات الوسيطة (صفحات PDF المستخرجة كصور، إلخ)
│   └── output/                             # الملفات والتقارير المستخرجة
│
├── models/                                 # الأوزان المحلية للنماذج في حال تخزينها محلياً
├── logs/                                   # سجلات تشغيل النظام
│
├── src/                                    # الكود المصدري الأساسي للنظام
│   ├── __init__.py
│   ├── pipeline.py                         # فئة Orchestrator الأساسية (ProcessingPipeline)
│   ├── utils.py                            # أدوات إدارة الذاكرة، تقسيم النصوص وتوليد السجلات
│   │
│   ├── ingestion/                          # طبقة الاستقبال والتوجيه
│   │   ├── __init__.py
│   │   ├── file_detector.py                # التحقق من وجود الملف وامتداده
│   │   └── router.py                       # توجيه الملف للمسار المتخصص المناسب
│   │
│   ├── processors/                         # معالجات أنواع الملفات المختلفة
│   │   ├── __init__.py
│   │   ├── pdf_processor.py                # كشف نوع الـ PDF، استخراج نصوصه أو تحويله لصور
│   │   ├── image_processor.py              # فحص الصور وتعديل التباين وتصحيح التدوير EXIF
│   │   ├── word_processor.py               # قراءة ملفات docx (الفقرات والجداول)
│   │   ├── structured_processor.py         # قراءة ملفات Excel و CSV باستخدام Pandas
│   │   └── extraction_schema.py            # قوالب توحيد بيانات الاستخراج المبدئي
│   │
│   ├── ocr/                                # طبقة التعرف الضوئي على الحروف
│   │   ├── __init__.py
│   │   ├── device.py                       # كشف كارت الشاشة (CUDA) أو العمل على المعالج (CPU)
│   │   ├── ocr_engine.py                   # محرك PaddleOCR للنصوص المطبوعة
│   │   ├── handwriting_ocr.py              # محرك Qwen2.5-VL-3B لخط اليد والأدوية
│   │   ├── ocr_router.py                   # التوجيه الذكي بين محركات الـ OCR
│   │   └── ocr_utils.py                    # أدوات تنظيف النصوص وتجهيز السجلات
│   │
│   ├── llm/                                # طبقة الذكاء الاصطناعي والتنظيم
│   │   ├── __init__.py
│   │   ├── local_llm.py                    # وسيط الاتصال بـ Ollama محلياً بنسق JSON
│   │   ├── llm_schema.py                   # مخططات Pydantic للـ 19 كياناً طبياً
│   │   └── llm_processor.py                # هندسة البرومبتات الطبية وتطبيع التواريخ والأرقام
│   │
│   ├── validation/                         # طبقة التحقق الأمني والمنطقي
│   │   ├── __init__.py
│   │   ├── extraction_guard.py             # حارس استخراج الروشتات ومنع هلوسة الكيانات
│   │   └── validator.py                    # فحص مطابقة البيانات لمخطط Pydantic
│   │
│   └── database/                           # طبقة قاعدة البيانات SQL Server
│       ├── __init__.py
│       ├── database.py                     # اتصال pyodbc والعمليات الذرية
│       ├── repository.py                   # الفئة العامة للتعامل مع أي جدول (Base CRUD)
│       ├── relation_resolver.py            # البحث عن المعرفات وربط المفاتيح الأجنبية (FKs)
│       ├── mapper.py                       # الحفظ التتابعي المتكامل لكافة الجداول الـ 19
│       └── [11 ملف مستودع فرعي]           # مستودعات مخصصة للعملاء، الفواتير، المواعيد...
│
├── tests/                                  # مجلد الاختبارات الشاملة (Unit & Integration & E2E)
│   ├── test_full_system_e2e.py             # الاختبار النهائي الشامل لكافة أنواع الملفات
│   ├── test_pipeline.py                    # اختبارات تدفق البايبلاين
│   ├── test_mapper.py                      # اختبارات تخزين الجداول
│   ├── test_rollback.py                    # اختبار التراجع التام عند فشل المعاملة
│   └── ...                                 # اختبارات فرعية متخصصة
│
├── main.py                                 # ملف نقطة الدخول (Entry point)
├── requirements.txt                        # الحزم والمكتبات المطلوبة
└── PROJECT_CONTEXT.md                      # ملخص السياق المعماري
```

---

## 5. الشرح التفصيلي لملفات النظام ومسؤولياتها

### 5.1 طبقة الإعدادات والأدوات (Config & Utilities)
* **`config/settings.py`**:
  * يحدد مسارات المجلدات الرئيسية (`DATA_DIR`, `INPUT_DIR`, `PROCESSED_DIR`, `LOGS_DIR`).
  * يضبط المعايير التشغيلية: الحد الأقصى لحجم دفعة النصوص `MAX_BATCH_TEXT_SIZE = 12000` حرف، ونسبة أمان الذاكرة `BATCH_MEMORY_SAFETY_RATIO = 0.25`.
  * يحدد قائمة الامتدادات المدعومة للصور (`.jpg`, `.jpeg`, `.png`, `.webp`) والملفات (`.pdf`, `.docx`, `.xlsx`, `.csv`).
* **`src/utils.py`**:
  * فحص الذاكرة العشوائية المتاحة ديناميكياً عبر مكتبة `psutil` لحساب ميزانية الدفعة قبل المعالجة (`get_dynamic_batch_limit`).
  * تقسيم النصوص الطويلة إلى أجزاء سياقية (Contextual Chunks) بحجم 1500 حرف وتداخل 300 حرف باستخدام `RecursiveCharacterTextSplitter`.

### 5.2 طبقة الاستقبال والتوجيه (Ingestion)
* **`src/ingestion/file_detector.py`**:
  * الدالة `detect_file_type(file_path)`: تتحقق من وجود الملف فيزيائياً، وتستخرج الامتداد، وتقارنه بجدول الامتدادات المدعومة.
* **`src/ingestion/router.py`**:
  * الدالة `route_file(file_info)`: تحدد اسم المسار المتخصص المناسب: `pdf_pipeline` أو `image_pipeline` أو `excel_pipeline` أو `csv_pipeline` أو `word_pipeline`.

### 5.3 طبقة المعالجات المتخصصة (Processors)
* **`src/processors/pdf_processor.py`**:
  * `detect_pdf_type(file_path)`: يفحص صفحات الـ PDF عبر مكتبة `pymupdf / fitz`؛ فإذا وُجد نص يُصنف كـ `digital`، وإن كان خالياً من النصوص يُصنف كـ `scanned`.
  * `process_pdf_to_chunks(file_path)`: للـ PDF الرقمي، يستخرج النصوص مجمعة في دفعات وفق ميزانية الذاكرة ويقسمها لأجزاء جاهزة للـ LLM.
  * `convert_pdf_to_images(file_path, output_dir)`: للـ PDF الممسوح، يحول كل صفحة إلى صورة بدقة عالية ومصفوفة `Matrix(1,1)` ويحفظها تمهيداً لفرزها للـ OCR.
* **`src/processors/image_processor.py`**:
  * `load_and_validate_image(file_path)`: يتحقق من سلامة الصورة وعدم تلفها عبر Pillow.
  * `preprocess_image(file_path, output_path)`: يصحح اتجاه الصورة بناءً على بيانات EXIF، ويحولها لتدرج رمادي (Grayscale)، ويطبق تحسين التباين التلقائي (Auto Contrast) لزيادة دقة الـ OCR.
* **`src/processors/word_processor.py`**:
  * `extract_word_content(file_path)`: يقرأ ملفات DOCX، ويستخرج الفقرات والجداول بصورة منسقة، ثم يمررها لأداة التقطيع النصي.
* **`src/processors/structured_processor.py`**:
  * `extract_structured_data(file_info)`: يقرأ ملفات Excel بكافة أوراقها (Sheets) أو ملفات CSV عبر Pandas، محافظاً على البيانات الخام دون أي تعديل أو تنظيف مبكر.

### 5.4 طبقة التعرف الضوئي على الحروف (OCR Layer)
* **`src/ocr/device.py`**:
  * يحدد بيئة المعالجة تلقائياً (`cuda` في حال توفر كارت شاشة Nvidia يدعم PyTorch، أو `cpu`).
* **`src/ocr/ocr_engine.py`**:
  * يغلف محرك `PaddleOCR` للتعامل مع النصوص العربية والإنجليزية المطبوعة مع تعطيل mkldnn لتفادي المشاكل على معالجات معينة.
* **`src/ocr/handwriting_ocr.py`**:
  * محرك متطور جداً يعتمد على نموذج `sherif1313/Arabic-handwritten-OCR-4bit-Qwen2.5-VL-3B-v3`.
  * يستخدم تقنيات Vision-Language Models (VLM) لقراءة خط اليد في الروشتات الطبية العربية والإنجليزية ببراعة واستخراج أسماء الأدوية والجرعات.
* **`src/ocr/ocr_router.py`**:
  * يدير المحركات بأسلوب Lazy Loading؛ فلا يحمل نموذج الـ Qwen أو PaddleOCR في الذاكرة إلا عند أول طلب، ويوجه الصورة للمحرك المطلوب (`qwen` أو `paddle`).

### 5.5 طبقة الذكاء الاصطناعي والتنظيم (LLM Layer)
* **`src/llm/local_llm.py`**:
  * وسيط للتواصل مع سيرفر **Ollama** المحلي عبر الـ API (`/api/generate`)، محدد الموديل افتراضياً `qwen3:latest` مع إجبار الموديل على إخراج `format: "json"` وضبط المهلة إلى 600 ثانية.
* **`src/llm/llm_schema.py`**:
  * يحدد بنية الـ 19 كياناً عبر Pydantic مثل: `ClientData`, `StaffData`, `AppointmentData`, `MedicationData`, `VitalData`, `LabResultData`, `InvoiceData`, إلخ.
* **`src/llm/llm_processor.py`**:
  * يحوي برومبت طبي هندسي غاية في الصرامة والدقة (Strict Prompt Engineering).
  * يفرض قواعد "كتلة الدواء" (Medication Block Rule) بحيث يرتبط اسم الدواء بجرعته وتكراره دون خلط بين الأدوية.
  * يمنع ترجمة أو اختراع أسماء الأدوية.
  * يطبق دوال تطبيع (Normalization) للأرقام، والتواريخ (`YYYY-MM-DD`)، وحقول الوقت (`YYYY-MM-DD HH:MM:SS`).

### 5.6 طبقة الحماية والتحقق (Validation & Guardrails)
* **`src/validation/extraction_guard.py`**:
  * يحتوي على `ExtractionGuard`؛ إذا كان المستند عبارة عن "روشتة علاجية" (Prescription)، يقوم فوراً بتصفير أي كيانات أخرى قام الموديل بتخمينها (مثل تصفير الفواتير والمواعيد والخدمات) للحفاظ على جدول `medications` فقط ومنع الهلوسة.
  * يحذف أي سجلات فارغة كلياً قبل محاولة حفظها.
* **`src/validation/validator.py`**:
  * يتحقق من مطابقة المخرجات لمخطط `LLMExtractionResult`، ويعيد رسائل أخطاء تفصيلية واضحة في حال عدم المطابقة.

### 5.7 طبقة قاعدة البيانات (Database Layer)
* **`src/database/database.py`**:
  * يدير الاتصال بقاعدة بيانات `ZaWolfDB` على SQL Server عبر `pyodbc` ومشغل `ODBC Driver 18 for SQL Server`.
* **`src/database/repository.py`**:
  * يوفر دوال الإدخال `insert(data, cursor)` مع خاصية `OUTPUT INSERTED.id` لإرجاع المعرف التلقائي الجديد فوراً لاستخدامه كمفتاح أجنبي (FK).
* **`src/database/relation_resolver.py`**:
  * يبحث عن الكيانات الموجودة مسبقاً (مثل العميل عبر الاسم ورقم الهاتف، أو الطبيب، أو الفرع، أو الخدمة) لمنع تكرار البيانات ولربط العلاقات بشكل صحيح.
* **`src/database/mapper.py`**:
  * المكون الأكثر حساسية وأهمية في طبقة البيانات؛ ينظم ترتيب إدخال الجداول في معاملة واحدة:
    1. الفروع (Locations)
    2. الأطباء والموظفين (Staff)
    3. العملاء والمرضى (Clients)
    4. البيانات الطبية (Medical History, Vitals, Lab Results, Medications)
    5. الخدمات والمنتجات والباقات (Services, Packages, Products)
    6. المواعيد (Appointments)
    7. سجلات العلاج والجلسات (Treatment Records)
    8. الإقرارات والصور (Consents, Photos)
    9. الفواتير وبنودها والدفعات (Invoices, Invoice Items, Payments)
    10. باقات العميل والمستند المصدر (Client Packages, Source Documents).
  * في حال فشل أي إدخال لأي سبب، يتم استدعاء `connection.rollback()` تلقائياً.

### 5.8 المنسق الرئيسي (Pipeline Orchestration)
* **`src/pipeline.py` (`ProcessingPipeline`)**:
  * يربط جميع ما سبق في نقطة واحدة عبر دالتين رئيسيتين:
    - `process_file(file_path)`: لقراءة وتحليل وتجهيز البيانات والتحقق منها دون حفظ.
    - `process_and_save_file(file_path)`: لتنفيذ الدورة كاملة من الاستخراج حتى الحفظ في قاعدة البيانات وإرجاع المعرفات المدرجة.

---

## 6. الكيانات وقاعدة البيانات (Database Entities - 19 Tables)

النظام مهيأ لحفظ 19 جدولاً مترابطاً تغطي كافة عمليات المستشفيات والعيادات الطبية:

| # | اسم الكيان / الجدول | الوظيفة والمعلومات المخزنة | المفاتيح الأجنبية المرتبطة |
|---|---|---|---|
| 1 | `locations` | فروع المستشفى / العيادة (الاسم، العنوان، الهاتف) | - |
| 2 | `staff` | الطاقم الطبي والإداري (الاسم، الدور، رقم الترخيص) | `location_id` |
| 3 | `clients` | المرضى والعملاء (الاسم، تاريخ الميلاد، الهاتف، التنبيهات الطبية) | - |
| 4 | `medical_history` | التاريخ المرضي والحساسيات والعمليات السابقة | `client_id` |
| 5 | `vitals` | العلامات الحيوية (الضغط، النبض، الحرارة، الوزن) | `client_id` |
| 6 | `lab_results` | نتائج التحاليل المخبرية، القيم المقاسة والمعدل الطبيعي | `client_id` |
| 7 | `medications` | الأدوية الموصوفة، الجرعة، التكرار، والمدة | `client_id` (اختياري للروشتات العامة) |
| 8 | `services` | الخدمات الطبية والإجراءات والأسعار ومدة الجلسة | - |
| 9 | `appointments` | المواعيد، الغرفة، التوقيت، وحالة الحجز | `client_id`, `staff_id`, `location_id`, `service_id` |
| 10 | `treatment_records` | تفاصيل الجلسة والعلاج المعطى وإعدادات الأجهزة | `appointment_id`, `product_id` |
| 11 | `consents` | إقرارات وموافقات المريض وتوقيعاتها والملف المرفق | `client_id`, `appointment_id` |
| 12 | `photos` | صور الحالة الطبية قبل وبعد الإجراء | `client_id`, `treatment_id` |
| 13 | `invoices` | الفواتير، الإجمالي، الخصم، والضريبة | `client_id`, `appointment_id` |
| 14 | `invoice_items` | بنود الفاتورة الفردية والكمية وسعر الوحدة | `invoice_id` |
| 15 | `payments` | المدفوعات المسددة وطريقة الدفع والمرجع | `invoice_id` |
| 16 | `packages` | باقات العروض والجلسات المجمعة | - |
| 17 | `client_packages` | باقات المريض المشتراة وعدد الجلسات المتبقية | `client_id`, `package_id` |
| 18 | `products` | الأدوية والمستلزمات في المخزن وسعر التكلفة والبيع | - |
| 19 | `source_documents` | أرشفة المستند الأصلي، نص الـ OCR، وسجل الـ LLM بصيغة JSON | - |

---

## 7. دليل التثبيت والتشغيل (How to Run & Test)

### 7.1 متطلبات البيئة (Prerequisites)
1. **Python:** 3.11.x (المشروع مضبوط على Python 3.11.9).
2. **Microsoft SQL Server:** مثبت محلياً وقاعدة بيانات باسم `ZaWolfDB` ومفعل بها `Trusted_Connection=yes`.
3. **Ollama:** يعمل محلياً على المنفذ `http://localhost:11434` وتم تنزيل الموديل المطلوب:
   ```bash
   ollama pull qwen3:latest
   ```
4. **PyTorch & CUDA:** (اختياري ومفضل لتسريع التعرف الضوئي لخط اليد عبر بطاقة Nvidia).

### 7.2 تشغيل الاختبار الشامل للنظام (Full System E2E Test)
للتحقق من سلامة كافة المسارات لجميع أنواع الملفات السبعة في وقت واحد:
```powershell
cd E:\ZaWolf_project
.\.venv\Scripts\python tests\test_full_system_e2e.py
```

### 7.3 استخدام الـ Pipeline في كودك الخاص
```python
from pathlib import Path
from src.pipeline import ProcessingPipeline

# إنشاء نسخة من المعالج
pipeline = ProcessingPipeline(ocr_engine="qwen") # أو ocr_engine="paddle"

# معالجة ملف وحفظه في قاعدة البيانات
file_to_process = Path(r"E:\ZaWolf_project\data\input\medical_report.pdf")
result = pipeline.process_and_save_file(file_to_process)

print("الحالة:", result["status"])
print("البيانات المحفوظة:", result["inserted"])
```

---

## 8. ملاحظات تقنية وإرشادات التطوير المستقبلي

1. **ملف `main.py`:** في مرحلة التطوير المبكرة كان يستدعي دالة قديمة `run_pipeline`؛ يُنصح بتحديثه دائماً ليستدعي الفئة الحديثة `ProcessingPipeline`.
2. **تحذير `fitz`:** يظهر تحذير أحياناً بخصوص مكتبة PyMuPDF (`fitz API is deprecated`)، وهو مجرد تنبيه شكلي لا يؤثر على نجاح المعالجة.
3. **أمان البيانات الطبية:** تأكد دائماً من وجود `.env` و `.venv` وملفات الصور الحقيقية للمرضى داخل ملف `.gitignore` لحماية البيانات قبل أي رفع على GitHub.
