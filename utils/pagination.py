"""
نظام Pagination - Pagination System
For handling long lists with navigation buttons
"""
import discord
from discord import ui
from typing import List, Callable, Any
import math


class PaginationView(ui.View):
    """View with pagination buttons"""
    
    def __init__(self, 
                 items: List[Any],
                 per_page: int = 10,
                 user_id: str = None,
                 embed_generator: Callable = None,
                 timeout: int = 180):
        """
        Initialize pagination view
        
        Args:
            items: List of items to paginate
            per_page: Number of items per page
            user_id: User ID for permission check
            embed_generator: Function to generate embed for current page
            timeout: View timeout in seconds
        """
        super().__init__(timeout=timeout)
        self.items = items
        self.per_page = per_page
        self.user_id = user_id
        self.embed_generator = embed_generator
        self.current_page = 0
        self.max_page = math.ceil(len(items) / per_page) - 1
        
        # Update button states
        self._update_buttons()
    
    def _update_buttons(self):
        """Update button states based on current page"""
        # Clear existing items
        self.clear_items()
        
        # First page button
        first_button = ui.Button(
            label="⏮️",
            style=discord.ButtonStyle.secondary,
            disabled=(self.current_page == 0)
        )
        first_button.callback = self._first_page
        self.add_item(first_button)
        
        # Previous button
        prev_button = ui.Button(
            label="◀️",
            style=discord.ButtonStyle.primary,
            disabled=(self.current_page == 0)
        )
        prev_button.callback = self._previous_page
        self.add_item(prev_button)
        
        # Page indicator
        page_button = ui.Button(
            label=f"📄 {self.current_page + 1}/{self.max_page + 1}",
            style=discord.ButtonStyle.secondary,
            disabled=True
        )
        self.add_item(page_button)
        
        # Next button
        next_button = ui.Button(
            label="▶️",
            style=discord.ButtonStyle.primary,
            disabled=(self.current_page >= self.max_page)
        )
        next_button.callback = self._next_page
        self.add_item(next_button)
        
        # Last page button
        last_button = ui.Button(
            label="⏭️",
            style=discord.ButtonStyle.secondary,
            disabled=(self.current_page >= self.max_page)
        )
        last_button.callback = self._last_page
        self.add_item(last_button)
    
    async def _first_page(self, interaction: discord.Interaction):
        """Go to first page"""
        self.current_page = 0
        await self._update_page(interaction)
    
    async def _previous_page(self, interaction: discord.Interaction):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
        await self._update_page(interaction)
    
    async def _next_page(self, interaction: discord.Interaction):
        """Go to next page"""
        if self.current_page < self.max_page:
            self.current_page += 1
        await self._update_page(interaction)
    
    async def _last_page(self, interaction: discord.Interaction):
        """Go to last page"""
        self.current_page = self.max_page
        await self._update_page(interaction)
    
    async def _update_page(self, interaction: discord.Interaction):
        """Update the page display"""
        # Update button states
        self._update_buttons()
        
        # Get current page items
        start_idx = self.current_page * self.per_page
        end_idx = start_idx + self.per_page
        current_items = self.items[start_idx:end_idx]
        
        # Generate embed if generator provided
        if self.embed_generator:
            embed = self.embed_generator(current_items, self.current_page, self.max_page)
        else:
            # Default embed
            embed = discord.Embed(
                title=f"Page {self.current_page + 1}/{self.max_page + 1}",
                description=f"Showing {len(current_items)} items",
                color=discord.Color.blue()
            )
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check if user owns this menu"""
        if self.user_id and str(interaction.user.id) != self.user_id:
            await interaction.response.send_message(
                "❌ This menu is not for you!",
                ephemeral=True
            )
            return False
        return True


def create_paginated_embed(items: List[Any],
                           title: str,
                           formatter: Callable,
                           page: int = 0,
                           max_page: int = 0,
                           color: discord.Color = discord.Color.blue()) -> discord.Embed:
    """
    Create a paginated embed
    
    Args:
        items: List of items for current page
        title: Embed title
        formatter: Function to format each item
        page: Current page number (0-indexed)
        max_page: Maximum page number (0-indexed)
        color: Embed color
    
    Returns:
        discord.Embed: Formatted embed
    """
    embed = discord.Embed(
        title=title,
        description=f"📄 Page {page + 1}/{max_page + 1}",
        color=color
    )
    
    for item in items:
        formatted = formatter(item)
        if isinstance(formatted, tuple):
            name, value = formatted
            embed.add_field(name=name, value=value, inline=False)
        else:
            embed.description += f"\n{formatted}"
    
    embed.set_footer(text=f"Total items: {(max_page + 1) * len(items)}")
    
    return embed
