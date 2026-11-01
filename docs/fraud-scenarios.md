# Fraud scenarios

The dataset labels every transaction with the ground truth (`is_fraud`), how
the fraud happened (`fraud_scenario`) and whether the cardholder contested it
(`disputed`). The scenarios follow common typologies of the Brazilian
benefits-card market; every number is synthetic (`config/simulation_config.yaml
→ fraud`). Generator: `src/data_generators/entities/fraud_generator.py`.

Fraud attempts go through the same issuer as the legit ones, so some are
declined — a wrong PIN, an empty wallet, a shop the wallet isn't accepted at.
Fraudsters don't give up after a balance decline, as cardholders mostly do,
and target shops where the card's wallets work.

| Scenario | What happens | Signature in the data |
|---|---|---|
| `account_takeover_wallet` | The cardholder's app account is taken over and the card added to a mobile wallet | A burst of 3–8 Apple Pay / Google Pay / NFC payments within hours, in shops of another state, larger tickets than usual |
| `card_not_present` | A brand card's number is used online | 4–12 e-commerce purchases over hours or days, draining the open (GIFT) wallet until `51` |
| `intercepted_card` | A new card is used before the cardholder gets it | Days after the issue date, in another state: contactless purchases, chip attempts with a wrong PIN (`55`) |
| `point_of_compromise` | Cards are skimmed at one shop and the cloned stripe is used later | Several cards with a legit visit to the same terminal (a fuel station or supermarket); 3–15 days later, magnetic-stripe purchases with the PIN in another state |

## Disputes

- Most approved fraud is contested, card by card (`fraud.report_ratio`):
  `disputed` and `is_fraud`.
- Some legit purchases made with card and PIN are contested too, by mistake
  or bad faith (`friendly_disputes_per_fraud_dispute`): `disputed` without
  `is_fraud`. A model trained on disputes alone learns this noise.
- Declined attempts are never contested; fraud is never reversed by the
  merchant.

## Volume

About `fraud.share_of_attempts` (0.5%) of the attempts belong to fraud
incidents, split by the scenario weights. That is above the market's rate on
purpose: enough positives to study.
