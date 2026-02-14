"""
نظام التحالف - Alliance System
Complete alliance management with member control and ranks
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

logger = logging.getLogger('alliance_system')


class AllianceMenuView(discord.ui.View):
    """Alliance main menu"""
    
    def __init__(self, user_id: str, has_permissions: bool = False):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.has_permissions = has_permissions
        self._build_buttons()
    
    def _build_buttons(self):
        """Build alliance menu buttons"""
        user_id = self.user_id
        
        # Alliance info button (always visible)
        self.add_item(discord.ui.Button(
            label=get_text(user_id, 'alliance.info'),
            style=discord.ButtonStyle.primary,
            custom_id='alliance_info',
            emoji='ℹ️',
            row=0
        ))
        
        # Member management (only with permissions)
        if self.has_permissions:
            self.add_item(discord.ui.Button(
                label=get_text(user_id, 'alliance.members'),
                style=discord.ButtonStyle.primary,
                custom_id='alliance_members',
                emoji='👥',
                row=0
            ))
            
            self.add_item(discord.ui.Button(
                label=get_text(user_id, 'alliance.ranks'),
                style=discord.ButtonStyle.primary,
                custom_id='alliance_ranks',
                emoji='🎖️',
                row=0
            ))
        
        # Back button
        self.add_item(discord.ui.Button(
            label=get_text(user_id, 'common.back'),
            style=discord.ButtonStyle.secondary,
            custom_id='alliance_back',
            row=1
        ))
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check if user owns this menu"""
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message(
                "❌ This menu is not for you!",
                ephemeral=True
            )
            return False
        return True


