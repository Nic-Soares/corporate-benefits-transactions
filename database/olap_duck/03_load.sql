-- ============================================================================
-- OLAP LOAD - DuckDB
-- From the OLTP tables staged as stg_<table> (src/pipeline/etl.py) into the
-- star schema. Full refresh: the ETL builds a new database file each run.
-- ============================================================================

INSERT INTO dim_wallets BY NAME
SELECT id, name, category, active FROM stg_wallets;

INSERT INTO dim_card_programs BY NAME
SELECT id, name, network_type, active FROM stg_card_programs;

INSERT INTO dim_transaction_modalities BY NAME
SELECT id, name, type, active FROM stg_transaction_modalities;

INSERT INTO dim_acquirers BY NAME
SELECT id, name, active FROM stg_acquirers;

-- Public dataset: no CNPJ (a generated one can be a real company's), no
-- cardholder name, no CPF or card number hashes. The ids identify.
INSERT INTO dim_companies BY NAME
SELECT id, parent_id, name, trade_name, segment, city, state, status, registration_date
FROM stg_companies;

INSERT INTO dim_cardholders BY NAME
SELECT id, company_id, city, state, position, department, admission_date, status
FROM stg_cardholders;

INSERT INTO dim_cards BY NAME
SELECT id, cardholder_id, program_id, modality_id, card_type, expiration_date, issue_date, status
FROM stg_cards;

INSERT INTO dim_card_wallets BY NAME
SELECT id, card_id, wallet_id, monthly_credit, daily_limit, monthly_limit, daily_count_limit,
       current_balance AS final_balance, activation_date, status
FROM stg_card_wallets;

INSERT INTO dim_establishments BY NAME
SELECT id, name, trade_name, main_cnae, mcc_code, category, city, state, status,
       accreditation_date
FROM stg_establishments;

INSERT INTO ref_response_codes BY NAME
SELECT id, description FROM stg_response_codes;

INSERT INTO ref_cnae_wallets BY NAME
SELECT cnae_code, wallet_id, cnae_description, active FROM stg_cnae_wallets;

INSERT INTO ref_mcc_wallets BY NAME
SELECT mcc_code, wallet_id FROM stg_mcc_wallets;

INSERT INTO ref_mcc_modalities BY NAME
SELECT mcc_code, modality_id, mcc_description, active FROM stg_mcc_modalities;

INSERT INTO dim_terminals BY NAME
SELECT id, establishment_id, acquirer_id, model, type, status, installation_date
FROM stg_terminals;

-- Each transaction with the keys a user would otherwise join for
INSERT INTO fact_transactions BY NAME
SELECT
  t.id, t.related_transaction_id,
  t.card_id, c.cardholder_id, h.company_id, c.program_id, c.modality_id,
  t.card_wallet_id, cw.wallet_id,
  t.transaction_type, t.wallet_option,
  t.establishment_id, t.terminal_id, tm.acquirer_id,
  t.amount, t.date, t.capture_type, t.pin_status,
  t.response_code, rc.description AS response_message, t.decline_reason,
  t.nsu, t.authorization_code,
  t.is_fraud, t.fraud_scenario, t.disputed
FROM stg_transactions t
JOIN stg_cards c ON c.id = t.card_id
JOIN stg_cardholders h ON h.id = c.cardholder_id
JOIN stg_terminals tm ON tm.id = t.terminal_id
LEFT JOIN stg_card_wallets cw ON cw.id = t.card_wallet_id
LEFT JOIN stg_response_codes rc ON rc.id = t.response_code;

INSERT INTO fact_balance_movements BY NAME
SELECT b.id, b.card_wallet_id, cw.card_id, cw.wallet_id, b.transaction_id, b.operation_type,
       b.operation_amount, b.previous_balance, b.posterior_balance, b.operation_date
FROM stg_balance_history b
JOIN stg_card_wallets cw ON cw.id = b.card_wallet_id;
