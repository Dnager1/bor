# 🔧 Environment Variable Setup Guide
# دليل إعداد متغيرات البيئة

<div dir="rtl">

## 📋 نظرة عامة | Overview

يدعم البوت طريقتين لتعيين متغيرات البيئة:

The bot supports two methods for setting environment variables:

1. **ملف .env** - `.env` file (for local development and traditional hosting)
2. **متغيرات البيئة النظامية** - System environment variables (for Docker, Pterodactyl, and modern hosting platforms)

---

## ✅ متغيرات البيئة المطلوبة | Required Environment Variables

### المطلوب دائماً | Always Required:

```env
DISCORD_BOT_TOKEN=your_bot_token_here
```

### اختياري | Optional:

```env
GUILD_ID=your_server_id
OWNER_ID=your_discord_user_id
ADMIN_ROLE_ID=role_id
MODERATOR_ROLE_ID=role_id
LOG_CHANNEL_ID=channel_id
ANNOUNCEMENT_CHANNEL_ID=channel_id
MAX_ACTIVE_BOOKINGS=5
LANGUAGE=ar
TIMEZONE=Asia/Riyadh
REMINDER_24H=true
REMINDER_1H=true
REMINDER_NOW=true
AUTO_BACKUP_HOURS=6
```

---

## 📁 الطريقة الأولى: ملف .env | Method 1: .env File

### للتطوير المحلي أو VPS | For Local Development or VPS

1. **نسخ ملف المثال:**
   ```bash
   cp .env.example .env
   ```

2. **تعديل الملف:**
   ```bash
   nano .env
   # أو استخدم أي محرر نصوص
   ```

3. **إضافة التوكن:**
   ```env
   DISCORD_BOT_TOKEN=your_actual_token_here
   GUILD_ID=123456789
   OWNER_ID=987654321
   ```

4. **حفظ الملف وتشغيل البوت:**
   ```bash
   python bot.py
   ```

---

## 🐳 الطريقة الثانية: متغيرات البيئة النظامية | Method 2: System Environment Variables

### لـ Docker أو Pterodactyl أو منصات الاستضافة | For Docker, Pterodactyl, or Hosting Platforms

هذه الطريقة مفضلة للبيئات التالية:
- Docker Containers
- Pterodactyl Panel
- Railway, Heroku, Render
- WispByte (with environment variables)
- أي منصة استضافة حديثة

#### A) Docker Compose

```yaml
version: '3.8'
services:
  discord-bot:
    build: .
    environment:
      - DISCORD_BOT_TOKEN=your_token_here
      - GUILD_ID=123456789
      - OWNER_ID=987654321
    # Or use env_file:
    # env_file:
    #   - .env
```

#### B) Docker Run

```bash
docker run -d \
  -e DISCORD_BOT_TOKEN=your_token_here \
  -e GUILD_ID=123456789 \
  -e OWNER_ID=987654321 \
  discord-bot
```

#### C) Pterodactyl Panel

في لوحة التحكم:
1. اذهب إلى **Startup**
2. اضغط **Environment Variables** أو **Variables**
3. أضف المتغيرات:
   - Variable: `DISCORD_BOT_TOKEN`
   - Value: `your_token_here`
4. احفظ وأعد تشغيل البوت

#### D) Railway / Heroku / Render

في لوحة التحكم:
1. اذهب إلى **Settings** أو **Environment Variables**
2. أضف المتغيرات:
   ```
   DISCORD_BOT_TOKEN = your_token_here
   GUILD_ID = 123456789
   ```
3. Deploy/Restart

#### E) Linux/Unix Terminal (للاختبار)

```bash
export DISCORD_BOT_TOKEN='your_token_here'
export GUILD_ID='123456789'
python bot.py
```

---

## 🔍 كيفية التحقق | How to Verify

عند تشغيل البوت، ستظهر إحدى الرسائل التالية:

### ✅ نجاح | Success:

```
✅ تم التحقق من الإعدادات بنجاح | Configuration validated successfully
```

### ❌ فشل | Failure:

```
============================================================
❌ خطأ: DISCORD_BOT_TOKEN غير موجود
❌ Error: DISCORD_BOT_TOKEN not found
============================================================

يرجى تعيين المتغير DISCORD_BOT_TOKEN بإحدى الطرق التالية:
Please set DISCORD_BOT_TOKEN using one of the following methods:

1️⃣  إنشاء ملف .env في المجلد الحالي:
    Create a .env file in the current directory:
    cp .env.example .env
    # ثم قم بتعديل الملف وإضافة التوكن
    # Then edit the file and add your token

2️⃣  أو تعيين متغير البيئة مباشرة:
    Or set the environment variable directly:
    export DISCORD_BOT_TOKEN='your_token_here'

3️⃣  لـ Docker أو منصات الاستضافة:
    For Docker or hosting platforms:
    # قم بتعيين المتغير في لوحة التحكم أو docker-compose.yml
    # Set the variable in your control panel or docker-compose.yml
============================================================
```

