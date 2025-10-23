# Business Rules

## Product Authorization Rules

### Vale Alimentação (VA)
- **Allowed**: Supermarkets, groceries, food stores
- **CNAE codes**: 4711, 4721, 4722, 4729
- **Restriction**: No ready-to-eat meals

### Vale Refeição (VR)
- **Allowed**: Restaurants, cafeterias, food trucks
- **CNAE codes**: 5611, 5612, 5620
- **Restriction**: No grocery shopping

### Vale Combustível (VC)
- **Allowed**: Gas stations only
- **CNAE codes**: 4731, 47318
- **Restriction**: Fuel and related services

### Cartão GF (Gift Card)
- **Allowed**: Various establishments
- **Usage**: Gifts, bonuses, incentives
- **Flexibility**: Multiple categories

## Authorization Logic

### Branded Networks (Visa, Master, Elo)
- Authorization based on **MCC codes**
- Cross-reference with `mcc_modalities` table

### Proprietary Network
- Authorization based on **CNAE codes**
- Cross-reference with `cnae_products` table

## Response Codes
- `00`: Approved
- `51`: Insufficient funds
- `14`: Invalid card
- `96`: System error
