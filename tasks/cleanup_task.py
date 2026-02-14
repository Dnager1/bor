"""
مهمة التنظيف - Cleanup Task
Auto-cleanup of expired bookings and old logs
"""
import discord
from discord.ext import commands, tasks
import logging
from datetime import datetime, timedelta

from database import db
from utils import datetime_helper

logger = logging.getLogger('cleanup')

class CleanupTask(commands.Cog):
    """مهمة تنظيف البيانات المجدولة"""
    
    def __init__(self, bot):
        self.bot = bot
        self.cleanup_expired.start()
        self.cleanup_old_logs.start()
    
    def cog_unload(self):
        """عند إلغاء تحميل الـ Cog"""
        self.cleanup_expired.cancel()
        self.cleanup_old_logs.cancel()
    
    @tasks.loop(hours=6)
    async def cleanup_expired(self):
        """تنظيف الحجوزات المنتهية كل 6 ساعات"""
        try:
            logger.info("🧹 بدء تنظيف الحجوزات المنتهية...")
            
            # Get all active bookings
            bookings = await db.get_all_active_bookings()
            
            expired_count = 0
            now = datetime_helper.get_now()
            
            for booking in bookings:
                # If the booking time + duration has passed
                booking_end_time = booking.scheduled_time + timedelta(days=booking.duration_days)
                
                if datetime_helper.is_past(booking_end_time):
                    # Mark as expired
                    await db.update_booking_status(booking.booking_id, 'expired')
                    expired_count += 1
                    
                    logger.info(f"Expired booking #{booking.booking_id} - ended at {booking_end_time}")
            
            if expired_count > 0:
                logger.info(f"✅ Marked {expired_count} bookings as expired")
                
                await db.log_action(
                    'cleanup',
                    f"Cleaned up {expired_count} expired bookings",
                    None,
                    None
                )
            else:
                logger.info("✅ No expired bookings to clean")
            
        except Exception as e:
            logger.error(f"❌ Error in cleanup: {e}", exc_info=e)
    
    @tasks.loop(hours=24)
    async def cleanup_old_logs(self):
        """تنظيف السجلات القديمة كل 24 ساعة"""
        try:
            logger.info("🧹 بدء تنظيف السجلات القديمة...")
            
            # Delete logs older than 90 days
            cutoff_date = datetime.now() - timedelta(days=90)
            
            result = await db.execute(
                "DELETE FROM logs WHERE created_at < ?",
                (cutoff_date,)
            )
            
            # Get count of deleted rows (approximate)
            count_result = await db.fetchone(
                "SELECT changes()"
            )
            deleted_count = count_result[0] if count_result else 0
            
            if deleted_count > 0:
                logger.info(f"✅ Deleted {deleted_count} old log entries")
                
                await db.log_action(
                    'cleanup',
                    f"Cleaned up {deleted_count} old log entries",
                    None,
                    None
                )
            else:
                logger.info("✅ No old logs to clean")
            
        except Exception as e:
            logger.error(f"❌ Error cleaning old logs: {e}", exc_info=e)
    
    @cleanup_expired.before_loop
    async def before_cleanup(self):
        """الانتظار حتى يصبح البوت جاهزاً"""
        await self.bot.wait_until_ready()
        logger.info("✅ بدأت مهمة التنظيف")
    
    @cleanup_old_logs.before_loop
    async def before_cleanup_logs(self):
        """الانتظار حتى يصبح البوت جاهزاً"""
        await self.bot.wait_until_ready()
        logger.info("✅ بدأت مهمة تنظيف السجلات")

async def setup(bot):
    """إعداد الـ Cog"""
    await bot.add_cog(CleanupTask(bot))
