-- Views for Corporate Products Transactions System
-- This file contains useful views for reporting and analysis

-- View: Complete transaction details with all related dimensions
CREATE VIEW vw_transaction_details AS
SELECT 
    ft.transaction_id,
    ft.related_transaction_id,
    ft.nsu_transacao,
    ft.nsu_autorizacao,
    
    -- Date and time information
    dd.data_completa as data_transacao,
    ft.hora_transacao,
    ft.data_efetiva_transacao,
    ft.data_captura,
    dd.ano,
    dd.mes,
    dd.trimestre,
    dd.nome_dia_semana,
    dd.is_feriado,
    dd.is_fim_semana,
    
    -- Financial information
    ft.valor_transacao,
    ft.valor_comissao,
    ft.codigo_moeda,
    
    -- Transaction status and type
    ft.status_transacao,
    ft.tipo_transacao,
    ft.codigo_tipo_transacao,
    ft.origem_transacao,
    ft.descricao_transacao,
    
    -- Product information
    dp.codigo_produto,
    dp.nome_produto,
    dp.categoria as categoria_produto,
    
    -- Card and cardholder information
    c.tipo_cartao,
    c.status as status_cartao,
    ch.status as status_portador,
    ch.data_admissao,
    
    -- Company information
    comp.razao_social,
    comp.cnpj as cnpj_empresa,
    comp.tipo_empresa,
    ds.segmento_nome,
    ds.categoria_segmento,
    
    -- Establishment information
    est.nome_empresarial as nome_estabelecimento,
    est.nome_fantasia,
    est.cnpj as cnpj_estabelecimento,
    est.porte_empresa,
    est.situacao_cadastral,
    
    -- Location information (establishment)
    dm_est.municipio_nome as municipio_estabelecimento,
    dm_est.uf_nome as uf_estabelecimento,
    dm_est.regiao as regiao_estabelecimento,
    
    -- Location information (cardholder)
    dm_ch.municipio_nome as municipio_portador,
    dm_ch.uf_nome as uf_portador,
    dm_ch.regiao as regiao_portador,
    
    -- Terminal and technology information
    dt.modelo_terminal,
    dt.tipo_terminal,
    dt.status as status_terminal,
    dtc.nome_tecnologia,
    dtc.categoria_tecnologia,
    dtc.requires_plastico,
    
    -- Acquirer and brand information
    da.nome_adquirente,
    dba.nome_bandeira,
    
    -- CNAE information
    dcnae.codigo_cnae,
    dcnae.descricao_cnae,
    dcnae.secao as cnae_secao,
    dcnae.divisao as cnae_divisao,
    
    -- Rejection reason (if applicable)
    dmn.codigo_retorno,
    dmn.descricao_motivo,
    dmn.categoria_motivo,
    dmn.eh_fraude_potencial,
    
    -- Liquidation information
    ft.requer_liquidacao_bandeira,
    ft.data_liquidacao,
    ft.status_liquidacao

FROM fact_transactions ft
    INNER JOIN dim_data dd ON ft.data_transacao = dd.data_id
    INNER JOIN dim_produtos dp ON ft.produto_id = dp.produto_id
    INNER JOIN cards c ON ft.card_id = c.card_id
    INNER JOIN cardholders ch ON c.cardholder_id = ch.cardholder_id
    INNER JOIN companies comp ON ch.company_id = comp.company_id
    INNER JOIN dim_segmentos ds ON comp.segmento_id = ds.segmento_id
    INNER JOIN establishments est ON ft.establishment_id = est.establishment_id
    INNER JOIN dim_municipios dm_est ON est.municipio_id = dm_est.municipio_id
    INNER JOIN dim_municipios dm_ch ON ch.municipio_id = dm_ch.municipio_id
    INNER JOIN dim_terminais dt ON ft.terminal_id = dt.terminal_id
    INNER JOIN dim_tecnologias_captura dtc ON ft.tecnologia_captura_id = dtc.tecnologia_id
    INNER JOIN dim_adquirentes da ON dt.adquirente_id = da.adquirente_id
    INNER JOIN dim_cnae dcnae ON est.cnae_principal_id = dcnae.cnae_id
    LEFT JOIN dim_bandeiras dba ON c.bandeira_id = dba.bandeira_id
    LEFT JOIN dim_motivos_negacao dmn ON ft.motivo_negacao_id = dmn.motivo_negacao_id;

