"""
نظام الحجوزات - Reservations System
Three sections: Building, Training, Research
"""
import discord
from discord import app_commands
from discord.ext import commands
from discord import ui
import logging
from datetime import datetime, timedelta
import pytz

from utils.translator import translator, get_text
from utils.ui_components import create_colored_embed
from utils import permissions
from database import db

logger = logging.getLogger('reservations_system')


class ReservationsMenuView(discord.ui.View):
    """Reservations main menu"""
    
    def __init__(self, user_id: str):
        super().__init__(timeout=180)
        self.user_id = user_id
        self._build_buttons()
    
    def _build_buttons(self):
        """Build reservation menu buttons"""
        user_id = self.user_id
        
        # Row 1: Three sections
        self.add_item(discord.ui.Button(
            label=get_text(user_id, 'reservations.building'),
            style=discord.ButtonStyle.primary,
            custom_id='res_building',
            emoji='🏗️',
            row=0
        ))
        
        self.add_item(discord.ui.Button(
            label=get_text(user_id, 'reservations.training'),
            style=discord.ButtonStyle.primary,
            custom_id='res_training',
            emoji='⚔️',
            row=0
        ))
        
        self.add_item(discord.ui.Button(
            label=get_text(user_id, 'reservations.research'),
            style=discord.ButtonStyle.primary,
            custom_id='res_research',
            emoji='🔬',
            row=0
        ))
        
        # Row 2: My reservations
        self.add_item(discord.ui.Button(
            label=get_text(user_id, 'reservations.my_reservations'),
            style=discord.ButtonStyle.secondary,
            custom_id='res_my_reservations',
            emoji='📋',
            row=1
        ))
        
        # Row 3: Back button
        self.add_item(discord.ui.Button(
            label=get_text(user_id, 'common.back'),
            style=discord.ButtonStyle.secondary,
            custom_id='res_back',
            row=2
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


class ReservationSectionView(discord.ui.View):
    """View for a specific reservation section (Building/Training/Research)"""
    
    def __init__(self, user_id: str, section_type: str):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.section_type = section_type  # 'building', 'training', 'research'
        self._build_buttons()
    
    def _build_buttons(self):
        """Build section buttons"""
        user_id = self.user_id
        
        # Create reservation button
        self.add_item(discord.ui.Button(
            label=get_text(user_id, 'reservations.create_reservation'),
            style=discord.ButtonStyle.success,
            custom_id=f'res_create_{self.section_type}',
            emoji='➕',
            row=0
        ))
        
        # View schedule button
        self.add_item(discord.ui.Button(
            label=get_text(user_id, 'reservations.view_schedule'),
            style=discord.ButtonStyle.primary,
            custom_id=f'res_schedule_{self.section_type}',
            emoji='📊',
            row=0
        ))
        
        # Back button
        self.add_item(discord.ui.Button(
            label=get_text(user_id, 'common.back'),
            style=discord.ButtonStyle.secondary,
            custom_id='res_back_to_menu',
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


class ReservationModal(ui.Modal):
    """Modal for creating a reservation"""
    
    def __init__(self, user_id: str, section_type: str):
        self.user_id = user_id
        self.section_type = section_type
        
        title = get_text(user_id, 'reservations.modal_title')
        super().__init__(title=title, timeout=300)
        
        # Member name
        self.member_name = ui.TextInput(
            label=get_text(user_id, 'reservations.member_name'),
            placeholder=get_text(user_id, 'reservations.member_name_placeholder'),
            required=True,
            max_length=100
        )
        self.add_item(self.member_name)
        
        # Alliance name
        self.alliance_name = ui.TextInput(
            label=get_text(user_id, 'reservations.alliance_name'),
            placeholder=get_text(user_id, 'reservations.alliance_name_placeholder'),
            required=True,
            max_length=100
        )
        self.add_item(self.alliance_name)
        
        # Date
        self.date = ui.TextInput(
            label=get_text(user_id, 'reservations.date'),
            placeholder=get_text(user_id, 'reservations.date_placeholder'),
            required=True,
            max_length=10
        )
        self.add_item(self.date)
        
        # Time
        self.time = ui.TextInput(
            label=get_text(user_id, 'reservations.time'),
            placeholder=get_text(user_id, 'reservations.time_placeholder'),
            required=True,
            max_length=5
        )
        self.add_item(self.time)
        
        # Duration
        self.duration = ui.TextInput(
            label=get_text(user_id, 'reservations.duration_days'),
            placeholder=get_text(user_id, 'reservations.duration_days_placeholder'),
            required=True,
            max_length=3
        )
        self.add_item(self.duration)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle form submission"""
        try:
            # Parse date and time
            date_str = self.date.value.strip()
            time_str = self.time.value.strip()
            datetime_str = f"{date_str} {time_str}"
            scheduled_time = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
            
            # Make timezone aware (UTC)
            scheduled_time = pytz.UTC.localize(scheduled_time)
            
            # Parse duration
            duration_days = int(self.duration.value.strip())
            
            if duration_days < 1 or duration_days > 365:
                await interaction.response.send_message(
                    "❌ Duration must be between 1 and 365 days",
                    ephemeral=True
                )
                return
            
            # Get or create user
            user = await db.get_user_by_discord_id(self.user_id)
            if not user:
                user = await db.get_or_create_user(
                    self.user_id,
                    interaction.user.name,
                    self.user_id
                )
            
            # Check for conflicts
            conflict = await db.check_booking_conflict(user.user_id, scheduled_time)
            if conflict:
                await interaction.response.send_message(
                    get_text(self.user_id, 'reservations.conflict_msg'),
                    ephemeral=True
                )
                return
            
            # Create booking object
            from database.models import Booking
            booking = Booking(
                booking_id=None,
                user_id=user.user_id,
                booking_type=self.section_type,
                player_name=self.member_name.value.strip(),
                player_id=self.user_id,
                alliance_name=self.alliance_name.value.strip(),
                scheduled_time=scheduled_time,
                duration_days=duration_days,
                details="",
                status='active',
                created_by=self.user_id,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Save to database
            booking_id = await db.create_booking(booking)
            
            # Log action
            await db.log_action(
                'reservation_created',
                f"Created {self.section_type} reservation",
                self.user_id,
                booking_id,
                f"Member: {self.member_name.value}, Alliance: {self.alliance_name.value}"
            )
            
            # Success message
            embed = create_colored_embed(
                get_text(self.user_id, 'common.success'),
                get_text(self.user_id, 'reservations.created_success'),
                'success'
            )
            
            embed.add_field(
                name="📝 Details",
                value=f"**Member:** {self.member_name.value}\n**Alliance:** {self.alliance_name.value}\n**Time:** {scheduled_time.strftime('%Y-%m-%d %H:%M UTC')}\n**Duration:** {duration_days} days",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except ValueError as e:
            await interaction.response.send_message(
                f"❌ Invalid format. Please use YYYY-MM-DD for date and HH:MM for time.",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error creating reservation: {e}")
            await interaction.response.send_message(
                f"❌ Error: {str(e)}",
                ephemeral=True
            )


class ReservationsSystemCog(commands.Cog):
    """Reservations System"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def show_reservations_menu(self, interaction: discord.Interaction):
        """Show reservations main menu"""
        user_id = str(interaction.user.id)
        
        view = ReservationsMenuView(user_id)
        
        embed = create_colored_embed(
            get_text(user_id, 'reservations.menu_title'),
            get_text(user_id, 'reservations.menu_desc'),
            'info'
        )
        
        await interaction.response.edit_message(embed=embed, view=view)
    
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Handle reservation interactions"""
        if interaction.type != discord.InteractionType.component:
            return
        
        custom_id = interaction.data.get('custom_id', '')
        
        # Only handle reservation buttons
        if not custom_id.startswith('res_'):
            return
        
        user_id = str(interaction.user.id)
        
        # Load user language
        await translator.load_user_language_from_db(db, user_id)
        
        # Handle section selection
        if custom_id in ['res_building', 'res_training', 'res_research']:
            section_type = custom_id.replace('res_', '')
            await self._show_section(interaction, section_type)
        
        # Handle create reservation
        elif custom_id.startswith('res_create_'):
            section_type = custom_id.replace('res_create_', '')
            modal = ReservationModal(user_id, section_type)
            await interaction.response.send_modal(modal)
        
        # Handle view schedule
        elif custom_id.startswith('res_schedule_'):
            section_type = custom_id.replace('res_schedule_', '')
            await self._show_schedule(interaction, section_type)
        
        # Handle my reservations
        elif custom_id == 'res_my_reservations':
            await self._show_my_reservations(interaction)
        
        # Handle back buttons
        elif custom_id == 'res_back_to_menu':
            await self.show_reservations_menu(interaction)
        
        elif custom_id == 'res_back':
            await self._back_to_main(interaction)
    
    async def _show_section(self, interaction: discord.Interaction, section_type: str):
        """Show a specific section"""
        user_id = str(interaction.user.id)
        
        view = ReservationSectionView(user_id, section_type)
        
        section_emoji = {
            'building': '🏗️',
            'training': '⚔️',
            'research': '🔬'
        }
        
        embed = create_colored_embed(
            f"{section_emoji.get(section_type, '📅')} {get_text(user_id, f'reservations.{section_type}')}",
            get_text(user_id, 'reservations.menu_desc'),
            'info'
        )
        
        await interaction.response.edit_message(embed=embed, view=view)
    
    async def _show_schedule(self, interaction: discord.Interaction, section_type: str):
        """Show schedule for a section"""
        user_id = str(interaction.user.id)
        
        try:
            # Get all active bookings for this type
            bookings = await db.get_bookings_by_type(section_type, 'active')
            
            embed = discord.Embed(
                title=f"📊 {get_text(user_id, 'reservations.view_schedule')}",
                description=f"Active reservations for {section_type}",
                color=discord.Color.blue()
            )
            
            if not bookings:
                embed.description = get_text(user_id, 'reservations.no_data_msg')
            else:
                for booking in bookings[:10]:  # Show first 10
                    time_str = booking.scheduled_time.strftime('%Y-%m-%d %H:%M UTC')
                    embed.add_field(
                        name=f"{booking.player_name} ({booking.alliance_name})",
                        value=f"**Time:** {time_str}\n**Duration:** {booking.duration_days} days",
                        inline=False
                    )
            
            # Back button
            view = discord.ui.View(timeout=180)
            view.add_item(discord.ui.Button(
                label=get_text(user_id, 'common.back'),
                style=discord.ButtonStyle.secondary,
                custom_id=f'res_{section_type}'
            ))
            
            await interaction.response.edit_message(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error showing schedule: {e}")
            await interaction.response.send_message(
                f"❌ Error: {str(e)}",
                ephemeral=True
            )
    
    async def _show_my_reservations(self, interaction: discord.Interaction):
        """Show user's reservations"""
        user_id = str(interaction.user.id)
        
        try:
            user = await db.get_user_by_discord_id(user_id)
            if not user:
                await interaction.response.send_message(
                    get_text(user_id, 'reservations.no_data_msg'),
                    ephemeral=True
                )
                return
            
            bookings = await db.get_user_bookings(user.user_id, 'active')
            
            embed = discord.Embed(
                title=get_text(user_id, 'reservations.my_reservations'),
                color=discord.Color.green()
            )
            
            if not bookings:
                embed.description = get_text(user_id, 'reservations.no_reservations')
            else:
                for booking in bookings:
                    time_str = booking.scheduled_time.strftime('%Y-%m-%d %H:%M UTC')
                    type_emoji = {'building': '🏗️', 'training': '⚔️', 'research': '🔬'}
                    embed.add_field(
                        name=f"{type_emoji.get(booking.booking_type, '📅')} {booking.booking_type.title()}",
                        value=f"**Member:** {booking.player_name}\n**Alliance:** {booking.alliance_name}\n**Time:** {time_str}\n**Duration:** {booking.duration_days} days",
                        inline=False
                    )
            
            # Back button
            view = discord.ui.View(timeout=180)
            view.add_item(discord.ui.Button(
                label=get_text(user_id, 'common.back'),
                style=discord.ButtonStyle.secondary,
                custom_id='res_back_to_menu'
            ))
            
            await interaction.response.edit_message(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error showing my reservations: {e}")
            await interaction.response.send_message(
                f"❌ Error: {str(e)}",
                ephemeral=True
            )
    
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
    await bot.add_cog(ReservationsSystemCog(bot))
