## VALIDAÇÕES DE STATUS E ATIVAÇÃO
# validation_order:
#   - "status_validations"
#   - "temporal_validations"
#   - "business_rules_validations"
#   - "balance_and_limits_validations"
#   - "infrastructure_validations"


def validate_card_status(single_transaction, cards_df):
    """
    Valida o status do cartão de uma transação

    Args:
        single_transaction: Linha da transação com 'card_id'
        cards_df: DataFrame dos cartões

    Returns:
        dict: {'passed': bool, 'error_code': str or None}
    """
    # Códigos de erro por status
    error_codes = validation_rules["status_validations"]["card_status"]["error_codes"]

    card_id = single_transaction["card_id"]

    # Buscar cartão
    card = cards_df[cards_df["card_id"] == card_id]

    if card.empty:
        return {"passed": False, "error_code": "99"}  # Cartão não encontrado

    status = card["status"].iloc[0]

    # Só passa se for 'active'
    if status == "active":
        return {"passed": True, "error_code": None}
    else:
        return {"passed": False, "error_code": error_codes.get(status, "99")}


def cardholder_status_validation(single_transaction, cards_df, cardholders_df):
    """
    Valida o status do portador do cartão de uma transação

    Args:
        single_transaction: Linha da transação com 'card_id'
        cards_df: DataFrame dos cartões
        cardholders_df: DataFrame dos portadores de cartão

    Returns:
        dict: {'passed': bool, 'error_code': str or None}
    """

    # Códigos de erro por status
    error_codes = {"inactive": "16", "terminated": "17"}

    card_id = single_transaction["card_id"]

    # Buscar cartão
    card = cards_df[cards_df["card_id"] == card_id]

    if card.empty:
        return {"passed": False, "error_code": "99"}  # Cartão não encontrado

    cardholder_id = card["cardholder_id"].iloc[0]

    # Buscar portador do cartão
    cardholder = cardholders_df[cardholders_df["cardholder_id"] == cardholder_id]

    if cardholder.empty:
        return {"passed": False, "error_code": "98"}  # Portador do cartão não encontrado

    status = cardholder["status"].iloc[0]

    # Só passa se for 'active'
    if status == "active":
        return {"passed": True, "error_code": None}
    else:
        return {"passed": False, "error_code": error_codes.get(status, "99")}


def validate_establishment_status(single_transaction, establishments_df):
    """
    Valida o status do estabelecimento de uma transação

    Args:
        single_transaction: Linha da transação com 'establishment_id'
        establishments_df: DataFrame dos estabelecimentos

    Returns:
        dict: {'passed': bool, 'error_code': str or None}
    """
    # Códigos de erro por status
    error_codes = {"INATIVA": "18", "SUSPENSA": "19", "BAIXADA": "20"}

    establishment_id = single_transaction["establishment_id"]

    # Buscar estabelecimento
    establishment = establishments_df[establishments_df["establishment_id"] == establishment_id]

    if establishment.empty:
        return {"passed": False, "error_code": "97"}  # Estabelecimento não encontrado

    status = establishment["registration_status"].iloc[0]

    # Só passa se for 'ATIVA'
    if status == "ATIVA":
        return {"passed": True, "error_code": None}
    else:
        return {"passed": False, "error_code": error_codes.get(status, "99")}


def validate_terminal_status(single_transaction, terminals_df):
    """
    Valida o status do terminal
    """
    # Forma correta de acessar os códigos de erro do terminal
    terminal_error_codes = validation_rules["status_validations"]["terminal_status"]["error_codes"]

    terminal_id = single_transaction["terminal_id"]

    # Buscar terminal (corrigido o filtro)
    terminal = terminals_df[terminals_df["terminal_id"] == terminal_id]

    if terminal.empty:
        return {"passed": False, "error_code": "96"}  # Terminal não encontrado

    status = terminal["status"].iloc[0]

    # Só passa se for 'active'
    if status == "active":
        return {"passed": True, "error_code": None}
    else:
        return {"passed": False, "error_code": terminal_error_codes.get(status, "99")}


