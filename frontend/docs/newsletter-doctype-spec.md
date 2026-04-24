# HR Newsletter Doctype Spec

این سند مشخصات دیتامدل پیشنهادی برای خبرنامه داخلی را تعریف می‌کند تا فرانت‌اند `frontend/src/views/newsletter` به‌صورت کامل کار کند.

## 1) Doctype: `HR Newsletter`

### هدف
نگه‌داری اطلاعیه/خبرنامه سازمانی با قابلیت پیش‌نویس، زمان‌بندی انتشار، انتشار فوری، هدف‌گیری مخاطب، و گزارش مطالعه.

### فیلدهای اصلی
- `title` (Data, reqd)
- `summary` (Small Text)
- `content` (Text Editor / Long Text)
- `cover_image` (Attach Image)
- `cover_caption` (Data)
- `status` (Select: `Draft`, `Scheduled`, `Published`, `Cancelled`)
- `scheduled_publish_at` (Datetime)
- `published_on` (Datetime)
- `expires_on` (Datetime)
- `audience_mode` (Select: `All Employees`, `By Role`, `Specific Employees`)
- `target_roles_json` (Long Text: JSON array)
- `target_employees_json` (Long Text: JSON array)
- `excluded_employees_json` (Long Text: JSON array برای حالت `By Role`)
- `send_push_notification` (Check)
- `recipient_count` (Int, read only)
- `read_count` (Int, read only)
- `unread_count` (Int, read only)
- `read_rate` (Percent, read only)

## 2) Doctype: `HR Newsletter Receipt`

### هدف
ثبت وضعیت مشاهده هر خبرنامه برای هر کارمند.

### فیلدها
- `newsletter` (Link -> `HR Newsletter`, reqd)
- `employee` (Link -> `Employee`, reqd)
- `employee_name` (Data)
- `designation` (Data)
- `is_read` (Check)
- `read_on` (Datetime)
- `delivery_channel` (Select: `In-App`, `Push`, `Email`)

### ایندکس‌های پیشنهادی
- Unique: (`newsletter`, `employee`)
- Index: (`newsletter`, `is_read`)

## 3) Poll Doctypes

### `HR Newsletter Poll`
- `newsletter` (Link -> `HR Newsletter`)
- `question` (Data)
- `allow_multiple` (Check)
- `is_private` (Check)
- `show_voters` (Check)
- `placeholder_token` (Data, read only) مانند `[[POLL:NWP-2026-00001]]`
- `options` (Table -> `HR Newsletter Poll Option`)

### `HR Newsletter Poll Option` (Child Table)
- `option_text` (Data)

### `HR Newsletter Poll Vote`
- `newsletter` (Link)
- `poll` (Link -> `HR Newsletter Poll`)
- `employee` (Link -> `Employee`)
- `employee_name` (Data)
- `option` (Data)

## 4) API Contract موردنیاز فرانت‌اند

### `hrms.api.newsletter.get_newsletter_dashboard_context`
- خروجی:
  - `employee_newsletters[]`
  - `managed_newsletters[]`
  - `stats: { total_sent, published, scheduled, read_count, unread_count }`

### `hrms.api.newsletter.get_newsletter_audience_options`
- خروجی:
  - `roles[]`
  - `role_options[]` شامل `value`, `label`
  - `employees[]` شامل `name`, `employee_name`

### `hrms.api.newsletter.get_newsletter_detail`
- ورودی: `newsletter_name`
- خروجی:
  - `newsletter` شامل محتوای کامل + `attachments[]` + `polls[]`

### `hrms.api.newsletter.upsert_newsletter`
- ورودی: `payload` (JSON string)
- خروجی: داکیومنت ذخیره‌شده خبرنامه

### `hrms.api.newsletter.mark_newsletter_read`
- ورودی: `newsletter_name`
- خروجی: success + receipt row

### `hrms.api.newsletter.get_newsletter_report`
- ورودی: `newsletter_name`
- خروجی:
  - `newsletter`
  - `stats: { recipient_count, read_count, unread_count, read_rate }`
  - `recipients[]`
  - `by_role[]`

### `hrms.api.newsletter.submit_poll_vote`
- ورودی: `newsletter_name`, `poll_name`, `selected_options[]`
- خروجی:
  - `poll` نسخه به‌روز شده نظرسنجی

## 5) منطق زمان‌بندی انتشار

- اگر `status = Scheduled` و زمان `scheduled_publish_at` رسید:
  - `status` به `Published` تغییر کند
  - رکوردهای `HR Newsletter Receipt` بر اساس مخاطبین ساخته شود
  - در صورت فعال بودن `send_push_notification` اعلان ارسال شود

## 6) مخاطب‌یابی (Targeting)

- `All Employees`: همه کارکنان فعال
- `By Role`: کارکنانی که نقش کاربری آن‌ها در `target_roles_json` باشد
  - امکان استثنا: `excluded_employees_json` برای حذف کارمندهای خاص از همین گروه
- `Specific Employees`: کارکنان انتخاب‌شده در `target_employees_json`
