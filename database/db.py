"""
Database compatibility layer.
Provides legacy import path: database.db
"""

from .db_manager import db, DatabaseManager

__all__ = ["db", "DatabaseManager"]
