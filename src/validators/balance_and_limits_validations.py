## balance_and_limits_validations
def validate_current_balance(single_transaction, card_products_df):
    """
    Valida se há saldo suficiente no produto
    """
    card_id = single_transaction['card_id']
    product_id = single_transaction['product_id']
    amount = single_transaction['amount']
    
    # Buscar produto do cartão
    card_product = card_products_df[
        (card_products_df['card_id'] == card_id) & 
        (card_products_df['product_id'] == product_id)
    ]
    
    if card_product.empty:
        return {'passed': False, 'error_code': '99'}  # Produto do cartão não encontrado
    
    current_balance = card_product['current_balance'].iloc[0]
    
    # Verificar se há saldo suficiente
    if current_balance < amount:
        return {'passed': False, 'error_code': '51'}  # Saldo insuficiente
    
    return {'passed': True, 'error_code': None}

## daily_limit
def validate_daily_limit(single_transaction, card_products_df, daily_usage=0):
    """
    Valida se o limite diário não foi ultrapassado
    
    Args:
        single_transaction: Transação atual
        card_products_df: DataFrame dos produtos do cartão
        daily_usage: Uso diário atual (simulado como 0 por padrão)
    """
    card_id = single_transaction['card_id']
    product_id = single_transaction['product_id']
    amount = single_transaction['amount']
    
    # Buscar produto do cartão
    card_product = card_products_df[
        (card_products_df['card_id'] == card_id) & 
        (card_products_df['product_id'] == product_id)
    ]
    
    if card_product.empty:
        return {'passed': False, 'error_code': '99'}  # Produto do cartão não encontrado
    
    daily_limit = card_product['daily_limit'].iloc[0]
    
    # Se limite = 0, não há restrição
    if daily_limit <= 0:
        return {'passed': True, 'error_code': None}
    
    # Verificar se limite diário seria ultrapassado
    if (daily_usage + amount) > daily_limit:
        return {'passed': False, 'error_code': '61'}  # Limite diário excedido
    
    return {'passed': True, 'error_code': None}

### monthly_limit
def validate_monthly_limit(single_transaction, card_products_df, monthly_usage=0):
    """
    Valida se o limite mensal não foi ultrapassado
    
    Args:
        single_transaction: Transação atual
        card_products_df: DataFrame dos produtos do cartão
        monthly_usage: Uso mensal atual (simulado como 0 por padrão)
    """
    card_id = single_transaction['card_id']
    product_id = single_transaction['product_id']
    amount = single_transaction['amount']
    
    # Buscar produto do cartão
    card_product = card_products_df[
        (card_products_df['card_id'] == card_id) & 
        (card_products_df['product_id'] == product_id)
    ]
    
    if card_product.empty:
        return {'passed': False, 'error_code': '99'}  # Produto do cartão não encontrado
    
    monthly_limit = card_product['monthly_limit'].iloc[0]
    
    # Se limite = 0, não há restrição
    if monthly_limit <= 0:
        return {'passed': True, 'error_code': None}
    
    # Verificar se limite mensal seria ultrapassado
    if (monthly_usage + amount) > monthly_limit:
        return {'passed': False, 'error_code': '62'}  # Limite mensal excedido
    
    return {'passed': True, 'error_code': None}


# Teste das validações de saldo e limites
result_balance = validate_current_balance(single_transaction, card_products_df)
result_daily = validate_daily_limit(single_transaction, card_products_df, daily_usage=100)
result_monthly = validate_monthly_limit(single_transaction, card_products_df, monthly_usage=1000)

print(f"Saldo suficiente: {result_balance}")
print(f"Limite diário: {result_daily}")
print(f"Limite mensal: {result_monthly}")