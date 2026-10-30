# Business Rules

How a transaction is authorized. The rules live in `config/`; this page explains them. Response codes follow ISO 8583 (`config/pre_populated_data.yaml → response_codes`); every decline also records a specific `decline_reason`.

## Programs and wallets

A card belongs to a **program**. The program fixes which **wallets** (*carteiras*) the card holds and which **network** it runs on. Each wallet has its own balance and limits.

| Program | Name | Network | Wallets |
|---|---|---|---|
| `FOOD` | Alimentação | Proprietary (3-party) | FOOD |
| `MEAL` | Refeição | Proprietary (3-party) | MEAL |
| `MULTI_3P` | Multibenefícios (rede própria) | Proprietary (3-party) | FOOD, MEAL, MOBILITY, HEALTH, HOME_OFFICE, EDUCATION, GIFT |
| `MULTI_4P` | Multibenefícios (bandeirado) | Brand (4-party): Visa, Mastercard or Elo | FOOD, MEAL, MOBILITY, HEALTH, HOME_OFFICE, EDUCATION, GIFT |
| `GIFT` | Presente | Proprietary (3-party) | GIFT |
| `PREMIUM` | Premiação | Proprietary (3-party) | PREMIUM |
| `FUEL` | Combustível | Proprietary (3-party) | MOBILITY |

```mermaid
flowchart LR
    CARD["Card"] -->|belongs to| PROGRAM["Program<br/>MULTI_3P, MULTI_4P, FOOD…"]
    PROGRAM -->|fixes| NETWORK{"Network"}
    PROGRAM -->|fixes| WALLETS["Wallets<br/>FOOD, MEAL, MOBILITY,<br/>HEALTH, HOME_OFFICE,<br/>EDUCATION, GIFT, PREMIUM"]
    NETWORK -->|3-party| OWN["OWN<br/>issuer's own network"]
    NETWORK -->|4-party| BRAND["Visa / Mastercard / Elo"]
    CARD -->|holds one balance per| WALLETS
```

Source: `config/pre_populated_data.yaml → wallets`, `card_programs`.

## The two networks

| | Proprietary network (`OWN`, 3-party) | Brand network (Visa, Mastercard, Elo — 4-party) |
|---|---|---|
| Chain | Terminal → issuer | Terminal → acquirer → brand → issuer |
| Who picks the wallet | The cardholder, on the terminal | The issuer, from the establishment's **MCC** |
| What authorizes the place | The establishment's **CNAE** accepts that wallet | The brand accepts the MCC |
| Rule data | `cnae_wallets` | `mcc_modalities` (MCC × brand) + `mcc_wallets` (MCC × wallet) |

### CNAE rule (proprietary network)

`cnae_wallets` lists CNAE prefixes at several levels. **The longest prefix of the establishment's CNAE decides**, so a subclass entry replaces its class's list. Example: `5611` (restaurants and bars) accepts MEAL and GIFT, but `5611201` (restaurants) lists only MEAL, so GIFT is declined at a `5611201` restaurant.

- The chosen wallet isn't accepted → `57`, `wallet_not_accepted_at_cnae`
- Rule exists but inactive → `57`, `cnae_rule_inactive`

### MCC rules (brand network)

1. The brand must accept the MCC (`validation_rules.yaml → mcc_acceptance_rules`, `E` Elo, `M` Mastercard, `V` Visa). Otherwise `57`, `mcc_not_accepted_by_brand`.
2. The issuer **routes the wallet**: it walks `wallet_priority` (MEAL → FOOD → MOBILITY → HEALTH → HOME_OFFICE → EDUCATION → GIFT) and takes the first wallet that the card holds, is active, accepts the MCC (`mcc_wallets`; GIFT accepts any MCC) and has enough balance.
   - No wallet accepts the MCC → `57`, `no_wallet_for_mcc`
   - Some do, none with enough balance → `51`, `insufficient_balance`

