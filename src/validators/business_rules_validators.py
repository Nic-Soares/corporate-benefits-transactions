def validate_mcc_modality(single_transaction, mcc_modalities_df, establishments_df, cards_df):
    """Valida se MCC aceita modalidade do cartão da transação"""
    # Pega MCC do estabelecimento
    est = establishments_df[
        establishments_df["establishment_id"] == single_transaction["establishment_id"]
    ]
    if est.empty:
        return {"passed": False, "error_code": "97"}

    mcc_code = est["mcc_code"].iloc[0]

    # Pega modalidade do cartão
    card = cards_df[cards_df["card_id"] == single_transaction["card_id"]]
    if card.empty:
        return {"passed": False, "error_code": "99"}

    modality_id = card["modality_id"].iloc[0]

    # Verifica se existe o mapeamento
    exists = mcc_modalities_df[
        (mcc_modalities_df["mcc_code"] == mcc_code)
        & (mcc_modalities_df["modality_id"] == modality_id)
        & (mcc_modalities_df["active"] == True)
    ]

    return {"passed": not exists.empty, "error_code": "59" if exists.empty else None}


# Exemplo de uso: alimentar estrutura com a transação atual
mcc_modalities_df = structure_mcc_modalities_from_transaction(
    single_transaction, mcc_df, transaction_modalities_df, establishments_df
)

# Validar a transação
result = validate_mcc_modality(single_transaction, mcc_modalities_df, establishments_df, cards_df)


def validate_mcc_modality_rules_active(
    single_transaction, mcc_modalities_df, establishments_df, cards_df
):
    """
    Valida se a regra MCC x Modalidade está ativa
    """
    # Pega MCC do estabelecimento
    est = establishments_df[
        establishments_df["establishment_id"] == single_transaction["establishment_id"]
    ]
    if est.empty:
        return {"passed": False, "error_code": "97"}

    mcc_code = est["mcc_code"].iloc[0]

    # Pega modalidade do cartão
    card = cards_df[cards_df["card_id"] == single_transaction["card_id"]]
    if card.empty:
        return {"passed": False, "error_code": "99"}

    modality_id = card["modality_id"].iloc[0]

    # Verifica se existe o mapeamento e se está ativo
    rule = mcc_modalities_df[
        (mcc_modalities_df["mcc_code"] == mcc_code)
        & (mcc_modalities_df["modality_id"] == modality_id)
    ]

    if rule.empty:
        return {"passed": False, "error_code": "59"}  # Regra não existe

    # Verifica se a regra está ativa
    if not rule["active"].iloc[0]:
        return {"passed": False, "error_code": "29"}  # Regra MCC desativada

    return {"passed": True, "error_code": None}


def validate_cnae_product_rules_active(single_transaction, cnae_products_df, establishments_df):
    """
    Valida se a regra CNAE x Produto está ativa
    """
    # Pega CNAE do estabelecimento
    est = establishments_df[
        establishments_df["establishment_id"] == single_transaction["establishment_id"]
    ]
    if est.empty:
        return {"passed": False, "error_code": "97"}

    cnae_code = est["main_cnae_id"].iloc[0]
    product_id = single_transaction["product_id"]

    # Verifica se existe o mapeamento
    rule = cnae_products_df[
        (cnae_products_df["cnae_code"] == cnae_code)
        & (cnae_products_df["product_id"] == product_id)
    ]

    if rule.empty:
        return {"passed": False, "error_code": "60"}  # Regra não existe

    # Verifica se a regra está ativa
    if not rule["active"].iloc[0]:
        return {"passed": False, "error_code": "30"}  # Regra CNAE desativada

    return {"passed": True, "error_code": None}


# Teste das novas validações
result_mcc_active = validate_mcc_modality_rules_active(
    single_transaction, mcc_modalities_df, establishments_df, cards_df
)
result_cnae_active = validate_cnae_product_rules_active(
    single_transaction, cnae_products_df, establishments_df
)

