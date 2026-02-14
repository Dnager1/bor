"""
مهمة التذكيرات - Reminders Task
Enhanced with configurable reminder times and i18n support
"""
import discord
from discord.ext import commands, tasks
import logging
from datetime import datetime, timedelta

from database import db
from utils import datetime_helper
from utils.translator import translator, get_text
from utils.ui_components import create_colored_embed
from config import config

logger = logging.getLogger('reminders')

class RemindersTask(commands.Cog):
    """مهمة التذكيرات المجدولة"""
    
    def __init__(self, bot):
        self.bot = bot
        self.check_reminders.start()
        
        # Configurable reminder times (in hours before event)
        self.reminder_times = [
            24,  # 1 day before
            6,   # 6 hours before
            3,   # 3 hours before
            1,   # 1 hour before
        ]
    
    def cog_unload(self):
        """عند إلغاء تحميل الـ Cog"""
        self.check_reminders.cancel()
    
    @tasks.loop(minutes=5)
    async def check_reminders(self):
        """فحص التذكيرات كل 5 دقائق"""
        try:
            logger.info("🔔 فحص التذكيرات...")
            
            # Get all active bookings
            bookings = await db.get_all_active_bookings()
            
            sent_count = 0
            now = datetime.now(datetime_helper.get_timezone())
            
            for booking in bookings:
                # Check each reminder time
                for hours in self.reminder_times:
                    if self._should_send_reminder(booking, hours, now):
                        await self.send_reminder(booking, hours)
                        await self._mark_reminder_sent(booking.booking_id, hours)
                        sent_count += 1
                
                # Check for immediate reminder (event time)
                if self._should_send_now_reminder(booking, now):
                    await self.send_now_reminder(booking)
                    await db.update_reminder_sent(booking.booking_id, 'now')
                    sent_count += 1
            
            if sent_count > 0:
                logger.info(f"✅ تم إرسال {sent_count} تذكير")
            
        except Exception as e:
            logger.error(f"❌ خطأ في فحص التذكيرات: {e}", exc_info=e)
    
    @check_reminders.before_loop
    async def before_check_reminders(self):
        """الانتظار حتى يصبح البوت جاهزاً"""
        await self.bot.wait_until_ready()
        logger.info("✅ بدأت مهمة التذكيرات")
    
    def _should_send_reminder(self, booking, hours: int, now: datetime) -> bool:
        """Check if reminder should be sent"""
        reminder_time = booking.scheduled_time - timedelta(hours=hours)
        
        # Check if it's time to send and not already sent
        if now >= reminder_time:
            # Check if already sent (use reminder flags based on hours)
            if hours == 24 and booking.reminder_24h_sent:
                return False
            elif hours == 1 and booking.reminder_1h_sent:
                return False
            
            # Check if we're within the reminder window (5 minutes after reminder time)
            if now - reminder_time < timedelta(minutes=5):
                return True
        
        return False
    
    def _should_send_now_reminder(self, booking, now: datetime) -> bool:
        """Check if 'now' reminder should be sent"""
        if booking.reminder_now_sent:
            return False
        
        # Send if event time has arrived
        return now >= booking.scheduled_time and now - booking.scheduled_time < timedelta(minutes=5)
    
    async def _mark_reminder_sent(self, booking_id: int, hours: int):
        """Mark reminder as sent in database"""
        if hours == 24:
            await db.update_reminder_sent(booking_id, '24h')
        elif hours == 1:
            await db.update_reminder_sent(booking_id, '1h')
    
    async def send_reminder(self, booking, hours: int):
        """إرسال تذكير مخصص"""
        try:
            user = await self.bot.fetch_user(int(booking.created_by))
            user_id = str(booking.created_by)
            
            # Load user language
            await translator.load_user_language_from_db(db, user_id)
            
            # Determine reminder message based on hours
            if hours >= 24:
                title = get_text(user_id, 'reminders.before_1d')
                color = 'info'
            elif hours >= 6:
                title = get_text(user_id, 'reminders.before_6h')
                color = 'info'
            elif hours >= 3:
                title = get_text(user_id, 'reminders.before_3h')
                color = 'warning'
            else:
                title = get_text(user_id, 'reminders.before_1h')
                color = 'warning'
            
            time_str = booking.scheduled_time.strftime('%Y-%m-%d %H:%M UTC')
            
            description = get_text(user_id, 'reminders.upcoming').replace(
                '{time}', f"{hours}h"
            )
            
            embed = create_colored_embed(
                f"🔔 {title}",
                description,
                color
            )
            
            # Booking details
            type_emoji = {'building': '🏗️', 'training': '⚔️', 'research': '🔬'}
            type_name = booking.booking_type.title()
            
            embed.add_field(
                name=get_text(user_id, 'reminders.type').replace('{type}', ''),
                value=f"{type_emoji.get(booking.booking_type, '📅')} {type_name}",
                inline=True
            )
            
            embed.add_field(
                name="ID",
                value=f"#{booking.booking_id}",
                inline=True
            )
            
            embed.add_field(
                name="Time",
                value=time_str,
                inline=False
            )
            
            embed.add_field(
                name="Member",
                value=booking.player_name,
                inline=True
            )
            
            embed.add_field(
                name="Alliance",
                value=booking.alliance_name,
                inline=True
            )
            
            if booking.details:
                embed.add_field(
                    name="Details",
                    value=booking.details,
                    inline=False
                )
            
            await user.send(embed=embed)
            
            await db.log_action(
                f'reminder_{hours}h',
                f"Sent {hours}h reminder for booking #{booking.booking_id}",
                booking.created_by,
                booking.booking_id
            )
            
            logger.info(f"Reminder {hours}h: booking #{booking.booking_id}")
            
        except discord.Forbidden:
            logger.warning(f"Cannot send DM to user {booking.created_by}")
        except Exception as e:
            logger.error(f"Error sending {hours}h reminder: {e}")
    
    async def send_now_reminder(self, booking):
        """إرسال تذكير الآن"""
        try:
            user = await self.bot.fetch_user(int(booking.created_by))
            user_id = str(booking.created_by)
            
            # Load user language
            await translator.load_user_language_from_db(db, user_id)
            
            embed = create_colored_embed(
                "🚨 " + get_text(user_id, 'reminders.title'),
                get_text(user_id, 'reminders.upcoming'),
                'error'
            )
            
            # Booking details
            type_emoji = {'building': '🏗️', 'training': '⚔️', 'research': '🔬'}
            type_name = booking.booking_type.title()
            
            embed.add_field(
                name="Type",
                value=f"{type_emoji.get(booking.booking_type, '📅')} {type_name}",
                inline=True
            )
            
            embed.add_field(
                name="ID",
                value=f"#{booking.booking_id}",
                inline=True
            )
            
            embed.add_field(
                name="Member",
                value=booking.player_name,
                inline=True
            )
            
            embed.add_field(
                name="Alliance",
                value=booking.alliance_name,
                inline=True
            )
            
            if booking.details:
                embed.add_field(
                    name="Details",
                    value=booking.details,
                    inline=False
                )
            
            await user.send(embed=embed)
            
            await db.log_action(
                'reminder_now',
                f"Sent immediate reminder for booking #{booking.booking_id}",
                booking.created_by,
                booking.booking_id
            )
            
            logger.info(f"Immediate reminder: booking #{booking.booking_id}")
            
        except discord.Forbidden:
            logger.warning(f"Cannot send DM to user {booking.created_by}")
        except Exception as e:
            logger.error(f"Error sending immediate reminder: {e}")

async def setup(bot):
    """إعداد الـ Cog"""
    await bot.add_cog(RemindersTask(bot))
