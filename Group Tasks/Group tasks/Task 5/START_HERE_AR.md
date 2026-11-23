# التشغيل والتسليم

المشروع ده تكملة Week 7 لتاسك 5، وملفات Terraform لتاسك 6 في `infra/terraform`.

## تاسك 5

1. افتحي Terminal في فولدر Task 5 اللي فيه `api.py`.
2. استخدمي Python 3.11 أو 3.12 واعملي بيئة جديدة:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-task5.txt
Copy-Item app.env.example app.env
```

3. افتحي `app.env` وحطي مفتاح OpenRouter بتاعك. خلي `APP_MODE=llm` لتشغيل الـRetriever والـAnalyst والـAnswer Agent الأصليين. لو عاوزة تجربة من غير مفتاح خلي `APP_MODE=extractive`: الوضع ده بيرجع نصوص المصادر المطابقة، ومش بيعمل تحليل LLM.
4. شغّلي:

```powershell
python -m uvicorn api:app --host 127.0.0.1 --port 8000 --workers 1
```

5. افتحي `http://127.0.0.1:8000`. ارفعي مستند واسألي، أو جرّبي `samples/sales_image.png` مع سؤال `What is the total revenue?`. تقدري ترفعي `samples/question.wav` أو تسجّلي من الميكروفون.
6. اختاري تصميم التقرير وحمّلي الـPDF. الصوت التجريبي مولّد آليًا، مش تسجيل حد من التيم. OCR الحالي للنص اللاتيني/الصيني؛ مش بيدعم الصور العربية.

أول تشغيل بيحتاج إنترنت لتحميل موديلات الصوت والـretrieval. ملف المفتاح `app.env` ما يترفعش على GitHub.

## تاسك 6

افتحي Terminal في Task 6 وشغّلي `python verify.py` بعد تثبيت Terraform، أو اتبعي أوامر الـREADME. نتائج التنفيذ الفعلية موجودة في `evidence`. خطة AWS اتجهزت من غير إنشاء موارد؛ ما تشغّليش `terraform apply`.

## التسليم

احتفظي بالمصدر والـREADME والاختبارات والعينات والتقارير وسجلات التحقق. تقسيم الموديولات Person A/B/C موجود في `TEAM_ROLES.md`، وهو تقسيم مسؤوليات، مش سجل مشاركة فردي. مشروع الـVoice Agents المنفصل لسه خارج الحزمة.
