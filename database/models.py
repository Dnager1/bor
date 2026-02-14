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
    alliance_rank: str = 'R1'
    points: int = 0
    total_bookings: int = 0
    completed_bookings: int = 0
    cancelled_bookings: int = 0
    language: str = 'ar'
    last_activity: Optional[datetime] = None
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
    duration_days: int = 1

@dataclass
class Alliance:
    """نموذج التحالف"""
    alliance_id: Optional[int] = None
    name: str = ''
    description: str = ''
    rules: str = ''
    leader_id: int = 0
    level: int = 1
    total_power: int = 0
    member_count: int = 1
    max_members: int = 50
    location: str = ''
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

@dataclass
class AllianceMember:
    """نموذج عضو التحالف"""
    member_id: Optional[int] = None
    user_id: int = 0
    alliance_id: int = 0
    rank: str = 'member'
    joined_at: Optional[datetime] = None
    contribution_points: int = 0
    activity_status: str = 'active'

@dataclass
class AllianceJoinRequest:
    """نموذج طلب الانضمام للتحالف"""
    request_id: Optional[int] = None
    user_id: int = 0
    alliance_id: int = 0
    status: str = 'pending'
    message: Optional[str] = None
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[int] = None

@dataclass
class AllianceChallenge:
    """نموذج تحدي التحالف"""
    challenge_id: Optional[int] = None
    alliance1_id: int = 0
    alliance2_id: Optional[int] = None
    challenge_type: str = ''
    title: str = ''
    description: Optional[str] = None
    target_value: int = 0
    current_value: int = 0
    reward: Optional[str] = None
    status: str = 'active'
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None

@dataclass
class AllianceMessage:
    """نموذج رسالة التحالف"""
    message_id: Optional[int] = None
    alliance_id: int = 0
    user_id: int = 0
    message_type: str = 'announcement'
    title: str = ''
    content: str = ''
    created_at: Optional[datetime] = None
