"""
Migration script to upgrade database to Version 2.0
ترقية قاعدة البيانات إلى الإصدار 2.0
"""
import aiosqlite
import asyncio
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('migration_v2')

async def migrate_database(db_path: str = 'data/bookings.db'):
    """تنفيذ الترقية"""
    logger.info("🚀 بدء ترقية قاعدة البيانات إلى الإصدار 2.0...")
    
    async with aiosqlite.connect(db_path) as db:
        try:
            # 1. Add language column to users table if not exists
            logger.info("1️⃣ إضافة عمود اللغة إلى جدول المستخدمين...")
            try:
                await db.execute("""
                    ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'en' 
                    CHECK(language IN ('ar', 'en'))
                """)
                logger.info("✅ تمت إضافة عمود اللغة")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    logger.info("⚠️ عمود اللغة موجود مسبقاً")
                else:
                    logger.error(f"❌ خطأ في إضافة عمود اللغة: {e}")
            
            # 2. Add duration_days to bookings if not exists
            logger.info("2️⃣ إضافة عمود عدد الأيام إلى جدول الحجوزات...")
            try:
                await db.execute("""
                    ALTER TABLE bookings ADD COLUMN duration_days INTEGER DEFAULT 1
                """)
                logger.info("✅ تمت إضافة عمود عدد الأيام")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    logger.info("⚠️ عمود عدد الأيام موجود مسبقاً")
                else:
                    logger.error(f"❌ خطأ في إضافة عمود عدد الأيام: {e}")
            
            # 3. Add reminder_sent JSON column to bookings
            logger.info("3️⃣ إضافة عمود التذكيرات المرنة...")
            try:
                await db.execute("""
                    ALTER TABLE bookings ADD COLUMN reminder_sent TEXT DEFAULT '{}'
                """)
                logger.info("✅ تمت إضافة عمود التذكيرات المرنة")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    logger.info("⚠️ عمود التذكيرات المرنة موجود مسبقاً")
                else:
                    logger.error(f"❌ خطأ: {e}")
            
            # 4. Enhance alliances table
            logger.info("4️⃣ تحسين جدول التحالفات...")
            new_alliance_columns = [
                ("logo", "TEXT DEFAULT '🏰'"),
                ("level", "INTEGER DEFAULT 1"),
                ("total_power", "INTEGER DEFAULT 0"),
                ("rules", "TEXT"),
                ("location", "TEXT"),
                ("max_members", "INTEGER DEFAULT 50"),
                ("completed_bookings", "INTEGER DEFAULT 0"),
                ("alliance_type", "TEXT DEFAULT 'public'"),
                ("requirements", "TEXT"),
                ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            ]
            
            for col_name, col_def in new_alliance_columns:
                try:
                    await db.execute(f"ALTER TABLE alliances ADD COLUMN {col_name} {col_def}")
                    logger.info(f"✅ تمت إضافة عمود {col_name} للتحالفات")
                except Exception as e:
                    if "duplicate column name" in str(e).lower():
                        logger.info(f"⚠️ عمود {col_name} موجود مسبقاً")
                    else:
                        logger.error(f"❌ خطأ في إضافة {col_name}: {e}")
            
            # 5. Create alliance_members table
            logger.info("5️⃣ إنشاء جدول أعضاء التحالف...")
            await db.execute("""
                CREATE TABLE IF NOT EXISTS alliance_members (
                    member_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    alliance_id INTEGER NOT NULL,
                    rank TEXT DEFAULT 'R1' CHECK(rank IN ('R5', 'R4', 'R3', 'R2', 'R1')),
                    power INTEGER DEFAULT 0,
                    contribution_points INTEGER DEFAULT 0,
                    activity_status TEXT DEFAULT 'active' CHECK(activity_status IN ('active', 'inactive', 'away')),
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (alliance_id) REFERENCES alliances(alliance_id),
                    UNIQUE(user_id, alliance_id)
                )
            """)
            logger.info("✅ تم إنشاء جدول أعضاء التحالف")
            
            # 6. Create alliance_join_requests table
            logger.info("6️⃣ إنشاء جدول طلبات الانضمام...")
            await db.execute("""
                CREATE TABLE IF NOT EXISTS alliance_join_requests (
                    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    alliance_id INTEGER NOT NULL,
                    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'accepted', 'rejected')),
                    message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    processed_by INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (alliance_id) REFERENCES alliances(alliance_id),
                    FOREIGN KEY (processed_by) REFERENCES users(user_id)
                )
            """)
            logger.info("✅ تم إنشاء جدول طلبات الانضمام")
            
            # 7. Create/Update bot_permissions table
            logger.info("7️⃣ إنشاء/تحديث جدول صلاحيات البوت...")
            await db.execute("""
                CREATE TABLE IF NOT EXISTS bot_permissions (
                    permission_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_id TEXT UNIQUE NOT NULL,
                    username TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('owner', 'admin', 'moderator')),
                    permissions TEXT DEFAULT '{}',
                    granted_by TEXT NOT NULL,
                    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT
                )
            """)
            logger.info("✅ تم إنشاء/تحديث جدول صلاحيات البوت")
            
            # 8. Create permissions_log table
            logger.info("8️⃣ إنشاء جدول سجل الصلاحيات...")
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
            logger.info("✅ تم إنشاء جدول سجل الصلاحيات")
            
            # 9. Create reminder_config table
            logger.info("9️⃣ إنشاء جدول إعدادات التذكير...")
            await db.execute("""
                CREATE TABLE IF NOT EXISTS reminder_config (
                    config_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    hours_before INTEGER NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_by TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert default reminder configurations
            await db.execute("""
                INSERT OR IGNORE INTO reminder_config (config_id, name, hours_before, is_active, created_by) VALUES
                (1, '1_hour', 1, 1, 'system'),
                (2, '3_hours', 3, 1, 'system'),
                (3, '6_hours', 6, 1, 'system'),
                (4, '24_hours', 24, 1, 'system')
            """)
            logger.info("✅ تم إنشاء جدول إعدادات التذكير مع القيم الافتراضية")
            
            # 10. Enhance settings table
            logger.info("🔟 تحسين جدول الإعدادات...")
            try:
                await db.execute("""
                    ALTER TABLE settings ADD COLUMN setting_type TEXT DEFAULT 'string' 
                    CHECK(setting_type IN ('string', 'integer', 'boolean', 'json'))
                """)
                await db.execute("""
                    ALTER TABLE settings ADD COLUMN description TEXT
                """)
                await db.execute("""
                    ALTER TABLE settings ADD COLUMN updated_by TEXT
                """)
                logger.info("✅ تم تحسين جدول الإعدادات")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    logger.info("⚠️ أعمدة الإعدادات موجودة مسبقاً")
                else:
                    logger.error(f"❌ خطأ في تحسين الإعدادات: {e}")
            
            # 11. Create indexes
            logger.info("1️⃣1️⃣ إنشاء الفهارس...")
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_users_language ON users(language)",
                "CREATE INDEX IF NOT EXISTS idx_bookings_created_at ON bookings(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_alliance_members_user_id ON alliance_members(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_alliance_members_alliance_id ON alliance_members(alliance_id)",
                "CREATE INDEX IF NOT EXISTS idx_alliance_members_rank ON alliance_members(rank)",
                "CREATE INDEX IF NOT EXISTS idx_alliance_requests_user_id ON alliance_join_requests(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_alliance_requests_alliance_id ON alliance_join_requests(alliance_id)",
                "CREATE INDEX IF NOT EXISTS idx_alliance_requests_status ON alliance_join_requests(status)",
                "CREATE INDEX IF NOT EXISTS idx_permissions_discord_id ON bot_permissions(discord_id)",
                "CREATE INDEX IF NOT EXISTS idx_permissions_role ON bot_permissions(role)",
                "CREATE INDEX IF NOT EXISTS idx_logs_user_id ON logs(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_achievements_type ON achievements(achievement_type)"
            ]
            
            for index_sql in indexes:
                try:
                    await db.execute(index_sql)
                except Exception as e:
                    logger.error(f"⚠️ خطأ في إنشاء فهرس: {e}")
            
            logger.info("✅ تم إنشاء الفهارس")
            
            # 12. Create views
            logger.info("1️⃣2️⃣ إنشاء العروض (Views)...")
            
            # Drop existing views if they exist
            await db.execute("DROP VIEW IF EXISTS v_active_bookings")
            await db.execute("DROP VIEW IF EXISTS v_alliance_members_details")
            
            # Create active bookings view
            await db.execute("""
                CREATE VIEW v_active_bookings AS
                SELECT 
                    b.booking_id,
                    b.booking_type,
                    b.player_name,
                    b.player_id,
                    b.alliance_name,
                    b.scheduled_time,
                    b.duration_days,
                    b.status,
                    u.discord_id,
                    u.username,
                    u.language
                FROM bookings b
                JOIN users u ON b.user_id = u.user_id
                WHERE b.status = 'active'
                ORDER BY b.scheduled_time ASC
            """)
            
            # Create alliance members details view
            await db.execute("""
                CREATE VIEW v_alliance_members_details AS
                SELECT 
                    am.member_id,
                    am.alliance_id,
                    a.name as alliance_name,
                    u.user_id,
                    u.discord_id,
                    u.username,
                    u.player_id,
                    am.rank,
                    am.power,
                    am.contribution_points,
                    am.activity_status,
                    am.last_activity,
                    am.joined_at
                FROM alliance_members am
                JOIN users u ON am.user_id = u.user_id
                JOIN alliances a ON am.alliance_id = a.alliance_id
                ORDER BY 
                    CASE am.rank
                        WHEN 'R5' THEN 1
                        WHEN 'R4' THEN 2
                        WHEN 'R3' THEN 3
                        WHEN 'R2' THEN 4
                        WHEN 'R1' THEN 5
                    END,
                    am.power DESC
            """)
            
            logger.info("✅ تم إنشاء العروض")
            
            # 13. Migrate existing alliance members to new table
            logger.info("1️⃣3️⃣ ترحيل أعضاء التحالف الموجودين...")
            cursor = await db.execute("""
                SELECT user_id, alliance_id FROM users WHERE alliance_id IS NOT NULL
            """)
            existing_members = await cursor.fetchall()
            
            for user_id, alliance_id in existing_members:
                try:
                    await db.execute("""
                        INSERT OR IGNORE INTO alliance_members 
                        (user_id, alliance_id, rank, power, contribution_points, activity_status)
                        VALUES (?, ?, 'R1', 0, 0, 'active')
                    """, (user_id, alliance_id))
                except Exception as e:
                    logger.error(f"خطأ في ترحيل العضو {user_id}: {e}")
            
            logger.info(f"✅ تم ترحيل {len(existing_members)} عضو")
            
            # Commit all changes
            await db.commit()
            logger.info("✅ تم حفظ جميع التغييرات")
            
            # 14. Update version in settings
            await db.execute("""
                INSERT OR REPLACE INTO settings (setting_key, setting_value, setting_type, description, updated_by)
                VALUES ('database_version', '2.0', 'string', 'Database schema version', 'migration_script')
            """)
            await db.commit()
            logger.info("✅ تم تحديث رقم إصدار قاعدة البيانات")
            
            logger.info("🎉 اكتملت الترقية بنجاح إلى الإصدار 2.0!")
            
        except Exception as e:
            logger.error(f"❌ خطأ فادح في الترقية: {e}")
            raise

async def verify_migration(db_path: str = 'data/bookings.db'):
    """التحقق من نجاح الترقية"""
    logger.info("🔍 التحقق من الترقية...")
    
    async with aiosqlite.connect(db_path) as db:
        # Check tables exist
        cursor = await db.execute("""
            SELECT name FROM sqlite_master WHERE type='table' 
            ORDER BY name
        """)
        tables = await cursor.fetchall()
        table_names = [t[0] for t in tables]
        
        required_tables = [
            'users', 'bookings', 'alliances', 'alliance_members',
            'alliance_join_requests', 'bot_permissions', 'permissions_log',
            'reminder_config', 'achievements', 'logs', 'settings'
        ]
        
        missing_tables = [t for t in required_tables if t not in table_names]
        
        if missing_tables:
            logger.error(f"❌ جداول مفقودة: {missing_tables}")
            return False
        
        logger.info(f"✅ جميع الجداول المطلوبة موجودة: {len(table_names)} جداول")
        
        # Check views exist
        cursor = await db.execute("""
            SELECT name FROM sqlite_master WHERE type='view'
            ORDER BY name
        """)
        views = await cursor.fetchall()
        view_names = [v[0] for v in views]
        
        logger.info(f"✅ العروض (Views) موجودة: {view_names}")
        
        # Check version
        cursor = await db.execute("""
            SELECT setting_value FROM settings WHERE setting_key = 'database_version'
        """)
        version = await cursor.fetchone()
        
        if version and version[0] == '2.0':
            logger.info(f"✅ إصدار قاعدة البيانات: {version[0]}")
            return True
        else:
            logger.error(f"❌ إصدار قاعدة البيانات غير صحيح: {version}")
            return False

async def main():
    """الدالة الرئيسية"""
    db_path = 'data/bookings.db'
    
    print("=" * 60)
    print("  Database Migration to Version 2.0")
    print("  ترقية قاعدة البيانات إلى الإصدار 2.0")
    print("=" * 60)
    print()
    
    # Run migration
    await migrate_database(db_path)
    
    print()
    print("=" * 60)
    print("  Verification")
    print("  التحقق من النتائج")
    print("=" * 60)
    print()
    
    # Verify migration
    success = await verify_migration(db_path)
    
    if success:
        print()
        print("🎉" * 30)
        print("✅ Migration completed successfully!")
        print("✅ اكتملت الترقية بنجاح!")
        print("🎉" * 30)
    else:
        print()
        print("❌" * 30)
        print("❌ Migration verification failed!")
        print("❌ فشل التحقق من الترقية!")
        print("❌" * 30)

if __name__ == "__main__":
    asyncio.run(main())