-- View: Monthly transaction summary by product type
CREATE VIEW vw_monthly_product_summary AS
SELECT 
    dd.ano,
    dd.mes,
    dp.codigo_produto,
    dp.nome_produto,
    dp.categoria as categoria_produto,
    COUNT(*) as total_transacoes,
    COUNT(CASE WHEN ft.status_transacao = 'aprovada' THEN 1 END) as transacoes_aprovadas,
    COUNT(CASE WHEN ft.status_transacao = 'negada' THEN 1 END) as transacoes_negadas,
    SUM(CASE WHEN ft.status_transacao = 'aprovada' THEN ft.valor_transacao ELSE 0 END) as valor_aprovado,
    AVG(CASE WHEN ft.status_transacao = 'aprovada' THEN ft.valor_transacao END) as valor_medio_aprovado,
    COUNT(DISTINCT ch.cardholder_id) as portadores_unicos,
    COUNT(DISTINCT est.establishment_id) as estabelecimentos_unicos
FROM fact_transactions ft
    INNER JOIN dim_data dd ON ft.data_transacao = dd.data_id
    INNER JOIN dim_produtos dp ON ft.produto_id = dp.produto_id
    INNER JOIN cards c ON ft.card_id = c.card_id
    INNER JOIN cardholders ch ON c.cardholder_id = ch.cardholder_id
    INNER JOIN establishments est ON ft.establishment_id = est.establishment_id
GROUP BY dd.ano, dd.mes, dp.codigo_produto, dp.nome_produto, dp.categoria;

-- View: Company product usage summary
CREATE VIEW vw_company_product_usage AS
SELECT 
    comp.company_id,
    comp.razao_social,
    comp.cnpj,
    ds.segmento_nome,
    dp.codigo_produto,
    dp.nome_produto,
    COUNT(DISTINCT ch.cardholder_id) as total_portadores,
    COUNT(DISTINCT c.card_id) as total_cartoes,
    COUNT(*) as total_transacoes,
    SUM(CASE WHEN ft.status_transacao = 'aprovada' THEN ft.valor_transacao ELSE 0 END) as valor_total_gasto,
    AVG(CASE WHEN ft.status_transacao = 'aprovada' THEN ft.valor_transacao END) as valor_medio_transacao,
    COUNT(CASE WHEN ft.status_transacao = 'aprovada' THEN 1 END) / COUNT(*)::DOUBLE * 100 as taxa_aprovacao
FROM companies comp
    INNER JOIN dim_segmentos ds ON comp.segmento_id = ds.segmento_id
    INNER JOIN cardholders ch ON comp.company_id = ch.company_id
    INNER JOIN cards c ON ch.cardholder_id = c.cardholder_id
    INNER JOIN fact_transactions ft ON c.card_id = ft.card_id
    INNER JOIN dim_produtos dp ON ft.produto_id = dp.produto_id
GROUP BY comp.company_id, comp.razao_social, comp.cnpj, ds.segmento_nome, dp.codigo_produto, dp.nome_produto;

-- View: Technology usage trends
CREATE VIEW vw_technology_usage_trends AS
SELECT 
    dd.ano,
    dd.mes,
    dtc.nome_tecnologia,
    dtc.categoria_tecnologia,
    dtc.requires_plastico,
    COUNT(*) as total_transacoes,
    COUNT(CASE WHEN ft.status_transacao = 'aprovada' THEN 1 END) as transacoes_aprovadas,
    SUM(CASE WHEN ft.status_transacao = 'aprovada' THEN ft.valor_transacao ELSE 0 END) as valor_total,
    COUNT(CASE WHEN ft.status_transacao = 'aprovada' THEN 1 END) / COUNT(*)::DOUBLE * 100 as taxa_aprovacao
FROM fact_transactions ft
    INNER JOIN dim_data dd ON ft.data_transacao = dd.data_id
    INNER JOIN dim_tecnologias_captura dtc ON ft.tecnologia_captura_id = dtc.tecnologia_id
GROUP BY dd.ano, dd.mes, dtc.nome_tecnologia, dtc.categoria_tecnologia, dtc.requires_plastico;

