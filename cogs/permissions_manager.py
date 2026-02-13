"""
مدير الصلاحيات - Permissions Manager Cog
Allows owner to manage admins, moderators, and custom permissions
"""
import discord
from discord import app_commands
from discord.ext import commands
import logging
from typing import Optional, Literal

from database import db
from utils.permissions import permissions_manager
from utils.translator import get_text
from utils.ui_components import create_colored_embed
from config import config

logger = logging.getLogger('permissions_manager')

class PermissionSelectView(discord.ui.View):
    """واجهة اختيار الصلاحيات"""
    
    def __init__(self, target_user: discord.User, cog):
        super().__init__(timeout=300)
        self.target_user = target_user
        self.cog = cog
        self.selected_permissions = {}
    
    @discord.ui.select(
        placeholder="اختر الصلاحيات للمنح...",
        min_values=0,
        max_values=5,
        options=[
            discord.SelectOption(label="إدارة الحجوزات", value="manage_bookings", emoji="📅"),
            discord.SelectOption(label="إدارة التحالفات", value="manage_alliances", emoji="🤝"),
            discord.SelectOption(label="عرض الإحصائيات", value="view_stats", emoji="📊"),
            discord.SelectOption(label="تصدير البيانات", value="export_data", emoji="📥"),
            discord.SelectOption(label="إنشاء نسخ احتياطية", value="create_backups", emoji="💾"),
        ]
    )
    async def permission_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        """عند اختيار الصلاحيات"""
        for value in select.values:
            self.selected_permissions[value] = True
        
        await interaction.response.send_message(
            f"✅ تم اختيار {len(select.values)} صلاحية",
            ephemeral=True
        )
    
    @discord.ui.button(label="✅ تأكيد المنح", style=discord.ButtonStyle.success, row=1)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """زر تأكيد المنح"""
        if not self.selected_permissions:
            await interaction.response.send_message(
                "⚠️ لم تختر أي صلاحيات!",
                ephemeral=True
            )
            return
        
        # منح الصلاحيات
        for perm in self.selected_permissions:
            await permissions_manager.grant_permission(
                str(self.target_user.id),
                perm,
                str(interaction.user.id)
            )
        
        perms_list = "\n".join([f"• {p}" for p in self.selected_permissions.keys()])
        
        embed = create_colored_embed(
            "✅ تم منح الصلاحيات",
            f"تم منح الصلاحيات التالية للمستخدم {self.target_user.mention}:\n\n{perms_list}",
            'success'
        )
        
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()
    
    @discord.ui.button(label="❌ إلغاء", style=discord.ButtonStyle.danger, row=1)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """زر الإلغاء"""
        await interaction.response.edit_message(
            content="❌ تم إلغاء العملية",
            view=None
        )
        self.stop()

