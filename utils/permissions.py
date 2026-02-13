"""
إدارة الصلاحيات - Permissions Manager
Enhanced with owner and database-backed permissions
"""
import discord
from typing import Optional, Dict, List
from config import config
import json
import logging

logger = logging.getLogger('permissions')

class PermissionsManager:
    """إدارة الصلاحيات"""
    
    def __init__(self):
        self.db = None
    
    def set_db(self, db_manager):
        """تعيين مدير قاعدة البيانات"""
        self.db = db_manager
    
    @staticmethod
    def is_owner(user: discord.User | discord.Member) -> bool:
        """التحقق من أن المستخدم هو المالك"""
        return user.id == config.OWNER_ID
    
    async def get_user_role(self, discord_id: str) -> Optional[str]:
        """الحصول على دور المستخدم من قاعدة البيانات"""
        if not self.db:
            return None
        
        try:
            result = await self.db.fetchone(
                "SELECT role FROM bot_permissions WHERE discord_id = ?",
                (discord_id,)
            )
            return result[0] if result else None
        except Exception as e:
            logger.error(f"خطأ في الحصول على دور المستخدم: {e}")
            return None
    
    async def get_user_permissions(self, discord_id: str) -> Dict:
        """الحصول على صلاحيات المستخدم من قاعدة البيانات"""
        if not self.db:
            return {}
        
        try:
            result = await self.db.fetchone(
                "SELECT permissions FROM bot_permissions WHERE discord_id = ?",
                (discord_id,)
            )
            if result and result[0]:
                return json.loads(result[0])
            return {}
        except Exception as e:
            logger.error(f"خطأ في الحصول على صلاحيات المستخدم: {e}")
            return {}
    
    async def is_admin(self, member: discord.Member) -> bool:
        """التحقق من أن المستخدم مشرف"""
        # المالك هو مشرف بشكل تلقائي
        if self.is_owner(member):
            return True
        
        # التحقق من قاعدة البيانات
        user_role = await self.get_user_role(str(member.id))
        if user_role in ['owner', 'admin']:
            return True
        
        # التحقق من صلاحيات السيرفر
        if member.guild_permissions.administrator:
            return True
        
        # التحقق من الأدوار
        if config.ADMIN_ROLE_ID:
            return any(role.id == config.ADMIN_ROLE_ID for role in member.roles)
        
        return False
    
    async def is_moderator(self, member: discord.Member) -> bool:
        """التحقق من أن المستخدم مراقب"""
        # المالك والمشرف هم مراقبون بشكل تلقائي
        if self.is_owner(member):
            return True
        
        if await self.is_admin(member):
            return True
        
        # التحقق من قاعدة البيانات
        user_role = await self.get_user_role(str(member.id))
        if user_role in ['owner', 'admin', 'moderator']:
            return True
        
        # التحقق من الأدوار
        if config.MODERATOR_ROLE_ID:
            return any(role.id == config.MODERATOR_ROLE_ID for role in member.roles)
        
        return False
    
    async def has_permission(self, member: discord.Member, permission: str) -> bool:
        """التحقق من أن المستخدم لديه صلاحية معينة"""
        # المالك لديه كل الصلاحيات
        if self.is_owner(member):
            return True
        
        # التحقق من الصلاحيات المخصصة
        perms = await self.get_user_permissions(str(member.id))
        return perms.get(permission, False)
    
    async def can_manage_booking(self, member: discord.Member, booking_owner_discord_id: str) -> bool:
        """التحقق من إمكانية إدارة الحجز"""
        # المالك يمكنه إدارة كل شيء
        if self.is_owner(member):
            return True
        
        # المشرفون يمكنهم إدارة كل الحجوزات
        if await self.is_admin(member):
            return True
        
        # المراقبون يمكنهم إدارة كل الحجوزات
        if await self.is_moderator(member):
            return True
        
        # صاحب الحجز يمكنه إدارة حجزه
        return str(member.id) == booking_owner_discord_id
    
    async def can_use_admin_commands(self, member: discord.Member) -> bool:
        """التحقق من إمكانية استخدام أوامر الإدارة"""
        return await self.is_admin(member) or self.is_owner(member)
    
    async def check_permissions(self, interaction: discord.Interaction, require_admin: bool = False, require_owner: bool = False) -> tuple[bool, Optional[str]]:
        """التحقق من الصلاحيات"""
        member = interaction.user
        
        if require_owner:
            if not self.is_owner(member):
                return False, "❌ هذا الأمر متاح للمالك فقط!"
        
        if require_admin:
            if not await self.is_admin(member):
                return False, "❌ هذا الأمر متاح للمشرفين فقط!"
        
        return True, None
    
    async def set_user_role(self, discord_id: str, username: str, role: str, granted_by: str, notes: str = None) -> bool:
        """تعيين دور المستخدم"""
        if not self.db:
            return False
        
        try:
            # التحقق من وجود المستخدم
            existing = await self.db.fetchone(
                "SELECT role FROM bot_permissions WHERE discord_id = ?",
                (discord_id,)
            )
            
            old_role = existing[0] if existing else None
            
            if existing:
                # تحديث الدور
                await self.db.execute(
                    """UPDATE bot_permissions 
                       SET role = ?, username = ?, granted_by = ?, 
                           updated_at = CURRENT_TIMESTAMP, notes = ?
                       WHERE discord_id = ?""",
                    (role, username, granted_by, notes, discord_id)
                )
            else:
                # إضافة دور جديد
                await self.db.execute(
                    """INSERT INTO bot_permissions 
                       (discord_id, username, role, granted_by, notes)
                       VALUES (?, ?, ?, ?, ?)""",
                    (discord_id, username, role, granted_by, notes)
                )
            
            # تسجيل التغيير
            await self.db.execute(
                """INSERT INTO permissions_log 
                   (action, target_discord_id, target_username, performed_by, 
                    old_role, new_role, reason)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                ('role_changed', discord_id, username, granted_by, 
                 old_role, role, notes)
            )
            
            logger.info(f"تم تعيين دور {role} للمستخدم {username} ({discord_id})")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في تعيين دور المستخدم: {e}")
            return False
    
    async def grant_permission(self, discord_id: str, permission: str, granted_by: str) -> bool:
        """منح صلاحية معينة للمستخدم"""
        if not self.db:
            return False
        
        try:
            perms = await self.get_user_permissions(discord_id)
            perms[permission] = True
            
            await self.db.execute(
                """UPDATE bot_permissions 
                   SET permissions = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE discord_id = ?""",
                (json.dumps(perms), discord_id)
            )
            
            # تسجيل التغيير
            await self.db.execute(
                """INSERT INTO permissions_log 
                   (action, target_discord_id, performed_by, permissions_changed)
                   VALUES (?, ?, ?, ?)""",
                ('permission_granted', discord_id, granted_by, permission)
            )
            
            return True
        except Exception as e:
            logger.error(f"خطأ في منح الصلاحية: {e}")
            return False
    
    async def revoke_permission(self, discord_id: str, permission: str, revoked_by: str) -> bool:
        """إلغاء صلاحية معينة من المستخدم"""
        if not self.db:
            return False
        
        try:
            perms = await self.get_user_permissions(discord_id)
            if permission in perms:
                perms[permission] = False
            
            await self.db.execute(
                """UPDATE bot_permissions 
                   SET permissions = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE discord_id = ?""",
                (json.dumps(perms), discord_id)
            )
            
            # تسجيل التغيير
            await self.db.execute(
                """INSERT INTO permissions_log 
                   (action, target_discord_id, performed_by, permissions_changed)
                   VALUES (?, ?, ?, ?)""",
                ('permission_revoked', discord_id, revoked_by, permission)
            )
            
            return True
        except Exception as e:
            logger.error(f"خطأ في إلغاء الصلاحية: {e}")
            return False
    
    async def remove_user_role(self, discord_id: str, removed_by: str) -> bool:
        """إزالة دور المستخدم"""
        if not self.db:
            return False
        
        try:
            # الحصول على الدور الحالي
            result = await self.db.fetchone(
                "SELECT role, username FROM bot_permissions WHERE discord_id = ?",
                (discord_id,)
            )
            
            if not result:
                return False
            
            old_role, username = result
            
            # حذف السجل
            await self.db.execute(
                "DELETE FROM bot_permissions WHERE discord_id = ?",
                (discord_id,)
            )
            
            # تسجيل التغيير
            await self.db.execute(
                """INSERT INTO permissions_log 
                   (action, target_discord_id, target_username, performed_by, old_role)
                   VALUES (?, ?, ?, ?, ?)""",
                ('role_removed', discord_id, username, removed_by, old_role)
            )
            
            return True
        except Exception as e:
            logger.error(f"خطأ في إزالة دور المستخدم: {e}")
            return False
    
    async def list_all_permissions(self) -> List[Dict]:
        """الحصول على قائمة بكل المستخدمين وصلاحياتهم"""
        if not self.db:
            return []
        
        try:
            results = await self.db.fetchall(
                """SELECT discord_id, username, role, permissions, granted_at, granted_by
                   FROM bot_permissions 
                   ORDER BY 
                     CASE role 
                       WHEN 'owner' THEN 1
                       WHEN 'admin' THEN 2
                       WHEN 'moderator' THEN 3
                       ELSE 4
                     END, username"""
            )
            
            permissions_list = []
            for row in results:
                perms = json.loads(row[3]) if row[3] else {}
                permissions_list.append({
                    'discord_id': row[0],
                    'username': row[1],
                    'role': row[2],
                    'permissions': perms,
                    'granted_at': row[4],
                    'granted_by': row[5]
                })
            
            return permissions_list
        except Exception as e:
            logger.error(f"خطأ في الحصول على قائمة الصلاحيات: {e}")
            return []

# نسخة للاستخدام المباشر (للتوافق مع الكود القديم)
class LegacyPermissions:
    """وظائف الصلاحيات القديمة للتوافق"""
    
    @staticmethod
    def is_admin(member: discord.Member) -> bool:
        """التحقق من أن المستخدم مشرف (نسخة متزامنة)"""
        # المالك هو مشرف بشكل تلقائي
        if member.id == config.OWNER_ID:
            return True
        
        if member.guild_permissions.administrator:
            return True
        
        if config.ADMIN_ROLE_ID:
            return any(role.id == config.ADMIN_ROLE_ID for role in member.roles)
        
        return False
    
    @staticmethod
    def is_moderator(member: discord.Member) -> bool:
        """التحقق من أن المستخدم مراقب (نسخة متزامنة)"""
        if member.id == config.OWNER_ID:
            return True
        
        if LegacyPermissions.is_admin(member):
            return True
        
        if config.MODERATOR_ROLE_ID:
            return any(role.id == config.MODERATOR_ROLE_ID for role in member.roles)
        
        return False
    
    @staticmethod
    def can_manage_booking(member: discord.Member, booking_owner_discord_id: str) -> bool:
        """التحقق من إمكانية إدارة الحجز"""
        if member.id == config.OWNER_ID:
            return True
        
        if LegacyPermissions.is_admin(member):
            return True
        
        if LegacyPermissions.is_moderator(member):
            return True
        
        return str(member.id) == booking_owner_discord_id
    
    @staticmethod
    def can_use_admin_commands(member: discord.Member) -> bool:
        """التحقق من إمكانية استخدام أوامر الإدارة"""
        return LegacyPermissions.is_admin(member) or member.id == config.OWNER_ID

permissions_manager = PermissionsManager()
permissions = LegacyPermissions()