-- View: Rejection analysis
CREATE VIEW vw_rejection_analysis AS
SELECT 
    dd.ano,
    dd.mes,
    dmn.codigo_retorno,
    dmn.descricao_motivo,
    dmn.categoria_motivo,
    dmn.eh_fraude_potencial,
    dp.codigo_produto,
    dp.nome_produto,
    COUNT(*) as total_negacoes,
    COUNT(DISTINCT ch.cardholder_id) as portadores_afetados,
    COUNT(DISTINCT est.establishment_id) as estabelecimentos_afetados,
    SUM(ft.valor_transacao) as valor_negado
FROM fact_transactions ft
    INNER JOIN dim_data dd ON ft.data_transacao = dd.data_id
    INNER JOIN dim_motivos_negacao dmn ON ft.motivo_negacao_id = dmn.motivo_negacao_id
    INNER JOIN dim_produtos dp ON ft.produto_id = dp.produto_id
    INNER JOIN cards c ON ft.card_id = c.card_id
    INNER JOIN cardholders ch ON c.cardholder_id = ch.cardholder_id
    INNER JOIN establishments est ON ft.establishment_id = est.establishment_id
WHERE ft.status_transacao = 'negada'
GROUP BY dd.ano, dd.mes, dmn.codigo_retorno, dmn.descricao_motivo, dmn.categoria_motivo, 
         dmn.eh_fraude_potencial, dp.codigo_produto, dp.nome_produto;

-- View: Establishment performance
CREATE VIEW vw_establishment_performance AS
SELECT 
    est.establishment_id,
    est.nome_empresarial,
    est.nome_fantasia,
    est.cnpj,
    dcnae.descricao_cnae,
    dm.municipio_nome,
    dm.uf_nome,
    dm.regiao,
    COUNT(*) as total_transacoes,
    COUNT(CASE WHEN ft.status_transacao = 'aprovada' THEN 1 END) as transacoes_aprovadas,
    SUM(CASE WHEN ft.status_transacao = 'aprovada' THEN ft.valor_transacao ELSE 0 END) as faturamento_total,
    AVG(CASE WHEN ft.status_transacao = 'aprovada' THEN ft.valor_transacao END) as ticket_medio,
    COUNT(DISTINCT ch.cardholder_id) as clientes_unicos,
    COUNT(CASE WHEN ft.status_transacao = 'aprovada' THEN 1 END) / COUNT(*)::DOUBLE * 100 as taxa_aprovacao
FROM establishments est
    INNER JOIN dim_cnae dcnae ON est.cnae_principal_id = dcnae.cnae_id
    INNER JOIN dim_municipios dm ON est.municipio_id = dm.municipio_id
    INNER JOIN fact_transactions ft ON est.establishment_id = ft.establishment_id
    INNER JOIN cards c ON ft.card_id = c.card_id
    INNER JOIN cardholders ch ON c.cardholder_id = ch.cardholder_id
GROUP BY est.establishment_id, est.nome_empresarial, est.nome_fantasia, est.cnpj,
         dcnae.descricao_cnae, dm.municipio_nome, dm.uf_nome, dm.regiao;

-- View: Regional analysis
CREATE VIEW vw_regional_analysis AS
SELECT 
    dm.regiao,
    dm.uf_nome,
    dd.ano,
    dd.mes,
    dp.categoria as categoria_produto,
    COUNT(*) as total_transacoes,
    COUNT(CASE WHEN ft.status_transacao = 'aprovada' THEN 1 END) as transacoes_aprovadas,
    SUM(CASE WHEN ft.status_transacao = 'aprovada' THEN ft.valor_transacao ELSE 0 END) as valor_total,
    COUNT(DISTINCT est.establishment_id) as estabelecimentos_ativos,
    COUNT(DISTINCT ch.cardholder_id) as portadores_ativos
FROM fact_transactions ft
    INNER JOIN dim_data dd ON ft.data_transacao = dd.data_id
    INNER JOIN dim_produtos dp ON ft.produto_id = dp.produto_id
    INNER JOIN establishments est ON ft.establishment_id = est.establishment_id
    INNER JOIN dim_municipios dm ON est.municipio_id = dm.municipio_id
    INNER JOIN cards c ON ft.card_id = c.card_id
    INNER JOIN cardholders ch ON c.cardholder_id = ch.cardholder_id
GROUP BY dm.regiao, dm.uf_nome, dd.ano, dd.mes, dp.categoria;