class PermissionsManagerCog(commands.Cog):
    """نظام إدارة الصلاحيات"""
    
    def __init__(self, bot):
        self.bot = bot
        # تعيين قاعدة البيانات لمدير الصلاحيات
        permissions_manager.set_db(db)
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """التحقق من أن المستخدم هو المالك"""
        if not permissions_manager.is_owner(interaction.user):
            await interaction.response.send_message(
                embed=create_colored_embed(
                    "❌ غير مصرح",
                    "هذه الأوامر متاحة للمالك فقط!",
                    'error'
                ),
                ephemeral=True
            )
            return False
        return True
    
    perms = app_commands.Group(name="perms", description="إدارة صلاحيات البوت")
    
    @perms.command(name='set_admin', description='👑 تعيين مشرف')
    @app_commands.describe(
        user='المستخدم المراد تعيينه كمشرف',
        notes='ملاحظات (اختياري)'
    )
    async def set_admin(self, interaction: discord.Interaction, user: discord.User, notes: str = None):
        """تعيين مشرف"""
        await interaction.response.defer(ephemeral=True)
        
        # لا يمكن تعيين المالك كمشرف
        if user.id == config.OWNER_ID:
            await interaction.followup.send(
                embed=create_colored_embed(
                    "❌ خطأ",
                    "المالك لديه صلاحيات كاملة بالفعل",
                    'error'
                ),
                ephemeral=True
            )
            return
        
        success = await permissions_manager.set_user_role(
            str(user.id),
            user.name,
            'admin',
            str(interaction.user.id),
            notes
        )
        
        if success:
            embed = create_colored_embed(
                "✅ تم التعيين",
                f"تم تعيين {user.mention} كمشرف بنجاح!\n\n"
                f"الصلاحيات:\n"
                f"• إدارة جميع الحجوزات\n"
                f"• إدارة التحالفات\n"
                f"• عرض الإحصائيات\n"
                f"• تصدير البيانات\n"
                f"• إنشاء نسخ احتياطية",
                'success'
            )
            
            # إرسال رسالة للمستخدم
            try:
                await user.send(
                    embed=create_colored_embed(
                        "🎉 تم تعيينك كمشرف",
                        f"تم تعيينك كمشرف في البوت بواسطة {interaction.user.mention}\n\n"
                        f"لديك الآن صلاحيات إدارة كاملة!",
                        'success'
                    )
                )
            except:
                pass
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            # تسجيل العملية
            await db.log_action(
                'admin_assigned',
                f"تم تعيين {user.name} كمشرف",
                str(interaction.user.id),
                details=notes
            )
        else:
            await interaction.followup.send(
                embed=create_colored_embed(
                    "❌ فشل",
                    "حدث خطأ أثناء تعيين المشرف",
                    'error'
                ),
                ephemeral=True
            )
    
    @perms.command(name='set_moderator', description='⭐ تعيين مراقب')
    @app_commands.describe(
        user='المستخدم المراد تعيينه كمراقب',
        notes='ملاحظات (اختياري)'
    )
    async def set_moderator(self, interaction: discord.Interaction, user: discord.User, notes: str = None):
        """تعيين مراقب"""
        await interaction.response.defer(ephemeral=True)
        
        # لا يمكن تعيين المالك كمراقب
        if user.id == config.OWNER_ID:
            await interaction.followup.send(
                embed=create_colored_embed(
                    "❌ خطأ",
                    "المالك لديه صلاحيات كاملة بالفعل",
                    'error'
                ),
                ephemeral=True
            )
            return
        
        success = await permissions_manager.set_user_role(
            str(user.id),
            user.name,
            'moderator',
            str(interaction.user.id),
            notes
        )
        
        if success:
            embed = create_colored_embed(
                "✅ تم التعيين",
                f"تم تعيين {user.mention} كمراقب بنجاح!\n\n"
                f"الصلاحيات:\n"
                f"• إدارة الحجوزات\n"
                f"• عرض إحصائيات محدودة\n"
                f"• مساعدة المستخدمين",
                'success'
            )
            
            # إرسال رسالة للمستخدم
            try:
                await user.send(
                    embed=create_colored_embed(
                        "🎉 تم تعيينك كمراقب",
                        f"تم تعيينك كمراقب في البوت بواسطة {interaction.user.mention}\n\n"
                        f"لديك الآن صلاحيات مراقبة محدودة!",
                        'success'
                    )
                )
            except:
                pass
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            # تسجيل العملية
            await db.log_action(
                'moderator_assigned',
                f"تم تعيين {user.name} كمراقب",
                str(interaction.user.id),
                details=notes
            )
        else:
            await interaction.followup.send(
                embed=create_colored_embed(
                    "❌ فشل",
                    "حدث خطأ أثناء تعيين المراقب",
                    'error'
                ),
                ephemeral=True
            )
    
    @perms.command(name='remove', description='🗑️ إزالة صلاحيات مستخدم')
    @app_commands.describe(user='المستخدم المراد إزالة صلاحياته')
    async def remove_permissions(self, interaction: discord.Interaction, user: discord.User):
        """إزالة صلاحيات مستخدم"""
        await interaction.response.defer(ephemeral=True)
        
        # لا يمكن إزالة صلاحيات المالك
        if user.id == config.OWNER_ID:
            await interaction.followup.send(
                embed=create_colored_embed(
                    "❌ خطأ",
                    "لا يمكن إزالة صلاحيات المالك",
                    'error'
                ),
                ephemeral=True
            )
            return
        
        success = await permissions_manager.remove_user_role(
            str(user.id),
            str(interaction.user.id)
        )
        
        if success:
            embed = create_colored_embed(
                "✅ تمت الإزالة",
                f"تمت إزالة جميع صلاحيات {user.mention}",
                'success'
            )
            
            # إرسال رسالة للمستخدم
            try:
                await user.send(
                    embed=create_colored_embed(
                        "📢 تغيير في الصلاحيات",
                        f"تمت إزالة صلاحياتك الإدارية في البوت بواسطة {interaction.user.mention}",
                        'warning'
                    )
                )
            except:
                pass
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            # تسجيل العملية
            await db.log_action(
                'permissions_removed',
                f"تمت إزالة صلاحيات {user.name}",
                str(interaction.user.id)
            )
        else:
            await interaction.followup.send(
                embed=create_colored_embed(
                    "❌ فشل",
                    "المستخدم ليس لديه صلاحيات مخصصة",
                    'error'
                ),
                ephemeral=True
            )
    
    @perms.command(name='grant', description='➕ منح صلاحية معينة')
    @app_commands.describe(user='المستخدم', permission='الصلاحية')
    async def grant_permission(self, interaction: discord.Interaction, user: discord.User):
        """منح صلاحية معينة"""
        # التحقق من وجود المستخدم في النظام
        user_role = await permissions_manager.get_user_role(str(user.id))
        
        if not user_role:
            await interaction.response.send_message(
                embed=create_colored_embed(
                    "❌ خطأ",
                    f"المستخدم {user.mention} غير موجود في نظام الصلاحيات.\n"
                    f"يجب تعيينه كمشرف أو مراقب أولاً.",
                    'error'
                ),
                ephemeral=True
            )
            return
        
        view = PermissionSelectView(user, self)
        
        embed = create_colored_embed(
            "➕ منح صلاحيات",
            f"اختر الصلاحيات التي تريد منحها لـ {user.mention}",
            'info'
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @perms.command(name='list', description='📋 عرض قائمة الصلاحيات')
    async def list_permissions(self, interaction: discord.Interaction):
        """عرض قائمة جميع المستخدمين وصلاحياتهم"""
        await interaction.response.defer(ephemeral=True)
        
        permissions_list = await permissions_manager.list_all_permissions()
        
        if not permissions_list:
            await interaction.followup.send(
                embed=create_colored_embed(
                    "📋 الصلاحيات",
                    "لا يوجد مستخدمون بصلاحيات مخصصة حالياً",
                    'info'
                ),
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="📋 قائمة الصلاحيات",
            description=f"عدد المستخدمين: {len(permissions_list)}",
            color=0x3498db
        )
        
        # المالك
        owner = await self.bot.fetch_user(config.OWNER_ID)
        embed.add_field(
            name="👑 المالك",
            value=f"**{owner.name}** (ID: {owner.id})\n• جميع الصلاحيات",
            inline=False
        )
        
        # المشرفون
        admins = [p for p in permissions_list if p['role'] == 'admin']
        if admins:
            admins_text = ""
            for admin in admins:
                admins_text += f"• **{admin['username']}** (ID: {admin['discord_id']})\n"
            embed.add_field(name="👨‍💼 المشرفون", value=admins_text, inline=False)
        
        # المراقبون
        mods = [p for p in permissions_list if p['role'] == 'moderator']
        if mods:
            mods_text = ""
            for mod in mods:
                mods_text += f"• **{mod['username']}** (ID: {mod['discord_id']})\n"
            embed.add_field(name="⭐ المراقبون", value=mods_text, inline=False)
        
        # الصلاحيات المخصصة
        custom = [p for p in permissions_list if p['permissions']]
        if custom:
            custom_text = ""
            for user in custom[:5]:  # عرض أول 5
                perms = ", ".join(user['permissions'].keys())
                custom_text += f"• **{user['username']}**: {perms}\n"
            if len(custom) > 5:
                custom_text += f"*...و {len(custom) - 5} مستخدم آخر*"
            embed.add_field(name="🔑 صلاحيات مخصصة", value=custom_text, inline=False)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @perms.command(name='check', description='🔍 التحقق من صلاحيات مستخدم')
    @app_commands.describe(user='المستخدم المراد التحقق من صلاحياته')
    async def check_user(self, interaction: discord.Interaction, user: discord.User):
        """التحقق من صلاحيات مستخدم معين"""
        await interaction.response.defer(ephemeral=True)
        
        # التحقق من المالك
        if user.id == config.OWNER_ID:
            embed = create_colored_embed(
                "👑 المالك",
                f"{user.mention} هو مالك البوت\n\n"
                f"الصلاحيات: **جميع الصلاحيات**",
                'success'
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # الحصول على الدور والصلاحيات
        user_role = await permissions_manager.get_user_role(str(user.id))
        user_perms = await permissions_manager.get_user_permissions(str(user.id))
        
        if not user_role:
            embed = create_colored_embed(
                "👤 مستخدم عادي",
                f"{user.mention} ليس لديه صلاحيات خاصة",
                'info'
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # رموز الأدوار
        role_emoji = {
            'admin': '👨‍💼',
            'moderator': '⭐',
            'user': '👤'
        }
        role_names = {
            'admin': 'مشرف',
            'moderator': 'مراقب',
            'user': 'مستخدم'
        }
        
        embed = discord.Embed(
            title=f"{role_emoji.get(user_role, '👤')} صلاحيات {user.name}",
            description=f"الدور: **{role_names.get(user_role, user_role)}**",
            color=0x3498db
        )
        
        # عرض الصلاحيات المخصصة
        if user_perms:
            perms_text = "\n".join([f"• {perm}" for perm, enabled in user_perms.items() if enabled])
            embed.add_field(name="🔑 صلاحيات مخصصة", value=perms_text or "لا توجد", inline=False)
        
        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    """إعداد الـ Cog"""
    await bot.add_cog(PermissionsManagerCog(bot))
