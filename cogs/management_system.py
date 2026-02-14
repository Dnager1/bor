"""
نظام الإدارة - Management System
Comprehensive admin panel with permissions control
"""
import discord
from discord import app_commands
from discord.ext import commands
from discord import ui
import logging
from datetime import datetime

from utils.translator import translator, get_text
from utils.ui_components import create_colored_embed
from utils import permissions
from database import db

logger = logging.getLogger('management_system')


class ManagementPanelView(discord.ui.View):
    """Management panel main view"""
    
    def __init__(self, user_id: str, is_owner: bool = False):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.is_owner = is_owner
        self._build_buttons()
    
    def _build_buttons(self):
        """Build management panel buttons"""
        user_id = self.user_id
        
        # Row 1: Alliance and Reservations management
        self.add_item(discord.ui.Button(
            label=get_text(user_id, 'admin.alliance_mgmt'),
            style=discord.ButtonStyle.primary,
            custom_id='mgmt_alliance',
            emoji='🤝',
            row=0
        ))
        
        self.add_item(discord.ui.Button(
            label=get_text(user_id, 'admin.reservations_mgmt'),
            style=discord.ButtonStyle.primary,
            custom_id='mgmt_reservations',
            emoji='📅',
            row=0
        ))
        
        # Row 2: Users and System management
        self.add_item(discord.ui.Button(
            label=get_text(user_id, 'admin.users_mgmt'),
            style=discord.ButtonStyle.primary,
            custom_id='mgmt_users',
            emoji='👥',
            row=1
        ))
        
        self.add_item(discord.ui.Button(
            label=get_text(user_id, 'admin.system_mgmt'),
            style=discord.ButtonStyle.primary,
            custom_id='mgmt_system',
            emoji='🔧',
            row=1
        ))
        
        # Row 3: Permissions (owner only)
        if self.is_owner:
            self.add_item(discord.ui.Button(
                label=get_text(user_id, 'admin.permissions'),
                style=discord.ButtonStyle.danger,
                custom_id='mgmt_permissions',
                emoji='🔐',
                row=2
            ))
        
        # Row 4: Back button
        self.add_item(discord.ui.Button(
            label=get_text(user_id, 'common.back'),
            style=discord.ButtonStyle.secondary,
            custom_id='mgmt_back',
            row=3
        ))
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check if user owns this menu"""
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message(
                "❌ This panel is not for you!",
                ephemeral=True
            )
            return False
        return True


class ManagementSystemCog(commands.Cog):
    """Management System"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def show_management_panel(self, interaction: discord.Interaction):
        """Show management panel"""
        user_id = str(interaction.user.id)
        
        # Check permissions
        if not permissions.is_admin(interaction.user) and not permissions.is_owner(interaction.user):
            await interaction.response.send_message(
                get_text(user_id, 'admin.no_permission'),
                ephemeral=True
            )
            return
        
        is_owner = permissions.is_owner(interaction.user)
        view = ManagementPanelView(user_id, is_owner)
        
        embed = create_colored_embed(
            get_text(user_id, 'admin.panel_title'),
            get_text(user_id, 'admin.panel_desc'),
            'warning'
        )
        
        await interaction.response.edit_message(embed=embed, view=view)
    
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Handle management interactions"""
        if interaction.type != discord.InteractionType.component:
            return
        
        custom_id = interaction.data.get('custom_id', '')
        
        # Only handle management buttons
        if not custom_id.startswith('mgmt_'):
            return
        
        user_id = str(interaction.user.id)
        
        # Load user language
        await translator.load_user_language_from_db(db, user_id)
        
        # Check permissions for all management actions
        if not permissions.is_admin(interaction.user) and not permissions.is_owner(interaction.user):
            await interaction.response.send_message(
                get_text(user_id, 'admin.no_permission'),
                ephemeral=True
            )
            return
        
        # Route to handlers
        if custom_id == 'mgmt_alliance':
            await self._show_alliance_management(interaction)
        
        elif custom_id == 'mgmt_reservations':
            await self._show_reservations_management(interaction)
        
        elif custom_id == 'mgmt_users':
            await self._show_users_management(interaction)
        
        elif custom_id == 'mgmt_system':
            await self._show_system_management(interaction)
        
        elif custom_id == 'mgmt_permissions':
            await self._show_permissions_management(interaction)
        
        elif custom_id == 'mgmt_back':
            await self._back_to_main(interaction)
        
        elif custom_id == 'mgmt_back_to_panel':
            await self.show_management_panel(interaction)
    
    async def _show_alliance_management(self, interaction: discord.Interaction):
        """Show alliance management"""
        user_id = str(interaction.user.id)
        
        # Check specific permission
        if not (permissions.is_owner(interaction.user) or
                permissions.is_admin(interaction.user) or
                await permissions.has_permission(interaction.user, 'alliance_management')):
            await interaction.response.send_message(
                get_text(user_id, 'admin.no_permission'),
                ephemeral=True
            )
            return
        
        try:
            # Get alliance statistics
            stats = await db.get_stats()
            
            embed = discord.Embed(
                title="🤝 Alliance Management",
                description="Alliance management and statistics",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="Total Alliances",
                value=str(stats.get('total_alliances', 0)),
                inline=True
            )
            
            # Get top alliances
            top_alliances = await db.get_top_alliances(5)
            if top_alliances:
                alliance_list = "\n".join([f"**{a.name}** - {a.member_count} members" for a in top_alliances])
                embed.add_field(
                    name="Top Alliances",
                    value=alliance_list,
                    inline=False
                )
            
            # Back button
            view = discord.ui.View(timeout=180)
            view.add_item(discord.ui.Button(
                label=get_text(user_id, 'common.back'),
                style=discord.ButtonStyle.secondary,
                custom_id='mgmt_back_to_panel'
            ))
            
            await interaction.response.edit_message(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error showing alliance management: {e}")
            await interaction.response.send_message(
                f"❌ Error: {str(e)}",
                ephemeral=True
            )
    
    async def _show_reservations_management(self, interaction: discord.Interaction):
        """Show reservations management"""
        user_id = str(interaction.user.id)
        
        # Check specific permission
        if not (permissions.is_owner(interaction.user) or
                permissions.is_admin(interaction.user) or
                await permissions.has_permission(interaction.user, 'reservations_management')):
            await interaction.response.send_message(
                get_text(user_id, 'admin.no_permission'),
                ephemeral=True
            )
            return
        
        try:
            # Get booking statistics
            stats = await db.get_stats()
            
            embed = discord.Embed(
                title="📅 Reservations Management",
                description="Reservations statistics and management",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="Total Reservations",
                value=str(stats.get('total_bookings', 0)),
                inline=True
            )
            
            embed.add_field(
                name="Active Reservations",
                value=str(stats.get('active_bookings', 0)),
                inline=True
            )
            
            embed.add_field(
                name="Completed Reservations",
                value=str(stats.get('completed_bookings', 0)),
                inline=True
            )
            
            # Back button
            view = discord.ui.View(timeout=180)
            view.add_item(discord.ui.Button(
                label=get_text(user_id, 'common.back'),
                style=discord.ButtonStyle.secondary,
                custom_id='mgmt_back_to_panel'
            ))
            
            await interaction.response.edit_message(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error showing reservations management: {e}")
            await interaction.response.send_message(
                f"❌ Error: {str(e)}",
                ephemeral=True
            )
    
    async def _show_users_management(self, interaction: discord.Interaction):
        """Show users management"""
        user_id = str(interaction.user.id)
        
        # Check specific permission
        if not (permissions.is_owner(interaction.user) or
                permissions.is_admin(interaction.user) or
                await permissions.has_permission(interaction.user, 'user_management')):
            await interaction.response.send_message(
                get_text(user_id, 'admin.no_permission'),
                ephemeral=True
            )
            return
        
        try:
            # Get user statistics
            stats = await db.get_stats()
            
            embed = discord.Embed(
                title="👥 User Management",
                description="User statistics and management",
                color=discord.Color.purple()
            )
            
            embed.add_field(
                name="Total Users",
                value=str(stats.get('total_users', 0)),
                inline=True
            )
            
            # Get top users
            top_users = await db.get_leaderboard(5)
            if top_users:
                user_list = "\n".join([f"**{u.username}** - {u.points} points" for u in top_users])
                embed.add_field(
                    name="Top Users",
                    value=user_list,
                    inline=False
                )
            
            # Back button
            view = discord.ui.View(timeout=180)
            view.add_item(discord.ui.Button(
                label=get_text(user_id, 'common.back'),
                style=discord.ButtonStyle.secondary,
                custom_id='mgmt_back_to_panel'
            ))
            
            await interaction.response.edit_message(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error showing users management: {e}")
            await interaction.response.send_message(
                f"❌ Error: {str(e)}",
                ephemeral=True
            )
    
    async def _show_system_management(self, interaction: discord.Interaction):
        """Show system management"""
        user_id = str(interaction.user.id)
        
        # Check specific permission
        if not (permissions.is_owner(interaction.user) or
                permissions.is_admin(interaction.user) or
                await permissions.has_permission(interaction.user, 'system_management')):
            await interaction.response.send_message(
                get_text(user_id, 'admin.no_permission'),
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="🔧 System Management",
            description="System settings and maintenance",
            color=discord.Color.orange()
        )
        
        embed.add_field(
            name="📊 Statistics",
            value="View bot statistics",
            inline=True
        )
        
        embed.add_field(
            name="📜 Logs",
            value="View system logs",
            inline=True
        )
        
        embed.add_field(
            name="💾 Backup",
            value="Create database backup",
            inline=True
        )
        
        embed.add_field(
            name="🗑️ Cleanup",
            value="Clean old data",
            inline=True
        )
        
        # Back button
        view = discord.ui.View(timeout=180)
        view.add_item(discord.ui.Button(
            label=get_text(user_id, 'common.back'),
            style=discord.ButtonStyle.secondary,
            custom_id='mgmt_back_to_panel'
        ))
        
        await interaction.response.edit_message(embed=embed, view=view)
    
    async def _show_permissions_management(self, interaction: discord.Interaction):
        """Show permissions management (owner only)"""
        user_id = str(interaction.user.id)
        
        # Owner only
        if not permissions.is_owner(interaction.user):
            await interaction.response.send_message(
                get_text(user_id, 'admin.owner_only'),
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="🔐 Permissions Management",
            description="Manage admin permissions and access control",
            color=discord.Color.red()
        )
        
        embed.add_field(
            name="➕ Add Admin",
            value="Grant admin access to users",
            inline=False
        )
        
        embed.add_field(
            name="➖ Remove Admin",
            value="Revoke admin access",
            inline=False
        )
        
        embed.add_field(
            name="👀 View Admins",
            value="List all admins and their permissions",
            inline=False
        )
        
        embed.add_field(
            name="📋 Permission Types",
            value="• Alliance Management\n• Reservations Management\n• User Management\n• System Management",
            inline=False
        )
        
        # Back button
        view = discord.ui.View(timeout=180)
        view.add_item(discord.ui.Button(
            label=get_text(user_id, 'common.back'),
            style=discord.ButtonStyle.secondary,
            custom_id='mgmt_back_to_panel'
        ))
        
        await interaction.response.edit_message(embed=embed, view=view)
    
    async def _back_to_main(self, interaction: discord.Interaction):
        """Go back to main control panel"""
        user_id = str(interaction.user.id)
        
        is_admin = permissions.is_admin(interaction.user)
        is_owner = permissions.is_owner(interaction.user)
        
        from cogs.main_control_panel import MainControlPanelView
        view = MainControlPanelView(user_id, is_admin, is_owner)
        
        embed = create_colored_embed(
            get_text(user_id, 'main_menu.title'),
            get_text(user_id, 'main_menu.description'),
            'info'
        )
        
        await interaction.response.edit_message(embed=embed, view=view)


async def setup(bot):
    """Setup the cog"""
    await bot.add_cog(ManagementSystemCog(bot))
