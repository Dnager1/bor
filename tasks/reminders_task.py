"""
مهمة التذكيرات - Reminders Task
"""
import discord
from discord.ext import commands, tasks
import logging
from datetime import datetime

from database import db
from utils import datetime_helper, embeds
from config import config

logger = logging.getLogger('reminders')

class RemindersTask(commands.Cog):
    """مهمة التذكيرات المجدولة"""
    
    def __init__(self, bot):
        self.bot = bot
        self.check_reminders.start()
    
    def cog_unload(self):
        """عند إلغاء تحميل الـ Cog"""
        self.check_reminders.cancel()
    
    @tasks.loop(minutes=5)
    async def check_reminders(self):
        """فحص التذكيرات كل 5 دقائق"""
        try:
            logger.info("🔔 فحص التذكيرات...")
            
            # الحصول على كل الحجوزات النشطة
            bookings = await db.get_all_active_bookings()
            
            sent_count = 0
            
            for booking in bookings:
                # تذكير 24 ساعة
                if datetime_helper.should_send_24h_reminder(booking):
                    await self.send_24h_reminder(booking)
                    await db.update_reminder_sent(booking.booking_id, '24h')
                    sent_count += 1
                
                # تذكير 1 ساعة
                elif datetime_helper.should_send_1h_reminder(booking):
                    await self.send_1h_reminder(booking)
                    await db.update_reminder_sent(booking.booking_id, '1h')
                    sent_count += 1
                
                # تذكير الآن
                elif datetime_helper.should_send_now_reminder(booking):
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
    
    async def send_24h_reminder(self, booking):
        """إرسال تذكير 24 ساعة"""
        try:
            user = await self.bot.fetch_user(int(booking.created_by))
            
            embed = embeds.create_info_embed(
                "🔔 تذكير: موعدك خلال 24 ساعة",
                f"لديك موعد قادم في غضون 24 ساعة!"
            )
            
            booking_info = config.BOOKING_TYPES.get(booking.booking_type, {})
            emoji = booking_info.get('emoji', '📅')
            type_name = booking_info.get('name', booking.booking_type)
            
            from utils.formatters import formatters
            
            embed.add_field(name="النوع", value=f"{emoji} {type_name}", inline=True)
            embed.add_field(name="رقم الحجز", value=f"#{booking.booking_id}", inline=True)
            embed.add_field(
                name="الموعد",
                value=formatters.format_datetime(booking.scheduled_time),
                inline=False
            )
            embed.add_field(name="اللاعب", value=booking.player_name, inline=True)
            embed.add_field(name="التحالف", value=booking.alliance_name, inline=True)
            
            if booking.details:
                embed.add_field(name="التفاصيل", value=booking.details, inline=False)
            
            await user.send(embed=embed)
            
            await db.log_action(
                'reminder_24h',
                f"تم إرسال تذكير 24 ساعة للحجز #{booking.booking_id}",
                booking.created_by,
                booking.booking_id
            )
            
            logger.info(f"تذكير 24ساعة: حجز #{booking.booking_id}")
            
        except Exception as e:
            logger.error(f"خطأ في إرسال تذكير 24 ساعة: {e}")
    
    async def send_1h_reminder(self, booking):
        """إرسال تذكير 1 ساعة"""
        try:
            # إرسال رسالة خاصة
            user = await self.bot.fetch_user(int(booking.created_by))
            
            embed = embeds.create_warning_embed(
                "⚠️ تذكير: موعدك خلال ساعة!",
                f"موعدك قريب جداً!"
            )
            
            booking_info = config.BOOKING_TYPES.get(booking.booking_type, {})
            emoji = booking_info.get('emoji', '📅')
            type_name = booking_info.get('name', booking.booking_type)
            
            from utils.formatters import formatters
            
            embed.add_field(name="النوع", value=f"{emoji} {type_name}", inline=True)
            embed.add_field(name="رقم الحجز", value=f"#{booking.booking_id}", inline=True)
            embed.add_field(
                name="الموعد",
                value=formatters.format_datetime(booking.scheduled_time),
                inline=False
            )
            
            await user.send(embed=embed)
            
            await db.log_action(
                'reminder_1h',
                f"تم إرسال تذكير 1 ساعة للحجز #{booking.booking_id}",
                booking.created_by,
                booking.booking_id
            )
            
            logger.info(f"تذكير 1 ساعة: حجز #{booking.booking_id}")
            
        except Exception as e:
            logger.error(f"خطأ في إرسال تذكير 1 ساعة: {e}")
    
    async def send_now_reminder(self, booking):
        """إرسال تذكير الآن"""
        try:
            user = await self.bot.fetch_user(int(booking.created_by))
            
            embed = embeds.create_warning_embed(
                "🚨 الموعد الآن!",
                f"حان موعد حجزك!"
            )
            
            booking_info = config.BOOKING_TYPES.get(booking.booking_type, {})
            emoji = booking_info.get('emoji', '📅')
            type_name = booking_info.get('name', booking.booking_type)
            
            from utils.formatters import formatters
            
            embed.add_field(name="النوع", value=f"{emoji} {type_name}", inline=True)
            embed.add_field(name="رقم الحجز", value=f"#{booking.booking_id}", inline=True)
            embed.add_field(name="اللاعب", value=booking.player_name, inline=True)
            embed.add_field(name="التحالف", value=booking.alliance_name, inline=True)
            
            if booking.details:
                embed.add_field(name="التفاصيل", value=booking.details, inline=False)
            
            embed.add_field(
                name="💡 تذكير",
                value=f"بعد إتمام المهمة، استخدم `/complete {booking.booking_id}` للحصول على النقاط!",
                inline=False
            )
            
            await user.send(embed=embed)
            
            await db.log_action(
                'reminder_now',
                f"تم إرسال تذكير الآن للحجز #{booking.booking_id}",
                booking.created_by,
                booking.booking_id
            )
            
            logger.info(f"تذكير الآن: حجز #{booking.booking_id}")
            
        except Exception as e:
            logger.error(f"خطأ في إرسال تذكير الآن: {e}")

async def setup(bot):
    """إعداد الـ Cog"""
    await bot.add_cog(RemindersTask(bot))
