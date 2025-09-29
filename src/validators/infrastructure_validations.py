## terminal acquirer match

def validate_terminal_acquirer_match(single_transaction, terminals_df, cards_df, transaction_modalities_df):
    """
    Valida se o terminal pertence ao adquirente compatível com a modalidade do cartão
    """
    terminal_id = single_transaction['terminal_id']
    card_id = single_transaction['card_id']
    
    # Buscar terminal
    terminal = terminals_df[terminals_df['terminal_id'] == terminal_id]
    if terminal.empty:
        return {'passed': False, 'error_code': '96'}  # Terminal não encontrado
    
    terminal_acquirer_id = terminal['acquirer_id'].iloc[0]
    
    # Buscar cartão para pegar modalidade
    card = cards_df[cards_df['card_id'] == card_id]
    if card.empty:
        return {'passed': False, 'error_code': '99'}  # Cartão não encontrado
    
    modality_id = card['modality_id'].iloc[0]
    
    # Buscar modalidade para verificar se é compatível
    modality = transaction_modalities_df[transaction_modalities_df['modality_id'] == modality_id]
    if modality.empty:
        return {'passed': False, 'error_code': '98'}  # Modalidade não encontrada
    
    # Para simplificação, vamos assumir que todos os terminais são compatíveis
    # Em um cenário real, teria uma tabela de compatibilidade terminal x modalidade
    return {'passed': True, 'error_code': None}

### capture_type_support
def validate_capture_type_support(single_transaction, terminals_df, transaction_modalities_df, cards_df):
    """
    Valida se o tipo de captura é suportado pelo terminal e modalidade
    """
    terminal_id = single_transaction['terminal_id']
    capture_type = single_transaction['capture_type']
    card_id = single_transaction['card_id']
    
    # Buscar terminal
    terminal = terminals_df[terminals_df['terminal_id'] == terminal_id]
    if terminal.empty:
        return {'passed': False, 'error_code': '96'}  # Terminal não encontrado
    
    terminal_type = terminal['terminal_type'].iloc[0]
    
    # Buscar cartão para pegar modalidade
    card = cards_df[cards_df['card_id'] == card_id]
    if card.empty:
        return {'passed': False, 'error_code': '99'}  # Cartão não encontrado
    
    modality_id = card['modality_id'].iloc[0]
    
    # Buscar modalidade
    modality = transaction_modalities_df[transaction_modalities_df['modality_id'] == modality_id]
    if modality.empty:
        return {'passed': False, 'error_code': '98'}  # Modalidade não encontrada
    
    # Regras de compatibilidade simplificadas
    # POS suporta: chip, magnetic_stripe, contactless
    # TEF suporta: chip, magnetic_stripe
    # Modalidades digitais (NFC, Apple Pay, etc.) só funcionam com POS
    
    if terminal_type == 'POS':
        supported_captures = ['chip', 'magnetic_stripe', 'contactless', 'nfc']
    elif terminal_type == 'TEF':
        supported_captures = ['chip', 'magnetic_stripe']
    else:
        supported_captures = ['chip', 'magnetic_stripe']  # Default
    
    if capture_type not in supported_captures:
        return {'passed': False, 'error_code': '32'}  # Tipo de captura não suportado
    
    return {'passed': True, 'error_code': None}


# Teste das validações de infraestrutura
result_terminal_acquirer = validate_terminal_acquirer_match(single_transaction, terminals_df, cards_df, transaction_modalities_df)
result_capture_support = validate_capture_type_support(single_transaction, terminals_df, transaction_modalities_df, cards_df)

print(f"Terminal/Adquirente compatível: {result_terminal_acquirer}")
print(f"Tipo de captura suportado: {result_capture_support}")
print(f"Transação usando capture_type: {single_transaction['capture_type']}")