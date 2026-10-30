# Business Rules

How a transaction is authorized. The rules live in `config/`; this page explains them. Codes are the response codes in `config/pre_populated_data.yaml → response_codes`.

## Products

| Code | Product | Category | Accepted at (CNAE) |
|---|---|---|---|
| `VA` | Vale Alimentação | Benefit | Supermarkets (`4711`), food retail (`4721`–`4729`) |
| `VR` | Vale Refeição | Benefit | Restaurants and bars (`5611`), street food (`5612`), catering and canteens (`5620`) |
| `VC` | Vale Combustível | Benefit | Fuel stations (`4731`) |
| `VF` | Vale Farmácia | Benefit | Pharmacies (`4771`) |
| `VM` | Multibenefícios | Benefit | Wherever VA, VR or VF is accepted |
| `PR` | Premiação | Incentive | Supermarkets, restaurants, pharmacies and general retail (`4751`–`4789`) |

Source: `config/pre_populated_data.yaml → products` and `cnae_products`.

## Networks

Every card has a modality (`config/pre_populated_data.yaml → transaction_modalities`):

| Modality | Type | Model | Authorized by |
|---|---|---|---|
| `OWN` | `proprietary_network` | 3-party: the issuer runs its own acceptance network | Establishment's **CNAE** × product |
| `VISA`, `MASTERCARD`, `ELO` | `brand` | 4-party: acquirer → brand → issuer | Establishment's **MCC** × brand |

### CNAE rule (proprietary network)

`cnae_products` lists CNAE prefixes at several levels — a 4-digit class (`5611`), a 5-digit class with check digit (`56112`), a 7-digit subclass (`5611201`). **The longest prefix of the establishment's CNAE decides.** Example: `5611` accepts VR, VM and PR, but `5611201` (restaurants) lists only VR and VM, so PR is declined at a `5611201` restaurant.

- No rule for the product → `28` (CNAE doesn't accept the product)
- Rule exists but inactive → `30`

### MCC rule (brands)

`validation_rules.yaml → mcc_acceptance_rules` lists, for each MCC, the brands that accept it (`E` Elo, `M` Mastercard, `V` Visa).

- No rule for the MCC × brand → `27`
- Rule exists but inactive → `29`

Each rule passes the cards of the other network, so both can run on every transaction.

## Validation order

`config/validation_rules.yaml → validation_order`. Every validator returns `{"passed", "error_code"}`.

1. **Status** — card, cardholder, establishment, terminal, card product must be active; product, modality and acquirer must be enabled. Codes `13`–`26`.
2. **Temporal** — card not expired (`54`); transaction after the cardholder's admission (`56`), the establishment's accreditation (`57`) and the terminal's installation (`58`).
3. **Business rules** — CNAE or MCC, above.
4. **Balance and limits** — enough balance (`51`), daily (`61`) and monthly (`62`) limits; a limit of 0 means no limit.
5. **Infrastructure** — the terminal type supports the capture technology (`32`): POS takes chip, stripe, contactless and wallets; TEF only chip and stripe.

A referenced record that doesn't exist declines with its own code (`92`–`99`); a status missing from a rule's list declines with `96`.

## Statuses

Valid statuses per entity are in `config/business_rules.yaml → status_options`; the generators draw them with the weights in `config/simulation_config.yaml → generation_settings`.

| Entity | Statuses |
|---|---|
| Card | `active`, `inactive`, `blocked`, `cancelled` |
| Card product | `active`, `suspended`, `cancelled` |
| Cardholder | `active`, `inactive`, `terminated` |
| Establishment | `active`, `inactive`, `suspended`, `terminated` |
| Terminal | `active`, `inactive`, `maintenance` |
