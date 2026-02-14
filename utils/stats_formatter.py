"""
نظام الإحصائيات - Statistics System
Enhanced statistics display with charts and analytics
"""
import discord
from typing import Dict, List, Any
from datetime import datetime, timedelta
import math


class StatsFormatter:
    """Formatter for statistics display"""
    
    @staticmethod
    def format_number(num: int) -> str:
        """Format number with commas"""
        return f"{num:,}"
    
    @staticmethod
    def format_percentage(value: float, total: float) -> str:
        """Calculate and format percentage"""
        if total == 0:
            return "0%"
        percentage = (value / total) * 100
        return f"{percentage:.1f}%"
    
    @staticmethod
    def create_progress_bar(value: int, max_value: int, length: int = 10) -> str:
        """Create ASCII progress bar"""
        if max_value == 0:
            filled = 0
        else:
            filled = math.floor((value / max_value) * length)
        
        bar = "█" * filled + "░" * (length - filled)
        percentage = StatsFormatter.format_percentage(value, max_value)
        return f"{bar} {percentage}"
    
    @staticmethod
    def create_user_stats_embed(user: Any, stats: Dict) -> discord.Embed:
        """Create user statistics embed"""
        embed = discord.Embed(
            title=f"📊 إحصائيات {user.username}",
            color=discord.Color.blue()
        )
        
        # Basic stats
        embed.add_field(
            name="📋 الحجوزات | Reservations",
            value=(
                f"إجمالي | Total: **{stats.get('total_bookings', 0)}**\n"
                f"نشطة | Active: **{stats.get('active_bookings', 0)}**\n"
                f"مكتملة | Completed: **{stats.get('completed_bookings', 0)}**\n"
                f"ملغاة | Cancelled: **{stats.get('cancelled_bookings', 0)}**"
            ),
            inline=True
        )
        
        # Points
        embed.add_field(
            name="⭐ النقاط | Points",
            value=f"**{stats.get('points', 0)}** نقطة",
            inline=True
        )
        
        # Alliance
        alliance_name = stats.get('alliance_name', 'غير منضم | Not in alliance')
        alliance_rank = stats.get('alliance_rank', '-')
        embed.add_field(
            name="🤝 التحالف | Alliance",
            value=f"**{alliance_name}**\nالرتبة | Rank: **{alliance_rank}**",
            inline=True
        )
        
        # Completion rate
        total = stats.get('total_bookings', 0)
        completed = stats.get('completed_bookings', 0)
        if total > 0:
            completion_bar = StatsFormatter.create_progress_bar(completed, total)
            embed.add_field(
                name="✅ معدل الإنجاز | Completion Rate",
                value=completion_bar,
                inline=False
            )
        
        # Last activity
        if 'last_activity' in stats:
            embed.add_field(
                name="🕐 آخر نشاط | Last Activity",
                value=f"<t:{int(stats['last_activity'].timestamp())}:R>",
                inline=True
            )
        
        embed.set_footer(text="📊 إحصائيات محدثة")
        embed.timestamp = datetime.now()
        
        return embed
    
    @staticmethod
    def create_leaderboard_embed(users: List[Any], title: str = "🏆 المتصدرين") -> discord.Embed:
        """Create leaderboard embed"""
        embed = discord.Embed(
            title=title,
            description="أفضل المستخدمين حسب النقاط\nTop users by points",
            color=discord.Color.gold()
        )
        
        medals = ["🥇", "🥈", "🥉"]
        
        for idx, user in enumerate(users[:10], 1):
            medal = medals[idx-1] if idx <= 3 else f"**{idx}.**"
            
            embed.add_field(
                name=f"{medal} {user.username}",
                value=(
                    f"⭐ {user.points} نقطة | points\n"
                    f"📋 {user.total_bookings} حجز | bookings"
                ),
                inline=False
            )
        
        embed.set_footer(text=f"إجمالي المستخدمين | Total users: {len(users)}")
        
        return embed
    
    @staticmethod
    def create_bot_stats_embed(stats: Dict) -> discord.Embed:
        """Create bot statistics embed"""
        embed = discord.Embed(
            title="📊 إحصائيات البوت | Bot Statistics",
            color=discord.Color.green()
        )
        
        # Bookings stats
        embed.add_field(
            name="📋 الحجوزات | Bookings",
            value=(
                f"إجمالي | Total: **{stats.get('total_bookings', 0)}**\n"
                f"نشطة | Active: **{stats.get('active_bookings', 0)}**\n"
                f"مكتملة | Completed: **{stats.get('completed_bookings', 0)}**"
            ),
            inline=True
        )
        
        # Users stats
        embed.add_field(
            name="👥 المستخدمون | Users",
            value=f"**{stats.get('total_users', 0)}** مستخدم",
            inline=True
        )
        
        # Alliances stats
        embed.add_field(
            name="🤝 التحالفات | Alliances",
            value=f"**{stats.get('total_alliances', 0)}** تحالف",
            inline=True
        )
        
        # Booking types breakdown
        if 'booking_types' in stats:
            types_text = ""
            for booking_type, count in stats['booking_types'].items():
                emoji = {
                    'building': '🏗️',
                    'training': '⚔️',
                    'research': '🔬'
                }.get(booking_type, '📋')
                types_text += f"{emoji} {booking_type}: **{count}**\n"
            
            embed.add_field(
                name="📊 أنواع الحجوزات | Booking Types",
                value=types_text,
                inline=False
            )
        
        embed.set_footer(text="📊 إحصائيات محدثة")
        embed.timestamp = datetime.now()
        
        return embed
    
    @staticmethod
    def create_alliance_stats_embed(alliance: Any, members: List[Any]) -> discord.Embed:
        """Create alliance statistics embed"""
        embed = discord.Embed(
            title=f"🤝 إحصائيات {alliance.name}",
            color=discord.Color.purple()
        )
        
        # Basic info
        embed.add_field(
            name="ℹ️ معلومات أساسية | Basic Info",
            value=(
                f"المستوى | Level: **{alliance.level}**\n"
                f"الأعضاء | Members: **{alliance.member_count}/{alliance.max_members}**\n"
                f"القوة الكلية | Total Power: **{alliance.total_power:,}**"
            ),
            inline=True
        )
        
        # Stats
        embed.add_field(
            name="📊 الإحصائيات | Statistics",
            value=(
                f"حجوزات كلية | Total Bookings: **{alliance.total_bookings}**\n"
                f"نقاط كلية | Total Points: **{alliance.total_points}**"
            ),
            inline=True
        )
        
        # Top members
        if members:
            top_members_text = ""
            for member in members[:5]:
                top_members_text += f"• {member.username} - {member.points} نقطة\n"
            
            embed.add_field(
                name="⭐ أفضل الأعضاء | Top Members",
                value=top_members_text,
                inline=False
            )
        
        # Member capacity
        capacity_bar = StatsFormatter.create_progress_bar(
            alliance.member_count,
            alliance.max_members
        )
        embed.add_field(
            name="👥 سعة الأعضاء | Member Capacity",
            value=capacity_bar,
            inline=False
        )
        
        if alliance.description:
            embed.add_field(
                name="📝 الوصف | Description",
                value=alliance.description,
                inline=False
            )
        
        embed.set_footer(text=f"تاريخ الإنشاء | Created: {alliance.created_at}")
        
        return embed


# Export
__all__ = ['StatsFormatter']
