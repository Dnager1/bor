"""
إدارة الصلاحيات - Permissions Manager
Enhanced with owner and database-backed permissions
"""
import discord
from typing import List
from config import config
import logging

logger = logging.getLogger('permissions')


def is_owner(user: discord.User | discord.Member) -> bool:
    """Check if user is the owner"""
    return user.id == config.OWNER_ID


def is_admin(member: discord.Member) -> bool:
    """Check if user is admin (server-based or role-based)"""
    # Owner is always admin
    if is_owner(member):
        return True
    
    # Check server permissions
    if member.guild_permissions.administrator:
        return True
    
    # Check role
    if config.ADMIN_ROLE_ID:
        return any(role.id == config.ADMIN_ROLE_ID for role in member.roles)
    
    return False


async def has_permission(user: discord.User | discord.Member, permission_type: str) -> bool:
    """Check if user has a specific permission"""
    # Owner has all permissions
    if is_owner(user):
        return True
    
    # Check if admin
    if isinstance(user, discord.Member) and is_admin(user):
        return True
    
    # Check database for specific permissions
    try:
        from database import db
        result = await db.fetchone(
            "SELECT COUNT(*) FROM permissions WHERE discord_id = ? AND permission_type = ?",
            (str(user.id), permission_type)
        )
        return result[0] > 0 if result else False
    except Exception as e:
        logger.error(f"Error checking permission: {e}")
        return False


async def grant_permission(user_id: str, permission_type: str, granted_by: str) -> bool:
    """Grant a permission to a user"""
    try:
        from database import db
        await db.execute(
            "INSERT OR IGNORE INTO permissions (discord_id, permission_type, granted_by) VALUES (?, ?, ?)",
            (user_id, permission_type, granted_by)
        )
        logger.info(f"Granted {permission_type} to {user_id} by {granted_by}")
        return True
    except Exception as e:
        logger.error(f"Error granting permission: {e}")
        return False


async def revoke_permission(user_id: str, permission_type: str) -> bool:
    """Revoke a permission from a user"""
    try:
        from database import db
        await db.execute(
            "DELETE FROM permissions WHERE discord_id = ? AND permission_type = ?",
            (user_id, permission_type)
        )
        logger.info(f"Revoked {permission_type} from {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error revoking permission: {e}")
        return False


async def get_user_permissions(user_id: str) -> List[str]:
    """Get all permissions for a user"""
    try:
        from database import db
        results = await db.fetchall(
            "SELECT permission_type FROM permissions WHERE discord_id = ?",
            (user_id,)
        )
        return [row[0] for row in results]
    except Exception as e:
        logger.error(f"Error getting user permissions: {e}")
        return []


# Permission types
PERMISSION_TYPES = [
    'alliance_management',
    'reservations_management',
    'user_management',
    'system_management'
]
