"""
مكونات واجهة المستخدم - UI Components
Reusable UI components for buttons, views, and modals
"""
import discord
from typing import Optional, Callable, List
import logging

logger = logging.getLogger('ui_components')

class NavigationButton(discord.ui.Button):
    """زر التنقل القابل لإعادة الاستخدام"""
    
    def __init__(
        self,
        label: str,
        emoji: Optional[str] = None,
        style: discord.ButtonStyle = discord.ButtonStyle.secondary,
        callback_func: Optional[Callable] = None,
        row: Optional[int] = None
    ):
        super().__init__(
            label=label,
            emoji=emoji,
            style=style,
            row=row
        )
        self.callback_func = callback_func
    
    async def callback(self, interaction: discord.Interaction):
        """معالجة الضغط على الزر"""
        if self.callback_func:
            await self.callback_func(interaction)

class ConfirmView(discord.ui.View):
    """عرض تأكيد بسيط مع زر نعم/لا"""
    
    def __init__(
        self,
        user_id: int,
        confirm_text: str = "✅ تأكيد",
        cancel_text: str = "❌ إلغاء",
        timeout: float = 180
    ):
        super().__init__(timeout=timeout)
        self.user_id = user_id
        self.value = None
        
        # زر التأكيد
        confirm_button = discord.ui.Button(
            label=confirm_text,
            style=discord.ButtonStyle.success,
            emoji="✅"
        )
        confirm_button.callback = self.confirm_callback
        self.add_item(confirm_button)
        
        # زر الإلغاء
        cancel_button = discord.ui.Button(
            label=cancel_text,
            style=discord.ButtonStyle.danger,
            emoji="❌"
        )
        cancel_button.callback = self.cancel_callback
        self.add_item(cancel_button)
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """التحقق من أن المستخدم الصحيح يستخدم الأزرار"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ هذه الأزرار ليست لك!",
                ephemeral=True
            )
            return False
        return True
    
    async def confirm_callback(self, interaction: discord.Interaction):
        """عند الضغط على تأكيد"""
        self.value = True
        self.stop()
    
    async def cancel_callback(self, interaction: discord.Interaction):
        """عند الضغط على إلغاء"""
        self.value = False
        self.stop()

class PaginationView(discord.ui.View):
    """عرض مع أزرار تنقل بين الصفحات"""
    
    def __init__(
        self,
        user_id: int,
        pages: List[discord.Embed],
        timeout: float = 180
    ):
        super().__init__(timeout=timeout)
        self.user_id = user_id
        self.pages = pages
        self.current_page = 0
        
        # تحديث حالة الأزرار
        self._update_buttons()
    
    def _update_buttons(self):
        """تحديث حالة أزرار التنقل"""
        self.clear_items()
        
        # زر الصفحة السابقة
        prev_button = discord.ui.Button(
            label="السابق",
            emoji="⬅️",
            style=discord.ButtonStyle.primary,
            disabled=(self.current_page == 0)
        )
        prev_button.callback = self.prev_page
        self.add_item(prev_button)
        
        # عرض رقم الصفحة
        page_button = discord.ui.Button(
            label=f"{self.current_page + 1}/{len(self.pages)}",
            style=discord.ButtonStyle.secondary,
            disabled=True
        )
        self.add_item(page_button)
        
        # زر الصفحة التالية
        next_button = discord.ui.Button(
            label="التالي",
            emoji="➡️",
            style=discord.ButtonStyle.primary,
            disabled=(self.current_page == len(self.pages) - 1)
        )
        next_button.callback = self.next_page
        self.add_item(next_button)
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """التحقق من المستخدم"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ هذه الأزرار ليست لك!",
                ephemeral=True
            )
            return False
        return True
    
    async def prev_page(self, interaction: discord.Interaction):
        """الصفحة السابقة"""
        if self.current_page > 0:
            self.current_page -= 1
            self._update_buttons()
            await interaction.response.edit_message(
                embed=self.pages[self.current_page],
                view=self
            )
    
    async def next_page(self, interaction: discord.Interaction):
        """الصفحة التالية"""
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self._update_buttons()
            await interaction.response.edit_message(
                embed=self.pages[self.current_page],
                view=self
            )

