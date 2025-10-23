from datetime import datetime, date
import random
import uuid


class Company:
    """
    Classe que representa uma empresa
    Versão simplificada com comentários explicativos
    """
    
    def __init__(self, segment_id, municipality_id, parent_company_id=None):
        """
        Construtor da classe Company
        
        Args:
            segment_id: ID do segmento da empresa (ex: tecnologia, alimentação)
            municipality_id: ID do município onde a empresa está localizada
            parent_company_id: ID da empresa matriz (opcional, para filiais)
        """
        # Gera um ID único para a empresa
        self.company_id = str(uuid.uuid4())
        
        # Define se é filial de outra empresa
        self.parent_company_id = parent_company_id
        
        # Gera nome da empresa
        self.name = self._gerar_nome_empresa()
        
        # Gera CNPJ da empresa
        self.cnpj = self._gerar_cnpj()
        
        # Define tipo da empresa (privada ou pública)
        self.company_type = random.choice(['Privada', 'Publica'])
        
        # Define segmento de atuação
        self.segment_id = segment_id
        
        # Define localização (município)
        self.municipality_id = municipality_id
        
        # Define data de cadastro no contrato
        self.contract_registration_date = self._gerar_data_contrato()
        
        # Define quando foi criado o registro
        self.created_at = datetime.now()
    
    def _gerar_nome_empresa(self):
        """Gera um nome fictício para a empresa"""
        # Prefixos comuns de empresas
        prefixos = [
            "Tech", "Inova", "Global", "Smart", "Digital", "Pro", "Master",
            "Premium", "Alpha", "Beta", "Mega", "Super", "Ultra", "Nova"
        ]
        
        # Sufixos comuns de empresas
        sufixos = [
            "Solutions", "Systems", "Corp", "Group", "Company", "Enterprises",
            "Industries", "Services", "Technologies", "Innovation", "Labs"
        ]
        
        # Tradução para português
        sufixos_pt = [
            "Soluções", "Sistemas", "Corporação", "Grupo", "Empresa", "Serviços",
            "Tecnologias", "Inovação", "Indústrias", "Consultoria", "Ltda"
        ]
        
        prefixo = random.choice(prefixos)
        sufixo = random.choice(sufixos + sufixos_pt)
        
        return f"{prefixo} {sufixo}"
    
    def _gerar_cnpj(self):
        """Gera um CNPJ fictício no formato XX.XXX.XXX/XXXX-XX"""
        # Gera 14 dígitos aleatórios
        numeros = [str(random.randint(0, 9)) for _ in range(14)]
        
        # Formata no padrão do CNPJ
        return f"{numeros[0]}{numeros[1]}.{numeros[2]}{numeros[3]}{numeros[4]}.{numeros[5]}{numeros[6]}{numeros[7]}/{numeros[8]}{numeros[9]}{numeros[10]}{numeros[11]}-{numeros[12]}{numeros[13]}"
    
    def _gerar_data_contrato(self):
        """Gera uma data de contrato entre 2020 e 2024"""
        ano = random.randint(2020, 2024)
        mes = random.randint(1, 12)
        dia = random.randint(1, 28)  # Uso 28 para evitar problemas com fevereiro
        return date(ano, mes, dia)
    
    def to_dict(self):
        """
        Converte a empresa para um dicionário
        Útil para salvar no banco de dados ou converter para DataFrame
        """
        return {
            "company_id": self.company_id,
            "parent_company_id": self.parent_company_id,
            "name": self.name,
            "cnpj": self.cnpj,
            "company_type": self.company_type,
            "segment_id": self.segment_id,
            "municipality_id": self.municipality_id,
            "contract_registration_date": self.contract_registration_date,
            "created_at": self.created_at
        }
    
    def __str__(self):
        """Representação em string da empresa para impressão"""
        tipo_empresa = "Filial" if self.parent_company_id else "Matriz"
        return f"{self.name} ({self.company_type}) - {tipo_empresa}"


