"""
لوحة التحكم الرئيسية - Main Control Panel
Button-only interface with no slash commands (except /start)
"""
import discord
from discord import app_commands
from discord.ext import commands
import logging

from utils.translator import translator, get_text
from utils.ui_components import create_colored_embed
from utils import permissions

logger = logging.getLogger('main_control_panel')

class MainControlPanelView(discord.ui.View):
    """Main Control Panel with buttons only"""
    
    def __init__(self, user_id: str, is_admin: bool = False, is_owner: bool = False):
        super().__init__(timeout=None)  # No timeout for main menu
        self.user_id = user_id
        self.is_admin = is_admin
        self.is_owner = is_owner
        self._build_buttons()
    
    def _build_buttons(self):
        """Build main menu buttons"""
        user_id = self.user_id
        
        # Row 1: Alliance
        self.add_item(discord.ui.Button(
            label=get_text(user_id, 'main_menu.buttons.alliance'),
            style=discord.ButtonStyle.primary,
            custom_id='main_btn_alliance',
            emoji='🤝',
            row=0
        ))
        
        # Row 2: Reservations
        self.add_item(discord.ui.Button(
            label=get_text(user_id, 'main_menu.buttons.reservations'),
            style=discord.ButtonStyle.primary,
            custom_id='main_btn_reservations',
            emoji='📅',
            row=1
        ))
        
        # Row 3: Management (only for admins)
        if self.is_admin or self.is_owner:
            self.add_item(discord.ui.Button(
                label=get_text(user_id, 'main_menu.buttons.management'),
                style=discord.ButtonStyle.danger,
                custom_id='main_btn_management',
                emoji='⚙️',
                row=2
            ))
        
        # Row 4: Language and My Info
        self.add_item(discord.ui.Button(
            label=get_text(user_id, 'main_menu.buttons.language'),
            style=discord.ButtonStyle.secondary,
            custom_id='main_btn_language',
            emoji='🌐',
            row=3
        ))
        
        self.add_item(discord.ui.Button(
            label=get_text(user_id, 'main_menu.buttons.my_info'),
            style=discord.ButtonStyle.secondary,
            custom_id='main_btn_my_info',
            emoji='👤',
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


class LanguageSelectView(discord.ui.View):
    """Language selection view"""
    
    def __init__(self, user_id: str):
        super().__init__(timeout=180)
        self.user_id = user_id
    
    @discord.ui.button(label="🇸🇦 العربية", style=discord.ButtonStyle.success, custom_id='lang_ar')
    async def arabic_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Arabic language button"""
        await self._change_language(interaction, 'ar')
    
    @discord.ui.button(label="🇬🇧 English", style=discord.ButtonStyle.success, custom_id='lang_en')
    async def english_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """English language button"""
        await self._change_language(interaction, 'en')
    
    @discord.ui.button(label="🔙 رجوع | Back", style=discord.ButtonStyle.secondary, custom_id='lang_back', row=1)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Back to main menu"""
        from database import db
        await translator.load_user_language_from_db(db, self.user_id)
        
        is_admin = permissions.is_admin(interaction.user)
        is_owner = permissions.is_owner(interaction.user)
        view = MainControlPanelView(self.user_id, is_admin, is_owner)
        
        embed = create_colored_embed(
            get_text(self.user_id, 'main_menu.title'),
            get_text(self.user_id, 'main_menu.description'),
            'info'
        )
        
        await interaction.response.edit_message(embed=embed, view=view)
    
    async def _change_language(self, interaction: discord.Interaction, lang_code: str):
        """Change user language"""
        from database import db
        
        # Set language in translator
        translator.set_user_language(self.user_id, lang_code)
        
        # Save to database
        try:
            user = await db.get_user_by_discord_id(self.user_id)
            if user:
                await db.execute(
                    "UPDATE users SET language = ? WHERE user_id = ?",
                    (lang_code, user.user_id)
                )
        except Exception as e:
            logger.error(f"Error saving language: {e}")
        
        # Success message
        embed = create_colored_embed(
            get_text(self.user_id, 'common.success'),
            get_text(self.user_id, 'language.changed'),
            'success'
        )
        
        await interaction.response.edit_message(embed=embed, view=None)
        
        # Reopen main menu after 1 second
        import asyncio
        await asyncio.sleep(1)
        
        is_admin = permissions.is_admin(interaction.user)
        is_owner = permissions.is_owner(interaction.user)
        view = MainControlPanelView(self.user_id, is_admin, is_owner)
        
        embed = create_colored_embed(
            get_text(self.user_id, 'main_menu.title'),
            get_text(self.user_id, 'main_menu.description'),
            'info'
        )
        
        await interaction.edit_original_response(embed=embed, view=view)
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check if user owns this menu"""
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message(
                "❌ This menu is not for you!",
                ephemeral=True
            )
            return False
        return True


class MyInfoView(discord.ui.View):
    """My Info display view"""
    
    def __init__(self, user_id: str):
        super().__init__(timeout=180)
        self.user_id = user_id
    
    @discord.ui.button(label="🔙 رجوع | Back", style=discord.ButtonStyle.secondary, custom_id='myinfo_back')
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Back to main menu"""
        from database import db
        await translator.load_user_language_from_db(db, self.user_id)
        
        is_admin = permissions.is_admin(interaction.user)
        is_owner = permissions.is_owner(interaction.user)
        view = MainControlPanelView(self.user_id, is_admin, is_owner)
        
        embed = create_colored_embed(
            get_text(self.user_id, 'main_menu.title'),
            get_text(self.user_id, 'main_menu.description'),
            'info'
        )
        
        await interaction.response.edit_message(embed=embed, view=view)
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check if user owns this menu"""
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message(
                "❌ This menu is not for you!",
                ephemeral=True
            )
            return False
        return True


class MainControlPanelCog(commands.Cog):
    """Main Control Panel System"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name='start', description='📖 Open Main Control Panel | فتح لوحة التحكم الرئيسية')
    async def start(self, interaction: discord.Interaction):
        """Show main control panel"""
        await self._show_main_panel(interaction)
    
    async def _show_main_panel(self, interaction: discord.Interaction):
        """Display main control panel"""
        user_id = str(interaction.user.id)
        
        # Load user language from database
        from database import db
        await translator.load_user_language_from_db(db, user_id)
        
        # Check admin permissions
        is_admin = permissions.is_admin(interaction.user)
        is_owner = permissions.is_owner(interaction.user)
        
        # Create view
        view = MainControlPanelView(user_id, is_admin, is_owner)
        
        # Create embed
        embed = create_colored_embed(
            get_text(user_id, 'main_menu.title'),
            get_text(user_id, 'main_menu.description'),
            'info'
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Handle button interactions"""
        if interaction.type != discord.InteractionType.component:
            return
        
        custom_id = interaction.data.get('custom_id', '')
        
        # Only handle main control panel buttons
        if not custom_id.startswith('main_btn_'):
            return
        
        user_id = str(interaction.user.id)
        
        # Load user language
        from database import db
        await translator.load_user_language_from_db(db, user_id)
        
        # Route to appropriate handler
        if custom_id == 'main_btn_alliance':
            await self._handle_alliance(interaction)
        
        elif custom_id == 'main_btn_reservations':
            await self._handle_reservations(interaction)
        
        elif custom_id == 'main_btn_management':
            await self._handle_management(interaction)
        
        elif custom_id == 'main_btn_language':
            await self._handle_language(interaction)
        
        elif custom_id == 'main_btn_my_info':
            await self._handle_my_info(interaction)
    
    async def _handle_alliance(self, interaction: discord.Interaction):
        """Handle alliance button"""
        from cogs.alliance_system import AllianceSystemCog
        
        cog = self.bot.get_cog('AllianceSystemCog')
        if cog:
            await cog.show_alliance_menu(interaction)
        else:
            await interaction.response.send_message(
                "🚧 Alliance system is being set up...",
                ephemeral=True
            )
    
    async def _handle_reservations(self, interaction: discord.Interaction):
        """Handle reservations button"""
        from cogs.reservations_system import ReservationsSystemCog
        
        cog = self.bot.get_cog('ReservationsSystemCog')
        if cog:
            await cog.show_reservations_menu(interaction)
        else:
            await interaction.response.send_message(
                "🚧 Reservations system is being set up...",
                ephemeral=True
            )
    
    async def _handle_management(self, interaction: discord.Interaction):
        """Handle management button"""
        user_id = str(interaction.user.id)
        
        # Check permissions
        if not permissions.is_admin(interaction.user) and not permissions.is_owner(interaction.user):
            await interaction.response.send_message(
                get_text(user_id, 'admin.no_permission'),
                ephemeral=True
            )
            return
        
        from cogs.management_system import ManagementSystemCog
        
        cog = self.bot.get_cog('ManagementSystemCog')
        if cog:
            await cog.show_management_panel(interaction)
        else:
            await interaction.response.send_message(
                "🚧 Management panel is being set up...",
                ephemeral=True
            )
    
    async def _handle_language(self, interaction: discord.Interaction):
        """Handle language button"""
        user_id = str(interaction.user.id)
        view = LanguageSelectView(user_id)
        
        embed = create_colored_embed(
            get_text(user_id, 'language.select_title'),
            "",
            'info'
        )
        
        await interaction.response.edit_message(embed=embed, view=view)
    
    async def _handle_my_info(self, interaction: discord.Interaction):
        """Handle my info button"""
        user_id = str(interaction.user.id)
        
        from database import db
        
        try:
            # Get user data
            user = await db.get_user_by_discord_id(user_id)
            
            if not user:
                # Create user if doesn't exist
                user = await db.get_or_create_user(
                    user_id,
                    interaction.user.name,
                    str(interaction.user.id)
                )
            
            # Get alliance info
            alliance_name = get_text(user_id, 'my_info.no_alliance')
            if user.alliance_id:
                alliance = await db.get_alliance(user.alliance_id)
                if alliance:
                    alliance_name = alliance.name
            
            # Get language name
            lang = translator.get_user_language(user_id)
            lang_name = "العربية" if lang == 'ar' else "English"
            
            # Get reservations count
            active_reservations = await db.get_active_bookings_count(user.user_id)
            
            # Build info embed
            embed = discord.Embed(
                title=get_text(user_id, 'my_info.title'),
                description=get_text(user_id, 'my_info.description'),
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name=get_text(user_id, 'my_info.username'),
                value=interaction.user.name,
                inline=True
            )
            
            embed.add_field(
                name=get_text(user_id, 'my_info.alliance'),
                value=alliance_name,
                inline=True
            )
            
            embed.add_field(
                name=get_text(user_id, 'my_info.language'),
                value=lang_name,
                inline=True
            )
            
            embed.add_field(
                name=get_text(user_id, 'my_info.active_reservations'),
                value=str(active_reservations),
                inline=True
            )
            
            embed.add_field(
                name=get_text(user_id, 'my_info.total_reservations'),
                value=str(user.total_bookings),
                inline=True
            )
            
            embed.set_footer(text=f"User ID: {user_id}")
            
            view = MyInfoView(user_id)
            
            await interaction.response.edit_message(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error showing my info: {e}")
            await interaction.response.send_message(
                f"❌ Error: {str(e)}",
                ephemeral=True
            )


async def setup(bot):
    """Setup the cog"""
    await bot.add_cog(MainControlPanelCog(bot))
