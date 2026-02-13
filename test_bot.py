#!/usr/bin/env python3
"""
اختبار سريع للبوت - Quick Bot Test
"""
import sys
import asyncio

print("🔍 بدء الاختبار السريع...")

# اختبار استيراد الوحدات
print("\n1️⃣ اختبار استيراد الوحدات...")
try:
    import discord
    print("  ✅ discord.py")
    import aiosqlite
    print("  ✅ aiosqlite")
    import pytz
    print("  ✅ pytz")
    from dotenv import load_dotenv
    print("  ✅ python-dotenv")
except ImportError as e:
    print(f"  ❌ خطأ في الاستيراد: {e}")
    print("\n💡 قم بتثبيت المتطلبات: pip install -r requirements.txt")
    sys.exit(1)

print("\n2️⃣ اختبار وحدات المشروع...")
try:
    from config import config
    print("  ✅ config")
    from database import db
    print("  ✅ database")
    from utils import validators, formatters, embeds, datetime_helper, permissions
    print("  ✅ utils")
except Exception as e:
    print(f"  ❌ خطأ: {e}")
    sys.exit(1)

print("\n3️⃣ اختبار الإعدادات...")
try:
    if config.BOT_TOKEN:
        print("  ✅ BOT_TOKEN موجود")
    else:
        print("  ⚠️  BOT_TOKEN غير محدد (سيحتاج للإعداد في .env)")
    
    print(f"  ℹ️  TIMEZONE: {config.TIMEZONE}")
    print(f"  ℹ️  MAX_ACTIVE_BOOKINGS: {config.MAX_ACTIVE_BOOKINGS}")
except Exception as e:
    print(f"  ❌ خطأ: {e}")
    sys.exit(1)

print("\n4️⃣ اختبار قاعدة البيانات...")
async def test_db():
    try:
        await db.initialize()
        print("  ✅ تم تهيئة قاعدة البيانات")
        
        # اختبار إنشاء مستخدم
        user = await db.get_or_create_user("test_123", "TestUser", "12345")
        print(f"  ✅ اختبار المستخدم: {user.username}")
        
        # اختبار الإحصائيات
        stats = await db.get_stats()
        print(f"  ✅ الإحصائيات: {stats['total_users']} مستخدم")
        
        return True
    except Exception as e:
        print(f"  ❌ خطأ في قاعدة البيانات: {e}")
        return False

try:
    result = asyncio.run(test_db())
    if not result:
        sys.exit(1)
except Exception as e:
    print(f"  ❌ خطأ: {e}")
    sys.exit(1)

print("\n5️⃣ اختبار الـ Validators...")
try:
    valid, error = validators.validate_player_id("12345678")
    if valid:
        print("  ✅ validator: player_id")
    
    valid, error = validators.validate_player_name("أحمد")
    if valid:
        print("  ✅ validator: player_name")
    
    valid, error = validators.validate_alliance_name("الفرسان")
    if valid:
        print("  ✅ validator: alliance_name")
except Exception as e:
    print(f"  ❌ خطأ: {e}")
    sys.exit(1)

print("\n6️⃣ اختبار الـ Formatters...")
try:
    from datetime import datetime
    dt = datetime.now()
    formatted = formatters.format_datetime(dt)
    print(f"  ✅ formatter: datetime - {formatted}")
except Exception as e:
    print(f"  ❌ خطأ: {e}")
    sys.exit(1)

print("\n7️⃣ اختبار الـ Embeds...")
try:
    embed = embeds.create_success_embed("اختبار", "هذا اختبار")
    print(f"  ✅ embed: success - {embed.title}")
    
    embed = embeds.create_error_embed("خطأ", "هذا اختبار خطأ")
    print(f"  ✅ embed: error - {embed.title}")
except Exception as e:
    print(f"  ❌ خطأ: {e}")
    sys.exit(1)

print("\n" + "="*50)
print("✅ جميع الاختبارات نجحت!")
print("="*50)

print("\n📝 الخطوات التالية:")
print("1. قم بإعداد ملف .env (انسخ من .env.example)")
print("2. أضف DISCORD_BOT_TOKEN في ملف .env")
print("3. شغّل البوت: python bot.py")
print("\n💡 للمزيد من التفاصيل، اقرأ INSTALL.md")
