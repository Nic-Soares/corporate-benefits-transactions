-- ============================================================================
-- OLAP FACT TABLE - DuckDB/Snowflake
-- Denormalized from OLTP: transactions (with the card, cardholder, terminal,
-- card wallet and response code they point to) and balance_history
-- No timestamps: read-only, append-only system
-- ============================================================================

CREATE TABLE IF NOT EXISTS fact_transactions (
  id VARCHAR PRIMARY KEY,
  related_transaction_id VARCHAR,
  card_id VARCHAR NOT NULL,
  cardholder_id VARCHAR NOT NULL,
  company_id VARCHAR NOT NULL,
  program_id VARCHAR NOT NULL,
  modality_id VARCHAR NOT NULL,
  card_wallet_id VARCHAR,
  wallet_id VARCHAR,
  transaction_type VARCHAR NOT NULL,
  wallet_option VARCHAR,
  establishment_id VARCHAR NOT NULL,
  terminal_id VARCHAR NOT NULL,
  acquirer_id VARCHAR NOT NULL,
  amount DECIMAL(15, 2) NOT NULL,
  date TIMESTAMP NOT NULL,
  capture_type VARCHAR NOT NULL,
  pin_status VARCHAR NOT NULL,
  response_code VARCHAR NOT NULL,
  response_message VARCHAR,
  decline_reason VARCHAR,
  nsu VARCHAR NOT NULL,
  authorization_code VARCHAR,
  is_fraud BOOLEAN NOT NULL,
  fraud_scenario VARCHAR,
  disputed BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_balance_movements (
  id VARCHAR PRIMARY KEY,
  card_wallet_id VARCHAR NOT NULL,
  card_id VARCHAR NOT NULL,
  wallet_id VARCHAR NOT NULL,
  transaction_id VARCHAR,
  operation_type VARCHAR NOT NULL,
  operation_amount DECIMAL(15, 2) NOT NULL,
  previous_balance DECIMAL(15, 2) NOT NULL,
  posterior_balance DECIMAL(15, 2) NOT NULL,
  operation_date TIMESTAMP NOT NULL
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_ft_date ON fact_transactions(date);
CREATE INDEX IF NOT EXISTS idx_ft_card_id ON fact_transactions(card_id);
CREATE INDEX IF NOT EXISTS idx_ft_cardholder_id ON fact_transactions(cardholder_id);
CREATE INDEX IF NOT EXISTS idx_ft_establishment_id ON fact_transactions(establishment_id);
CREATE INDEX IF NOT EXISTS idx_ft_terminal_id ON fact_transactions(terminal_id);
CREATE INDEX IF NOT EXISTS idx_ft_program_id ON fact_transactions(program_id);
CREATE INDEX IF NOT EXISTS idx_ft_wallet_id ON fact_transactions(wallet_id);
CREATE INDEX IF NOT EXISTS idx_ft_response_code ON fact_transactions(response_code);
CREATE INDEX IF NOT EXISTS idx_ft_company_id ON fact_transactions(company_id);
CREATE INDEX IF NOT EXISTS idx_fbm_card_wallet_id ON fact_balance_movements(card_wallet_id);
CREATE INDEX IF NOT EXISTS idx_fbm_operation_date ON fact_balance_movements(operation_date);
