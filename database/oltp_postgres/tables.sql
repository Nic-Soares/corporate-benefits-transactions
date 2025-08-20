CREATE TABLE IF NOT EXISTS "produtos" (
  "produto_id" varchar PRIMARY KEY,
  "codigo" varchar UNIQUE NOT NULL,
  "nome" varchar NOT NULL,
  "categoria" varchar NOT NULL,
  "ativo" boolean DEFAULT true,
  "created_at" timestamp DEFAULT (now()),
  "updated_at" timestamp
);

CREATE TABLE IF NOT EXISTS "modalidades_transacionais" (
  "modalidade_id" varchar PRIMARY KEY,
  "codigo" varchar UNIQUE NOT NULL,
  "nome" varchar NOT NULL,
  "tipo" varchar NOT NULL,
  "ativo" boolean DEFAULT true,
  "created_at" timestamp DEFAULT (now())
);

CREATE TABLE IF NOT EXISTS "adquirentes" (
  "adquirente_id" varchar PRIMARY KEY,
  "codigo" varchar UNIQUE NOT NULL,
  "nome" varchar NOT NULL,
  "ativo" boolean DEFAULT true,
  "created_at" timestamp DEFAULT (now())
);

CREATE TABLE IF NOT EXISTS "mcc_modalidades" (
  "mcc_code" varchar NOT NULL,
  "modalidade_id" varchar NOT NULL,
  "descricao_mcc" varchar NOT NULL,
  "observacao" varchar,
  "ativo" boolean DEFAULT true,
  "created_at" timestamp DEFAULT (now()),
  PRIMARY KEY ("mcc_code", "modalidade_id")
);

CREATE TABLE IF NOT EXISTS "cnae_produtos" (
  "cnae_code" varchar NOT NULL,
  "produto_id" varchar NOT NULL,
  "descricao_cnae" varchar NOT NULL,
  "observacao" varchar,
  "ativo" boolean DEFAULT true,
  "created_at" timestamp DEFAULT (now()),
  PRIMARY KEY ("cnae_code", "produto_id")
);

CREATE TABLE IF NOT EXISTS "empresas" (
  "empresa_id" varchar PRIMARY KEY,
  "cnpj" varchar UNIQUE NOT NULL,
  "razao_social" varchar NOT NULL,
  "nome_fantasia" varchar,
  "segmento" varchar NOT NULL,
  "municipio" varchar NOT NULL,
  "uf" varchar NOT NULL,
  "status" varchar NOT NULL DEFAULT 'ativo',
  "data_cadastro" date NOT NULL,
  "created_at" timestamp DEFAULT (now()),
  "updated_at" timestamp
);

CREATE TABLE IF NOT EXISTS "portadores" (
  "portador_id" varchar PRIMARY KEY,
  "empresa_id" varchar NOT NULL,
  "cpf_hash" varchar UNIQUE NOT NULL,
  "nome" varchar NOT NULL,
  "municipio" varchar NOT NULL,
  "uf" varchar NOT NULL,
  "data_admissao" date NOT NULL,
  "cargo" varchar,
  "departamento" varchar,
  "status" varchar NOT NULL DEFAULT 'ativo',
  "created_at" timestamp DEFAULT (now()),
  "updated_at" timestamp
);

CREATE TABLE IF NOT EXISTS "cartoes" (
  "cartao_id" varchar PRIMARY KEY,
  "portador_id" varchar NOT NULL,
  "numero_cartao_hash" varchar UNIQUE NOT NULL,
  "modalidade_id" varchar,
  "data_vencimento" date NOT NULL,
  "tipo_cartao" varchar NOT NULL,
  "status" varchar NOT NULL DEFAULT 'ativo',
  "data_emissao" date NOT NULL,
  "created_at" timestamp DEFAULT (now()),
  "updated_at" timestamp
);

CREATE TABLE IF NOT EXISTS "cartao_produtos" (
  "cartao_produto_id" varchar PRIMARY KEY,
  "cartao_id" varchar NOT NULL,
  "produto_id" varchar NOT NULL,
  "saldo_atual" decimal(15,2) NOT NULL DEFAULT 0,
  "limite_diario" decimal(15,2) DEFAULT 0,
  "limite_mensal" decimal(15,2) DEFAULT 0,
  "data_ativacao" date NOT NULL,
  "status" varchar NOT NULL DEFAULT 'ativo',
  "created_at" timestamp DEFAULT (now()),
  "updated_at" timestamp
);

CREATE TABLE IF NOT EXISTS "estabelecimentos" (
  "estabelecimento_id" varchar PRIMARY KEY,
  "cnpj" varchar UNIQUE NOT NULL,
  "razao_social" varchar NOT NULL,
  "nome_fantasia" varchar,
  "cnae_principal" varchar NOT NULL,
  "mcc_code" varchar NOT NULL,
  "categoria" varchar NOT NULL,
  "municipio" varchar NOT NULL,
  "uf" varchar NOT NULL,
  "status" varchar NOT NULL DEFAULT 'ativo',
  "data_credenciamento" date NOT NULL,
  "created_at" timestamp DEFAULT (now()),
  "updated_at" timestamp
);

