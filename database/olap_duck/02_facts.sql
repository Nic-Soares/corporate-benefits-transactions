-- ============================================================================
-- SNOWFLAKE OLAP - FACT TABLE
-- ============================================================================
-- Single fact table mapped DIRECTLY from OLTP transactions
-- No complex transformations, direct field mapping
-- ============================================================================

CREATE TABLE IF NOT EXISTS fact_transactions (
  -- Transaction IDs (direct from OLTP)
  transaction_id VARCHAR PRIMARY KEY,
  related_transaction_id VARCHAR,

  -- Foreign Keys (direct from OLTP)
  card_id VARCHAR NOT NULL,
  cardholder_id VARCHAR NOT NULL,
  product_id VARCHAR NOT NULL,
  establishment_id VARCHAR NOT NULL,
  terminal_id VARCHAR NOT NULL,

  -- Financial Measures (direct from OLTP)
  transaction_amount DECIMAL(15,2) NOT NULL,

  -- Transaction Timing (direct from OLTP)
  transaction_date TIMESTAMP NOT NULL,

  -- Transaction Details (direct from OLTP)
  capture_type VARCHAR NOT NULL,
  response_code VARCHAR NOT NULL,
  response_message VARCHAR,

  -- Metadata (direct from OLTP)
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP,

  -- Constraints mapping OLTP PKs
  FOREIGN KEY (card_id) REFERENCES dim_cards(card_id),
  FOREIGN KEY (cardholder_id) REFERENCES dim_cardholders(cardholder_id),
  FOREIGN KEY (product_id) REFERENCES dim_products(product_id),
  FOREIGN KEY (establishment_id) REFERENCES dim_establishments(establishment_id),
  FOREIGN KEY (terminal_id) REFERENCES dim_terminals(terminal_id)
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX idx_ft_transaction_date ON fact_transactions(transaction_date);
CREATE INDEX idx_ft_card_id ON fact_transactions(card_id);
CREATE INDEX idx_ft_cardholder_id ON fact_transactions(cardholder_id);
CREATE INDEX idx_ft_establishment_id ON fact_transactions(establishment_id);
CREATE INDEX idx_ft_product_id ON fact_transactions(product_id);
CREATE INDEX idx_ft_response_code ON fact_transactions(response_code);
CREATE INDEX idx_ft_created_at ON fact_transactions(created_at);
