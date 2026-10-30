-- ============================================================================
-- OLAP FACT TABLE - DuckDB/Snowflake
-- Denormalized from OLTP transactions + authorizations
-- No timestamps: read-only, append-only system
-- ============================================================================

CREATE TABLE IF NOT EXISTS fact_transactions (
  id VARCHAR PRIMARY KEY,
  related_transaction_id VARCHAR,
  card_id VARCHAR NOT NULL,
  cardholder_id VARCHAR NOT NULL,
  program_id VARCHAR NOT NULL,
  wallet_id VARCHAR,
  establishment_id VARCHAR NOT NULL,
  terminal_id VARCHAR NOT NULL,
  amount DECIMAL(15, 2) NOT NULL,
  date TIMESTAMP NOT NULL,
  capture_type VARCHAR NOT NULL,
  pin_status VARCHAR NOT NULL,
  response_code VARCHAR NOT NULL,
  response_message VARCHAR,
  decline_reason VARCHAR,
  authorization_code VARCHAR,
  nsu VARCHAR,
  authorization_datetime TIMESTAMP,
  authorization_status VARCHAR
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
CREATE INDEX IF NOT EXISTS idx_ft_authorization_status ON fact_transactions(authorization_status);
