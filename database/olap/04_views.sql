-- ============================================================================
-- ANALYTICAL VIEWS - DuckDB
-- Starting points for the questions the dataset is built for.
-- ============================================================================

-- Approval per program and network
CREATE OR REPLACE VIEW v_approval_by_program AS
SELECT f.program_id, p.name AS program, f.modality_id AS network,
       count(*) AS attempts,
       round(avg((f.response_code = '00')::INT), 4) AS approval_rate
FROM fact_transactions f
JOIN dim_card_programs p ON p.id = f.program_id
WHERE f.transaction_type <> 'reversal'
GROUP BY ALL
ORDER BY attempts DESC;

-- Declines by ISO code and specific reason
CREATE OR REPLACE VIEW v_declines AS
SELECT response_code, response_message, decline_reason,
       count(*) AS declines,
       round(count(*) / sum(count(*)) OVER (), 4) AS share
FROM fact_transactions
WHERE response_code <> '00'
GROUP BY ALL
ORDER BY declines DESC;

-- Ticket per kind of place, approved attempts
CREATE OR REPLACE VIEW v_ticket_by_category AS
SELECT e.category, f.transaction_type,
       count(*) AS approved,
       round(avg(f.amount), 2) AS average_ticket,
       round(median(f.amount), 2) AS median_ticket
FROM fact_transactions f
JOIN dim_establishments e ON e.id = f.establishment_id
WHERE f.response_code = '00' AND f.transaction_type <> 'reversal'
GROUP BY ALL
ORDER BY approved DESC;

-- Fraud per scenario: attempts, how many passed, how many were contested
CREATE OR REPLACE VIEW v_fraud_by_scenario AS
SELECT fraud_scenario,
       count(*) AS attempts,
       sum((response_code = '00')::INT) AS approved,
       sum(disputed::INT) AS disputed,
       round(sum(CASE WHEN response_code = '00' THEN amount ELSE 0 END), 2) AS approved_amount
FROM fact_transactions
WHERE is_fraud
GROUP BY ALL
ORDER BY attempts DESC;

-- Day by day: attempts, approvals, amount
CREATE OR REPLACE VIEW v_daily AS
SELECT date::DATE AS day,
       count(*) AS attempts,
       sum((response_code = '00')::INT) AS approved,
       round(sum(CASE WHEN response_code = '00' THEN amount ELSE 0 END), 2) AS approved_amount
FROM fact_transactions
GROUP BY ALL
ORDER BY day;

-- Money in and out of each wallet type per month
CREATE OR REPLACE VIEW v_wallet_flows_by_month AS
SELECT date_trunc('month', operation_date)::DATE AS month, wallet_id,
       round(sum(CASE WHEN operation_type = 'credit' THEN operation_amount ELSE 0 END), 2) AS credited,
       round(sum(CASE WHEN operation_type IN ('purchase', 'withdrawal')
                      THEN operation_amount ELSE 0 END), 2) AS spent,
       round(sum(CASE WHEN operation_type = 'reversal' THEN operation_amount ELSE 0 END), 2) AS reversed
FROM fact_balance_movements
GROUP BY ALL
ORDER BY month, wallet_id;
