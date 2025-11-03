-- ============================================================================
-- SNOWFLAKE OLAP - DIMENSIONS (Direct OLTP Mapping)
-- ============================================================================
-- Only create dimensions from tables that EXIST in OLTP
-- No synthetic or derived dimensions
-- ============================================================================

-- From OLTP: products table
CREATE TABLE IF NOT EXISTS dim_products (
  product_id VARCHAR PRIMARY KEY,
  name VARCHAR NOT NULL,
  category VARCHAR NOT NULL,
  active BOOLEAN DEFAULT true,
  created_at TIMESTAMP_NTZ
);

-- From OLTP: transaction_modalities table
CREATE TABLE IF NOT EXISTS dim_modalities (
  modality_id VARCHAR PRIMARY KEY,
  code VARCHAR UNIQUE NOT NULL,
  name VARCHAR NOT NULL,
  type VARCHAR NOT NULL,
  active BOOLEAN DEFAULT true,
  created_at TIMESTAMP_NTZ
);

-- From OLTP: acquirers table
CREATE TABLE IF NOT EXISTS dim_acquirers (
  acquirer_id VARCHAR PRIMARY KEY,
  name VARCHAR NOT NULL,
  active BOOLEAN DEFAULT true,
  created_at TIMESTAMP_NTZ
);

-- From OLTP: cards table (denormalized for quick lookup)
CREATE TABLE IF NOT EXISTS dim_cards (
  card_id VARCHAR PRIMARY KEY,
  cardholder_id VARCHAR NOT NULL,
  modality_id VARCHAR,
  card_type VARCHAR NOT NULL,
  expiration_date DATE NOT NULL,
  issue_date DATE NOT NULL,
  status VARCHAR NOT NULL,
  created_at TIMESTAMP_NTZ
);

-- From OLTP: cardholders table (denormalized)
CREATE TABLE IF NOT EXISTS dim_cardholders (
  cardholder_id VARCHAR PRIMARY KEY,
  company_id VARCHAR NOT NULL,
  name VARCHAR NOT NULL,
  city VARCHAR NOT NULL,
  state VARCHAR NOT NULL,
  position VARCHAR,
  department VARCHAR,
  admission_date DATE NOT NULL,
  status VARCHAR NOT NULL,
  created_at TIMESTAMP_NTZ
);

-- From OLTP: companies table (denormalized)
CREATE TABLE IF NOT EXISTS dim_companies (
  company_id VARCHAR PRIMARY KEY,
  cnpj VARCHAR UNIQUE NOT NULL,
  company_name VARCHAR NOT NULL,
  trade_name VARCHAR,
  segment VARCHAR NOT NULL,
  city VARCHAR NOT NULL,
  state VARCHAR NOT NULL,
  status VARCHAR NOT NULL,
  registration_date DATE NOT NULL,
  created_at TIMESTAMP_NTZ
);

-- From OLTP: establishments table (denormalized)
CREATE TABLE IF NOT EXISTS dim_establishments (
  establishment_id VARCHAR PRIMARY KEY,
  cnpj VARCHAR UNIQUE NOT NULL,
  company_name VARCHAR NOT NULL,
  trade_name VARCHAR,
  main_cnae VARCHAR NOT NULL,
  mcc_code VARCHAR NOT NULL,
  category VARCHAR NOT NULL,
  city VARCHAR NOT NULL,
  state VARCHAR NOT NULL,
  status VARCHAR NOT NULL,
  accreditation_date DATE NOT NULL,
  created_at TIMESTAMP_NTZ
);

-- From OLTP: terminals table (denormalized)
CREATE TABLE IF NOT EXISTS dim_terminals (
  terminal_id VARCHAR PRIMARY KEY,
  establishment_id VARCHAR NOT NULL,
  acquirer_id VARCHAR NOT NULL,
  model VARCHAR,
  type VARCHAR NOT NULL,
  status VARCHAR NOT NULL,
  installation_date DATE NOT NULL,
  created_at TIMESTAMP_NTZ
);