def validate_card_product(single_transaction, card_products_df):
    """
    Valida se o produto do cartão está ativo

    Args:
        single_transaction: Linha da transação com 'card_id', 'product_id' e 'amount'
        card_products_df: DataFrame dos produtos do cartão

    Returns:
        dict: {'passed': bool, 'error_code': str or None}
    """
    # Códigos de erro
    error_codes = {
        "inactive": "23",
    }

    card_id = single_transaction["card_id"]
    product_id = single_transaction["product_id"]

    # Buscar produto do cartão
    card_product = card_products_df[
        (card_products_df["card_id"] == card_id) & (card_products_df["product_id"] == product_id)
    ]

    if card_product.empty:
        return {"passed": False, "error_code": "99"}  # Produto do cartão não encontrado

    status = card_product["status"].iloc[0]

    if status != "active":
        return {"passed": False, "error_code": error_codes["inactive"]}

    return {"passed": True, "error_code": None}


def validate_product_active():
    """
    Valida se o produto como regra de negócio está ativo

    Returns:
        dict: {'passed': bool, 'error_code': str or None}
    """

    # Códigos de erro
    error_codes = {
        "inactive": "24",
    }

    # Para simulação, vamos assumir que todos os produtos estão ativos
    product_id = single_transaction["product_id"]

    product = products_df[products_df["product_id"] == product_id]

    if product.empty or product["status"].iloc[0] != "active":
        return {"passed": False, "error_code": error_codes["inactive"]}

    return {"passed": True, "error_code": None}


def validate_modality_active(single_transaction, transaction_modalities_df, cards_df):
    """
    Valida se a modalidade do cartão está ativa

    Args:
        single_transaction: Linha da transação com 'card_id'
        transaction_modalities_df: DataFrame das modalidades de transação
        cards_df: DataFrame dos cartões

    Returns:
        dict: {'passed': bool, 'error_code': str or None}
    """
    # Códigos de erro
    error_codes = {
        "inactive": "25",
    }

    card_id = single_transaction["card_id"]

    # Buscar cartão
    card = cards_df[cards_df["card_id"] == card_id]

    if card.empty:
        return {"passed": False, "error_code": "99"}  # Cartão não encontrado

    modality_id = card["modality_id"].iloc[0]

    # Buscar modalidade
    modality = transaction_modalities_df[transaction_modalities_df["modality_id"] == modality_id]

    if modality.empty:
        return {"passed": False, "error_code": "98"}  # Modalidade não encontrada

    # Para simulação, vamos assumir que todas as modalidades estão ativas
    return {"passed": True, "error_code": None}


def validate_acquirer_active(single_transaction, terminals_df, acquirers_df):
    """
    Valida se a adquirente do terminal está ativa

    Args:
        single_transaction: Linha da transação com 'terminal_id'
        terminals_df: DataFrame dos terminais
        acquirers_df: DataFrame das adquirentes

    Returns:
        dict: {'passed': bool, 'error_code': str or None}
    """
    # Códigos de erro
    error_codes = {
        "inactive": "26",
    }

    terminal_id = single_transaction["terminal_id"]

    # Buscar terminal
    terminal = terminals_df[terminals_df["terminal_id"] == terminal_id]

    if terminal.empty:
        return {"passed": False, "error_code": "97"}  # Terminal não encontrado

    acquirer_id = terminal["acquirer_id"].iloc[0]

    # Buscar adquirente
    acquirer = acquirers_df[acquirers_df["acquirer_id"] == acquirer_id]

    if acquirer.empty:
        return {"passed": False, "error_code": "96"}  # Adquirente não encontrada

    # Para simulação, vamos assumir que todas as adquirentes estão ativas
    return {"passed": True, "error_code": None}