print(f"MCC x Modalidade ativa: {result_mcc_active}")
print(f"CNAE x Produto ativo: {result_cnae_active}")


def validate_mcc_modality(single_transaction, mcc_modalities_df, establishments_df, cards_df):
    """Valida se MCC aceita modalidade do cartão da transação"""
    # Pega MCC do estabelecimento
    est = establishments_df[
        establishments_df["establishment_id"] == single_transaction["establishment_id"]
    ]
    if est.empty:
        return {"passed": False, "error_code": "97"}

    mcc_code = est["mcc_code"].iloc[0]

    # Pega modalidade do cartão
    card = cards_df[cards_df["card_id"] == single_transaction["card_id"]]
    if card.empty:
        return {"passed": False, "error_code": "99"}

    modality_id = card["modality_id"].iloc[0]

    # Verifica se existe o mapeamento
    exists = mcc_modalities_df[
        (mcc_modalities_df["mcc_code"] == mcc_code)
        & (mcc_modalities_df["modality_id"] == modality_id)
        & (mcc_modalities_df["active"] == True)
    ]

    return {"passed": not exists.empty, "error_code": "59" if exists.empty else None}


# Exemplo de uso: alimentar estrutura com a transação atual
mcc_modalities_df = structure_mcc_modalities_from_transaction(
    single_transaction, mcc_df, transaction_modalities_df, establishments_df
)

# Validar a transação
result = validate_mcc_modality(single_transaction, mcc_modalities_df, establishments_df, cards_df)


def validate_cnae_product(single_transaction, cnae_products_df, establishments_df):
    """Valida se CNAE aceita o produto da transação"""
    # Pega CNAE do estabelecimento
    est = establishments_df[
        establishments_df["establishment_id"] == single_transaction["establishment_id"]
    ]
    if est.empty:
        return {"passed": False, "error_code": "97"}

    cnae_code = est["main_cnae_id"].iloc[0]
    product_id = single_transaction["product_id"]

    # Verifica se existe o mapeamento
    exists = cnae_products_df[
        (cnae_products_df["cnae_code"] == cnae_code)
        & (cnae_products_df["product_id"] == product_id)
        & (cnae_products_df["active"] == True)
    ]

    return {"passed": not exists.empty, "error_code": "60" if exists.empty else None}


# Exemplo de uso: alimentar estrutura com a transação atual
cnae_products_df = structure_cnae_products_from_transaction(
    single_transaction, cnaes_df, products_df, business_data, establishments_df
)

# Validar a transação
result_cnae = validate_cnae_product(single_transaction, cnae_products_df, establishments_df)


def validate_mcc_modality_rules_active(
    single_transaction, mcc_modalities_df, establishments_df, cards_df
):
    """
    Valida se a regra MCC x Modalidade está ativa
    """
    # Pega MCC do estabelecimento
    est = establishments_df[
        establishments_df["establishment_id"] == single_transaction["establishment_id"]
    ]
    if est.empty:
        return {"passed": False, "error_code": "97"}

    mcc_code = est["mcc_code"].iloc[0]

    # Pega modalidade do cartão
    card = cards_df[cards_df["card_id"] == single_transaction["card_id"]]
    if card.empty:
        return {"passed": False, "error_code": "99"}

    modality_id = card["modality_id"].iloc[0]

    # Verifica se existe o mapeamento e se está ativo
    rule = mcc_modalities_df[
        (mcc_modalities_df["mcc_code"] == mcc_code)
        & (mcc_modalities_df["modality_id"] == modality_id)
    ]

    if rule.empty:
        return {"passed": False, "error_code": "59"}  # Regra não existe

    # Verifica se a regra está ativa
    if not rule["active"].iloc[0]:
        return {"passed": False, "error_code": "29"}  # Regra MCC desativada

    return {"passed": True, "error_code": None}


