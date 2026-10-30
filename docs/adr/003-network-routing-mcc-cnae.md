# ADR-003 — Route authorization by network: MCC for brands, CNAE for the proprietary network

## Status
Accepted (2026-10-30; settled in roadmap `ST-04.2`)

## Context
Brazilian benefit cards run on two kinds of network. On a brand network
(Visa, Mastercard, Elo — the 4-party model: acquirer → brand → issuer) the
transaction carries the establishment's MCC. On the issuer's own network
(the 3-party model) the issuer knows the establishment's CNAE and checks it
against the product. The config described the proprietary network as
"`cards.modality_id IS NULL`" while also listing an `OWN` modality.

## Decision
- The proprietary network is the modality `OWN` (type `proprietary_network`);
  every card has a modality, never null.
- Brand cards are authorized by `mcc_modalities` (MCC × brand); `OWN` cards
  by `cnae_products` (CNAE prefix × product). Each validator passes the cards
  of the other network, so a caller runs both.
- The CNAE rule matches by the **longest** prefix in `cnae_products`, so a
  subclass entry (`5611201`) overrides its class (`5611`). Confirmed by the
  product owner.

## Consequences
- The CNAE mapping must list every product at each level it's declared on:
  a subclass entry replaces the class's list, it doesn't add to it.
- The establishment generator applies the same longest-prefix rule to pick a
  category, so data and validation agree.
