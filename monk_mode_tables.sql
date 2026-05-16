-- ============================================================
-- MONK MODE — 90 Day Rebirth Protocol
-- SQL Migration Script for MySQL
-- 
-- Tables (7):
--   1. monk_mode_progress   — per-user activation & streak state
--   2. monk_mode_days       — 90 day rows with deadlines
--   3. monk_mode_tasks      — daily mandatory tasks
--   4. monk_mode_badges     — milestone badges
--   5. monk_mode_logs       — action audit log
--   6. monk_mode_resets     — reset history
--   7. monk_mode_levels     — level progression
--
-- Run against: mtalnflh_fitnessapp
-- ============================================================

-- 1. monk_mode_progress
CREATE TABLE IF NOT EXISTS `monk_mode_progress` (
    `id`              INT           NOT NULL AUTO_INCREMENT,
    `user_id`         INT           NOT NULL,
    `started_at`      DATETIME      NULL DEFAULT NULL,
    `status`          VARCHAR(20)   NOT NULL DEFAULT 'not_started',
    `current_day`     INT           NOT NULL DEFAULT 1,
    `streak`          INT           NOT NULL DEFAULT 0,
    `timezone_label`  VARCHAR(40)   NOT NULL DEFAULT 'UTC',
    `updated_at`      DATETIME      NULL DEFAULT NULL,
    `created_at`      DATETIME      NULL DEFAULT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_monk_mode_progress_user` (`user_id`),
    CONSTRAINT `fk_monk_mode_progress_user`
        FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- 2. monk_mode_days
CREATE TABLE IF NOT EXISTS `monk_mode_days` (
    `id`              INT           NOT NULL AUTO_INCREMENT,
    `progress_id`     INT           NOT NULL,
    `day_index`       INT           NOT NULL,
    `deadline_at`     DATETIME      NOT NULL,
    `scheduled_date`  DATE          NOT NULL,
    `status`          VARCHAR(20)   NOT NULL DEFAULT 'locked',
    `completed_at`    DATETIME      NULL DEFAULT NULL,
    `failed_reason`   VARCHAR(200)  NULL DEFAULT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_monk_mode_day_progress_day` (`progress_id`, `day_index`),
    INDEX `idx_monk_mode_day_progress_scheduled_date` (`progress_id`, `scheduled_date`),
    CONSTRAINT `fk_monk_mode_days_progress`
        FOREIGN KEY (`progress_id`) REFERENCES `monk_mode_progress` (`id`)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- 3. monk_mode_tasks
CREATE TABLE IF NOT EXISTS `monk_mode_tasks` (
    `id`              INT           NOT NULL AUTO_INCREMENT,
    `progress_id`     INT           NOT NULL,
    `day_index`       INT           NOT NULL,
    `task_key`        VARCHAR(80)   NOT NULL,
    `is_required`     TINYINT(1)    NOT NULL DEFAULT 1,
    `status`          VARCHAR(20)   NOT NULL DEFAULT 'pending',
    `completed_at`    DATETIME      NULL DEFAULT NULL,
    `notes`           TEXT          NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_monk_mode_task_progress_day_key` (`progress_id`, `day_index`, `task_key`),
    INDEX `idx_monk_mode_tasks_progress` (`progress_id`),
    CONSTRAINT `fk_monk_mode_tasks_progress`
        FOREIGN KEY (`progress_id`) REFERENCES `monk_mode_progress` (`id`)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- 4. monk_mode_badges
CREATE TABLE IF NOT EXISTS `monk_mode_badges` (
    `id`              INT           NOT NULL AUTO_INCREMENT,
    `progress_id`     INT           NOT NULL,
    `badge_key`       VARCHAR(80)   NOT NULL,
    `rarity`          VARCHAR(20)   NOT NULL DEFAULT 'common',
    `earned_at`       DATETIME      NULL DEFAULT NULL,
    `status`          VARCHAR(20)   NOT NULL DEFAULT 'locked',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_monk_mode_badge_progress_key` (`progress_id`, `badge_key`),
    INDEX `idx_monk_mode_badges_progress` (`progress_id`),
    CONSTRAINT `fk_monk_mode_badges_progress`
        FOREIGN KEY (`progress_id`) REFERENCES `monk_mode_progress` (`id`)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- 5. monk_mode_logs
CREATE TABLE IF NOT EXISTS `monk_mode_logs` (
    `id`              INT           NOT NULL AUTO_INCREMENT,
    `progress_id`     INT           NOT NULL,
    `action`          VARCHAR(60)   NOT NULL,
    `message`         VARCHAR(500)  NULL DEFAULT NULL,
    `created_at`      DATETIME      NOT NULL,
    PRIMARY KEY (`id`),
    INDEX `idx_monk_mode_logs_progress` (`progress_id`),
    CONSTRAINT `fk_monk_mode_logs_progress`
        FOREIGN KEY (`progress_id`) REFERENCES `monk_mode_progress` (`id`)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- 6. monk_mode_resets
CREATE TABLE IF NOT EXISTS `monk_mode_resets` (
    `id`                   INT           NOT NULL AUTO_INCREMENT,
    `progress_id`          INT           NOT NULL,
    `reset_reason`         VARCHAR(200)  NOT NULL,
    `triggered_at`         DATETIME      NOT NULL,
    `previous_current_day` INT           NULL DEFAULT NULL,
    `previous_streak`      INT           NULL DEFAULT NULL,
    PRIMARY KEY (`id`),
    INDEX `idx_monk_mode_resets_progress` (`progress_id`),
    CONSTRAINT `fk_monk_mode_resets_progress`
        FOREIGN KEY (`progress_id`) REFERENCES `monk_mode_progress` (`id`)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- 7. monk_mode_levels
CREATE TABLE IF NOT EXISTS `monk_mode_levels` (
    `id`                INT           NOT NULL AUTO_INCREMENT,
    `progress_id`       INT           NOT NULL,
    `level_key`         VARCHAR(40)   NOT NULL DEFAULT 'weak_mind',
    `level_index`       INT           NOT NULL DEFAULT 1,
    `progress_percent`  INT           NOT NULL DEFAULT 0,
    `updated_at`        DATETIME      NULL DEFAULT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_monk_mode_levels_progress` (`progress_id`),
    CONSTRAINT `fk_monk_mode_levels_progress`
        FOREIGN KEY (`progress_id`) REFERENCES `monk_mode_progress` (`id`)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
