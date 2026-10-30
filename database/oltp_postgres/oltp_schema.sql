-- ============================================================================
-- OLTP Schema - Corporate Benefits Operational System
-- PostgreSQL
-- ============================================================================
-- Naming Convention:
-- - Primary Keys: 'id' for all tables
-- - Foreign Keys: '*_id' (descriptive suffix)
-- ============================================================================

CREATE TABLE IF NOT EXISTS products (
  id CHAR(2) PRIMARY KEY,
  name VARCHAR NOT NULL,
  category VARCHAR NOT NULL,
  active BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS transaction_modalities (
  id VARCHAR PRIMARY KEY,
  name VARCHAR NOT NULL,
  type VARCHAR NOT NULL,
  active BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS acquirers (
  id VARCHAR PRIMARY KEY,
  name VARCHAR NOT NULL,
  active BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS mcc_modalities (
  mcc_code VARCHAR NOT NULL,
  modality_id VARCHAR NOT NULL,
  mcc_description VARCHAR NOT NULL,
  observation VARCHAR,
  active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT now(),
  PRIMARY KEY (mcc_code, modality_id),
  FOREIGN KEY (modality_id) REFERENCES transaction_modalities(id)
);

CREATE TABLE IF NOT EXISTS cnae_products (
  cnae_code VARCHAR NOT NULL,
  product_id VARCHAR NOT NULL,
  cnae_description VARCHAR,
  observation VARCHAR,
  active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT now(),
  PRIMARY KEY (cnae_code, product_id),
  FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS companies (
  id VARCHAR PRIMARY KEY,
  parent_id VARCHAR,
  cnpj VARCHAR UNIQUE NOT NULL,
  name VARCHAR NOT NULL,
  trade_name VARCHAR,
  segment VARCHAR NOT NULL,
  city VARCHAR NOT NULL,
  state VARCHAR NOT NULL,
  status VARCHAR NOT NULL DEFAULT 'active',
  registration_date DATE NOT NULL,
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP,
  FOREIGN KEY (parent_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS cardholders (
  id VARCHAR PRIMARY KEY,
  company_id VARCHAR NOT NULL,
  cpf_hash VARCHAR UNIQUE NOT NULL,
  name VARCHAR NOT NULL,
  city VARCHAR NOT NULL,
  state VARCHAR NOT NULL,
  admission_date DATE NOT NULL,
  position VARCHAR,
  department VARCHAR,
  status VARCHAR NOT NULL DEFAULT 'active',
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP,
  FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS cards (
  id VARCHAR PRIMARY KEY,
  cardholder_id VARCHAR NOT NULL,
  card_number_hash VARCHAR UNIQUE NOT NULL,
  modality_id VARCHAR,
  expiration_date DATE NOT NULL,
  card_type VARCHAR NOT NULL,
  status VARCHAR NOT NULL DEFAULT 'active',
  issue_date DATE NOT NULL,
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP,
  FOREIGN KEY (cardholder_id) REFERENCES cardholders(id),
  FOREIGN KEY (modality_id) REFERENCES transaction_modalities(id)
);

COMMENT ON COLUMN cards.modality_id IS 'NULL = proprietary network';

CREATE TABLE IF NOT EXISTS card_products (
  id VARCHAR PRIMARY KEY,
  card_id VARCHAR NOT NULL,
  product_id VARCHAR NOT NULL,
  current_balance DECIMAL(15,2) NOT NULL DEFAULT 0,
  daily_limit DECIMAL(15,2) DEFAULT 0,
  monthly_limit DECIMAL(15,2) DEFAULT 0,
  activation_date DATE NOT NULL,
  status VARCHAR NOT NULL DEFAULT 'active',
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP,
  FOREIGN KEY (card_id) REFERENCES cards(id),
  FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS establishments (
  id VARCHAR PRIMARY KEY,
  cnpj VARCHAR UNIQUE NOT NULL,
  name VARCHAR NOT NULL,
  trade_name VARCHAR,
  main_cnae VARCHAR NOT NULL,
  mcc_code VARCHAR NOT NULL,
  category VARCHAR NOT NULL,
  city VARCHAR NOT NULL,
  state VARCHAR NOT NULL,
  status VARCHAR NOT NULL DEFAULT 'active',
  accreditation_date DATE NOT NULL,
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS terminals (
  id VARCHAR PRIMARY KEY,
  establishment_id VARCHAR NOT NULL,
  acquirer_id VARCHAR NOT NULL,
  model VARCHAR,
  type VARCHAR NOT NULL,
  status VARCHAR NOT NULL DEFAULT 'active',
  installation_date DATE NOT NULL,
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP,
  FOREIGN KEY (establishment_id) REFERENCES establishments(id),
  FOREIGN KEY (acquirer_id) REFERENCES acquirers(id)
);

CREATE TABLE IF NOT EXISTS transactions (
  id VARCHAR PRIMARY KEY,
  card_id VARCHAR NOT NULL,
  product_id VARCHAR NOT NULL,
  establishment_id VARCHAR NOT NULL,
  terminal_id VARCHAR NOT NULL,
  amount DECIMAL(15,2) NOT NULL,
  date TIMESTAMP NOT NULL,
  capture_type VARCHAR NOT NULL,
  response_code VARCHAR NOT NULL,
  response_message VARCHAR,
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP,
  FOREIGN KEY (card_id) REFERENCES cards(id),
  FOREIGN KEY (product_id) REFERENCES products(id),
  FOREIGN KEY (establishment_id) REFERENCES establishments(id),
  FOREIGN KEY (terminal_id) REFERENCES terminals(id)
);

CREATE TABLE IF NOT EXISTS authorizations (
  id VARCHAR PRIMARY KEY,
  transaction_id VARCHAR NOT NULL,
  authorization_code VARCHAR,
  nsu VARCHAR NOT NULL,
  authorization_datetime TIMESTAMP NOT NULL,
  status VARCHAR NOT NULL,
  created_at TIMESTAMP DEFAULT now(),
  FOREIGN KEY (transaction_id) REFERENCES transactions(id)
);

CREATE TABLE IF NOT EXISTS balance_history (
  id VARCHAR PRIMARY KEY,
  card_product_id VARCHAR NOT NULL,
  transaction_id VARCHAR,
  operation_type VARCHAR NOT NULL,
  operation_amount DECIMAL(15,2) NOT NULL,
  previous_balance DECIMAL(15,2) NOT NULL,
  posterior_balance DECIMAL(15,2) NOT NULL,
  operation_date TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT now(),
  FOREIGN KEY (card_product_id) REFERENCES card_products(id),
  FOREIGN KEY (transaction_id) REFERENCES transactions(id)
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX idx_companies_cnpj ON companies(cnpj);
CREATE INDEX idx_companies_status ON companies(status);
CREATE INDEX idx_companies_parent_id ON companies(parent_id);

CREATE INDEX idx_cardholders_company_id ON cardholders(company_id);
CREATE INDEX idx_cardholders_status ON cardholders(status);

CREATE INDEX idx_cards_cardholder_id ON cards(cardholder_id);
CREATE INDEX idx_cards_status ON cards(status);

CREATE INDEX idx_card_products_card_id ON card_products(card_id);
CREATE INDEX idx_card_products_product_id ON card_products(product_id);

CREATE INDEX idx_establishments_cnpj ON establishments(cnpj);
CREATE INDEX idx_establishments_status ON establishments(status);

CREATE INDEX idx_terminals_establishment_id ON terminals(establishment_id);
CREATE INDEX idx_terminals_acquirer_id ON terminals(acquirer_id);

CREATE INDEX idx_transactions_card_id ON transactions(card_id);
CREATE INDEX idx_transactions_product_id ON transactions(product_id);
CREATE INDEX idx_transactions_establishment_id ON transactions(establishment_id);
CREATE INDEX idx_transactions_terminal_id ON transactions(terminal_id);
CREATE INDEX idx_transactions_date ON transactions(date);
CREATE INDEX idx_transactions_response_code ON transactions(response_code);

CREATE INDEX idx_authorizations_transaction_id ON authorizations(transaction_id);

CREATE INDEX idx_balance_history_card_product_id ON balance_history(card_product_id);
CREATE INDEX idx_balance_history_transaction_id ON balance_history(transaction_id);