class AllianceSystemCog(commands.Cog):
    """Alliance System"""
    
    def __init__(self, bot):
        self.bot = bot

    async def _safe_send(self, interaction: discord.Interaction, **kwargs):
        if interaction.response.is_done():
            return await interaction.followup.send(**kwargs)
        return await interaction.response.send_message(**kwargs)

    async def _safe_edit(self, interaction: discord.Interaction, **kwargs):
        if interaction.response.is_done():
            return await interaction.edit_original_response(**kwargs)
        return await interaction.response.edit_message(**kwargs)

    @app_commands.command(name='alliance', description='🤝 Alliance actions')
    @app_commands.describe(action='Action: menu/info/create/join/leave', name='Alliance name', tag='Alliance tag (3 chars)')
    @app_commands.choices(action=[
        app_commands.Choice(name='menu', value='menu'),
        app_commands.Choice(name='info', value='info'),
        app_commands.Choice(name='create', value='create'),
        app_commands.Choice(name='join', value='join'),
        app_commands.Choice(name='leave', value='leave'),
    ])
    async def alliance(self, interaction: discord.Interaction, action: app_commands.Choice[str], name: str = '', tag: str = ''):
        """Alliance slash entry point"""
        user_id = str(interaction.user.id)
        await translator.load_user_language_from_db(db, user_id)

        user = await db.get_user_by_discord_id(user_id)
        if not user:
            user = await db.get_or_create_user(user_id, interaction.user.name, user_id)

        if action.value == 'menu':
            return await self.show_alliance_menu(interaction)

        if action.value == 'info':
            return await self._show_alliance_info(interaction)

        if action.value == 'create':
            clean_tag = (tag or '').strip().upper()
            if len(clean_tag) != 3:
                return await self._safe_send(interaction, content='❌ TAG must be exactly 3 characters.', ephemeral=True)
            if user.alliance_id:
                return await self._safe_send(interaction, content=get_text(user_id, 'alliance.already_member'), ephemeral=True)
            if not name.strip():
                return await self._safe_send(interaction, content='❌ Please provide alliance name.', ephemeral=True)

            try:
                await db.create_alliance(name=name.strip(), tag=clean_tag, leader_id=user.user_id, description='')
                return await self._safe_send(interaction, content=get_text(user_id, 'alliance.created_success'), ephemeral=True)
            except Exception as e:
                return await self._safe_send(interaction, content=f'❌ {e}', ephemeral=True)

        if action.value == 'join':
            clean_tag = (tag or '').strip().upper()
            if len(clean_tag) != 3:
                return await self._safe_send(interaction, content='❌ TAG must be exactly 3 characters.', ephemeral=True)
            if user.alliance_id:
                return await self._safe_send(interaction, content=get_text(user_id, 'alliance.already_member'), ephemeral=True)

            alliance = await db.get_alliance_by_tag(clean_tag)
            if not alliance:
                return await self._safe_send(interaction, content=get_text(user_id, 'alliance.not_found'), ephemeral=True)

            await db.join_alliance(user.user_id, alliance.alliance_id)
            return await self._safe_send(interaction, content=get_text(user_id, 'alliance.joined_success'), ephemeral=True)

        if action.value == 'leave':
            if not user.alliance_id:
                return await self._safe_send(interaction, content=get_text(user_id, 'alliance.no_alliance'), ephemeral=True)

            alliance = await db.get_alliance(user.alliance_id)
            if alliance and alliance.leader_id == user.user_id:
                return await self._safe_send(interaction, content='❌ Leader cannot leave before transferring leadership.', ephemeral=True)

            await db.leave_alliance(user.user_id, user.alliance_id)
            return await self._safe_send(interaction, content=get_text(user_id, 'alliance.left_success'), ephemeral=True)
    
    async def show_alliance_menu(self, interaction: discord.Interaction):
        """Show alliance main menu"""
        user_id = str(interaction.user.id)
        
        try:
            # Get user
            user = await db.get_user_by_discord_id(user_id)
            
            if not user or not user.alliance_id:
                # User not in alliance
                embed = create_colored_embed(
                    get_text(user_id, 'alliance.menu_title'),
                    get_text(user_id, 'alliance.no_alliance'),
                    'warning'
                )
                
                # Back button only
                view = discord.ui.View(timeout=180)
                view.add_item(discord.ui.Button(
                    label=get_text(user_id, 'common.back'),
                    style=discord.ButtonStyle.secondary,
                    custom_id='alliance_back'
                ))
                
                await self._safe_edit(interaction, embed=embed, view=view)
                return
            
            # Check if user has alliance permissions
            has_permissions = (
                permissions.is_owner(interaction.user) or
                permissions.is_admin(interaction.user) or
                await permissions.has_permission(interaction.user, 'alliance_management')
            )
            
            view = AllianceMenuView(user_id, has_permissions)
            
            embed = create_colored_embed(
                get_text(user_id, 'alliance.menu_title'),
                get_text(user_id, 'alliance.menu_desc'),
                'info'
            )
            
            await self._safe_edit(interaction, embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error showing alliance menu: {e}")
            await self._safe_send(interaction, content=f"❌ Error: {str(e)}", ephemeral=True)
    
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Handle alliance interactions"""
        if interaction.type != discord.InteractionType.component:
            return
        
        custom_id = (interaction.data or {}).get('custom_id', '')
        
        # Only handle alliance buttons
        if not custom_id.startswith('alliance_'):
            return
        
        user_id = str(interaction.user.id)
        
        # Load user language
        await translator.load_user_language_from_db(db, user_id)
        
        # Route to handlers
        if custom_id == 'alliance_info':
            await self._show_alliance_info(interaction)
        
        elif custom_id == 'alliance_members':
            await self._show_members(interaction)
        
        elif custom_id == 'alliance_ranks':
            await self._show_ranks(interaction)
        
        elif custom_id == 'alliance_back':
            await self._back_to_main(interaction)
        
        elif custom_id == 'alliance_back_to_menu':
            await self.show_alliance_menu(interaction)
    
    async def _show_alliance_info(self, interaction: discord.Interaction):
        """Show alliance information"""
        user_id = str(interaction.user.id)
        
        try:
            user = await db.get_user_by_discord_id(user_id)
            if not user or not user.alliance_id:
                await self._safe_send(interaction, content=get_text(user_id, 'alliance.no_alliance'), ephemeral=True)
                return
            
            alliance = await db.get_alliance(user.alliance_id)
            if not alliance:
                await self._safe_send(interaction, content=get_text(user_id, 'alliance.not_found'), ephemeral=True)
                return
            
            embed = discord.Embed(
                title=f"🤝 {alliance.name}",
                description=get_text(user_id, 'alliance.info'),
                color=discord.Color.gold()
            )
            
            # Alliance details
            embed.add_field(
                name=get_text(user_id, 'alliance.name'),
                value=f"{alliance.name} [{alliance.tag}]",
                inline=True
            )
            
            embed.add_field(
                name=get_text(user_id, 'alliance.level'),
                value=str(alliance.level),
                inline=True
            )
            
            embed.add_field(
                name=get_text(user_id, 'alliance.member_count'),
                value=f"{alliance.member_count}/{alliance.max_members}",
                inline=True
            )
            
            embed.add_field(
                name=get_text(user_id, 'alliance.total_power'),
                value=str(alliance.total_power),
                inline=True
            )
            
            if alliance.description:
                embed.add_field(
                    name=get_text(user_id, 'alliance.description'),
                    value=alliance.description,
                    inline=False
                )
            
            if alliance.rules:
                embed.add_field(
                    name=get_text(user_id, 'alliance.rules'),
                    value=alliance.rules,
                    inline=False
                )
            
            # Back button
            view = discord.ui.View(timeout=180)
            view.add_item(discord.ui.Button(
                label=get_text(user_id, 'common.back'),
                style=discord.ButtonStyle.secondary,
                custom_id='alliance_back_to_menu'
            ))
            
            await self._safe_edit(interaction, embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error showing alliance info: {e}")
            await self._safe_send(interaction, content=f"❌ Error: {str(e)}", ephemeral=True)
    
    async def _show_members(self, interaction: discord.Interaction):
        """Show alliance members"""
        user_id = str(interaction.user.id)
        
        # Check permissions
        if not (permissions.is_owner(interaction.user) or 
                permissions.is_admin(interaction.user) or
                await permissions.has_permission(interaction.user, 'alliance_management')):
            await self._safe_send(interaction, content=get_text(user_id, 'alliance.no_permission'), ephemeral=True)
            return
        
        try:
            user = await db.get_user_by_discord_id(user_id)
            if not user or not user.alliance_id:
                await self._safe_send(interaction, content=get_text(user_id, 'alliance.no_alliance'), ephemeral=True)
                return
            
            alliance = await db.get_alliance(user.alliance_id)
            if not alliance:
                await self._safe_send(interaction, content=get_text(user_id, 'alliance.not_found'), ephemeral=True)
                return
            
            # Get all members
            members_data = await db.fetchall(
                "SELECT discord_id, username, alliance_rank, last_activity FROM users WHERE alliance_id = ? ORDER BY alliance_rank DESC",
                (alliance.alliance_id,)
            )
            
            embed = discord.Embed(
                title=get_text(user_id, 'alliance.members_title'),
                description=f"**{alliance.name}** - {len(members_data)} members",
                color=discord.Color.blue()
            )
            
            if members_data:
                for member in members_data[:15]:  # Show first 15
                    discord_id, username, rank, last_activity = member
                    rank_name = rank or "R1"
                    embed.add_field(
                        name=f"**{username}** - {rank_name}",
                        value=f"ID: {discord_id}",
                        inline=False
                    )
            else:
                embed.description = "No members found"
            
            # Back button
            view = discord.ui.View(timeout=180)
            view.add_item(discord.ui.Button(
                label=get_text(user_id, 'common.back'),
                style=discord.ButtonStyle.secondary,
                custom_id='alliance_back_to_menu'
            ))
            
            await self._safe_edit(interaction, embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error showing members: {e}")
            await self._safe_send(interaction, content=f"❌ Error: {str(e)}", ephemeral=True)
    
    async def _show_ranks(self, interaction: discord.Interaction):
        """Show rank system"""
        user_id = str(interaction.user.id)
        
        # Check permissions
        if not (permissions.is_owner(interaction.user) or 
                permissions.is_admin(interaction.user) or
                await permissions.has_permission(interaction.user, 'alliance_management')):
            await self._safe_send(interaction, content=get_text(user_id, 'alliance.no_permission'), ephemeral=True)
            return
        
        embed = discord.Embed(
            title=get_text(user_id, 'alliance.ranks_title'),
            description="Alliance rank system and permissions",
            color=discord.Color.purple()
        )
        
        # Define ranks
        ranks = [
            ('R5', get_text(user_id, 'alliance.rank_r5'), 'Full alliance control'),
            ('R4', get_text(user_id, 'alliance.rank_r4'), 'Can manage members and accept requests'),
            ('R3', get_text(user_id, 'alliance.rank_r3'), 'Can view and manage reservations'),
            ('R2', get_text(user_id, 'alliance.rank_r2'), 'Can create reservations'),
            ('R1', get_text(user_id, 'alliance.rank_r1'), 'Basic member access'),
        ]
        
        for rank_code, rank_name, permissions_desc in ranks:
            embed.add_field(
                name=f"**{rank_name}**",
                value=f"Permissions: {permissions_desc}",
                inline=False
            )
        
        # Back button
        view = discord.ui.View(timeout=180)
        view.add_item(discord.ui.Button(
            label=get_text(user_id, 'common.back'),
            style=discord.ButtonStyle.secondary,
            custom_id='alliance_back_to_menu'
        ))
        
        await self._safe_edit(interaction, embed=embed, view=view)
    
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
        
        await self._safe_edit(interaction, embed=embed, view=view)


async def setup(bot):
    """Setup the cog"""
    await bot.add_cog(AllianceSystemCog(bot))
