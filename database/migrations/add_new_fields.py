"""
Migration: Add new fields for enhanced bot features
- Add duration_days to bookings table
- Add language to users table  
- Add new alliance fields (logo, type, max_members, requirements, rank)
- Create alliance_members table
- Create alliance_join_requests table
- Create alliance_challenges table
- Create alliance_messages table
"""
import aiosqlite
import logging
from datetime import datetime

logger = logging.getLogger('migration')

async def run_migration(db_path: str):
    """تشغيل الترقية"""
    logger.info("🔄 بدء ترقية قاعدة البيانات...")
    
    async with aiosqlite.connect(db_path) as db:
        try:
            # 1. إضافة حقل duration_days إلى جدول bookings
            logger.info("إضافة حقل duration_days...")
            await db.execute("""
                ALTER TABLE bookings 
                ADD COLUMN duration_days INTEGER DEFAULT 1
            """)
            
            # 2. إضافة حقل language إلى جدول users
            logger.info("إضافة حقل language...")
            await db.execute("""
                ALTER TABLE users 
                ADD COLUMN language TEXT DEFAULT 'ar'
            """)
            
            # 3. إضافة حقول جديدة لجدول alliances
            logger.info("إضافة حقول جديدة للتحالفات...")
            try:
                await db.execute("""
                    ALTER TABLE alliances 
                    ADD COLUMN alliance_logo TEXT DEFAULT '🏰'
                """)
            except Exception:
                pass
            
            try:
                await db.execute("""
                    ALTER TABLE alliances 
                    ADD COLUMN alliance_type TEXT DEFAULT 'public' CHECK(alliance_type IN ('public', 'private'))
                """)
            except Exception:
                pass
            
            try:
                await db.execute("""
                    ALTER TABLE alliances 
                    ADD COLUMN max_members INTEGER DEFAULT 50
                """)
            except Exception:
                pass
            
            try:
                await db.execute("""
                    ALTER TABLE alliances 
                    ADD COLUMN requirements TEXT DEFAULT ''
                """)
            except Exception:
                pass
            
            try:
                await db.execute("""
                    ALTER TABLE alliances 
                    ADD COLUMN completed_bookings INTEGER DEFAULT 0
                """)
            except Exception:
                pass
            
            try:
                await db.execute("""
                    ALTER TABLE alliances 
                    ADD COLUMN alliance_rank INTEGER DEFAULT 0
                """)
            except Exception:
                pass
            
            # 4. إنشاء جدول alliance_members
            logger.info("إنشاء جدول alliance_members...")
            await db.execute("""
                CREATE TABLE IF NOT EXISTS alliance_members (
                    member_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    alliance_id INTEGER NOT NULL,
                    rank TEXT DEFAULT 'member' CHECK(rank IN ('leader', 'deputy', 'member')),
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    contribution_points INTEGER DEFAULT 0,
                    activity_status TEXT DEFAULT 'active' CHECK(activity_status IN ('active', 'inactive')),
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (alliance_id) REFERENCES alliances(alliance_id),
                    UNIQUE(user_id, alliance_id)
                )
            """)
            
            # 5. إنشاء جدول alliance_join_requests
            logger.info("إنشاء جدول alliance_join_requests...")
            await db.execute("""
                CREATE TABLE IF NOT EXISTS alliance_join_requests (
                    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    alliance_id INTEGER NOT NULL,
                    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected')),
                    message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP,
                    resolved_by INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (alliance_id) REFERENCES alliances(alliance_id),
                    FOREIGN KEY (resolved_by) REFERENCES users(user_id)
                )
            """)
            
            # 6. إنشاء جدول alliance_challenges
            logger.info("إنشاء جدول alliance_challenges...")
            await db.execute("""
                CREATE TABLE IF NOT EXISTS alliance_challenges (
                    challenge_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alliance1_id INTEGER NOT NULL,
                    alliance2_id INTEGER,
                    challenge_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    target_value INTEGER NOT NULL,
                    current_value INTEGER DEFAULT 0,
                    reward TEXT,
                    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'completed', 'failed', 'cancelled')),
                    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_date TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (alliance1_id) REFERENCES alliances(alliance_id),
                    FOREIGN KEY (alliance2_id) REFERENCES alliances(alliance_id)
                )
            """)
            
            # 7. إنشاء جدول alliance_messages
            logger.info("إنشاء جدول alliance_messages...")
            await db.execute("""
                CREATE TABLE IF NOT EXISTS alliance_messages (
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alliance_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    message_type TEXT DEFAULT 'announcement' CHECK(message_type IN ('announcement', 'event', 'achievement')),
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (alliance_id) REFERENCES alliances(alliance_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # 8. إنشاء فهارس جديدة
            logger.info("إنشاء فهارس جديدة...")
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_alliance_members_user 
                ON alliance_members(user_id)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_alliance_members_alliance 
                ON alliance_members(alliance_id)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_alliance_requests_status 
                ON alliance_join_requests(status)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_alliance_challenges_status 
                ON alliance_challenges(status)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_alliance_messages_alliance 
                ON alliance_messages(alliance_id)
            """)
            
            await db.commit()
            logger.info("✅ تم تطبيق الترقية بنجاح!")
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
