from datetime import datetime, date
import random
import uuid
import hashlib


class Card:
    """Classe que representa um cartão corporativo"""

    def __init__(self, cardholder_id, modality_id=None):
        """
        Construtor da classe Card - cria um novo cartão
        
        Args:
            cardholder_id: ID da pessoa que vai usar o cartão (obrigatório)
            modality_id: ID do tipo de cartão (opcional - pode ser None)
        """
        # Gera um ID único para este cartão
        self.id = str(uuid.uuid4())
        
        # Define quem é o dono do cartão (obrigatório)
        self.cardholder_id = cardholder_id
        
        # Define que tipo de cartão é (pode ser None)
        self.modality_id = modality_id
        
        # Gera o número do cartão e seu hash
        card_number = self._gerar_numero_cartao()
        self.card_number_hash = self._gerar_hash_cartao(card_number)
        
        # Gera data de validade do cartão (obrigatório)
        self.expiration_date = self._gerar_data_validade()
        
        # Define se é cartão de crédito ou débito (obrigatório)
        self.card_type = random.choice(['credit', 'debit'])
        
        # Define status do cartão (padrão é 'active')
        self.status = random.choice(['active', 'inactive', 'blocked', 'canceled'])
        
        # Define data de emissão do cartão (obrigatório)
        self.issue_date = self._gerar_data_emissao()

    def _gerar_numero_cartao(self):
        """Método privado para gerar número do cartão (16 dígitos)"""
        return "".join([str(random.randint(0, 9)) for _ in range(16)])

    def _gerar_hash_cartao(self, card_number):
        """Método privado para gerar hash do número do cartão"""
        # Usa SHA-256 para criar hash do número do cartão
        return hashlib.sha256(card_number.encode()).hexdigest()

    def _gerar_data_validade(self):
        """Método privado para gerar data de validade entre 2025 e 2029"""
        ano = random.randint(2025, 2029)
        mes = random.randint(1, 12)
        # Último dia do mês para data de validade
        if mes == 2:
            dia = 28  # Fevereiro
        elif mes in [4, 6, 9, 11]:
            dia = 30  # Meses com 30 dias
        else:
            dia = 31  # Meses com 31 dias
        return date(ano, mes, dia)

    def _gerar_data_emissao(self):
        """Método privado para gerar data de emissão (entre 2020 e hoje)"""
        ano = random.randint(2020, 2024)
        mes = random.randint(1, 12)
        dia = random.randint(1, 28)  # Uso 28 para evitar problemas
        return date(ano, mes, dia)

    def to_dict(self):
        """Converte o cartão para dicionário - exatamente como a tabela SQL"""
        return {
            "id": self.id,
            "cardholder_id": self.cardholder_id,
            "modality_id": self.modality_id,
            "card_number_hash": self.card_number_hash,
            "expiration_date": self.expiration_date,
            "card_type": self.card_type,
            "status": self.status,
            "issue_date": self.issue_date
        }

    def __str__(self):
        """Representação em string do cartão para impressão"""
        return f"Cartão {self.id} - {self.card_type} - {self.status}"


