# Data dictionary

Generated from `database/olap_duck/dictionary.yaml` by `python -m src.main export`.
Every record is synthetic.

## `fact_transactions`

Every attempt to pay, withdraw or reverse with a benefit card, and the issuer's answer. One row per attempt.

| Column | Type | Description |
|---|---|---|
| `id` | VARCHAR | Transaction id |
| `related_transaction_id` | VARCHAR | For a reversal, the purchase it undoes |
| `card_id` | VARCHAR | Card used (dim_cards) |
| `cardholder_id` | VARCHAR | Card's holder (dim_cardholders) |
| `company_id` | VARCHAR | Cardholder's employer (dim_companies) |
| `program_id` | VARCHAR | Card program (dim_card_programs) |
| `modality_id` | VARCHAR | Network the card runs on: OWN (issuer's proprietary network, 3-party) or VISA, MASTERCARD, ELO (4-party) |
| `card_wallet_id` | VARCHAR | Wallet of the card the issuer charged (dim_card_wallets); empty when none could be routed |
| `wallet_id` | VARCHAR | Type of that wallet: FOOD, MEAL, MOBILITY, HEALTH, HOME_OFFICE, EDUCATION, GIFT, PREMIUM |
| `transaction_type` | VARCHAR | purchase, withdrawal (cash, brand cards, GIFT wallet) or reversal |
| `wallet_option` | VARCHAR | Proprietary network: the option picked on the terminal (FOOD, MEAL, OTHERS); empty on brand cards |
| `establishment_id` | VARCHAR | Where (dim_establishments) |
| `terminal_id` | VARCHAR | Terminal that captured it (dim_terminals) |
| `acquirer_id` | VARCHAR | Terminal's acquirer (dim_acquirers) |
| `amount` | DECIMAL(15,2) | Amount in BRL |
| `date` | TIMESTAMP | Date and time of the attempt |
| `capture_type` | VARCHAR | How the card was read: CHIP, MAG_STRIPE, CONTACTLESS, MOBILE_NFC, APPLE_PAY, GOOGLE_PAY, ECOMMERCE |
| `pin_status` | VARCHAR | ok, wrong or not_required (contactless, wallets, online) |
| `response_code` | VARCHAR | ISO 8583 response code; 00 is approved (ref_response_codes) |
| `response_message` | VARCHAR | Description of the response code |
| `decline_reason` | VARCHAR | Specific cause of a decline (one ISO code covers several); empty when approved |
| `nsu` | VARCHAR | Sequence number the terminal gave the attempt |
| `authorization_code` | VARCHAR | Issuer's authorization code; empty when declined |
| `is_fraud` | BOOLEAN | Ground truth: made by someone other than the cardholder |
| `fraud_scenario` | VARCHAR | How the fraud happened: account_takeover_wallet, card_not_present, intercepted_card, point_of_compromise; empty when not fraud |
| `disputed` | BOOLEAN | The cardholder contested it; true for most approved fraud and for a few legit purchases contested by mistake |

## `fact_balance_movements`

Every change of a wallet's balance: the monthly credit, debits of approved purchases and withdrawals, reversals. One row per movement.

| Column | Type | Description |
|---|---|---|
| `id` | VARCHAR | Movement id |
| `card_wallet_id` | VARCHAR | Wallet of the card (dim_card_wallets) |
| `card_id` | VARCHAR | Card (dim_cards) |
| `wallet_id` | VARCHAR | Wallet type (dim_wallets) |
| `transaction_id` | VARCHAR | Transaction that moved it (fact_transactions); empty for the monthly credit |
| `operation_type` | VARCHAR | credit, purchase, withdrawal or reversal |
| `operation_amount` | DECIMAL(15,2) | Amount moved in BRL, always positive |
| `previous_balance` | DECIMAL(15,2) | Balance before the movement |
| `posterior_balance` | DECIMAL(15,2) | Balance after the movement |
| `operation_date` | TIMESTAMP | Date and time of the movement |

## `dim_card_wallets`

Each wallet a card holds, with its monthly credit and limits.

| Column | Type | Description |
|---|---|---|
| `id` | VARCHAR | Card wallet id |
| `card_id` | VARCHAR | Card (dim_cards) |
| `wallet_id` | VARCHAR | Wallet type (dim_wallets) |
| `monthly_credit` | DECIMAL(15,2) | Benefit credited on the 1st of each month, BRL |
| `daily_limit` | DECIMAL(15,2) | Most that can be spent per day, BRL; 0 = no limit |
| `monthly_limit` | DECIMAL(15,2) | Most that can be spent per month, BRL; 0 = no limit |
| `daily_count_limit` | INTEGER | Most approved purchases per day; 0 = no limit |
| `final_balance` | DECIMAL(15,2) | Balance at the end of the simulated period |
| `activation_date` | DATE | Date the wallet was activated |
| `status` | VARCHAR | active, suspended or cancelled |

## `dim_cards`

Benefit cards. The program fixes the wallets and the network.

| Column | Type | Description |
|---|---|---|
| `id` | VARCHAR | Card id |
| `cardholder_id` | VARCHAR | Holder (dim_cardholders) |
| `program_id` | VARCHAR | Program (dim_card_programs) |
| `modality_id` | VARCHAR | Network: OWN or a brand (dim_transaction_modalities) |
| `card_type` | VARCHAR | physical or virtual |
| `expiration_date` | DATE | Last day the card is valid |
| `issue_date` | DATE | Date issued |
| `status` | VARCHAR | active, inactive (not unlocked yet), blocked or cancelled |

## `dim_cardholders`

Employees who hold the cards. No names or documents.

| Column | Type | Description |
|---|---|---|
| `id` | VARCHAR | Cardholder id |
| `company_id` | VARCHAR | Employer (dim_companies) |
| `city` | VARCHAR | Municipality where they live (IBGE name) |
| `state` | VARCHAR | State (UF) |
| `position` | VARCHAR | Job position |
| `department` | VARCHAR | Department |
| `admission_date` | DATE | Date hired |
| `status` | VARCHAR | active, inactive or terminated |

## `dim_companies`

Employers that give the benefits. Holdings and their branches. No CNPJ.

| Column | Type | Description |
|---|---|---|
| `id` | VARCHAR | Company id |
| `parent_id` | VARCHAR | Holding of a branch; empty for a holding |
| `name` | VARCHAR | Legal name (synthetic) |
| `trade_name` | VARCHAR | Trade name (synthetic) |
| `segment` | VARCHAR | SME (1-250 employees), Middle (251-1,999), Corporate (2,000+) or Public (government) |
| `city` | VARCHAR | Municipality (IBGE name) |
| `state` | VARCHAR | State (UF) |
| `status` | VARCHAR | active, inactive or suspended |
| `registration_date` | DATE | Date registered |

## `dim_establishments`

Shops, online businesses and cash machines where cards are used. No CNPJ.

| Column | Type | Description |
|---|---|---|
| `id` | VARCHAR | Establishment id |
| `name` | VARCHAR | Legal name (synthetic) |
| `trade_name` | VARCHAR | Trade name (synthetic); says the kind of business |
| `main_cnae` | VARCHAR | Main economic activity, CNAE 2.3 subclass (7 digits); decides the proprietary network's acceptance |
| `mcc_code` | VARCHAR | Merchant Category Code; decides the brands' acceptance |
| `category` | VARCHAR | Kind of place: supermarket, food_retail, restaurant, fuel, health, home_office, education, retail, ride_hailing, digital_services, atm |
| `city` | VARCHAR | Municipality (IBGE name) |
| `state` | VARCHAR | State (UF) |
| `status` | VARCHAR | active, inactive, suspended or terminated |
| `accreditation_date` | DATE | Date accredited to accept the cards |

## `dim_terminals`

Terminals that capture the attempts.

| Column | Type | Description |
|---|---|---|
| `id` | VARCHAR | Terminal id |
| `establishment_id` | VARCHAR | Establishment (dim_establishments) |
| `acquirer_id` | VARCHAR | Acquirer (dim_acquirers) |
| `model` | VARCHAR | Terminal model |
| `type` | VARCHAR | POS, TEF, ECOMMERCE (online gateway) or ATM |
| `status` | VARCHAR | active, inactive or maintenance |
| `installation_date` | DATE | Date installed |

## `dim_wallets`

Wallet types: what each balance can be spent on.

| Column | Type | Description |
|---|---|---|
| `id` | VARCHAR | Wallet id |
| `name` | VARCHAR | Name in Portuguese |
| `category` | VARCHAR | Beneficio (benefit) or Incentivo (incentive) |
| `active` | BOOLEAN | Enabled |

## `dim_card_programs`

Card programs: the wallets a card holds and the network it runs on.

| Column | Type | Description |
|---|---|---|
| `id` | VARCHAR | Program id |
| `name` | VARCHAR | Name in Portuguese |
| `network_type` | VARCHAR | proprietary_network (3-party) or brand (4-party) |
| `active` | BOOLEAN | Enabled |

## `dim_transaction_modalities`

Networks: the issuer's proprietary network and the card brands.

| Column | Type | Description |
|---|---|---|
| `id` | VARCHAR | OWN, VISA, MASTERCARD or ELO |
| `name` | VARCHAR | Name |
| `type` | VARCHAR | proprietary_network or brand |
| `active` | BOOLEAN | Enabled |

## `dim_acquirers`

Acquirers that run the terminals, and the ATM network.

| Column | Type | Description |
|---|---|---|
| `id` | VARCHAR | Acquirer id |
| `name` | VARCHAR | Name |
| `active` | BOOLEAN | Enabled |

## `ref_response_codes`

ISO 8583 response codes used in the dataset.

| Column | Type | Description |
|---|---|---|
| `id` | VARCHAR | Code |
| `description` | VARCHAR | Meaning, in Portuguese |

## `ref_cnae_wallets`

Proprietary network: which wallets an establishment's CNAE accepts. The longest matching prefix of the CNAE decides. Synthetic rules.

| Column | Type | Description |
|---|---|---|
| `cnae_code` | VARCHAR | CNAE prefix (class, 4 digits, or subclass, 7 digits) |
| `wallet_id` | VARCHAR | Wallet accepted (dim_wallets) |
| `cnae_description` | VARCHAR | Description of the CNAE code (IBGE) |
| `active` | BOOLEAN | Rule in force |

## `ref_mcc_wallets`

Brand cards: which wallets the issuer can charge at each MCC. GIFT takes any MCC and has no rows. Synthetic rules.

| Column | Type | Description |
|---|---|---|
| `mcc_code` | VARCHAR | Merchant Category Code |
| `wallet_id` | VARCHAR | Wallet the issuer can charge (dim_wallets) |

## `ref_mcc_modalities`

Which brands accept each MCC. Synthetic rules, not the brands' official tables.

| Column | Type | Description |
|---|---|---|
| `mcc_code` | VARCHAR | Merchant Category Code |
| `modality_id` | VARCHAR | Brand that accepts it (dim_transaction_modalities) |
| `mcc_description` | VARCHAR | MCC description (public MCC list) |
| `active` | BOOLEAN | Rule in force |
