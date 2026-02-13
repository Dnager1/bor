"""
مدير قاعدة البيانات - Database Manager
"""
import aiosqlite
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from .models import User, Booking, Alliance, Achievement, Log
from config import config

class DatabaseManager:
    """مدير قاعدة البيانات"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.DATABASE_PATH
        
    async def initialize(self):
        """تهيئة قاعدة البيانات"""
        # إنشاء المجلد إذا لم يكن موجوداً
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # تنفيذ السكيما
        async with aiosqlite.connect(self.db_path) as db:
            with open('database/schema.sql', 'r', encoding='utf-8') as f:
                schema = f.read()
            await db.executescript(schema)
            await db.commit()
    
    async def execute(self, query: str, params: tuple = ()) -> aiosqlite.Cursor:
        """تنفيذ استعلام"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(query, params)
            await db.commit()
            return cursor
    
    async def fetchone(self, query: str, params: tuple = ()) -> Optional[tuple]:
        """جلب صف واحد"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(query, params)
            return await cursor.fetchone()
    
    async def fetchall(self, query: str, params: tuple = ()) -> List[tuple]:
        """جلب كل الصفوف"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(query, params)
            return await cursor.fetchall()
    
    # ====== User Methods ======
    
    async def get_or_create_user(self, discord_id: str, username: str, player_id: str) -> User:
        """الحصول على مستخدم أو إنشاؤه"""
        user_data = await self.fetchone(
            "SELECT * FROM users WHERE discord_id = ?", (discord_id,)
        )
        
        if user_data:
            return User(*user_data)
        
        await self.execute(
            """INSERT INTO users (discord_id, username, player_id) 
               VALUES (?, ?, ?)""",
            (discord_id, username, player_id)
        )
        
        user_data = await self.fetchone(
            "SELECT * FROM users WHERE discord_id = ?", (discord_id,)
        )
        return User(*user_data)
    
    async def get_user_by_discord_id(self, discord_id: str) -> Optional[User]:
        """الحصول على مستخدم بواسطة Discord ID"""
        user_data = await self.fetchone(
            "SELECT * FROM users WHERE discord_id = ?", (discord_id,)
        )
        return User(*user_data) if user_data else None
    
    async def update_user_points(self, user_id: int, points_delta: int):
        """تحديث نقاط المستخدم"""
        await self.execute(
            "UPDATE users SET points = points + ?, updated_at = ? WHERE user_id = ?",
            (points_delta, datetime.now(), user_id)
        )
    
    async def update_user_stats(self, user_id: int, stat_type: str):
        """تحديث إحصائيات المستخدم"""
        if stat_type == 'completed':
            await self.execute(
                """UPDATE users SET completed_bookings = completed_bookings + 1, 
                   total_bookings = total_bookings + 1, updated_at = ? WHERE user_id = ?""",
                (datetime.now(), user_id)
            )
        elif stat_type == 'cancelled':
            await self.execute(
                """UPDATE users SET cancelled_bookings = cancelled_bookings + 1, 
                   updated_at = ? WHERE user_id = ?""",
                (datetime.now(), user_id)
            )
    
    # ====== Booking Methods ======
    
    async def create_booking(self, booking: Booking) -> int:
        """إنشاء حجز جديد"""
        cursor = await self.execute(
            """INSERT INTO bookings 
               (user_id, booking_type, player_name, player_id, alliance_name, 
                scheduled_time, details, created_by, duration_days)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (booking.user_id, booking.booking_type, booking.player_name, 
             booking.player_id, booking.alliance_name, booking.scheduled_time,
             booking.details, booking.created_by, booking.duration_days)
        )
        return cursor.lastrowid
    
    async def get_booking(self, booking_id: int) -> Optional[Booking]:
        """الحصول على حجز"""
        data = await self.fetchone(
            "SELECT * FROM bookings WHERE booking_id = ?", (booking_id,)
        )
        if data:
            return Booking(*data)
        return None
    
    async def get_user_bookings(self, user_id: int, status: str = None) -> List[Booking]:
        """الحصول على حجوزات المستخدم"""
        if status:
            data = await self.fetchall(
                """SELECT * FROM bookings WHERE user_id = ? AND status = ? 
                   ORDER BY scheduled_time ASC""",
                (user_id, status)
            )
        else:
            data = await self.fetchall(
                "SELECT * FROM bookings WHERE user_id = ? ORDER BY scheduled_time ASC",
                (user_id,)
            )
        return [Booking(*row) for row in data]
    
    async def get_bookings_by_type(self, booking_type: str, status: str = 'active') -> List[Booking]:
        """الحصول على حجوزات حسب النوع"""
        data = await self.fetchall(
            """SELECT * FROM bookings WHERE booking_type = ? AND status = ? 
               ORDER BY scheduled_time ASC""",
            (booking_type, status)
        )
        return [Booking(*row) for row in data]
    
    async def get_all_active_bookings(self) -> List[Booking]:
        """الحصول على كل الحجوزات النشطة"""
        data = await self.fetchall(
            "SELECT * FROM bookings WHERE status = 'active' ORDER BY scheduled_time ASC"
        )
        return [Booking(*row) for row in data]
    
    async def update_booking_status(self, booking_id: int, status: str):
        """تحديث حالة الحجز"""
        await self.execute(
            "UPDATE bookings SET status = ?, updated_at = ? WHERE booking_id = ?",
            (status, datetime.now(), booking_id)
        )
    
    async def cancel_booking(self, booking_id: int, reason: str = None):
        """إلغاء حجز"""
        await self.execute(
            """UPDATE bookings SET status = 'cancelled', cancelled_at = ?, 
               cancellation_reason = ?, updated_at = ? WHERE booking_id = ?""",
            (datetime.now(), reason, datetime.now(), booking_id)
        )
    
    async def complete_booking(self, booking_id: int):
        """إكمال حجز"""
        await self.execute(
            """UPDATE bookings SET status = 'completed', completed_at = ?, 
               updated_at = ? WHERE booking_id = ?""",
            (datetime.now(), datetime.now(), booking_id)
        )
    
    async def update_reminder_sent(self, booking_id: int, reminder_type: str):
        """تحديث حالة إرسال التذكير"""
        field_map = {
            '24h': 'reminder_24h_sent',
            '1h': 'reminder_1h_sent',
            'now': 'reminder_now_sent'
        }
        field = field_map.get(reminder_type)
        if field:
            await self.execute(
                f"UPDATE bookings SET {field} = 1 WHERE booking_id = ?",
                (booking_id,)
            )
    
    async def check_booking_conflict(self, user_id: int, scheduled_time: datetime) -> bool:
        """التحقق من تعارض الحجوزات"""
        result = await self.fetchone(
            """SELECT COUNT(*) FROM bookings 
               WHERE user_id = ? AND status = 'active' AND scheduled_time = ?""",
            (user_id, scheduled_time)
        )
        return result[0] > 0 if result else False
    
    async def get_active_bookings_count(self, user_id: int) -> int:
        """عدد الحجوزات النشطة للمستخدم"""
        result = await self.fetchone(
            "SELECT COUNT(*) FROM bookings WHERE user_id = ? AND status = 'active'",
            (user_id,)
        )
        return result[0] if result else 0
    
    # ====== Alliance Methods ======
    
    async def create_alliance(self, name: str, leader_id: int, description: str = '') -> int:
        """إنشاء تحالف جديد"""
        cursor = await self.execute(
            "INSERT INTO alliances (name, leader_id, description) VALUES (?, ?, ?)",
            (name, leader_id, description)
        )
        return cursor.lastrowid
    
    async def get_alliance(self, alliance_id: int) -> Optional[Alliance]:
        """الحصول على تحالف"""
        data = await self.fetchone(
            "SELECT * FROM alliances WHERE alliance_id = ?", (alliance_id,)
        )
        return Alliance(*data) if data else None
    
    async def get_alliance_by_name(self, name: str) -> Optional[Alliance]:
        """الحصول على تحالف بالاسم"""
        data = await self.fetchone(
            "SELECT * FROM alliances WHERE name = ?", (name,)
        )
        return Alliance(*data) if data else None
    
    async def join_alliance(self, user_id: int, alliance_id: int):
        """الانضمام لتحالف"""
        await self.execute(
            "UPDATE users SET alliance_id = ? WHERE user_id = ?",
            (alliance_id, user_id)
        )
        await self.execute(
            "UPDATE alliances SET member_count = member_count + 1 WHERE alliance_id = ?",
            (alliance_id,)
        )
    
    async def leave_alliance(self, user_id: int, alliance_id: int):
        """مغادرة التحالف"""
        await self.execute(
            "UPDATE users SET alliance_id = NULL WHERE user_id = ?",
            (user_id,)
        )
        await self.execute(
            "UPDATE alliances SET member_count = member_count - 1 WHERE alliance_id = ?",
            (alliance_id,)
        )
    
    # ====== Achievement Methods ======
    
    async def award_achievement(self, user_id: int, achievement_type: str, achievement_name: str) -> bool:
        """منح إنجاز"""
        try:
            await self.execute(
                "INSERT INTO achievements (user_id, achievement_type, achievement_name) VALUES (?, ?, ?)",
                (user_id, achievement_type, achievement_name)
            )
            return True
        except:
            return False  # Already has this achievement
    
    async def get_user_achievements(self, user_id: int) -> List[Achievement]:
        """الحصول على إنجازات المستخدم"""
        data = await self.fetchall(
            "SELECT * FROM achievements WHERE user_id = ? ORDER BY earned_at DESC",
            (user_id,)
        )
        return [Achievement(*row) for row in data]
    
    # ====== Log Methods ======
    
    async def log_action(self, action_type: str, description: str, user_id: str = None, 
                        booking_id: int = None, details: str = None):
        """تسجيل عملية"""
        await self.execute(
            """INSERT INTO logs (action_type, user_id, booking_id, description, details)
               VALUES (?, ?, ?, ?, ?)""",
            (action_type, user_id, booking_id, description, details)
        )
    
    async def get_logs(self, limit: int = 100) -> List[Log]:
        """الحصول على السجلات"""
        data = await self.fetchall(
            "SELECT * FROM logs ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
        return [Log(*row) for row in data]
    
    # ====== Statistics Methods ======
    
    async def get_stats(self) -> Dict[str, Any]:
        """إحصائيات عامة"""
        total_bookings = await self.fetchone("SELECT COUNT(*) FROM bookings")
        active_bookings = await self.fetchone("SELECT COUNT(*) FROM bookings WHERE status = 'active'")
        completed_bookings = await self.fetchone("SELECT COUNT(*) FROM bookings WHERE status = 'completed'")
        total_users = await self.fetchone("SELECT COUNT(*) FROM users")
        total_alliances = await self.fetchone("SELECT COUNT(*) FROM alliances")
        
        return {
            'total_bookings': total_bookings[0] if total_bookings else 0,
            'active_bookings': active_bookings[0] if active_bookings else 0,
            'completed_bookings': completed_bookings[0] if completed_bookings else 0,
            'total_users': total_users[0] if total_users else 0,
            'total_alliances': total_alliances[0] if total_alliances else 0
        }
    
    async def get_leaderboard(self, limit: int = 10) -> List[User]:
        """لوحة المتصدرين"""
        data = await self.fetchall(
            "SELECT * FROM users ORDER BY points DESC, completed_bookings DESC LIMIT ?",
            (limit,)
        )
        return [User(*row) for row in data]
    
    async def get_top_alliances(self, limit: int = 10) -> List[Alliance]:
        """أفضل التحالفات"""
        data = await self.fetchall(
            "SELECT * FROM alliances ORDER BY total_points DESC, total_bookings DESC LIMIT ?",
            (limit,)
        )
        return [Alliance(*row) for row in data]

# Instance global
db = DatabaseManager()
