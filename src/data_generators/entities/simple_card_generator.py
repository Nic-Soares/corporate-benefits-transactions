import random
import uuid
from datetime import date, datetime


class Card:
    """
    Classe que representa um cartão corporativo
    Versão simplificada com comentários explicativos
    """

    def __init__(self, cardholder_id, modality_id):
        """
        Construtor da classe Card

        Args:
            cardholder_id: ID do portador do cartão
            modality_id: ID da modalidade do cartão (alimentação, refeição, etc.)
        """
        # Gera um ID único para o cartão
        self.card_id = str(uuid.uuid4())

        # Define quem é o dono do cartão
        self.cardholder_id = cardholder_id

        # Define qual modalidade (tipo) de cartão
        self.modality_id = modality_id

        # Gera número do cartão no formato XXXX XXXX XXXX XXXX
        self.card_number = self._gerar_numero_cartao()

        # Gera data de expiração (entre 2025 e 2029)
        self.expiration_date = self._gerar_data_expiracao()

        # Gera código CVV de 3 dígitos
        self.cvv = self._gerar_cvv()

        # Define tipo do cartão (crédito ou débito)
        self.card_type = random.choice(["credit", "debit"])

        # Define status do cartão
        self.status = random.choice(["active", "inactive", "blocked"])

        # Define quando o cartão foi criado
        self.created_at = datetime.now()

    def _gerar_numero_cartao(self):
        """Gera um número de cartão no formato XXXX XXXX XXXX XXXX"""
        # Gera 16 números aleatórios
        numeros = [str(random.randint(0, 9)) for _ in range(16)]
        # Junta em grupos de 4 com espaços
        return " ".join(
            [
                "".join(numeros[0:4]),
                "".join(numeros[4:8]),
                "".join(numeros[8:12]),
                "".join(numeros[12:16]),
            ]
        )

    def _gerar_data_expiracao(self):
        """Gera uma data de expiração aleatória entre 2025 e 2029"""
        ano = random.randint(2025, 2029)
        mes = random.randint(1, 12)
        return date(ano, mes, 1)

    def _gerar_cvv(self):
        """Gera um CVV de 3 dígitos"""
        return "".join([str(random.randint(0, 9)) for _ in range(3)])

    def to_dict(self):
        """
        Converte o cartão para um dicionário
        Útil para salvar no banco de dados ou converter para DataFrame
        """
        return {
            "card_id": self.card_id,
            "cardholder_id": self.cardholder_id,
            "modality_id": self.modality_id,
            "card_number": self.card_number,
            "expiration_date": self.expiration_date,
            "cvv": self.cvv,
            "card_type": self.card_type,
            "status": self.status,
            "created_at": self.created_at,
        }

    def __str__(self):
        """Representação em string do cartão para impressão"""
        return f"Cartão {self.card_number} - {self.card_type} - {self.status}"


class SimpleCardGenerator:
    """
    Gerador simples de cartões corporativos
    """

    def __init__(self, cardholder_ids, modality_ids):
        """
        Construtor do gerador de cartões

        Args:
            cardholder_ids: Lista com IDs dos portadores disponíveis
            modality_ids: Lista com IDs das modalidades disponíveis
        """
        # Armazena as listas de IDs disponíveis
        self.cardholder_ids = cardholder_ids
        self.modality_ids = modality_ids

    def gerar_um_cartao(self):
        """
        Gera um único cartão

        Returns:
            Card: Um objeto cartão novo
        """
        # Escolhe aleatoriamente um portador e uma modalidade
        cardholder_id = random.choice(self.cardholder_ids)
        modality_id = random.choice(self.modality_ids)

        # Cria e retorna um novo cartão
        return Card(cardholder_id, modality_id)

    def gerar_varios_cartoes(self, quantidade):
        """
        Gera vários cartões de uma vez

        Args:
            quantidade: Quantos cartões gerar

        Returns:
            list: Lista com objetos Card
        """
        cartoes = []
        for _ in range(quantidade):
            cartao = self.gerar_um_cartao()
            cartoes.append(cartao)
        return cartoes

    def gerar_cartoes_como_lista_dict(self, quantidade):
        """
        Gera cartões e retorna como lista de dicionários
        Útil para converter para DataFrame depois

        Args:
            quantidade: Quantos cartões gerar

        Returns:
            list: Lista de dicionários com dados dos cartões
        """
        cartoes = self.gerar_varios_cartoes(quantidade)
        return [cartao.to_dict() for cartao in cartoes]


# Exemplo de como usar
if __name__ == "__main__":
    # Dados de exemplo
    portadores = ["PORT001", "PORT002", "PORT003"]
    modalidades = ["ALIM001", "REFEICAO001", "COMBUSTIVEL001"]

    # Cria o gerador
    gerador = SimpleCardGenerator(portadores, modalidades)

    # Gera um cartão
    print("=== Um cartão ===")
    cartao = gerador.gerar_um_cartao()
    print(cartao)
    print(f"Detalhes: {cartao.to_dict()}")

    # Gera vários cartões
    print("\n=== Vários cartões ===")
    cartoes = gerador.gerar_varios_cartoes(3)
    for i, cartao in enumerate(cartoes, 1):
        print(f"Cartão {i}: {cartao}")

    # Gera como lista de dicionários
    print("\n=== Como lista de dicionários ===")
    cartoes_dict = gerador.gerar_cartoes_como_lista_dict(2)
    for cartao_dict in cartoes_dict:
        print(cartao_dict)
