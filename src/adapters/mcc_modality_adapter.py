def structure_mcc_modalities_from_transaction(single_transaction, mcc_df, transaction_modalities_df, establishments_df, existing_mcc_modalities_df=None):
    """
    Alimenta a estrutura MCC x Modalidades baseado numa única transação
    Adiciona apenas o MCC do estabelecimento da transação
    """
    if existing_mcc_modalities_df is None:
        mcc_modalities = []
    else:
        mcc_modalities = existing_mcc_modalities_df.to_dict('records')
    
    # Pega o MCC do estabelecimento da transação
    establishment_id = single_transaction['establishment_id']
    establishment = establishments_df[establishments_df['establishment_id'] == establishment_id]
    
    if establishment.empty:
        return pd.DataFrame(mcc_modalities) if mcc_modalities else pd.DataFrame()
    
    mcc_code = establishment['mcc_code'].iloc[0]
    
    # Verifica se já existe esse MCC na estrutura
    if existing_mcc_modalities_df is not None:
        existing_mcc = existing_mcc_modalities_df[existing_mcc_modalities_df['mcc_code'] == mcc_code]
        if not existing_mcc.empty:
            return existing_mcc_modalities_df  # Já existe, retorna sem mudanças
    
    # Busca informações do MCC
    mcc_info = mcc_df[mcc_df['mcc_code'] == mcc_code]
    if mcc_info.empty:
        return pd.DataFrame(mcc_modalities) if mcc_modalities else pd.DataFrame()
    
    mcc_row = mcc_info.iloc[0]
    mcc_description = mcc_row['mcc_description']
    brands = mcc_row['valid_payment_brands']
    
    # Processa as modalidades válidas para este MCC
    if pd.notna(brands):
        for brand in brands.upper():
            modality_map = {'V': 'VISA', 'M': 'MASTERCARD', 'E': 'ELO'}
            if brand in modality_map:
                modality = transaction_modalities_df[
                    transaction_modalities_df['code'] == modality_map[brand]
                ]
                if not modality.empty:
                    mcc_modalities.append({
                        'mcc_code': mcc_code,
                        'modality_id': modality['modality_id'].iloc[0],
                        'mcc_description': mcc_description,
                        'observation': None,  # Por enquanto vazio
                        'active': True,
                        'created_at': pd.Timestamp.now()
                    })
    
    return pd.DataFrame(mcc_modalities)