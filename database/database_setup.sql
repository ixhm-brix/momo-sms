CREATE DATABASE IF NOT EXISTS momo_sms_db;
USE momo_sms_db;

CREATE TABLE IF NOT EXISTS transaction_categories (
    category_id INT UNSIGNED AUTO_INCREMENT,
    category_code VARCHAR(30) NOT NULL,
    category_name VARCHAR(60) NOT NULL,
    direction VARCHAR(6) CHECK (direction IN ('CREDIT', 'DEBIT')),
    sms_pattern VARCHAR(255) NULL,
    description VARCHAR(255) NULL,
    PRIMARY KEY (category_id),
    UNIQUE KEY uq_category_code (category_code)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS users (
    user_id INT UNSIGNED AUTO_INCREMENT,
    full_name VARCHAR(100) NOT NULL,
    phone_number VARCHAR(15) NULL,
    masked_phone VARCHAR(15) NULL,
    merchant_code VARCHAR(10) NULL,
    account_number VARCHAR(30) NULL,
    user_type VARCHAR(20) CHECK (user_type IN ('CUSTOMER', 'AGENT', 'MERCHANT', 'SYSTEM')),
    created_at DATETIME DEFAULT NOW(),
    PRIMARY KEY (user_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS sms_messages (
    sms_id INT UNSIGNED AUTO_INCREMENT,
    protocol TINYINT,
    address VARCHAR(20) NOT NULL,
    msg_type TINYINT,
    date_ms BIGINT NOT NULL,
    date_sent_ms BIGINT,
    readable_date VARCHAR(40),
    body TEXT NOT NULL,
    service_center VARCHAR(20),
    imported_at DATETIME DEFAULT NOW(),
    PRIMARY KEY (sms_id),
    UNIQUE KEY uq_date_ms (date_ms)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id BIGINT UNSIGNED AUTO_INCREMENT,
    external_txn_id VARCHAR(20) NULL,
    sms_id INT UNSIGNED NOT NULL,
    category_id INT UNSIGNED NOT NULL,
    amount DECIMAL(12,2) CHECK (amount > 0),
    fee DECIMAL(10,2) DEFAULT 0 CHECK (fee >= 0),
    balance_after DECIMAL(12,2) NULL,
    currency CHAR(3) DEFAULT 'RWF',
    status VARCHAR(10) CHECK (status IN ('SUCCESS', 'FAILED', 'REVERSED')),
    token VARCHAR(40) NULL,
    message VARCHAR(255) NULL,
    transaction_date DATETIME NOT NULL,
    created_at DATETIME DEFAULT NOW(),
    PRIMARY KEY (transaction_id),
    UNIQUE KEY uq_external_txn_id (external_txn_id),
    UNIQUE KEY uq_txn_sms_id (sms_id),
    CONSTRAINT fk_transactions_sms FOREIGN KEY (sms_id) REFERENCES sms_messages(sms_id),
    CONSTRAINT fk_transactions_category FOREIGN KEY (category_id) REFERENCES transaction_categories(category_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS transaction_participants (
    transaction_id BIGINT UNSIGNED,
    user_id INT UNSIGNED,
    role VARCHAR(10) CHECK (role IN ('SENDER', 'RECEIVER', 'AGENT')),
    PRIMARY KEY (transaction_id, user_id, role),
    CONSTRAINT fk_participants_transaction FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id),
    CONSTRAINT fk_participants_user FOREIGN KEY (user_id) REFERENCES users(user_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS system_logs (
    log_id BIGINT UNSIGNED AUTO_INCREMENT,
    sms_id INT UNSIGNED NULL,
    transaction_id BIGINT UNSIGNED NULL,
    log_level VARCHAR(7) CHECK (log_level IN ('INFO', 'WARNING', 'ERROR')),
    event_type VARCHAR(20) NOT NULL,
    message VARCHAR(500),
    created_at DATETIME DEFAULT NOW(),
    PRIMARY KEY (log_id),
    CONSTRAINT fk_logs_sms FOREIGN KEY (sms_id) REFERENCES sms_messages(sms_id),
    CONSTRAINT fk_logs_transaction FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id)
) ENGINE=InnoDB;
-- 1. INTEGRITY & SECURITY CONSTRAINTS
-- Phone format check (Rwanda format)
ALTER TABLE users
    ADD CONSTRAINT chk_user_phone_format 
        CHECK (phone_number IS NULL OR phone_number REGEXP '^[0-9]{10,12}$');

-- Ensure financial balance cannot be negative
ALTER TABLE transactions
    ADD CONSTRAINT chk_tx_non_negative_balance 
        CHECK (balance_after IS NULL OR balance_after >= 0.00);

-- Enforce standardized 3-letter currency code (ISO 4217)
ALTER TABLE transactions
    ADD CONSTRAINT chk_tx_currency_format 
        CHECK (currency REGEXP '^[A-Z]{3}$');


-- 2. PERFORMANCE & RETRIEVAL INDEXES
-- Rapid phone number lookup for sender/receiver identification
CREATE INDEX idx_users_phone 
    ON users (phone_number);

-- Chronological sorting for statements, audits, and reconciliation
CREATE INDEX idx_tx_date 
    ON transactions (transaction_date DESC);

-- Compound index for category and status filtering
CREATE INDEX idx_tx_category_status 
    ON transactions (category_id, status);

-- Index for transaction participant lookups
CREATE INDEX idx_participants_user 
    ON transaction_participants (user_id);

-- Operational debugging: filter system logs by severity tier and time
CREATE INDEX idx_logs_level_created 
    ON system_logs (log_level, created_at DESC);
    -- Verification tests and integrity validation completed by Dana