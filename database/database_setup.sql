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
    user_type VARCHAR(20) CHECK (user_type IN ('ACCOUNT_OWNER''CUSTOMER', 'AGENT', 'MERCHANT', 'SYSTEM')),
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
--  3. Sample data manipulation language queries to add records in tables.
   -- adding new users in table.
INSERT INTO users
(full_name, phone_number, masked_phone, merchant_code, account_number, user_type)
VALUES
('Abebe Chala CHEBUDIE', NULL, '*********036', NULL, '36521838', 'ACCOUNT_OWNER'),
('Jane Smith', NULL, '*********013', NULL, NULL, 'INDIVIDUAL'),
('Jane Smith', NULL, NULL, '12845', NULL, 'MERCHANT'),
('Samuel Carter', '250791666666', NULL, NULL, NULL, 'INDIVIDUAL'),
('Agent Sophia', '250790777777', NULL, NULL, NULL, 'AGENT'),
('Airtime', NULL, NULL, NULL, NULL, 'BILLER');
 -- adding new transaction categories.
INSERT INTO transaction_categories (category_code, category_name, direction, sms_pattern, description) VALUES
('INCOMING_MONEY',    'Incoming Money',            'CREDIT', '^You have received',              'Money received from another MoMo user'),
('MERCHANT_PAYMENT',  'Payment to Code Holder',    'DEBIT',  '^TxId: \\d+\\. Your payment of',  'MoMo Pay payment to a merchant code'),
('MOBILE_TRANSFER',   'Transfer to Mobile Number', 'DEBIT',  '^\\*165\\*S\\*',                  'Person-to-person transfer to a phone number'),
('BANK_DEPOSIT',      'Bank Deposit',              'CREDIT', 'bank deposit of',                 'Cash or bank deposit into the MoMo wallet'),
('BANK_TRANSFER',     'Transfer via Bank',         'DEBIT',  '^You have transferred .* bank',   'Transfer made from a linked bank account'),
('AIRTIME',           'Airtime Purchase',          'DEBIT',  'to Airtime with token',           'Airtime bought with MoMo');
  -- adding records inside transactions table.
INSERT INTO transactions
(external_txn_id, sms_id, category_id, amount, fee, balance_after, status, token, message, transaction_date)
VALUES
('76662021700', 1, 1, 2000.00, 0.00, 2000.00, 'SUCCESS', NULL, NULL, '2024-05-10 16:30:51'),
('73214484437', 2, 2, 1000.00, 0.00, 1000.00, 'SUCCESS', NULL, NULL, '2024-05-10 16:31:39'),
(NULL, 3, 3, 10000.00, 100.00, 28300.00, 'SUCCESS', NULL, NULL, '2024-05-11 20:34:47'),
(NULL, 4, 4, 40000.00, 0.00, 40400.00, 'SUCCESS', NULL, NULL, '2024-05-11 18:43:49');
  -- adding records inside sms_message table.
INSERT INTO sms_messages (protocol, address, msg_type, date_ms, date_sent_ms, readable_date, body, service_center) VALUES
(0, 'M-Money', 1, 1715351458724, 1715351451000, '10 May 2024 4:30:58 PM',
 'You have received 2000 RWF from Jane Smith (*********013) on your mobile money account at 2024-05-10 16:30:51. Message from sender: . Your new balance:2000 RWF. Financial Transaction Id: 76662021700.',
 '+250788110381'),
(0, 'M-Money', 1, 1715351506754, 1715351498000, '10 May 2024 4:31:46 PM',
 'TxId: 73214484437. Your payment of 1,000 RWF to Jane Smith 12845 has been completed at 2024-05-10 16:31:39. Your new balance: 1,000 RWF. Fee was 0 RWF.Kanda*182*16# wiyandikishe muri poromosiyo ya BivaMoMotima, ugire amahirwe yo gutsindira ibihembo bishimishije.',
 '+250788110381'),
(0, 'M-Money', 1, 1715452495316, 1715452487000, '11 May 2024 8:34:55 PM',
 '*165*S*10000 RWF transferred to Samuel Carter (250791666666) from 36521838 at 2024-05-11 20:34:47 . Fee was: 100 RWF. New balance: 28300 RWF. Kugura ama inite cg interineti kuri MoMo, Kanda *182*2*1# .*EN#',
 '+250788110381'),
(0, 'M-Money', 1, 1715445936412, 1715445829000, '11 May 2024 6:45:36 PM',
 '*113*R*A bank deposit of 40000 RWF has been added to your mobile money account at 2024-05-11 18:43:49. Your NEW BALANCE :40400 RWF. Cash Deposit::CASH::::0::250795963036.Thank you for using MTN MobileMoney.*EN#',
 '+250788110381'),
(0, 'M-Money', 1, 1715506895734, 1715506888000, '12 May 2024 11:41:35 AM',
 '*162*TxId:13913173274*S*Your payment of 2000 RWF to Airtime with token  has been completed at 2024-05-12 11:41:28. Fee was 0 RWF. Your new balance: 25280 RWF . Message: - -. *EN#',
 '+250788110381');
 -- adding records inside transactions-participants.
INSERT INTO transaction_participants
(transaction_id, user_id, role)
VALUES
(6, 2, 'SENDER'),
(6, 1, 'RECEIVER'),
(7, 1, 'SENDER'),
(7, 3, 'RECEIVER'),
(8, 1, 'SENDER'),
(8, 4, 'RECEIVER'),
(9, 1, 'RECEIVER');
 -- adding records inside system-logs.
INSERT INTO system_logs
(sms_id, transaction_id, log_level, event_type, message, created_at)
VALUES
(NULL, NULL, 'INFO', 'IMPORT_START',
 'Import started: modified_sms_v2.xml (1693 messages)',
 '2026-09-15 09:00:00'),

(1, 6, 'INFO', 'PARSED',
 'Parsed INCOMING_MONEY 2000 RWF',
 '2026-09-15 09:00:01'),

(2, 7, 'INFO', 'PARSED',
 'Parsed MERCHANT_PAYMENT 1000 RWF',
 '2026-09-15 09:00:01'),

(3, 8, 'WARNING', 'PARSED',
 'Parsed MOBILE_TRANSFER 10000 RWF; no TxId in message',
 '2026-09-15 09:00:01'),

(4, 9, 'WARNING', 'PARSED',
 'Parsed BANK_DEPOSIT 40000 RWF; no TxId in message',
 '2026-09-15 09:00:01');
