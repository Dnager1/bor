-- Enhanced Database Schema for Discord Booking Bot
-- نظام قاعدة البيانات المحسّن لبوت الحجوزات
-- Version 2.0 - Full Production Refactor

-- ============================================
-- جدول المستخدمين - Users Table
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    discord_id TEXT UNIQUE NOT NULL,
    username TEXT NOT NULL,
    player_id TEXT NOT NULL,
    alliance_id INTEGER,
    language TEXT DEFAULT 'en' CHECK(language IN ('ar', 'en')),
    points INTEGER DEFAULT 0,
    total_bookings INTEGER DEFAULT 0,
    completed_bookings INTEGER DEFAULT 0,
    cancelled_bookings INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (alliance_id) REFERENCES alliances(alliance_id)
);

-- ============================================
-- جدول الحجوزات - Bookings Table
-- ============================================
CREATE TABLE IF NOT EXISTS bookings (
    booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    booking_type TEXT NOT NULL CHECK(booking_type IN ('building', 'training', 'research')),
    player_name TEXT NOT NULL,
    player_id TEXT NOT NULL,
    alliance_name TEXT NOT NULL,
    scheduled_time TIMESTAMP NOT NULL,
    duration_days INTEGER DEFAULT 1,
    details TEXT,
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'completed', 'cancelled', 'expired')),
    
    -- Reminder tracking with flexible timing
    reminder_sent JSON DEFAULT '{}',
    
    completed_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    cancellation_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT NOT NULL,
    
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- ============================================
-- جدول التحالفات - Alliances Table (Enhanced)
-- ============================================
CREATE TABLE IF NOT EXISTS alliances (
    alliance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    logo TEXT DEFAULT '🏰',
    level INTEGER DEFAULT 1,
    total_power INTEGER DEFAULT 0,
    description TEXT,
    rules TEXT,
    location TEXT,
    leader_id INTEGER NOT NULL,
    member_count INTEGER DEFAULT 1,
    max_members INTEGER DEFAULT 50,
    total_bookings INTEGER DEFAULT 0,
    completed_bookings INTEGER DEFAULT 0,
    total_points INTEGER DEFAULT 0,
    alliance_type TEXT DEFAULT 'public' CHECK(alliance_type IN ('public', 'private', 'invite_only')),
    requirements TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (leader_id) REFERENCES users(user_id)
);

-- ============================================
-- جدول أعضاء التحالف - Alliance Members Table
-- ============================================
CREATE TABLE IF NOT EXISTS alliance_members (
    member_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    alliance_id INTEGER NOT NULL,
    rank TEXT DEFAULT 'R1' CHECK(rank IN ('R5', 'R4', 'R3', 'R2', 'R1')),
    power INTEGER DEFAULT 0,
    contribution_points INTEGER DEFAULT 0,
    activity_status TEXT DEFAULT 'active' CHECK(activity_status IN ('active', 'inactive', 'away')),
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (alliance_id) REFERENCES alliances(alliance_id),
    UNIQUE(user_id, alliance_id)
);

-- ============================================
-- جدول طلبات الانضمام للتحالف - Alliance Join Requests
-- ============================================
CREATE TABLE IF NOT EXISTS alliance_join_requests (
    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    alliance_id INTEGER NOT NULL,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'accepted', 'rejected')),
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    processed_by INTEGER,
    
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (alliance_id) REFERENCES alliances(alliance_id),
    FOREIGN KEY (processed_by) REFERENCES users(user_id)
);

-- ============================================
-- جدول صلاحيات البوت - Bot Permissions Table (Enhanced)
-- ============================================
CREATE TABLE IF NOT EXISTS bot_permissions (
    permission_id INTEGER PRIMARY KEY AUTOINCREMENT,
    discord_id TEXT UNIQUE NOT NULL,
    username TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('owner', 'admin', 'moderator')),
    
    -- Granular permissions as JSON
    permissions JSON DEFAULT '{}',
    
    granted_by TEXT NOT NULL,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- ============================================
-- جدول سجل الصلاحيات - Permissions Log
-- ============================================
CREATE TABLE IF NOT EXISTS permissions_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    target_discord_id TEXT NOT NULL,
    target_username TEXT,
    performed_by TEXT NOT NULL,
    old_role TEXT,
    new_role TEXT,
    permissions_changed TEXT,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- جدول الإنجازات - Achievements Table
-- ============================================
CREATE TABLE IF NOT EXISTS achievements (
    achievement_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    achievement_type TEXT NOT NULL,
    achievement_name TEXT NOT NULL,
    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE(user_id, achievement_type)
);

