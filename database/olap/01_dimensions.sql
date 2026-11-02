-- ============================================================================
-- OLAP DIMENSIONS - DuckDB/Snowflake
-- Denormalized from OLTP
-- No timestamps: read-only, append-only system
-- ============================================================================

CREATE TABLE IF NOT EXISTS dim_wallets (
  id VARCHAR PRIMARY KEY,
  name VARCHAR NOT NULL,
  category VARCHAR NOT NULL,
  active BOOLEAN DEFAULT true
);

CREATE TABLE IF NOT EXISTS dim_card_programs (
  id VARCHAR PRIMARY KEY,
  name VARCHAR NOT NULL,
  network_type VARCHAR NOT NULL,
  active BOOLEAN DEFAULT true
);

CREATE TABLE IF NOT EXISTS dim_transaction_modalities (
  id VARCHAR PRIMARY KEY,
  name VARCHAR NOT NULL,
  type VARCHAR NOT NULL,
  active BOOLEAN DEFAULT true
);

CREATE TABLE IF NOT EXISTS dim_acquirers (
  id VARCHAR PRIMARY KEY,
  name VARCHAR NOT NULL,
  active BOOLEAN DEFAULT true
);

CREATE TABLE IF NOT EXISTS dim_cards (
  id VARCHAR PRIMARY KEY,
  cardholder_id VARCHAR NOT NULL,
  program_id VARCHAR NOT NULL,
  modality_id VARCHAR NOT NULL,
  card_type VARCHAR NOT NULL,
  expiration_date DATE NOT NULL,
  issue_date DATE NOT NULL,
  status VARCHAR NOT NULL,
  status_since DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_cardholders (
  id VARCHAR PRIMARY KEY,
  company_id VARCHAR NOT NULL,
  city VARCHAR NOT NULL,
  state VARCHAR NOT NULL,
  position VARCHAR,
  department VARCHAR,
  admission_date DATE NOT NULL,
  status VARCHAR NOT NULL,
  status_since DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_companies (
  id VARCHAR PRIMARY KEY,
  parent_id VARCHAR,
  name VARCHAR NOT NULL,
  trade_name VARCHAR,
  segment VARCHAR NOT NULL,
  city VARCHAR NOT NULL,
  state VARCHAR NOT NULL,
  status VARCHAR NOT NULL,
  registration_date DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_establishments (
  id VARCHAR PRIMARY KEY,
  name VARCHAR NOT NULL,
  trade_name VARCHAR,
  main_cnae VARCHAR NOT NULL,
  mcc_code VARCHAR NOT NULL,
  category VARCHAR NOT NULL,
  city VARCHAR NOT NULL,
  state VARCHAR NOT NULL,
  status VARCHAR NOT NULL,
  status_since DATE NOT NULL,
  accreditation_date DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_terminals (
  id VARCHAR PRIMARY KEY,
  establishment_id VARCHAR NOT NULL,
  acquirer_id VARCHAR NOT NULL,
  model VARCHAR,
  type VARCHAR NOT NULL,
  status VARCHAR NOT NULL,
  status_since DATE NOT NULL,
  installation_date DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_card_wallets (
  id VARCHAR PRIMARY KEY,
  card_id VARCHAR NOT NULL,
  wallet_id VARCHAR NOT NULL,
  monthly_credit DECIMAL(15, 2) NOT NULL,
  daily_limit DECIMAL(15, 2),
  monthly_limit DECIMAL(15, 2),
  daily_count_limit INTEGER,
  final_balance DECIMAL(15, 2) NOT NULL,
  activation_date DATE NOT NULL,
  status VARCHAR NOT NULL,
  status_since DATE NOT NULL
);

-- ============================================================================
-- REFERENCE TABLES: the rules behind the answers
-- ============================================================================

CREATE TABLE IF NOT EXISTS ref_response_codes (
  id VARCHAR PRIMARY KEY,
  description VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS ref_program_wallets (
  program_id VARCHAR NOT NULL,
  wallet_id VARCHAR NOT NULL,
  PRIMARY KEY (program_id, wallet_id)
);

CREATE TABLE IF NOT EXISTS ref_cnae_wallets (
  cnae_code VARCHAR NOT NULL,
  wallet_id VARCHAR NOT NULL,
  cnae_description VARCHAR,
  active BOOLEAN NOT NULL,
  PRIMARY KEY (cnae_code, wallet_id)
);

CREATE TABLE IF NOT EXISTS ref_mcc_wallets (
  mcc_code VARCHAR NOT NULL,
  wallet_id VARCHAR NOT NULL,
  PRIMARY KEY (mcc_code, wallet_id)
);

CREATE TABLE IF NOT EXISTS ref_mcc_modalities (
  mcc_code VARCHAR NOT NULL,
  modality_id VARCHAR NOT NULL,
  mcc_description VARCHAR NOT NULL,
  active BOOLEAN NOT NULL,
  PRIMARY KEY (mcc_code, modality_id)
);