---

## 🎯 استكشاف الأخطاء | Troubleshooting

### المشكلة: البوت يظهر "Token not found"

#### الحل 1: تحقق من ملف .env
```bash
# تحقق من وجود الملف
ls -la .env

# اعرض محتوى الملف (بدون مشاركته!)
cat .env | head -3
```

يجب أن يحتوي على:
```env
DISCORD_BOT_TOKEN=actual_token_not_placeholder
```

#### الحل 2: تحقق من متغيرات البيئة
```bash
# في Linux/Mac
echo $DISCORD_BOT_TOKEN

# يجب أن يظهر التوكن (إذا كان معيناً)
```

#### الحل 3: تحقق من موقع الملف
```bash
# تأكد أن .env في نفس المجلد مع bot.py
pwd
ls -la .env
ls -la bot.py
```

#### الحل 4: لمنصات الاستضافة
- تحقق من لوحة التحكم أن المتغيرات معينة بشكل صحيح
- تأكد من عدم وجود مسافات زائدة
- تأكد من عدم وجود علامات اقتباس زائدة
- أعد تشغيل البوت بعد تعيين المتغيرات

---

## 🔒 الأمان | Security

### ⚠️ تحذيرات مهمة | Important Warnings:

1. **لا تشارك ملف .env أبداً**
   - Never share your .env file
   - Never commit it to Git

2. **لا تنشر التوكن**
   - Never post your bot token publicly
   - Regenerate immediately if exposed

3. **استخدم .gitignore**
   ```gitignore
   .env
   .env.local
   .env.*.local
   ```

4. **للتطوير، استخدم توكن اختبار**
   - Use a separate test bot for development

---

## 📝 أمثلة عملية | Practical Examples

### مثال 1: Development على Windows

```powershell
# PowerShell
$env:DISCORD_BOT_TOKEN="your_token"
python bot.py
```

### مثال 2: Production على Linux VPS

```bash
# /etc/systemd/system/discord-bot.service
[Service]
Environment="DISCORD_BOT_TOKEN=your_token"
Environment="GUILD_ID=123456789"
ExecStart=/usr/bin/python3 /path/to/bot.py
```

### مثال 3: Docker Development

```bash
# docker-compose.dev.yml
version: '3.8'
services:
  bot:
    build: .
    env_file: .env
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
```

### مثال 4: Pterodactyl Egg

في Startup Variables:
```json
{
  "DISCORD_BOT_TOKEN": {
    "description": "Discord Bot Token",
    "env_variable": "DISCORD_BOT_TOKEN",
    "default_value": "",
    "user_viewable": true,
    "user_editable": true,
    "rules": "required|string"
  }
}
```

---

## ✅ قائمة التحقق النهائية | Final Checklist

- [ ] تم تعيين `DISCORD_BOT_TOKEN`
- [ ] تم التأكد من صحة التوكن (لا يحتوي على مسافات)
- [ ] تم تشغيل البوت وظهرت رسالة النجاح
- [ ] البوت يظهر Online في Discord
- [ ] الأوامر `/start` تعمل
- [ ] تم حفظ `.env` في `.gitignore` (إن وجد)

---

## 💡 نصائح إضافية | Additional Tips

1. **استخدم أسماء واضحة للمتغيرات**
   - جيد: `DISCORD_BOT_TOKEN`
   - سيء: `TOKEN` أو `BOT_TOKEN`

2. **وثّق المتغيرات المطلوبة**
   - استخدم `.env.example` كمرجع

3. **استخدم أدوات إدارة الأسرار للإنتاج**
   - Docker Secrets
   - Kubernetes Secrets
   - AWS Secrets Manager

4. **احتفظ بنسخة احتياطية آمنة**
   - احفظ التوكن في مكان آمن
   - استخدم مدير كلمات مرور

---

## 📞 الدعم | Support

إذا واجهت مشاكل:
1. راجع هذا الدليل
2. تحقق من السجلات في `logs/bot.log`
3. افتح Issue في GitHub مع:
   - وصف المشكلة
   - رسائل الخطأ (بدون التوكن!)
   - نوع منصة الاستضافة

---

Made with ❤️ for Discord Bot Developers

</div>
