"""
إدارة الصلاحيات - Permissions Manager
"""
import discord
from typing import Optional
from config import config

class PermissionsManager:
    """إدارة الصلاحيات"""
    
    @staticmethod
    def is_admin(member: discord.Member) -> bool:
        """التحقق من أن المستخدم مشرف"""
        if member.guild_permissions.administrator:
            return True
        
        if config.ADMIN_ROLE_ID:
            return any(role.id == config.ADMIN_ROLE_ID for role in member.roles)
        
        return False
    
    @staticmethod
    def is_moderator(member: discord.Member) -> bool:
        """التحقق من أن المستخدم مراقب"""
        if PermissionsManager.is_admin(member):
            return True
        
        if config.MODERATOR_ROLE_ID:
            return any(role.id == config.MODERATOR_ROLE_ID for role in member.roles)
        
        return False
    
    @staticmethod
    def can_manage_booking(member: discord.Member, booking_owner_discord_id: str) -> bool:
        """التحقق من إمكانية إدارة الحجز"""
        # المشرفون يمكنهم إدارة كل الحجوزات
        if PermissionsManager.is_admin(member):
            return True
        
        # المراقبون يمكنهم إدارة كل الحجوزات
        if PermissionsManager.is_moderator(member):
            return True
        
        # صاحب الحجز يمكنه إدارة حجزه
        return str(member.id) == booking_owner_discord_id
    
    @staticmethod
    def can_use_admin_commands(member: discord.Member) -> bool:
        """التحقق من إمكانية استخدام أوامر الإدارة"""
        return PermissionsManager.is_admin(member)
    
    @staticmethod
    async def check_permissions(interaction: discord.Interaction, require_admin: bool = False) -> tuple[bool, Optional[str]]:
        """التحقق من الصلاحيات"""
        member = interaction.user
        
        if require_admin:
            if not PermissionsManager.is_admin(member):
                return False, "❌ هذا الأمر متاح للمشرفين فقط!"
        
        return True, None

permissions = PermissionsManager()