-- ============================================
-- جدول السجلات - Logs Table
-- ============================================
CREATE TABLE IF NOT EXISTS logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    action_type TEXT NOT NULL,
    user_id TEXT,
    booking_id INTEGER,
    alliance_id INTEGER,
    description TEXT NOT NULL,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- جدول الإعدادات - Settings Table
-- ============================================
CREATE TABLE IF NOT EXISTS settings (
    setting_key TEXT PRIMARY KEY,
    setting_value TEXT NOT NULL,
    setting_type TEXT DEFAULT 'string' CHECK(setting_type IN ('string', 'integer', 'boolean', 'json')),
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by TEXT
);

-- ============================================
-- جدول التذكيرات المخصصة - Custom Reminders Configuration
-- ============================================
CREATE TABLE IF NOT EXISTS reminder_config (
    config_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    hours_before INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    created_by TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default reminder configurations
INSERT OR IGNORE INTO reminder_config (config_id, name, hours_before, is_active, created_by) VALUES
(1, '1_hour', 1, 1, 'system'),
(2, '3_hours', 3, 1, 'system'),
(3, '6_hours', 6, 1, 'system'),
(4, '24_hours', 24, 1, 'system');

-- ============================================
-- الفهارس لتحسين الأداء - Performance Indexes
-- ============================================
CREATE INDEX IF NOT EXISTS idx_users_discord_id ON users(discord_id);
CREATE INDEX IF NOT EXISTS idx_users_alliance_id ON users(alliance_id);
CREATE INDEX IF NOT EXISTS idx_users_language ON users(language);

CREATE INDEX IF NOT EXISTS idx_bookings_user_id ON bookings(user_id);
CREATE INDEX IF NOT EXISTS idx_bookings_scheduled_time ON bookings(scheduled_time);
CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(status);
CREATE INDEX IF NOT EXISTS idx_bookings_type ON bookings(booking_type);
CREATE INDEX IF NOT EXISTS idx_bookings_created_at ON bookings(created_at);

CREATE INDEX IF NOT EXISTS idx_alliances_name ON alliances(name);
CREATE INDEX IF NOT EXISTS idx_alliances_leader_id ON alliances(leader_id);

CREATE INDEX IF NOT EXISTS idx_alliance_members_user_id ON alliance_members(user_id);
CREATE INDEX IF NOT EXISTS idx_alliance_members_alliance_id ON alliance_members(alliance_id);
CREATE INDEX IF NOT EXISTS idx_alliance_members_rank ON alliance_members(rank);

CREATE INDEX IF NOT EXISTS idx_alliance_requests_user_id ON alliance_join_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_alliance_requests_alliance_id ON alliance_join_requests(alliance_id);
CREATE INDEX IF NOT EXISTS idx_alliance_requests_status ON alliance_join_requests(status);

CREATE INDEX IF NOT EXISTS idx_permissions_discord_id ON bot_permissions(discord_id);
CREATE INDEX IF NOT EXISTS idx_permissions_role ON bot_permissions(role);

CREATE INDEX IF NOT EXISTS idx_logs_action_type ON logs(action_type);
CREATE INDEX IF NOT EXISTS idx_logs_created_at ON logs(created_at);
CREATE INDEX IF NOT EXISTS idx_logs_user_id ON logs(user_id);

CREATE INDEX IF NOT EXISTS idx_achievements_user_id ON achievements(user_id);
CREATE INDEX IF NOT EXISTS idx_achievements_type ON achievements(achievement_type);

-- ============================================
-- Views for easy data access
-- ============================================

-- View: Active bookings with user info
CREATE VIEW IF NOT EXISTS v_active_bookings AS
SELECT 
    b.booking_id,
    b.booking_type,
    b.player_name,
    b.player_id,
    b.alliance_name,
    b.scheduled_time,
    b.duration_days,
    b.status,
    u.discord_id,
    u.username,
    u.language
FROM bookings b
JOIN users u ON b.user_id = u.user_id
WHERE b.status = 'active'
ORDER BY b.scheduled_time ASC;

-- View: Alliance members with details
CREATE VIEW IF NOT EXISTS v_alliance_members_details AS
SELECT 
    am.member_id,
    am.alliance_id,
    a.name as alliance_name,
    u.user_id,
    u.discord_id,
    u.username,
    u.player_id,
    am.rank,
    am.power,
    am.contribution_points,
    am.activity_status,
    am.last_activity,
    am.joined_at
FROM alliance_members am
JOIN users u ON am.user_id = u.user_id
JOIN alliances a ON am.alliance_id = a.alliance_id
ORDER BY 
    CASE am.rank
        WHEN 'R5' THEN 1
        WHEN 'R4' THEN 2
        WHEN 'R3' THEN 3
        WHEN 'R2' THEN 4
        WHEN 'R1' THEN 5
    END,
    am.power DESC;
