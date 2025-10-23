CREATE TABLE IF NOT EXISTS products (
  id CHAR(2) PRIMARY KEY,
  name varchar NOT NULL,
  category varchar NOT NULL,
  active boolean DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(), -- Pensar se o banco vai gerar ou o python
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now() -- Pensar se o banco vai gerar ou o python
);

CREATE TABLE IF NOT EXISTS transaction_modalities (
  id varchar PRIMARY KEY,
  code varchar UNIQUE NOT NULL,
  name varchar NOT NULL,
  type varchar NOT NULL,
  active boolean DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS acquirers (
  id varchar PRIMARY KEY,
  name varchar NOT NULL,
  active boolean DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS mcc_modalities (
  mcc_code varchar NOT NULL,
  modality_id varchar NOT NULL, -- Required to exist transaction_modalities table
  mcc_description varchar NOT NULL,
  observation varchar,
  active boolean DEFAULT true,
  created_at timestamp DEFAULT (now()),
  PRIMARY KEY (mcc_code, modality_id)
);

CREATE TABLE IF NOT EXISTS cnae_products (
  cnae_code varchar NOT NULL,
  product_id varchar NOT NULL, -- Required to exist in products table
  cnae_description varchar NOT NULL,
  observation varchar,
  active boolean DEFAULT true,
  created_at timestamp DEFAULT (now()),
  PRIMARY KEY (cnae_code, product_id)
);

CREATE TABLE IF NOT EXISTS companies (
  company_id varchar PRIMARY KEY,
  cnpj varchar UNIQUE NOT NULL,
  company_name varchar NOT NULL,
  trade_name varchar,
  segment varchar NOT NULL,
  city varchar NOT NULL,
  state varchar NOT NULL,
  status varchar NOT NULL DEFAULT 'active',
  registration_date date NOT NULL,
  created_at timestamp DEFAULT (now()),
  updated_at timestamp
);

CREATE TABLE IF NOT EXISTS cardholders (
  cardholder_id varchar PRIMARY KEY,
  company_id varchar NOT NULL,
  cpf_hash varchar UNIQUE NOT NULL,
  name varchar NOT NULL,
  city varchar NOT NULL,
  state varchar NOT NULL,
  admission_date date NOT NULL,
  position varchar,
  department varchar,
  status varchar NOT NULL DEFAULT 'active',
  created_at timestamp DEFAULT (now()),
  updated_at timestamp
);

CREATE TABLE IF NOT EXISTS cards (
  id varchar PRIMARY KEY,
  cardholder_id varchar NOT NULL,
  modality_id varchar,
  card_number_hash varchar UNIQUE NOT NULL,
  expiration_date date NOT NULL,
  card_type varchar NOT NULL,
  status varchar NOT NULL DEFAULT 'active',
  issue_date date NOT NULL,
  created_at timestamp DEFAULT (now()),
  updated_at timestamp
);

CREATE TABLE IF NOT EXISTS card_products (
  card_product_id varchar PRIMARY KEY,
  card_id varchar NOT NULL,
  product_id varchar NOT NULL,
  current_balance decimal(15,2) NOT NULL DEFAULT 0,
  daily_limit decimal(15,2) DEFAULT 0,
  monthly_limit decimal(15,2) DEFAULT 0,
  activation_date date NOT NULL,
  status varchar NOT NULL DEFAULT 'active',
  created_at timestamp DEFAULT (now()),
  updated_at timestamp
);

CREATE TABLE IF NOT EXISTS establishments (
  establishment_id varchar PRIMARY KEY,
  cnpj varchar UNIQUE NOT NULL,
  company_name varchar NOT NULL,
  trade_name varchar,
  main_cnae varchar NOT NULL,
  mcc_code varchar NOT NULL,
  category varchar NOT NULL,
  city varchar NOT NULL,
  state varchar NOT NULL,
  status varchar NOT NULL DEFAULT 'active',
  accreditation_date date NOT NULL,
  created_at timestamp DEFAULT (now()),
  updated_at timestamp
);

CREATE TABLE IF NOT EXISTS terminals (
  id varchar PRIMARY KEY,
  establishment_id varchar NOT NULL,
  acquirer_id varchar NOT NULL,
  model varchar,
  type varchar NOT NULL,
  status varchar NOT NULL DEFAULT 'active',
  installation_date date NOT NULL,
  created_at timestamp DEFAULT (now()),
  updated_at timestamp
);

CREATE TABLE IF NOT EXISTS transactions (
  transaction_id varchar PRIMARY KEY,
  card_id varchar NOT NULL,
  product_id varchar NOT NULL,
  establishment_id varchar NOT NULL,
  terminal_id varchar NOT NULL,
  transaction_amount decimal(15,2) NOT NULL,
  transaction_date timestamp NOT NULL,
  capture_type varchar NOT NULL,
  response_code varchar NOT NULL,
  response_message varchar,
  created_at timestamp DEFAULT (now()),
  updated_at timestamp
);

CREATE TABLE IF NOT EXISTS authorizations (
  authorization_id varchar PRIMARY KEY,
  transaction_id varchar NOT NULL,
  authorization_code varchar,
  nsu varchar NOT NULL,
  authorization_datetime timestamp NOT NULL,
  status varchar NOT NULL,
  created_at timestamp DEFAULT (now())
);

CREATE TABLE IF NOT EXISTS balance_history (
  history_id varchar PRIMARY KEY,
  card_product_id varchar NOT NULL,
  transaction_id varchar,
  operation_type varchar NOT NULL,
  operation_amount decimal(15,2) NOT NULL,
  previous_balance decimal(15,2) NOT NULL,
  posterior_balance decimal(15,2) NOT NULL,
  operation_date timestamp NOT NULL,
  created_at timestamp DEFAULT (now())
);

COMMENT ON COLUMN cards.modality_id IS 'NULL = proprietary network';

ALTER TABLE cardholders ADD FOREIGN KEY (company_id) REFERENCES companies (company_id);

ALTER TABLE cards ADD FOREIGN KEY (cardholder_id) REFERENCES cardholders (cardholder_id);

ALTER TABLE cards ADD FOREIGN KEY (modality_id) REFERENCES transaction_modalities (modality_id);

ALTER TABLE card_products ADD FOREIGN KEY (card_id) REFERENCES cards (card_id);

ALTER TABLE card_products ADD FOREIGN KEY (product_id) REFERENCES products (product_id);

ALTER TABLE terminals ADD FOREIGN KEY (establishment_id) REFERENCES establishments (establishment_id);

ALTER TABLE terminals ADD FOREIGN KEY (acquirer_id) REFERENCES acquirers (acquirer_id);

ALTER TABLE mcc_modalities ADD FOREIGN KEY (modality_id) REFERENCES transaction_modalities (modality_id);

ALTER TABLE cnae_products ADD FOREIGN KEY (product_id) REFERENCES products (product_id);

ALTER TABLE transactions ADD FOREIGN KEY (card_id) REFERENCES cards (card_id);

ALTER TABLE transactions ADD FOREIGN KEY (product_id) REFERENCES products (product_id);

ALTER TABLE transactions ADD FOREIGN KEY (establishment_id) REFERENCES establishments (establishment_id);

ALTER TABLE transactions ADD FOREIGN KEY (terminal_id) REFERENCES terminals (terminal_id);

ALTER TABLE authorizations ADD FOREIGN KEY (transaction_id) REFERENCES transactions (transaction_id);

ALTER TABLE balance_history ADD FOREIGN KEY (card_product_id) REFERENCES card_products (card_product_id);

ALTER TABLE balance_history ADD FOREIGN KEY (transaction_id) REFERENCES transactions (transaction_id);
