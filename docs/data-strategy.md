# Data Strategy

## Pre-populated Tables
```sql
products                    -- 4 fixed products (VA, VR, VC, GF)
transaction_modalities      -- 4 modalities (Visa, Master, Elo, Proprietary)
acquirers                   -- 6 acquirers (Cielo, Rede, Stone, etc)
mcc_modalities              -- MCC x Modalities mapping (~500 records)
cnae_products               -- CNAE x Products mapping (~200 records)
```

## On-demand Tables
```sql
companies                   -- Created when employees need cards
cardholders                 -- Created when employees join companies
cards                       -- Issued on-demand for cardholders
card_products               -- Products activated as needed
establishments              -- Registered when accepting cards
terminals                   -- Installed when establishments need them
```

## Transactional Tables
```sql
transactions                -- Each purchase attempt
authorizations              -- Response for each transaction
balance_history             -- Balance updates (when approved)
```

## Implementation Flow

### Setup (once)
1. Load reference data from `config/business_rules.yaml`
2. Generate MCC mappings from `data/raw/mcc.csv`
3. Generate CNAE mappings from business rules

### Transaction Generation (continuous)
1. `get_or_create_company()`
2. `get_or_create_cardholder(company)`
3. `get_or_create_card(cardholder)`
4. `get_or_create_establishment()`
5. `get_or_create_terminal(establishment)`
6. `create_transaction()`
7. `create_authorization(transaction)`
8. `update_balance_history()` (if approved)