class CardGenerator:
    """Gerador de cartões corporativos"""

    def __init__(self, cardholder_ids, modality_ids=None):
        """
        Construtor do gerador de cartões
        
        Args:
            cardholder_ids: Lista com IDs das pessoas que podem ter cartão
            modality_ids: Lista com IDs dos tipos de cartão (opcional)
        """
        # Guarda as listas de IDs disponíveis
        self.cardholder_ids = cardholder_ids
        self.modality_ids = modality_ids or []

    def generate_card(self, cardholder_id=None, modality_id=None):
        """
        Gera um único cartão
        
        Args:
            cardholder_id: ID específico do portador (opcional - escolhe aleatório se None)
            modality_id: ID específico da modalidade (opcional - escolhe aleatório se None)
            
        Returns:
            Card: Um objeto cartão novo
        """
        # Se não especificou portador, escolhe aleatoriamente
        if cardholder_id is None:
            cardholder_id = random.choice(self.cardholder_ids)
        
        # Se não especificou modalidade e tem modalidades disponíveis, escolhe uma
        if modality_id is None and self.modality_ids:
            modality_id = random.choice(self.modality_ids)
        
        # Cria e retorna o cartão
        return Card(cardholder_id, modality_id)

    def generate_card_as_dict(self, cardholder_id=None, modality_id=None):
        """
        Gera um único cartão e retorna como dicionário
        Pronto para inserir no banco de dados
        
        Args:
            cardholder_id: ID específico do portador (opcional - escolhe aleatório se None)
            modality_id: ID específico da modalidade (opcional - escolhe aleatório se None)
            
        Returns:
            Dict: Dicionário com dados do cartão
        """
        cartao = self.generate_card(cardholder_id, modality_id)
        return cartao.to_dict()

    def generate_multiple_cards(self, n_cards):
        """
        Gera vários cartões de uma vez
        
        Args:
            n_cards: Quantos cartões gerar
            
        Returns:
            List[Card]: Lista com os cartões criados
        """
        cartoes = []
        for _ in range(n_cards):
            cartao = self.generate_card()
            cartoes.append(cartao)
        return cartoes

    def generate_cards_as_dicts(self, n_cards):
        """
        Gera cartões e retorna como lista de dicionários
        Pronto para inserir no banco de dados
        
        Args:
            n_cards: Quantos cartões gerar
            
        Returns:
            List[Dict]: Lista de dicionários com dados dos cartões
        """
        cartoes = self.generate_multiple_cards(n_cards)
        return [cartao.to_dict() for cartao in cartoes]

    def generate_cards_for_cardholder(self, cardholder_id, n_cards=1):
        """
        Gera cartão(ões) para um portador específico
        
        Args:
            cardholder_id: ID do portador específico
            n_cards: Quantos cartões gerar para este portador (padrão: 1)
            
        Returns:
            List[Card] se n_cards > 1, Card se n_cards = 1
        """
        if n_cards == 1:
            return self.generate_card(cardholder_id=cardholder_id)
        
        cartoes = []
        for _ in range(n_cards):
            cartao = self.generate_card(cardholder_id=cardholder_id)
            cartoes.append(cartao)
        return cartoes


# Exemplo de como usar as classes
if __name__ == "__main__":
    # Dados de exemplo
    portadores = ["PESSOA001", "PESSOA002", "PESSOA003", "PESSOA004"]
    modalidades = ["ALIMENTACAO", "REFEICAO", "COMBUSTIVEL"]  # Pode ser None
    
    # Cria o gerador
    gerador = CardGenerator(portadores, modalidades)
    
    print("=== GERANDO UM CARTÃO (caso mais comum) ===")
    # Gera um cartão aleatório
    cartao = gerador.generate_card()
    print(f"ID: {cartao.id}")
    print(f"Portador: {cartao.cardholder_id}")
    print(f"Hash do número: {cartao.card_number_hash[:20]}...")
    print(f"Tipo: {cartao.card_type}")
    print(f"Status: {cartao.status}")
    print(f"Validade: {cartao.expiration_date}")
    
    # Gera um cartão direto como dicionário (pronto para banco)
    print("\n=== Um cartão direto para o banco ===")
    cartao_dict = gerador.generate_card_as_dict()
    print(f"ID: {cartao_dict['id']}")
    print(f"Hash: {cartao_dict['card_number_hash'][:20]}...")
    print(f"Emissão: {cartao_dict['issue_date']}")
    
    # Gera cartão para portador específico
    print("\n=== Cartão para portador específico ===")
    cartao2 = gerador.generate_card(cardholder_id="PESSOA001")
    print(f"Portador: {cartao2.cardholder_id}")
    
    # Cartão específico direto como dict
    cartao_dict2 = gerador.generate_card_as_dict(cardholder_id="PESSOA002", modality_id="ALIMENTACAO")
    print(f"Portador específico: {cartao_dict2['cardholder_id']}")
    print(f"Modalidade específica: {cartao_dict2['modality_id']}")
    
    print("\n=== GERANDO MÚLTIPLOS CARTÕES ===")
    # Gera vários cartões
    cartoes = gerador.generate_multiple_cards(3)
    for i, cartao in enumerate(cartoes, 1):
        print(f"Cartão {i}: {cartao.cardholder_id} - {cartao.card_type} - {cartao.status}")
    
    # Gera vários cartões para um portador específico
    print("\n=== Vários cartões para um portador ===")
    cartoes_pessoa = gerador.generate_cards_for_cardholder("PESSOA003", n_cards=2)
    for i, cartao in enumerate(cartoes_pessoa, 1):
        print(f"Cartão {i} da PESSOA003: {cartao.card_type} - {cartao.status}")
    
    # Gera como dicionários para o banco
    print("\n=== Para inserir no banco de dados (múltiplos) ===")
    cartoes_dict = gerador.generate_cards_as_dicts(2)
    for i, cartao_dict in enumerate(cartoes_dict, 1):
        print(f"Cartão {i} - ID: {cartao_dict['id']}")
        print(f"Hash: {cartao_dict['card_number_hash'][:20]}...")
        print(f"Emissão: {cartao_dict['issue_date']}")
        print("---")