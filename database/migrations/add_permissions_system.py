"""
Migration: Add bot permissions system
- Create bot_permissions table for role and permission management
- Add owner, admin, moderator roles with custom permissions
"""
import aiosqlite
import logging
from datetime import datetime

logger = logging.getLogger('migration')

async def run_migration(db_path: str):
    """تشغيل ترقية نظام الصلاحيات"""
    logger.info("🔄 بدء ترقية نظام الصلاحيات...")
    
    async with aiosqlite.connect(db_path) as db:
        try:
            # 1. إنشاء جدول صلاحيات البوت
            logger.info("إنشاء جدول bot_permissions...")
            await db.execute("""
                CREATE TABLE IF NOT EXISTS bot_permissions (
                    permission_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('owner', 'admin', 'moderator', 'user')),
                    permissions TEXT DEFAULT '{}',
                    granted_by TEXT,
                    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    UNIQUE(discord_id)
                )
            """)
            
            # 2. إنشاء جدول سجل الصلاحيات
            logger.info("إنشاء جدول permissions_log...")
            await db.execute("""
                CREATE TABLE IF NOT EXISTS permissions_log (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    target_discord_id TEXT NOT NULL,
                    target_username TEXT,
                    performed_by TEXT NOT NULL,
                    old_role TEXT,
                    new_role TEXT,
                    permissions_changed TEXT,
                    reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 3. إنشاء فهارس
            logger.info("إنشاء فهارس...")
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_bot_permissions_discord_id 
                ON bot_permissions(discord_id)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_bot_permissions_role 
                ON bot_permissions(role)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_permissions_log_target 
                ON permissions_log(target_discord_id)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_permissions_log_performed_by 
                ON permissions_log(performed_by)
            """)
            
            await db.commit()
            logger.info("✅ تم تطبيق ترقية نظام الصلاحيات بنجاح!")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في تطبيق الترقية: {e}")
            await db.rollback()
            return False

if __name__ == "__main__":
    import asyncio
    import sys
    
    # إعداد نظام السجلات
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # مسار قاعدة البيانات
    db_path = "data/bookings.db"
    
    # تشغيل الترقية
    asyncio.run(run_migration(db_path))
