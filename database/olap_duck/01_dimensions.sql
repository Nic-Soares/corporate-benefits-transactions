CREATE TABLE "dim_municipios" (
  "municipio_id" VARCHAR PRIMARY KEY,
  "municipio_nome" VARCHAR,
  "rgi_id" VARCHAR,
  "rgi_nome" VARCHAR,
  "rgint_id" VARCHAR,
  "rgint_nome" VARCHAR,
  "uf_id" VARCHAR,
  "uf_nome" VARCHAR,
  "uf_sigla" VARCHAR,
  "regiao_id" VARCHAR,
  "regiao_nome" VARCHAR,
  "regiao_sigla" VARCHAR,
  "concu_id" VARCHAR,
  "concu_nome" VARCHAR,
  "area_km2" DOUBLE,
  "latitude" DOUBLE,
  "longitude" DOUBLE,
  "created_at" TIMESTAMP
);

CREATE TABLE "dim_cnae" (
  "cnae_id" VARCHAR PRIMARY KEY,
  "codigo_cnae" VARCHAR,
  "descricao_cnae" VARCHAR,
  "secao" VARCHAR,
  "divisao" VARCHAR,
  "grupo" VARCHAR,
  "classe" VARCHAR,
  "subclasse" VARCHAR,
  "created_at" TIMESTAMP
);

CREATE TABLE "dim_segmentos" (
  "segmento_id" VARCHAR PRIMARY KEY,
  "segmento_nome" VARCHAR,
  "categoria_segmento" VARCHAR,
  "created_at" TIMESTAMP
);

CREATE TABLE "dim_data" (
  "data_id" VARCHAR PRIMARY KEY,
  "data_completa" DATE,
  "ano" INTEGER,
  "mes" INTEGER,
  "dia" INTEGER,
  "dia_semana" INTEGER,
  "nome_dia_semana" VARCHAR,
  "is_feriado" BOOLEAN,
  "is_fim_semana" BOOLEAN,
  "trimestre" INTEGER,
  "semestre" INTEGER,
  "created_at" TIMESTAMP
);

CREATE TABLE "dim_adquirentes" (
  "adquirente_id" VARCHAR PRIMARY KEY,
  "codigo_adquirente" VARCHAR,
  "nome_adquirente" VARCHAR,
  "created_at" TIMESTAMP
);

CREATE TABLE "dim_bandeiras" (
  "bandeira_id" VARCHAR PRIMARY KEY,
  "codigo_bandeira" VARCHAR,
  "nome_bandeira" VARCHAR,
  "created_at" TIMESTAMP
);

CREATE TABLE "dim_tecnologias_captura" (
  "tecnologia_id" VARCHAR PRIMARY KEY,
  "codigo_tecnologia" VARCHAR,
  "categoria_tecnologia" VARCHAR,
  "nome_tecnologia" VARCHAR,
  "requires_plastico" BOOLEAN,
  "created_at" TIMESTAMP
);

CREATE TABLE "dim_produtos" (
  "produto_id" VARCHAR PRIMARY KEY,
  "codigo" VARCHAR,
  "nome" VARCHAR,
  "categoria" VARCHAR,
  "descricao" VARCHAR,
  "created_at" TIMESTAMP
);

-- dim_terminais moved to after establishments table creation
-- since it references establishments

CREATE TABLE "dim_motivos_negacao" (
  "motivo_negacao_id" VARCHAR PRIMARY KEY,
  "codigo_retorno" VARCHAR,
  "descricao_motivo" VARCHAR,
  "categoria_motivo" VARCHAR,
  "eh_fraude_potencial" BOOLEAN,
  "created_at" TIMESTAMP
);
