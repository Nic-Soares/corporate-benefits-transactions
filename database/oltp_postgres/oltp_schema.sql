-- ============================================================================
-- OLTP Schema - Corporate Benefits Operational System
-- PostgreSQL
-- ============================================================================
-- Naming Convention:
-- - Primary Keys: 'id' for all tables
-- - Foreign Keys: '*_id' (descriptive suffix)
-- ============================================================================

CREATE TABLE IF NOT EXISTS wallets (
  id VARCHAR PRIMARY KEY,
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

CREATE TABLE IF NOT EXISTS response_codes (
  id VARCHAR PRIMARY KEY,
  description VARCHAR NOT NULL
);

COMMENT ON TABLE response_codes IS 'ISO 8583 response codes';

CREATE TABLE IF NOT EXISTS card_programs (
  id VARCHAR PRIMARY KEY,
  name VARCHAR NOT NULL,
  network_type VARCHAR NOT NULL,
  active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP
);

COMMENT ON COLUMN card_programs.network_type IS 'proprietary_network (3-party) or brand (4-party)';

CREATE TABLE IF NOT EXISTS card_program_wallets (
  program_id VARCHAR NOT NULL,
  wallet_id VARCHAR NOT NULL,
  PRIMARY KEY (program_id, wallet_id),
  FOREIGN KEY (program_id) REFERENCES card_programs(id),
  FOREIGN KEY (wallet_id) REFERENCES wallets(id)
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

CREATE TABLE IF NOT EXISTS cnae_wallets (
  cnae_code VARCHAR NOT NULL,
  wallet_id VARCHAR NOT NULL,
  cnae_description VARCHAR,
  observation VARCHAR,
  active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT now(),
  PRIMARY KEY (cnae_code, wallet_id),
  FOREIGN KEY (wallet_id) REFERENCES wallets(id)
);

CREATE TABLE IF NOT EXISTS mcc_wallets (
  mcc_code VARCHAR NOT NULL,
  wallet_id VARCHAR NOT NULL,
  PRIMARY KEY (mcc_code, wallet_id),
  FOREIGN KEY (wallet_id) REFERENCES wallets(id)
);

COMMENT ON TABLE mcc_wallets IS 'Brand (4-party) cards: wallets the issuer can charge at each MCC; GIFT takes any MCC and has no rows';

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
  program_id VARCHAR NOT NULL,
  card_number_hash VARCHAR UNIQUE NOT NULL,
  modality_id VARCHAR NOT NULL,
  expiration_date DATE NOT NULL,
  card_type VARCHAR NOT NULL,
  status VARCHAR NOT NULL DEFAULT 'active',
  issue_date DATE NOT NULL,
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP,
  FOREIGN KEY (cardholder_id) REFERENCES cardholders(id),
  FOREIGN KEY (program_id) REFERENCES card_programs(id),
  FOREIGN KEY (modality_id) REFERENCES transaction_modalities(id)
);

COMMENT ON COLUMN cards.modality_id IS 'OWN for proprietary-network programs; VISA, MASTERCARD or ELO for brand programs';

CREATE TABLE IF NOT EXISTS card_wallets (
  id VARCHAR PRIMARY KEY,
  card_id VARCHAR NOT NULL,
  wallet_id VARCHAR NOT NULL,
  current_balance DECIMAL(15,2) NOT NULL DEFAULT 0,
  monthly_credit DECIMAL(15,2) NOT NULL DEFAULT 0,
  daily_limit DECIMAL(15,2) DEFAULT 0,
  monthly_limit DECIMAL(15,2) DEFAULT 0,
  daily_count_limit INTEGER DEFAULT 0,
  activation_date DATE NOT NULL,
  status VARCHAR NOT NULL DEFAULT 'active',
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP,
  FOREIGN KEY (card_id) REFERENCES cards(id),
  FOREIGN KEY (wallet_id) REFERENCES wallets(id),
  UNIQUE (card_id, wallet_id)
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
  card_wallet_id VARCHAR,
  transaction_type VARCHAR NOT NULL,
  wallet_option VARCHAR,
  establishment_id VARCHAR NOT NULL,
  terminal_id VARCHAR NOT NULL,
  amount DECIMAL(15,2) NOT NULL,
  date TIMESTAMP NOT NULL,
  capture_type VARCHAR NOT NULL,
  pin_status VARCHAR NOT NULL,
  response_code VARCHAR NOT NULL,
  decline_reason VARCHAR,
  nsu VARCHAR NOT NULL,
  authorization_code VARCHAR,
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP,
  FOREIGN KEY (card_id) REFERENCES cards(id),
  FOREIGN KEY (card_wallet_id) REFERENCES card_wallets(id),
  FOREIGN KEY (establishment_id) REFERENCES establishments(id),
  FOREIGN KEY (terminal_id) REFERENCES terminals(id),
  FOREIGN KEY (response_code) REFERENCES response_codes(id)
);

COMMENT ON COLUMN card_wallets.monthly_credit IS 'Benefit credited on the credit day each month (synthetic)';
COMMENT ON COLUMN card_wallets.daily_count_limit IS 'Purchases per day on the wallet; 0 = no limit';
COMMENT ON COLUMN transactions.card_wallet_id IS 'Wallet of the card charged, routed by the issuer; NULL when no wallet could be routed';
COMMENT ON COLUMN transactions.transaction_type IS 'purchase or withdrawal';
COMMENT ON COLUMN transactions.wallet_option IS 'Proprietary network: FOOD, MEAL or OTHERS, picked on the terminal; NULL on brand cards';
COMMENT ON COLUMN transactions.pin_status IS 'ok, wrong or not_required';
COMMENT ON COLUMN transactions.decline_reason IS 'Specific cause behind the ISO response code; NULL when approved';
COMMENT ON COLUMN transactions.nsu IS 'Sequence number the terminal gives the attempt';
COMMENT ON COLUMN transactions.authorization_code IS 'Issued by the issuer on approval; NULL when declined';

CREATE TABLE IF NOT EXISTS balance_history (
  id VARCHAR PRIMARY KEY,
  card_wallet_id VARCHAR NOT NULL,
  transaction_id VARCHAR,
  operation_type VARCHAR NOT NULL,
  operation_amount DECIMAL(15,2) NOT NULL,
  previous_balance DECIMAL(15,2) NOT NULL,
  posterior_balance DECIMAL(15,2) NOT NULL,
  operation_date TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT now(),
  FOREIGN KEY (card_wallet_id) REFERENCES card_wallets(id),
  FOREIGN KEY (transaction_id) REFERENCES transactions(id)
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_companies_cnpj ON companies(cnpj);
CREATE INDEX IF NOT EXISTS idx_companies_status ON companies(status);
CREATE INDEX IF NOT EXISTS idx_companies_parent_id ON companies(parent_id);

CREATE INDEX IF NOT EXISTS idx_cardholders_company_id ON cardholders(company_id);
CREATE INDEX IF NOT EXISTS idx_cardholders_status ON cardholders(status);

CREATE INDEX IF NOT EXISTS idx_cards_cardholder_id ON cards(cardholder_id);
CREATE INDEX IF NOT EXISTS idx_cards_status ON cards(status);

CREATE INDEX IF NOT EXISTS idx_cards_program_id ON cards(program_id);

CREATE INDEX IF NOT EXISTS idx_card_wallets_card_id ON card_wallets(card_id);
CREATE INDEX IF NOT EXISTS idx_card_wallets_wallet_id ON card_wallets(wallet_id);

CREATE INDEX IF NOT EXISTS idx_establishments_cnpj ON establishments(cnpj);
CREATE INDEX IF NOT EXISTS idx_establishments_status ON establishments(status);

CREATE INDEX IF NOT EXISTS idx_terminals_establishment_id ON terminals(establishment_id);
CREATE INDEX IF NOT EXISTS idx_terminals_acquirer_id ON terminals(acquirer_id);

CREATE INDEX IF NOT EXISTS idx_transactions_card_id ON transactions(card_id);
CREATE INDEX IF NOT EXISTS idx_transactions_card_wallet_id ON transactions(card_wallet_id);
CREATE INDEX IF NOT EXISTS idx_transactions_establishment_id ON transactions(establishment_id);
CREATE INDEX IF NOT EXISTS idx_transactions_terminal_id ON transactions(terminal_id);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_transactions_response_code ON transactions(response_code);

CREATE INDEX IF NOT EXISTS idx_balance_history_card_wallet_id ON balance_history(card_wallet_id);
CREATE INDEX IF NOT EXISTS idx_balance_history_transaction_id ON balance_history(transaction_id);