Example: a Visa multi-benefit card at a restaurant (MCC `5812`) with MEAL 20.00 and GIFT 1,000.00 buys 50.00 → MEAL can't pay, FOOD doesn't take `5812`, GIFT pays.

## Authorization

`config/validation_rules.yaml → validation_order`; the first failure declines.

```mermaid
flowchart TD
    TX["Purchase attempt<br/>card, terminal, amount, capture, PIN"] --> S["1. Status<br/>card, cardholder, establishment,<br/>terminal, wallet, modality, acquirer"]
    S --> T["2. Temporal<br/>expiry, admission,<br/>accreditation, installation"]
    T --> P["3. Security<br/>PIN"]
    P --> NET{"Network?"}
    NET -->|OWN| CNAE["4. CNAE × chosen wallet"]
    NET -->|brand| MCC["4. Brand × MCC,<br/>then route the wallet by MCC"]
    CNAE --> B["5. Balance and limits<br/>on that wallet"]
    MCC --> B
    B --> I["6. Infrastructure<br/>capture × terminal type"]
    I --> OK(["00 approved<br/>wallet debited"])
    S -. fail .-> NO(["Declined<br/>ISO code + decline_reason"])
    T -. fail .-> NO
    P -. fail .-> NO
    CNAE -. fail .-> NO
    MCC -. fail .-> NO
    B -. fail .-> NO
    I -. fail .-> NO
```

| Group | Check | ISO code | `decline_reason` |
|---|---|---|---|
| Status | Card inactive / blocked / cancelled | `78` / `62` / `46` | `card_inactive`, `card_blocked`, `card_cancelled` |
| | Cardholder inactive or terminated | `62` | `cardholder_inactive`, `cardholder_terminated` |
| | Establishment not active | `03` | `establishment_<status>` |
| | Terminal inactive or in maintenance | `58` | `terminal_<status>` |
| | Wallet on the card suspended or cancelled | `57` | `card_wallet_<status>` |
| | Wallet, modality disabled / acquirer disabled | `57` / `58` | `wallet_disabled`, `modality_disabled` / `acquirer_disabled` |
| Temporal | Card expired | `54` | `card_expired` |
| | Before the cardholder's admission | `62` | `before_admission` |
| | Before accreditation / installation | `03` / `58` | `before_accreditation` / `before_installation` |
| Security | Wrong PIN (chip and stripe ask for it) | `55` | `wrong_pin` |
| Business rules | See the networks above | `57`, `51` | |
| Balance and limits | Balance below the amount | `51` | `insufficient_balance` |
| | Daily / monthly limit (0 = no limit) | `61` | `daily_limit_exceeded`, `monthly_limit_exceeded` |
| Infrastructure | TEF terminals take only chip and stripe | `58` | `capture_not_supported` |

A referenced record that doesn't exist declines with the ISO code for that party (`14` card or cardholder, `57` wallet not on the card, `15` modality, `03` establishment, `58` terminal, `92` acquirer) and `<entity>_not_found`. A status missing from a rule's list declines with `96`.

## Balance

Each wallet starts the simulation with a balance (`simulation_config.yaml → generation_settings.wallet_starting_balance`). An approved purchase debits the charged wallet and writes a `balance_history` row (`src/processors/balance.py`), so a later purchase on the same wallet can be declined with `51`. Where the balance comes from (employer credit orders) is out of scope.

## Statuses

Valid statuses per entity are in `config/business_rules.yaml → status_options`; the generators draw them with the weights in `config/simulation_config.yaml → generation_settings`.

| Entity | Statuses |
|---|---|
| Card | `active`, `inactive`, `blocked`, `cancelled` |
| Card wallet | `active`, `suspended`, `cancelled` |
| Cardholder | `active`, `inactive`, `terminated` |
| Establishment | `active`, `inactive`, `suspended`, `terminated` |
| Terminal | `active`, `inactive`, `maintenance` |

## Out of scope

Fees and establishment payments (MDR, reimbursement, settlement), the employer side (credit orders, credit expiry) and wallet-to-wallet transfers.
