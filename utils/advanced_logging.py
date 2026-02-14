"""
نظام Logging المتقدم - Advanced Logging System
Enhanced logging with rotation and filtering
"""
import logging
import os
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_advanced_logging(logs_dir: str = 'logs'):
    """Setup advanced logging system"""
    
    # Create logs directory
    os.makedirs(logs_dir, exist_ok=True)
    
    # Define log format
    file_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    console_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    root_logger.handlers = []
    
    # Console handler with colors
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = ColoredFormatter(console_format, date_format)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Main log file (rotating by size)
    main_handler = RotatingFileHandler(
        f'{logs_dir}/bot.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    main_handler.setLevel(logging.INFO)
    main_formatter = logging.Formatter(file_format, date_format)
    main_handler.setFormatter(main_formatter)
    root_logger.addHandler(main_handler)
    
    # Error log file (rotating by time)
    error_handler = TimedRotatingFileHandler(
        f'{logs_dir}/errors.log',
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter(file_format, date_format)
    error_handler.setFormatter(error_formatter)
    root_logger.addHandler(error_handler)
    
    # Bookings log file (rotating daily)
    bookings_handler = TimedRotatingFileHandler(
        f'{logs_dir}/bookings.log',
        when='midnight',
        interval=1,
        backupCount=90,
        encoding='utf-8'
    )
    bookings_handler.setLevel(logging.INFO)
    bookings_formatter = logging.Formatter(file_format, date_format)
    bookings_handler.setFormatter(bookings_formatter)
    
    # Setup bookings logger
    bookings_logger = logging.getLogger('bookings')
    bookings_logger.addHandler(bookings_handler)
    bookings_logger.setLevel(logging.INFO)
    
    # Database log file
    db_handler = RotatingFileHandler(
        f'{logs_dir}/database.log',
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    db_handler.setLevel(logging.DEBUG)
    db_formatter = logging.Formatter(file_format, date_format)
    db_handler.setFormatter(db_formatter)
    
    # Setup database logger
    db_logger = logging.getLogger('database')
    db_logger.addHandler(db_handler)
    db_logger.setLevel(logging.DEBUG)
    
    # Interactions log file
    interactions_handler = RotatingFileHandler(
        f'{logs_dir}/interactions.log',
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    interactions_handler.setLevel(logging.INFO)
    interactions_formatter = logging.Formatter(file_format, date_format)
    interactions_handler.setFormatter(interactions_formatter)
    
    # Setup interactions logger
    interactions_logger = logging.getLogger('interactions')
    interactions_logger.addHandler(interactions_handler)
    interactions_logger.setLevel(logging.INFO)
    
    # Reduce discord.py logging noise
    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('discord.http').setLevel(logging.WARNING)
    logging.getLogger('discord.gateway').setLevel(logging.WARNING)
    
    # Log startup message
    root_logger.info("=" * 70)
    root_logger.info("📝 نظام Logging المتقدم جاهز | Advanced Logging System Ready")
    root_logger.info(f"📁 مجلد السجلات | Logs Directory: {logs_dir}")
    root_logger.info("=" * 70)


class ActionLogger:
    """Logger for user actions"""
    
    def __init__(self):
        self.logger = logging.getLogger('interactions')
    
    def log_button_click(self, user_id: str, button_id: str, action: str = "clicked"):
        """Log button click"""
        self.logger.info(f"🔘 Button {action}: {button_id} by user {user_id}")
    
    def log_command(self, user_id: str, command: str, success: bool = True):
        """Log command execution"""
        status = "✅ SUCCESS" if success else "❌ FAILED"
        self.logger.info(f"⚙️  Command {status}: /{command} by user {user_id}")
    
    def log_booking_created(self, user_id: str, booking_id: int, booking_type: str):
        """Log booking creation"""
        self.logger.info(f"📅 Booking created: ID={booking_id}, Type={booking_type}, User={user_id}")
    
    def log_booking_cancelled(self, user_id: str, booking_id: int, reason: str = ""):
        """Log booking cancellation"""
        self.logger.info(f"❌ Booking cancelled: ID={booking_id}, User={user_id}, Reason={reason}")
    
    def log_booking_completed(self, user_id: str, booking_id: int):
        """Log booking completion"""
        self.logger.info(f"✅ Booking completed: ID={booking_id}, User={user_id}")
    
    def log_alliance_action(self, user_id: str, action: str, alliance_id: int = None):
        """Log alliance action"""
        self.logger.info(f"🤝 Alliance action: {action} by user {user_id}, Alliance={alliance_id}")
    
    def log_permission_change(self, admin_id: str, user_id: str, permission: str, granted: bool):
        """Log permission change"""
        action = "granted" if granted else "revoked"
        self.logger.info(f"🔐 Permission {action}: {permission} for user {user_id} by admin {admin_id}")
    
    def log_error(self, context: str, error: str, user_id: str = None):
        """Log error"""
        user_info = f" (User: {user_id})" if user_id else ""
        self.logger.error(f"❌ Error in {context}{user_info}: {error}")


# Global action logger instance
action_logger = ActionLogger()


# Export
__all__ = ['setup_advanced_logging', 'ActionLogger', 'action_logger']
