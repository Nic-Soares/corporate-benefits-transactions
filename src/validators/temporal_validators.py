def validate_card_expiration(single_transaction, cards_df):
    """
    Valida se o cartão não está vencido
    """
    card_id = single_transaction['card_id']
    print(card_id)
    transaction_date = single_transaction['date']
    print(transaction_date)
    
    # Buscar cartão pelo ID
    card = cards_df[cards_df['card_id'] == card_id]
    print(card)
    
    if card.empty:
        return {'passed': False, 'error_code': '99'}  # Cartão não encontrado
    
    expiration_date = card['expiration_date'].iloc[0]
    
    # Verificar se cartão está vencido
    if transaction_date.date() > expiration_date:
        return {'passed': False, 'error_code': '54'}  # Cartão vencido
    
    return {'passed': True, 'error_code': None}

def cardholder_admission_validation(single_transaction, cards_df, cardholders_df):
    """
    Valida se a transação ocorreu após a admissão do portador
    """
    card_id = single_transaction['card_id']
    transaction_date = single_transaction['date']
    
    # Buscar cartão
    card = cards_df[cards_df['card_id'] == card_id]
    
    if card.empty:
        return {'passed': False, 'error_code': '99'}  # Cartão não encontrado
    
    cardholder_id = card['cardholder_id'].iloc[0]
    
    # Buscar portador
    cardholder = cardholders_df[cardholders_df['cardholder_id'] == cardholder_id]
    
    if cardholder.empty:
        return {'passed': False, 'error_code': '98'}  # Portador não encontrado
    
    admission_date = cardholder['admission_date'].iloc[0]
    
    # Verificar se transação é posterior à admissão
    if transaction_date.date() < admission_date:
        return {'passed': False, 'error_code': '56'}  # Transação antes da admissão
    
    return {'passed': True, 'error_code': None}

def establishment_accreditation_validation(single_transaction, establishments_df):
    """
    Valida se a transação ocorreu após o credenciamento do estabelecimento
    """
    establishment_id = single_transaction['establishment_id']
    transaction_date = single_transaction['date']
    
    # Buscar estabelecimento
    establishment = establishments_df[establishments_df['establishment_id'] == establishment_id]
    
    if establishment.empty:
        return {'passed': False, 'error_code': '97'}  # Estabelecimento não encontrado
    
    # Usar opening_date como accreditation_date (conforme estrutura atual)
    accreditation_date = establishment['opening_date'].iloc[0]
    
    # Verificar se transação é posterior ao credenciamento
    if transaction_date.date() < accreditation_date:
        return {'passed': False, 'error_code': '57'}  # Estabelecimento ainda não credenciado
    
    return {'passed': True, 'error_code': None}

def terminal_installation_validation(single_transaction, terminals_df):
    """
    Valida se a transação ocorreu após a instalação do terminal
    """
    terminal_id = single_transaction['terminal_id']
    transaction_date = single_transaction['date']
    
    # Buscar terminal
    terminal = terminals_df[terminals_df['terminal_id'] == terminal_id]
    
    if terminal.empty:
        return {'passed': False, 'error_code': '96'}  # Terminal não encontrado
    
    installation_date = terminal['installation_date'].iloc[0]
    
    # Verificar se transação é posterior à instalação
    if transaction_date.date() < installation_date:
        return {'passed': False, 'error_code': '58'}  # Terminal ainda não instalado
    
    return {'passed': True, 'error_code': None}
