-- OLTP Model - Sistema Transacional de Benefícios Corporativos

-- TABELAS DE APOIO

-- Produtos: VA, VR, PREMIUM
CREATE TABLE produtos (
  produto_id VARCHAR PRIMARY KEY,
  codigo VARCHAR UNIQUE NOT NULL,
  nome VARCHAR NOT NULL,
  categoria VARCHAR NOT NULL,
  ativo BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP
);

-- Modalidades Transacionais: ELO, MASTER, VISA, REDE_FECHADA
CREATE TABLE modalidades_transacionais (
  modalidade_id VARCHAR PRIMARY KEY,
  codigo VARCHAR UNIQUE NOT NULL,
  nome VARCHAR NOT NULL,
  tipo VARCHAR NOT NULL,
  ativo BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Adquirentes: Cielo, Rede, Stone
CREATE TABLE adquirentes (
  adquirente_id VARCHAR PRIMARY KEY,
  codigo VARCHAR UNIQUE NOT NULL,
  nome VARCHAR NOT NULL,
  ativo BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Mapeamento MCC x Modalidades (para bandeiras)
CREATE TABLE mcc_modalidades (
  mcc_code VARCHAR NOT NULL,
  modalidade_id VARCHAR NOT NULL,
  descricao_mcc VARCHAR NOT NULL,
  observacao VARCHAR,
  ativo BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (mcc_code, modalidade_id),
  FOREIGN KEY (modalidade_id) REFERENCES modalidades_transacionais(modalidade_id)
);

-- Mapeamento CNAE x Produtos (para rede fechada)
CREATE TABLE cnae_produtos (
  cnae_code VARCHAR NOT NULL,
  produto_id VARCHAR NOT NULL,
  descricao_cnae VARCHAR NOT NULL,
  observacao VARCHAR,
  ativo BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (cnae_code, produto_id),
  FOREIGN KEY (produto_id) REFERENCES produtos(produto_id)
);

-- Empresas
CREATE TABLE empresas (
  empresa_id VARCHAR PRIMARY KEY,
  cnpj VARCHAR UNIQUE NOT NULL,
  razao_social VARCHAR NOT NULL,
  nome_fantasia VARCHAR,
  segmento VARCHAR NOT NULL,
  municipio VARCHAR NOT NULL,
  uf VARCHAR NOT NULL,
  status VARCHAR NOT NULL DEFAULT 'ativo',
  data_cadastro DATE NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP
);

-- Portadores
CREATE TABLE portadores (
  portador_id VARCHAR PRIMARY KEY,
  empresa_id VARCHAR NOT NULL,
  cpf_hash VARCHAR UNIQUE NOT NULL,
  nome VARCHAR NOT NULL,
  municipio VARCHAR NOT NULL,
  uf VARCHAR NOT NULL,
  data_admissao DATE NOT NULL,
  cargo VARCHAR,
  departamento VARCHAR,
  status VARCHAR NOT NULL DEFAULT 'ativo',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP,
  FOREIGN KEY (empresa_id) REFERENCES empresas(empresa_id)
);

-- Cartões
CREATE TABLE cartoes (
  cartao_id VARCHAR PRIMARY KEY,
  portador_id VARCHAR NOT NULL,
  numero_cartao_hash VARCHAR UNIQUE NOT NULL,
  modalidade_id VARCHAR,
  data_vencimento DATE NOT NULL,
  tipo_cartao VARCHAR NOT NULL,
  status VARCHAR NOT NULL DEFAULT 'ativo',
  data_emissao DATE NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP,
  FOREIGN KEY (portador_id) REFERENCES portadores(portador_id),
  FOREIGN KEY (modalidade_id) REFERENCES modalidades_transacionais(modalidade_id)
);

-- Cartão Produtos
CREATE TABLE cartao_produtos (
  cartao_produto_id VARCHAR PRIMARY KEY,
  cartao_id VARCHAR NOT NULL,
  produto_id VARCHAR NOT NULL,
  saldo_atual DECIMAL(15,2) NOT NULL DEFAULT 0,
  limite_diario DECIMAL(15,2) DEFAULT 0,
  limite_mensal DECIMAL(15,2) DEFAULT 0,
  data_ativacao DATE NOT NULL,
  status VARCHAR NOT NULL DEFAULT 'ativo',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP,
  FOREIGN KEY (cartao_id) REFERENCES cartoes(cartao_id),
  FOREIGN KEY (produto_id) REFERENCES produtos(produto_id)
);

-- Estabelecimentos
CREATE TABLE estabelecimentos (
  estabelecimento_id VARCHAR PRIMARY KEY,
  cnpj VARCHAR UNIQUE NOT NULL,
  razao_social VARCHAR NOT NULL,
  nome_fantasia VARCHAR,
  cnae_principal VARCHAR NOT NULL,
  mcc_code VARCHAR NOT NULL,
  categoria VARCHAR NOT NULL,
  municipio VARCHAR NOT NULL,
  uf VARCHAR NOT NULL,
  status VARCHAR NOT NULL DEFAULT 'ativo',
  data_credenciamento DATE NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP
);

-- Terminais
CREATE TABLE terminais (
  terminal_id VARCHAR PRIMARY KEY,
  estabelecimento_id VARCHAR NOT NULL,
  adquirente_id VARCHAR NOT NULL,
  codigo_terminal VARCHAR NOT NULL,
  modelo VARCHAR,
  tipo VARCHAR NOT NULL,
  status VARCHAR NOT NULL DEFAULT 'ativo',
  data_instalacao DATE NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP,
  FOREIGN KEY (estabelecimento_id) REFERENCES estabelecimentos(estabelecimento_id),
  FOREIGN KEY (adquirente_id) REFERENCES adquirentes(adquirente_id)
);

-- Transações
CREATE TABLE transacoes (
  transacao_id VARCHAR PRIMARY KEY,
  cartao_id VARCHAR NOT NULL,
  produto_id VARCHAR NOT NULL,
  estabelecimento_id VARCHAR NOT NULL,
  terminal_id VARCHAR NOT NULL,
  valor_transacao DECIMAL(15,2) NOT NULL,
  data_transacao TIMESTAMP NOT NULL,
  tipo_captura VARCHAR NOT NULL,
  codigo_resposta VARCHAR NOT NULL,
  mensagem_resposta VARCHAR,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP,
  FOREIGN KEY (cartao_id) REFERENCES cartoes(cartao_id),
  FOREIGN KEY (produto_id) REFERENCES produtos(produto_id),
  FOREIGN KEY (estabelecimento_id) REFERENCES estabelecimentos(estabelecimento_id),
  FOREIGN KEY (terminal_id) REFERENCES terminais(terminal_id)
);

-- Autorizações
CREATE TABLE autorizacoes (
  autorizacao_id VARCHAR PRIMARY KEY,
  transacao_id VARCHAR NOT NULL,
  codigo_autorizacao VARCHAR,
  nsu VARCHAR NOT NULL,
  data_hora_autorizacao TIMESTAMP NOT NULL,
  status VARCHAR NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (transacao_id) REFERENCES transacoes(transacao_id)
);

-- Histórico de Saldos
CREATE TABLE historico_saldos (
  historico_id VARCHAR PRIMARY KEY,
  cartao_produto_id VARCHAR NOT NULL,
  transacao_id VARCHAR,
  tipo_operacao VARCHAR NOT NULL,
  valor_operacao DECIMAL(15,2) NOT NULL,
  saldo_anterior DECIMAL(15,2) NOT NULL,
  saldo_posterior DECIMAL(15,2) NOT NULL,
  data_operacao TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (cartao_produto_id) REFERENCES cartao_produtos(cartao_produto_id),
  FOREIGN KEY (transacao_id) REFERENCES transacoes(transacao_id)
);