class BackButton(discord.ui.Button):
    """زر رجوع قابل لإعادة الاستخدام"""
    
    def __init__(
        self,
        label: str = "🔙 رجوع",
        callback_func: Optional[Callable] = None,
        row: int = 4
    ):
        super().__init__(
            label=label,
            style=discord.ButtonStyle.secondary,
            row=row
        )
        self.callback_func = callback_func
    
    async def callback(self, interaction: discord.Interaction):
        """معالجة الضغط على الزر"""
        if self.callback_func:
            await self.callback_func(interaction)

class LoadingEmbed:
    """إنشاء embed للتحميل"""
    
    @staticmethod
    def create(title: str = "⏳ جاري التحميل...", description: str = "الرجاء الانتظار..."):
        """إنشاء embed للتحميل"""
        embed = discord.Embed(
            title=title,
            description=description,
            color=0x3498db
        )
        embed.set_footer(text="⏳ جاري المعالجة...")
        return embed

class ProgressBar:
    """إنشاء شريط تقدم نصي"""
    
    @staticmethod
    def create(
        current: int,
        total: int,
        length: int = 10,
        filled: str = "█",
        empty: str = "░"
    ) -> str:
        """
        إنشاء شريط تقدم
        
        Args:
            current: القيمة الحالية
            total: القيمة الكاملة
            length: طول الشريط
            filled: رمز الامتلاء
            empty: رمز الفراغ
        
        Returns:
            شريط التقدم كنص
        """
        if total == 0:
            return empty * length
        
        filled_length = int(length * current / total)
        bar = filled * filled_length + empty * (length - filled_length)
        percentage = int(100 * current / total)
        
        return f"{bar} {percentage}%"

class SelectMenuView(discord.ui.View):
    """عرض مع قائمة اختيار"""
    
    def __init__(
        self,
        user_id: int,
        options: List[discord.SelectOption],
        placeholder: str = "اختر خياراً...",
        callback_func: Optional[Callable] = None,
        timeout: float = 180
    ):
        super().__init__(timeout=timeout)
        self.user_id = user_id
        self.callback_func = callback_func
        self.selected_value = None
        
        # إنشاء القائمة
        select = discord.ui.Select(
            placeholder=placeholder,
            options=options,
            min_values=1,
            max_values=1
        )
        select.callback = self.select_callback
        self.add_item(select)
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """التحقق من المستخدم"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ هذه القائمة ليست لك!",
                ephemeral=True
            )
            return False
        return True
    
    async def select_callback(self, interaction: discord.Interaction):
        """عند الاختيار من القائمة"""
        self.selected_value = interaction.data['values'][0]
        if self.callback_func:
            await self.callback_func(interaction, self.selected_value)

def create_colored_embed(
    title: str,
    description: str,
    color_type: str = "info",
    fields: Optional[List[tuple]] = None
) -> discord.Embed:
    """
    إنشاء embed ملون حسب النوع
    
    Args:
        title: العنوان
        description: الوصف
        color_type: نوع اللون (success, error, warning, info)
        fields: قائمة من (name, value, inline)
    
    Returns:
        discord.Embed
    """
    color_map = {
        'success': 0x2ecc71,  # أخضر
        'error': 0xe74c3c,    # أحمر
        'warning': 0xf39c12,  # أصفر
        'info': 0x3498db      # أزرق
    }
    
    color = color_map.get(color_type, 0x3498db)
    
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )
    
    if fields:
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
    
    # إضافة emoji للعنوان حسب النوع
    emoji_map = {
        'success': '✅',
        'error': '❌',
        'warning': '⚠️',
        'info': 'ℹ️'
    }
    
    if color_type in emoji_map:
        embed.title = f"{emoji_map[color_type]} {embed.title}"
    
    return embed
