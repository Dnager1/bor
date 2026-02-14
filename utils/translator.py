"""
نظام الترجمة - Translation System
Supports Arabic and English with easy language switching
"""
import json
import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger('translator')

class Translator:
    """نظام الترجمة للبوت"""
    
    def __init__(self):
        self.languages: Dict[str, Dict[str, Any]] = {}
        self.user_languages: Dict[str, str] = {}  # {user_id: language_code}
        self.default_language = 'en'
        self.available_languages = ['ar', 'en']
        self.load_languages()
    
    def load_languages(self):
        """تحميل ملفات اللغات من JSON"""
        languages_dir = os.path.join(os.path.dirname(__file__), 'languages')
        
        for lang_code in self.available_languages:
            file_candidates = [
                os.path.join(languages_dir, f'messages_{lang_code}.json'),
                os.path.join(languages_dir, f'{lang_code}.json'),
            ]
            try:
                loaded = False
                for file_path in file_candidates:
                    if not os.path.exists(file_path):
                        continue
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self.languages[lang_code] = json.load(f)
                    logger.info(f"✅ تم تحميل ملف اللغة: {file_path}")
                    loaded = True
                    break
                if not loaded:
                    logger.error(f"❌ لم يتم العثور على ملف لغة لـ: {lang_code}")
            except FileNotFoundError:
                logger.error(f"❌ لم يتم العثور على ملف اللغة: {lang_code}")
            except json.JSONDecodeError as e:
                logger.error(f"❌ خطأ في تحليل ملف اللغة {lang_code}: {e}")
    
    def _get_from_dict(self, data: Dict[str, Any], key_path: str) -> str:
        """
        الحصول على قيمة من قاموس متداخل باستخدام مسار النقاط
        مثال: 'main_menu.buttons.book' -> data['main_menu']['buttons']['book']
        """
        keys = key_path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return key_path  # إرجاع المفتاح إذا لم يتم العثور على الترجمة
        
        return str(value)
    
    def get_text(self, user_id: str, key: str, **kwargs) -> str:
        """
        الحصول على النص المترجم مع دعم المتغيرات
        
        Args:
            user_id: معرف المستخدم
            key: مفتاح الترجمة (مثل: 'main_menu.title')
            **kwargs: متغيرات للاستبدال في النص
        
        Returns:
            النص المترجم
        """
        lang = self.get_user_language(user_id)
        
        if lang not in self.languages:
            lang = self.default_language
        
        text = self._get_from_dict(self.languages[lang], key)
        
        # استبدال المتغيرات
        try:
            if kwargs:
                text = text.format(**kwargs)
        except KeyError as e:
            logger.warning(f"متغير غير موجود في النص: {e}")
        
        return text
    
    def get_user_language(self, user_id: str) -> str:
        """الحصول على لغة المستخدم"""
        return self.user_languages.get(user_id, self.default_language)
    
    def set_user_language(self, user_id: str, lang_code: str):
        """
        تعيين لغة المستخدم
        
        Args:
            user_id: معرف المستخدم
            lang_code: رمز اللغة ('ar' أو 'en')
        """
        if lang_code in self.available_languages:
            self.user_languages[user_id] = lang_code
            logger.info(f"تم تعيين لغة المستخدم {user_id} إلى {lang_code}")
        else:
            logger.warning(f"رمز لغة غير صالح: {lang_code}")
    
    async def load_user_language_from_db(self, db_manager, user_id: str):
        """تحميل لغة المستخدم من قاعدة البيانات"""
        try:
            user = await db_manager.get_user_by_discord_id(user_id)
            if user and hasattr(user, 'language'):
                self.set_user_language(user_id, user.language)
        except Exception as e:
            logger.error(f"خطأ في تحميل لغة المستخدم من قاعدة البيانات: {e}")
    
    def get_all_texts(self, user_id: str, section: str) -> Dict[str, str]:
        """
        الحصول على جميع النصوص في قسم معين
        
        Args:
            user_id: معرف المستخدم
            section: القسم (مثل: 'main_menu.buttons')
        
        Returns:
            قاموس بجميع النصوص
        """
        lang = self.get_user_language(user_id)
        
        if lang not in self.languages:
            lang = self.default_language
        
        return self._get_from_dict(self.languages[lang], section)

# إنشاء نسخة واحدة من المترجم
translator = Translator()

# دوال مساعدة للوصول السريع
def get_text(user_id: str, key: str, **kwargs) -> str:
    """دالة مساعدة للحصول على نص مترجم"""
    return translator.get_text(user_id, key, **kwargs)

def set_language(user_id: str, lang_code: str):
    """دالة مساعدة لتعيين لغة المستخدم"""
    translator.set_user_language(user_id, lang_code)

def get_language(user_id: str) -> str:
    """دالة مساعدة للحصول على لغة المستخدم"""
    return translator.get_user_language(user_id)