class SimpleCompanyGenerator:
    """
    Gerador simples de empresas
    """
    
    def __init__(self, segment_ids, municipality_ids):
        """
        Construtor do gerador de empresas
        
        Args:
            segment_ids: Lista com IDs dos segmentos disponíveis
            municipality_ids: Lista com IDs dos municípios disponíveis
        """
        # Armazena as listas de IDs disponíveis
        self.segment_ids = segment_ids
        self.municipality_ids = municipality_ids
        
        # Lista para armazenar empresas já criadas (para criar filiais)
        self.empresas_criadas = []
    
    def gerar_uma_empresa(self, chance_filial=0.2):
        """
        Gera uma única empresa
        
        Args:
            chance_filial: Probabilidade de criar uma filial (0.0 a 1.0)
            
        Returns:
            Company: Um objeto empresa novo
        """
        # Escolhe aleatoriamente um segmento e município
        segment_id = random.choice(self.segment_ids)
        municipality_id = random.choice(self.municipality_ids)
        
        # Decide se será filial (só se já existem empresas)
        parent_company_id = None
        if self.empresas_criadas and random.random() < chance_filial:
            # Escolhe uma empresa existente como matriz
            empresa_matriz = random.choice(self.empresas_criadas)
            parent_company_id = empresa_matriz.company_id
        
        # Cria a nova empresa
        empresa = Company(segment_id, municipality_id, parent_company_id)
        
        # Adiciona à lista de empresas criadas
        self.empresas_criadas.append(empresa)
        
        return empresa
    
    def gerar_varias_empresas(self, quantidade, chance_filial=0.2):
        """
        Gera várias empresas de uma vez
        
        Args:
            quantidade: Quantas empresas gerar
            chance_filial: Probabilidade de criar filiais
            
        Returns:
            list: Lista com objetos Company
        """
        empresas = []
        for _ in range(quantidade):
            empresa = self.gerar_uma_empresa(chance_filial)
            empresas.append(empresa)
        return empresas
    
    def gerar_empresas_como_lista_dict(self, quantidade, chance_filial=0.2):
        """
        Gera empresas e retorna como lista de dicionários
        Útil para converter para DataFrame depois
        
        Args:
            quantidade: Quantas empresas gerar
            chance_filial: Probabilidade de criar filiais
            
        Returns:
            list: Lista de dicionários com dados das empresas
        """
        empresas = self.gerar_varias_empresas(quantidade, chance_filial)
        return [empresa.to_dict() for empresa in empresas]
    
    def limpar_empresas_criadas(self):
        """Limpa a lista de empresas criadas (útil para recomeçar)"""
        self.empresas_criadas = []


# Exemplo de como usar
if __name__ == "__main__":
    # Dados de exemplo
    segmentos = ["TECH001", "FOOD001", "RETAIL001", "FINANCE001"]
    municipios = ["SP001", "RJ001", "MG001", "RS001"]
    
    # Cria o gerador
    gerador = SimpleCompanyGenerator(segmentos, municipios)
    
    # Gera uma empresa
    print("=== Uma empresa ===")
    empresa = gerador.gerar_uma_empresa()
    print(empresa)
    print(f"Detalhes: {empresa.to_dict()}")
    
    # Gera várias empresas (algumas podem ser filiais)
    print("\n=== Várias empresas ===")
    empresas = gerador.gerar_varias_empresas(5, chance_filial=0.3)
    for i, empresa in enumerate(empresas, 1):
        print(f"Empresa {i}: {empresa}")
    
    # Gera como lista de dicionários
    print("\n=== Como lista de dicionários ===")
    gerador.limpar_empresas_criadas()  # Limpa para recomeçar
    empresas_dict = gerador.gerar_empresas_como_lista_dict(3, chance_filial=0.5)
    for empresa_dict in empresas_dict:
        print(f"Nome: {empresa_dict['name']} - CNPJ: {empresa_dict['cnpj']}")