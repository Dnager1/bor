"""
مهمة التنظيف - Cleanup Task
"""
import discord
from discord.ext import commands, tasks
import logging
from datetime import datetime

from database import db
from utils import datetime_helper

logger = logging.getLogger('cleanup')

class CleanupTask(commands.Cog):
    """مهمة تنظيف البيانات المجدولة"""
    
    def __init__(self, bot):
        self.bot = bot
        self.cleanup_expired.start()
    
    def cog_unload(self):
        """عند إلغاء تحميل الـ Cog"""
        self.cleanup_expired.cancel()
    
    @tasks.loop(hours=6)
    async def cleanup_expired(self):
        """تنظيف الحجوزات المنتهية كل 6 ساعات"""
        try:
            logger.info("🧹 بدء تنظيف الحجوزات المنتهية...")
            
            # الحصول على الحجوزات النشطة
            bookings = await db.get_all_active_bookings()
            
            expired_count = 0
            now = datetime_helper.get_now()
            
            for booking in bookings:
                # إذا مر الموعد بأكثر من 24 ساعة
                if datetime_helper.is_past(booking.scheduled_time):
                    time_passed = now - booking.scheduled_time
                    if time_passed.total_seconds() > 86400:  # 24 ساعة
                        await db.update_booking_status(booking.booking_id, 'expired')
                        expired_count += 1
            
            if expired_count > 0:
                logger.info(f"✅ تم تحديث {expired_count} حجز منتهي")
                
                await db.log_action(
                    'cleanup',
                    f"تم تنظيف {expired_count} حجز منتهي",
                    None,
                    None
                )
            else:
                logger.info("✅ لا توجد حجوزات منتهية")
            
        except Exception as e:
            logger.error(f"❌ خطأ في التنظيف: {e}", exc_info=e)
    
    @cleanup_expired.before_loop
    async def before_cleanup(self):
        """الانتظار حتى يصبح البوت جاهزاً"""
        await self.bot.wait_until_ready()
        logger.info("✅ بدأت مهمة التنظيف")

async def setup(bot):
    """إعداد الـ Cog"""
    await bot.add_cog(CleanupTask(bot))
