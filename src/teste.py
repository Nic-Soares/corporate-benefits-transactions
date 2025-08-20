import pandas as pd
import random
import hashlib
from datetime import datetime, timedelta
from faker import Faker
fake = Faker('pt_BR')

class TransactionProcessor:
    """
    Simula operações transacionais e abastece OLTP

    Fluxo:
    1. Dados RAW → 2. Simulação Transacional → 3. Processamento OLTP → 4. Insert DB
    """

    def __init__(self, raw_data, transaction_config):
        self.raw_data = raw_data
        self.config = transaction_config

    # ========================================
    # STEP 1: PROCESSAR DADOS RAW PARA OLTP
    # ========================================

    def process_raw_to_oltp(self):
        """
        Converte dados RAW em formato OLTP (com hashing e campos específicos)
        """
        print("🔐 Processando dados RAW para OLTP...")

        oltp_data = {}

        # Processar companies
        oltp_data['companies'] = self.process_companies_to_oltp()

        # Processar cardholders
        oltp_data['cardholders'] = self.process_cardholders_to_oltp()

        # Processar cards
        oltp_data['cards'] = self.process_cards_to_oltp()

        # Processar establishments
        oltp_data['establishments'] = self.process_establishments_to_oltp()

        # Processar card_products
        oltp_data['card_products'] = self.process_card_products_to_oltp()

        return oltp_data

    def process_cardholders_to_oltp(self):
        """Hash CPF e ajusta campos para OLTP"""
        cardholders = self.raw_data['cardholders'].copy()

        # Hash do CPF
        cardholders['cpf_hash'] = cardholders['cpf'].apply(
            lambda x: hashlib.sha256(x.encode()).hexdigest()[:32]
        )

        # Remove CPF original
        cardholders.drop('cpf', axis=1, inplace=True)

        # Renomeia campos para OLTP
        cardholders.rename(columns={
            'full_name': 'name',
            'municipality_id': 'municipality'  # OLTP usa string direta
        }, inplace=True)

        # Adiciona campos OLTP
        cardholders['state'] = cardholders.apply(lambda x: fake.state_abbr(), axis=1)
        cardholders['updated_at'] = datetime.now()

        return cardholders

    def process_cards_to_oltp(self):
        """Hash número do cartão e CVV"""
        cards = self.raw_data['cards'].copy()

        # Hash do número do cartão
        cards['card_number_hash'] = cards['card_number'].apply(
            lambda x: hashlib.sha256(x.replace(' ', '').encode()).hexdigest()[:32]
        )

        # Remove número original
        cards.drop('card_number', axis=1, inplace=True)

        # Remove CVV (OLTP não armazena)
        if 'cvv' in cards.columns:
            cards.drop('cvv', axis=1, inplace=True)

        cards['updated_at'] = datetime.now()
        return cards

    def process_companies_to_oltp(self):
        """Ajusta companies para OLTP"""
        companies = self.raw_data['companies'].copy()

        # OLTP usa string direta para segment
        if 'segment_id' in companies.columns:
            companies['segment'] = companies['segment_id'].str.replace('SEG_', '')
            companies.drop('segment_id', axis=1, inplace=True)

        # OLTP usa string para municipality
        if 'municipality_id' in companies.columns:
            companies['municipality'] = companies['municipality_id'].apply(lambda x: fake.city())
            companies.drop('municipality_id', axis=1, inplace=True)

        companies['state'] = companies.apply(lambda x: fake.state_abbr(), axis=1)
        companies['updated_at'] = datetime.now()

        return companies

    def process_establishments_to_oltp(self):
        """Ajusta establishments para OLTP"""
        establishments = self.raw_data['establishments'].copy()
        establishments['updated_at'] = datetime.now()
        return establishments

    def process_card_products_to_oltp(self):
        """Remove campos não utilizados no OLTP"""
        card_products = self.raw_data['card_products'].copy()

        # OLTP não tem deactivation_date
        if 'deactivation_date' in card_products.columns:
            card_products.drop('deactivation_date', axis=1, inplace=True)

        card_products['updated_at'] = datetime.now()
        return card_products

    # ========================================
    # STEP 2: SIMULAR TRANSAÇÕES
    # ========================================

    def simulate_transactions(self, oltp_data, num_transactions=1000):
        """
        Simula transações baseadas nos dados OLTP
        """
        print(f"⚡ Simulando {num_transactions} transações...")

        transactions = []
        authorizations = []
        balance_history = []

        # Obter dados ativos para simulação
        active_cards = oltp_data['cards'][oltp_data['cards']['status'] == 'active']
        active_establishments = oltp_data['establishments'][oltp_data['establishments']['registration_status'] == 'ATIVA']
        active_terminals = self.raw_data.get('terminals', pd.DataFrame())

        if active_terminals.empty:
            # Criar terminais simples se não existir
            active_terminals = pd.DataFrame([
                {'terminal_id': f'TERM_{i:06d}', 'establishment_id': est_id}
                for i, est_id in enumerate(active_establishments['establishment_id'].head(50))
            ])

        for i in range(num_transactions):
            # Selecionar dados aleatórios
            card = active_cards.sample(1).iloc[0]
            establishment = active_establishments.sample(1).iloc[0]
            terminal = active_terminals.sample(1).iloc[0]

            # Obter produtos do cartão
            card_products = oltp_data['card_products'][
                (oltp_data['card_products']['card_id'] == card['card_id']) &
                (oltp_data['card_products']['status'] == 'active')
            ]

            if card_products.empty:
                continue

            card_product = card_products.sample(1).iloc[0]

            # Simular transação
            transaction, authorization, balance_update = self.create_transaction(
                card, card_product, establishment, terminal, i
            )

            transactions.append(transaction)
            if authorization:
                authorizations.append(authorization)
            if balance_update:
                balance_history.append(balance_update)

        return {
            'transactions': pd.DataFrame(transactions),
            'authorizations': pd.DataFrame(authorizations) if authorizations else pd.DataFrame(),
            'balance_history': pd.DataFrame(balance_history) if balance_history else pd.DataFrame()
        }

    def create_transaction(self, card, card_product, establishment, terminal, transaction_idx):
        """Cria uma transação individual"""

        # Valor da transação
        product_code = card_product['product_id'].split('_')[1]  # VA, VR, etc
        amount_config = self.config['usage_patterns']['average_amounts'].get(product_code, {})
        transaction_amount = round(random.uniform(
            amount_config.get('min', 10.0),
            amount_config.get('max', 100.0)
        ), 2)

        # Verificar se há saldo suficiente
        current_balance = card_product['current_balance']
        has_sufficient_balance = current_balance >= transaction_amount

        # Determinar resultado da transação
        approval_rate = self.config['approval_rates']['overall']
        is_approved = has_sufficient_balance and random.random() < approval_rate

        # Código de resposta
        if is_approved:
            response_code = "00"
            response_message = "Approved"
        else:
            # Escolher motivo de negação
            if not has_sufficient_balance:
                response_code = "51"
                response_message = "Insufficient funds"
            else:
                denied_codes = list(self.config['response_codes']['denied'].keys())
                response_code = random.choice(denied_codes)
                response_message = self.config['response_codes']['denied'][response_code]['description']

        # Criar transação
        transaction = {
            'transaction_id': f"TXN_{transaction_idx:08d}",
            'card_id': card['card_id'],
            'product_id': card_product['product_id'],
            'establishment_id': establishment['establishment_id'],
            'terminal_id': terminal['terminal_id'],
            'transaction_amount': transaction_amount,
            'transaction_date': fake.date_time_this_month(),
            'capture_type': random.choice(['chip', 'magnetic_stripe', 'contactless', 'nfc']),
            'response_code': response_code,
            'response_message': response_message,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }

        # Criar autorização se aprovada
        authorization = None
        if is_approved:
            authorization = {
                'authorization_id': f"AUTH_{transaction_idx:08d}",
                'transaction_id': transaction['transaction_id'],
                'authorization_code': f"AUTH{random.randint(100000, 999999)}",
                'nsu': f"NSU{random.randint(100000000, 999999999)}",
                'authorization_datetime': transaction['transaction_date'],
                'status': 'approved',
                'created_at': datetime.now()
            }

        # Criar histórico de saldo se aprovada
        balance_update = None
        if is_approved:
            new_balance = current_balance - transaction_amount
            balance_update = {
                'history_id': f"HIST_{transaction_idx:08d}",
                'card_product_id': card_product['card_product_id'],
                'transaction_id': transaction['transaction_id'],
                'operation_type': 'debit',
                'operation_amount': transaction_amount,
                'previous_balance': current_balance,
                'new_balance': new_balance,
                'operation_date': transaction['transaction_date'],
                'created_at': datetime.now()
            }

            # Atualizar saldo no card_product (simulação)
            # Em produção, isso seria feito no banco
            card_product['current_balance'] = new_balance

        return transaction, authorization, balance_update

    # ========================================
    # STEP 3: INSERIR NO BANCO OLTP
    # ========================================

    def insert_to_database(self, oltp_data, transaction_data, db_connection):
        """
        Insere dados processados no banco PostgreSQL
        """
        print("💾 Inserindo dados no banco OLTP...")

        try:
            # Inserir dados estáticos primeiro
            self._insert_static_data(oltp_data, db_connection)

            # Inserir dados transacionais
            self._insert_transaction_data(transaction_data, db_connection)

            print("✅ Dados inseridos com sucesso!")

        except Exception as e:
            print(f"❌ Erro ao inserir dados: {e}")
            db_connection.rollback()
            raise

    def _insert_static_data(self, oltp_data, db_connection):
        """Insere dados estáticos (companies, cardholders, etc.)"""

        # Ordem correta para respeitar foreign keys
        insert_order = [
            'companies',
            'cardholders',
            'cards',
            'establishments',
            'card_products'
        ]

        for table_name in insert_order:
            if table_name in oltp_data:
                df = oltp_data[table_name]
                df.to_sql(table_name, db_connection, if_exists='append', index=False)
                print(f"  ✓ Inseridos {len(df)} registros em {table_name}")

    def _insert_transaction_data(self, transaction_data, db_connection):
        """Insere dados transacionais"""

        # Inserir transações
        if not transaction_data['transactions'].empty:
            transaction_data['transactions'].to_sql(
                'transactions', db_connection, if_exists='append', index=False
            )
            print(f"  ✓ Inseridas {len(transaction_data['transactions'])} transações")

        # Inserir autorizações
        if not transaction_data['authorizations'].empty:
            transaction_data['authorizations'].to_sql(
                'authorizations', db_connection, if_exists='append', index=False
            )
            print(f"  ✓ Inseridas {len(transaction_data['authorizations'])} autorizações")

        # Inserir histórico de saldo
        if not transaction_data['balance_history'].empty:
            transaction_data['balance_history'].to_sql(
                'balance_history', db_connection, if_exists='append', index=False
            )
            print(f"  ✓ Inseridos {len(transaction_data['balance_history'])} históricos de saldo")

# ========================================
# EXEMPLO DE USO COMPLETO
# ========================================

def run_complete_simulation(raw_data, transaction_config, db_connection):
    """
    Executa simulação completa: RAW → OLTP → Transações → Database
    """
    print("🚀 Iniciando simulação completa...")

    # Inicializar processador
    processor = TransactionProcessor(raw_data, transaction_config)

    # STEP 1: Processar dados RAW para OLTP
    oltp_data = processor.process_raw_to_oltp()

    # STEP 2: Simular transações
    transaction_data = processor.simulate_transactions(oltp_data, num_transactions=5000)

    # STEP 3: Inserir no banco
    processor.insert_to_database(oltp_data, transaction_data, db_connection)

    print("🎉 Simulação completa finalizada!")

    return {
        'oltp_data': oltp_data,
        'transaction_data': transaction_data
    }
