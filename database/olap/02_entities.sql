CREATE TABLE "establishments" (
  "establishment_id" VARCHAR PRIMARY KEY,
  "cnpj" VARCHAR,
  "nome_empresarial" VARCHAR,
  "nome_fantasia" VARCHAR,
  "cnae_principal_id" VARCHAR NOT NULL REFERENCES dim_cnae(cnae_id),
  "natureza_juridica" VARCHAR,
  "porte_empresa" VARCHAR,
  "municipio_id" VARCHAR NOT NULL REFERENCES dim_municipios(municipio_id),
  "cep" VARCHAR,
  "logradouro" VARCHAR,
  "numero" VARCHAR,
  "complemento" VARCHAR,
  "bairro" VARCHAR,
  "email" VARCHAR,
  "telefone" VARCHAR,
  "situacao_cadastral" VARCHAR,
  "data_situacao_cadastral" DATE,
  "motivo_situacao" VARCHAR,
  "data_abertura" DATE,
  "created_at" TIMESTAMP
);

CREATE TABLE "companies" (
  "company_id" VARCHAR PRIMARY KEY,
  "parent_company_id" VARCHAR REFERENCES companies(company_id),
  "codigo_cliente" VARCHAR,
  "razao_social" VARCHAR,
  "cnpj" VARCHAR,
  "tipo_empresa" VARCHAR,
  "segmento_id" VARCHAR NOT NULL REFERENCES dim_segmentos(segmento_id),
  "municipio_id" VARCHAR NOT NULL REFERENCES dim_municipios(municipio_id),
  "data_cadastro_contrato" DATE,
  "forma_recebimento" VARCHAR,
  "created_at" TIMESTAMP
);

CREATE TABLE "cardholders" (
  "cardholder_id" VARCHAR PRIMARY KEY,
  "company_id" VARCHAR NOT NULL REFERENCES companies(company_id),
  "cpf_hash" VARCHAR,
  "municipio_id" VARCHAR NOT NULL REFERENCES dim_municipios(municipio_id),
  "data_admissao" DATE,
  "status" VARCHAR,
  "created_at" TIMESTAMP
);

CREATE TABLE "cardholder_products" (
  "cardholder_product_id" VARCHAR PRIMARY KEY,
  "cardholder_id" VARCHAR NOT NULL REFERENCES cardholders(cardholder_id),
  "produto_id" VARCHAR NOT NULL REFERENCES dim_produtos(produto_id),
  "data_inicio" DATE,
  "data_fim" DATE,
  "status" VARCHAR,
  "created_at" TIMESTAMP
);

CREATE TABLE "cards" (
  "card_id" VARCHAR PRIMARY KEY,
  "cardholder_id" VARCHAR NOT NULL REFERENCES cardholders(cardholder_id),
  "numero_cartao_hash" VARCHAR,
  "data_vencimento" DATE,
  "cvv_hash" VARCHAR,
  "bandeira_id" VARCHAR REFERENCES dim_bandeiras(bandeira_id),
  "tipo_cartao" VARCHAR,
  "status" VARCHAR,
  "created_at" TIMESTAMP
);

CREATE TABLE "dim_terminais" (
  "terminal_id" VARCHAR PRIMARY KEY,
  "codigo_afiliacao" VARCHAR,
  "numero_filiacao" VARCHAR,
  "establishment_id" VARCHAR NOT NULL REFERENCES establishments(establishment_id),
  "adquirente_id" VARCHAR NOT NULL REFERENCES dim_adquirentes(adquirente_id),
  "modelo_terminal" VARCHAR,
  "tipo_terminal" VARCHAR,
  "status" VARCHAR,
  "data_instalacao" DATE,
  "created_at" TIMESTAMP
);