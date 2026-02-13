"""
نماذج البيانات - Database Models
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class User:
    """نموذج المستخدم"""
    user_id: int
    discord_id: str
    username: str
    player_id: str
    alliance_id: Optional[int] = None
    points: int = 0
    total_bookings: int = 0
    completed_bookings: int = 0
    cancelled_bookings: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class Booking:
    """نموذج الحجز"""
    booking_id: Optional[int] = None
    user_id: Optional[int] = None
    booking_type: str = ''
    player_name: str = ''
    player_id: str = ''
    alliance_name: str = ''
    scheduled_time: Optional[datetime] = None
    details: str = ''
    status: str = 'active'
    reminder_24h_sent: bool = False
    reminder_1h_sent: bool = False
    reminder_now_sent: bool = False
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: str = ''

@dataclass
class Alliance:
    """نموذج التحالف"""
    alliance_id: Optional[int] = None
    name: str = ''
    description: str = ''
    leader_id: int = 0
    member_count: int = 1
    total_bookings: int = 0
    total_points: int = 0
    created_at: Optional[datetime] = None

@dataclass
class Achievement:
    """نموذج الإنجاز"""
    achievement_id: Optional[int] = None
    user_id: int = 0
    achievement_type: str = ''
    achievement_name: str = ''
    earned_at: Optional[datetime] = None

@dataclass
class Log:
    """نموذج السجل"""
    log_id: Optional[int] = None
    action_type: str = ''
    user_id: Optional[str] = None
    booking_id: Optional[int] = None
    description: str = ''
    details: Optional[str] = None
    created_at: Optional[datetime] = None