def validate_cnae_product_rules_active(single_transaction, cnae_products_df, establishments_df):
    """
    Valida se a regra CNAE x Produto está ativa
    """
    # Pega CNAE do estabelecimento
    est = establishments_df[
        establishments_df["establishment_id"] == single_transaction["establishment_id"]
    ]
    if est.empty:
        return {"passed": False, "error_code": "97"}

    cnae_code = est["main_cnae_id"].iloc[0]
    product_id = single_transaction["product_id"]

    # Verifica se existe o mapeamento
    rule = cnae_products_df[
        (cnae_products_df["cnae_code"] == cnae_code)
        & (cnae_products_df["product_id"] == product_id)
    ]

    if rule.empty:
        return {"passed": False, "error_code": "60"}  # Regra não existe

    # Verifica se a regra está ativa
    if not rule["active"].iloc[0]:
        return {"passed": False, "error_code": "30"}  # Regra CNAE desativada

    return {"passed": True, "error_code": None}


# Teste das novas validações
result_mcc_active = validate_mcc_modality_rules_active(
    single_transaction, mcc_modalities_df, establishments_df, cards_df
)
result_cnae_active = validate_cnae_product_rules_active(
    single_transaction, cnae_products_df, establishments_df
)

print(f"MCC x Modalidade ativa: {result_mcc_active}")
print(f"CNAE x Produto ativo: {result_cnae_active}")


def validate_mcc_modality_rules_active(
    single_transaction, mcc_modalities_df, establishments_df, cards_df
):
    """
    Valida se a regra MCC x Modalidade está ativa
    """
    # Pega MCC do estabelecimento
    est = establishments_df[
        establishments_df["establishment_id"] == single_transaction["establishment_id"]
    ]
    if est.empty:
        return {"passed": False, "error_code": "97"}

    mcc_code = est["mcc_code"].iloc[0]

    # Pega modalidade do cartão
    card = cards_df[cards_df["card_id"] == single_transaction["card_id"]]
    if card.empty:
        return {"passed": False, "error_code": "99"}

    modality_id = card["modality_id"].iloc[0]

    # Verifica se existe o mapeamento e se está ativo
    rule = mcc_modalities_df[
        (mcc_modalities_df["mcc_code"] == mcc_code)
        & (mcc_modalities_df["modality_id"] == modality_id)
    ]

    if rule.empty:
        return {"passed": False, "error_code": "59"}  # Regra não existe

    # Verifica se a regra está ativa
    if not rule["active"].iloc[0]:
        return {"passed": False, "error_code": "29"}  # Regra MCC desativada

    return {"passed": True, "error_code": None}


def validate_cnae_product_rules_active(single_transaction, cnae_products_df, establishments_df):
    """
    Valida se a regra CNAE x Produto está ativa
    """
    # Pega CNAE do estabelecimento
    est = establishments_df[
        establishments_df["establishment_id"] == single_transaction["establishment_id"]
    ]
    if est.empty:
        return {"passed": False, "error_code": "97"}

    cnae_code = est["main_cnae_id"].iloc[0]
    product_id = single_transaction["product_id"]

    # Verifica se existe o mapeamento
    rule = cnae_products_df[
        (cnae_products_df["cnae_code"] == cnae_code)
        & (cnae_products_df["product_id"] == product_id)
    ]

    if rule.empty:
        return {"passed": False, "error_code": "60"}  # Regra não existe

    # Verifica se a regra está ativa
    if not rule["active"].iloc[0]:
        return {"passed": False, "error_code": "30"}  # Regra CNAE desativada

    return {"passed": True, "error_code": None}


# Teste das novas validações
result_mcc_active = validate_mcc_modality_rules_active(
    single_transaction, mcc_modalities_df, establishments_df, cards_df
)
result_cnae_active = validate_cnae_product_rules_active(
    single_transaction, cnae_products_df, establishments_df
)

print(f"MCC x Modalidade ativa: {result_mcc_active}")
print(f"CNAE x Produto ativo: {result_cnae_active}")
