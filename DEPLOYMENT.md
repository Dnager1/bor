# 🎮 Discord Bot - White Survival Management System
## بوت ديسكورد لإدارة النجاة في الصقيع

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Discord.py](https://img.shields.io/badge/discord.py-2.3.0+-blue.svg)](https://discordpy.readthedocs.io/en/stable/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 📋 نظرة عامة | Overview

بوت ديسكورد احترافي متقدم لإدارة الحجوزات والتحالفات في لعبة "النجاة في الصقيع" مع واجهة تفاعلية كاملة بالأزرار.

A professional Discord bot for managing reservations and alliances in "White Survival" game with a complete button-based interface.

---

## ✨ الميزات الرئيسية | Main Features

### 🎯 لوحة التحكم الرئيسية | Main Control Panel
- **واجهة أزرار فقط** - Button-only interface (NO commands except `/start`)
- **دعم متعدد اللغات** - Multi-language support (Arabic & English)
- **تخزين تفضيلات المستخدم** - Per-user language preferences
- **أزرار رجوع في كل قائمة** - Back buttons in all submenus

### 📅 نظام الحجوزات | Reservations System
- **3 أقسام رئيسية:**
  - 🏗️ البناء | Building
  - ⚔️ التدريب | Training
  - 🔬 الأبحاث | Research
- منع التعارض بين الحجوزات
- دعم مدة الحجز (بالأيام)
- عرض الجداول والسجلات

### 🤝 نظام التحالف | Alliance System
- معلومات كاملة عن التحالف
- إدارة الأعضاء (للمخولين فقط)
- نظام الرتب (R5 إلى R1)
- صلاحيات مفصلة لكل رتبة

### ⚙️ نظام الإدارة | Management System
- **صلاحيات متعددة المستويات:**
  - مالك البوت (Owner) - صلاحيات كاملة
  - المشرفون (Admins) - صلاحيات إدارية
  - صلاحيات جزئية قابلة للتخصيص
- إدارة التحالفات
- إدارة الحجوزات
- إدارة المستخدمين
- إدارة النظام

### 🔔 نظام التذكيرات | Reminders System
- تذكيرات تلقائية قابلة للتكوين:
  - قبل 24 ساعة
  - قبل 6 ساعات
  - قبل 3 ساعات
  - قبل ساعة
  - عند الموعد بالضبط
- إرسال رسائل خاصة للمستخدمين
- دعم متعدد اللغات في التذكيرات

### 🗑️ نظام التنظيف التلقائي | Auto-Cleanup System
- حذف الحجوزات المنتهية تلقائياً
- تنظيف السجلات القديمة (أقدم من 90 يوم)
- عمل مستمر بدون تأثير على الأداء

---

## 🚀 التثبيت والإعداد | Installation & Setup

### المتطلبات | Requirements

```bash
Python 3.9+
discord.py 2.3.0+
aiosqlite 0.19.0+
python-dotenv 1.0.0+
pytz 2024.1+
```

### خطوات التثبيت | Installation Steps

1. **استنساخ المشروع | Clone the repository:**
```bash
git clone https://github.com/Dnager1/bor.git
cd bor
```

2. **تثبيت المتطلبات | Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **إعداد ملف البيئة | Setup environment file:**
```bash
cp .env.example .env
```

4. **تعديل ملف .env | Edit .env file:**
```env
# Discord Bot Token (Required)
DISCORD_BOT_TOKEN=your_bot_token_here

# Server Configuration
GUILD_ID=your_server_id

# Owner Configuration (Required)
OWNER_ID=your_discord_user_id

# Optional: Role IDs for Permissions
ADMIN_ROLE_ID=123456789
MODERATOR_ROLE_ID=987654321
```

5. **تشغيل البوت | Run the bot:**
```bash
python bot.py
```

---

## 📁 هيكلة المشروع | Project Structure

```
bor/
├── bot.py                      # Main bot file
├── config.py                   # Configuration
├── requirements.txt            # Dependencies
├── .env                        # Environment variables (create this)
│
├── cogs/                       # Bot cogs (modules)
│   ├── main_control_panel.py  # Main menu system
│   ├── reservations_system.py # Reservations management
│   ├── alliance_system.py     # Alliance management
│   └── management_system.py   # Admin panel
│
├── database/                   # Database layer
│   ├── db_manager.py          # Database manager
│   ├── models.py              # Data models
│   └── schema.sql             # Database schema
│
├── tasks/                      # Scheduled tasks
│   ├── reminders_task.py      # Reminders system
│   ├── cleanup_task.py        # Auto-cleanup
│   └── backup_task.py         # Auto-backup
│
├── utils/                      # Utilities
│   ├── translator.py          # i18n system
│   ├── permissions.py         # Permissions manager
│   ├── ui_components.py       # UI helpers
│   └── languages/             # Language files
│       ├── ar.json            # Arabic
│       └── en.json            # English
│
├── data/                       # Data storage
│   ├── bookings.db            # SQLite database
│   └── backups/               # Database backups
│
└── logs/                       # Log files
    ├── bot.log                # General logs
    ├── errors.log             # Error logs
    └── bookings.log           # Booking logs
```

---

## 🎮 الاستخدام | Usage

### بدء البوت | Starting the Bot

1. دعوة البوت إلى السيرفر
2. التأكد من الصلاحيات المطلوبة
3. استخدام الأمر `/start` لفتح لوحة التحكم

### لوحة التحكم الرئيسية | Main Control Panel

```
📖 لوحة التحكم الرئيسية
Welcome to White Survival Management System

[🤝 التحالف]  [📅 الحجوزات]
[⚙️ الإدارة]   [🌐 اللغة]  [👤 معلوماتي]
```

### إنشاء حجز | Creating a Reservation

1. اضغط على `📅 الحجوزات`
2. اختر القسم (Building/Training/Research)
3. اضغط `➕ إنشاء حجز`
4. املأ النموذج:
   - اسم العضو
   - اسم التحالف
   - التاريخ (YYYY-MM-DD)
   - الوقت (HH:MM UTC)
   - عدد الأيام

---

## 🔐 نظام الصلاحيات | Permissions System

### مستويات الصلاحيات | Permission Levels

1. **المالك (Owner):**
   - صلاحيات كاملة
   - إدارة المشرفين
   - إدارة الصلاحيات

2. **المشرف (Admin):**
   - الوصول للوحة الإدارة
   - إدارة التحالفات
   - إدارة الحجوزات
   - عرض الإحصائيات

3. **صلاحيات جزئية:**
   - `alliance_management` - إدارة التحالف
   - `reservations_management` - إدارة الحجوزات
   - `user_management` - إدارة المستخدمين
   - `system_management` - إدارة النظام

---

## 🌐 دعم اللغات | Language Support

### اللغات المدعومة | Supported Languages

- 🇸🇦 العربية (Arabic) - Default for bot owner
- 🇬🇧 English

### تغيير اللغة | Changing Language

1. افتح لوحة التحكم `/start`
2. اضغط `🌐 اللغة`
3. اختر اللغة المفضلة
4. سيتم حفظ الاختيار تلقائياً

---

## 📊 قاعدة البيانات | Database

### الجداول | Tables

- **users** - بيانات المستخدمين
- **bookings** - الحجوزات
- **alliances** - التحالفات
- **permissions** - الصلاحيات
- **logs** - السجلات
- **achievements** - الإنجازات
- **settings** - الإعدادات

### النسخ الاحتياطي | Backup

- نسخ احتياطي تلقائي كل 6 ساعات
- الحفظ في `data/backups/`
- تسمية بالتاريخ والوقت

---

## 🔧 الصيانة | Maintenance

### التنظيف التلقائي | Auto-Cleanup

- حذف الحجوزات المنتهية كل 6 ساعات
- تنظيف السجلات القديمة كل 24 ساعة
- لا يؤثر على الأداء

### السجلات | Logs

موقع ملفات السجلات:
```
logs/bot.log       - سجل عام
logs/errors.log    - سجل الأخطاء
logs/bookings.log  - سجل الحجوزات
```

---

## 🐛 استكشاف الأخطاء | Troubleshooting

### مشاكل شائعة | Common Issues

**1. البوت لا يستجيب:**
- تأكد من TOKEN صحيح
- تأكد من الصلاحيات في السيرفر
- راجع سجل الأخطاء

**2. الأزرار لا تعمل:**
- تأكد من تفعيل Intents
- أعد مزامنة الأوامر
- أعد تشغيل البوت

**3. قاعدة البيانات:**
- تأكد من وجود مجلد `data/`
- تحقق من صلاحيات الكتابة
- استرجع من النسخة الاحتياطية

---

## 📝 الترخيص | License

هذا المشروع مرخص تحت MIT License.

---

## 👥 المساهمة | Contributing

المساهمات مرحب بها! يرجى:
1. عمل Fork للمشروع
2. إنشاء Branch للميزة الجديدة
3. Commit التغييرات
4. Push وإنشاء Pull Request

---

## 📧 التواصل | Contact

لأي استفسارات أو دعم، يرجى التواصل عبر:
- GitHub Issues
- Discord Server

---

## 🙏 شكر وتقدير | Acknowledgments

- Discord.py Library
- White Survival Game Community
- All Contributors

---

**Made with ❤️ for White Survival Community**

**صُنع بـ ❤️ لمجتمع النجاة في الصقيع**