CREATE TABLE IF NOT EXISTS "terminais" (
  "terminal_id" varchar PRIMARY KEY,
  "estabelecimento_id" varchar NOT NULL,
  "adquirente_id" varchar NOT NULL,
  "codigo_terminal" varchar NOT NULL,
  "modelo" varchar,
  "tipo" varchar NOT NULL,
  "status" varchar NOT NULL DEFAULT 'ativo',
  "data_instalacao" date NOT NULL,
  "created_at" timestamp DEFAULT (now()),
  "updated_at" timestamp
);

CREATE TABLE IF NOT EXISTS "transacoes" (
  "transacao_id" varchar PRIMARY KEY,
  "cartao_id" varchar NOT NULL,
  "produto_id" varchar NOT NULL,
  "estabelecimento_id" varchar NOT NULL,
  "terminal_id" varchar NOT NULL,
  "valor_transacao" decimal(15,2) NOT NULL,
  "data_transacao" timestamp NOT NULL,
  "tipo_captura" varchar NOT NULL,
  "codigo_resposta" varchar NOT NULL,
  "mensagem_resposta" varchar,
  "created_at" timestamp DEFAULT (now()),
  "updated_at" timestamp
);

CREATE TABLE IF NOT EXISTS "autorizacoes" (
  "autorizacao_id" varchar PRIMARY KEY,
  "transacao_id" varchar NOT NULL,
  "codigo_autorizacao" varchar,
  "nsu" varchar NOT NULL,
  "data_hora_autorizacao" timestamp NOT NULL,
  "status" varchar NOT NULL,
  "created_at" timestamp DEFAULT (now())
);

CREATE TABLE IF NOT EXISTS "historico_saldos" (
  "historico_id" varchar PRIMARY KEY,
  "cartao_produto_id" varchar NOT NULL,
  "transacao_id" varchar,
  "tipo_operacao" varchar NOT NULL,
  "valor_operacao" decimal(15,2) NOT NULL,
  "saldo_anterior" decimal(15,2) NOT NULL,
  "saldo_posterior" decimal(15,2) NOT NULL,
  "data_operacao" timestamp NOT NULL,
  "created_at" timestamp DEFAULT (now())
);

COMMENT ON COLUMN "cartoes"."modalidade_id" IS 'NULL = rede própria';

ALTER TABLE "portadores" ADD FOREIGN KEY ("empresa_id") REFERENCES "empresas" ("empresa_id");

ALTER TABLE "cartoes" ADD FOREIGN KEY ("portador_id") REFERENCES "portadores" ("portador_id");

ALTER TABLE "cartoes" ADD FOREIGN KEY ("modalidade_id") REFERENCES "modalidades_transacionais" ("modalidade_id");

ALTER TABLE "cartao_produtos" ADD FOREIGN KEY ("cartao_id") REFERENCES "cartoes" ("cartao_id");

ALTER TABLE "cartao_produtos" ADD FOREIGN KEY ("produto_id") REFERENCES "produtos" ("produto_id");

ALTER TABLE "terminais" ADD FOREIGN KEY ("estabelecimento_id") REFERENCES "estabelecimentos" ("estabelecimento_id");

ALTER TABLE "terminais" ADD FOREIGN KEY ("adquirente_id") REFERENCES "adquirentes" ("adquirente_id");

ALTER TABLE "mcc_modalidades" ADD FOREIGN KEY ("modalidade_id") REFERENCES "modalidades_transacionais" ("modalidade_id");

ALTER TABLE "cnae_produtos" ADD FOREIGN KEY ("produto_id") REFERENCES "produtos" ("produto_id");

ALTER TABLE "transacoes" ADD FOREIGN KEY ("cartao_id") REFERENCES "cartoes" ("cartao_id");

ALTER TABLE "transacoes" ADD FOREIGN KEY ("produto_id") REFERENCES "produtos" ("produto_id");

ALTER TABLE "transacoes" ADD FOREIGN KEY ("estabelecimento_id") REFERENCES "estabelecimentos" ("estabelecimento_id");

ALTER TABLE "transacoes" ADD FOREIGN KEY ("terminal_id") REFERENCES "terminais" ("terminal_id");

ALTER TABLE "autorizacoes" ADD FOREIGN KEY ("transacao_id") REFERENCES "transacoes" ("transacao_id");

ALTER TABLE "historico_saldos" ADD FOREIGN KEY ("cartao_produto_id") REFERENCES "cartao_produtos" ("cartao_produto_id");

ALTER TABLE "historico_saldos" ADD FOREIGN KEY ("transacao_id") REFERENCES "transacoes" ("transacao_id");
