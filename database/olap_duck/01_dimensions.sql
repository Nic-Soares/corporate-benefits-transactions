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
  status VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_cardholders (
  id VARCHAR PRIMARY KEY,
  company_id VARCHAR NOT NULL,
  name VARCHAR NOT NULL,
  city VARCHAR NOT NULL,
  state VARCHAR NOT NULL,
  position VARCHAR,
  department VARCHAR,
  admission_date DATE NOT NULL,
  status VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_companies (
  id VARCHAR PRIMARY KEY,
  parent_id VARCHAR,
  cnpj VARCHAR UNIQUE NOT NULL,
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
  cnpj VARCHAR UNIQUE NOT NULL,
  name VARCHAR NOT NULL,
  trade_name VARCHAR,
  main_cnae VARCHAR NOT NULL,
  mcc_code VARCHAR NOT NULL,
  category VARCHAR NOT NULL,
  city VARCHAR NOT NULL,
  state VARCHAR NOT NULL,
  status VARCHAR NOT NULL,
  accreditation_date DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_terminals (
  id VARCHAR PRIMARY KEY,
  establishment_id VARCHAR NOT NULL,
  acquirer_id VARCHAR NOT NULL,
  model VARCHAR,
  type VARCHAR NOT NULL,
  status VARCHAR NOT NULL,
  installation_date DATE NOT NULL
);
