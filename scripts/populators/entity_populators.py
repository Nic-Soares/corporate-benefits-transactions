import pandas as pd
import random
from faker import Faker
from scripts.queries.data_queries import get_municipio_ids, get_cnae_ids
from .common import inserir_dados

fake = Faker('pt_BR')




def popular_companies(conn, volumes):
    """Popula a tabela companies com dados sintéticos"""
    print("Populando companies")

    municipio_ids = get_municipio_ids(conn)

    empresas = []

    for i in range(volumes['empresas']):
        empresa = {
            'company_id': f"COMP_{i+1:06d}",
            'parent_company_id': None,
            'codigo_cliente': f"CLI_{i+1:06d}",
            'razao_social': fake.company(),
            'cnpj': fake.cnpj(),
            'tipo_empresa': random.choice(['Matriz', 'Filial']),
            'segmento_id': f"SEG_{random.randint(1, 10):03d}",
            'municipio_id': random.choice(municipio_ids),
            'data_cadastro_contrato': fake.date_between(start_date='-2y', end_date='today'),
            'forma_recebimento': random.choice(['TED', 'DOC', 'PIX']),
            'created_at': pd.Timestamp.now()
        }
        empresas.append(empresa)

    df = pd.DataFrame(empresas)
    inserir_dados(conn, df, 'companies')
    print(f"{len(empresas)} empresas inseridos")


def popular_establishments(conn, volumes):
    """Popula a tabela establishments com dados sintéticos"""
    print("🏪 Populando establishments...")

    municipio_ids = get_municipio_ids(conn)
    cnae_ids = get_cnae_ids(conn)

    estabelecimentos = []
    for i in range(volumes['estabelecimentos']):
        estabelecimento = {
            'establishment_id': f"EST_{i+1:06d}",
            'cnpj': fake.cnpj(),
            'nome_empresarial': fake.company(),
            'nome_fantasia': fake.company_suffix(),  # Nome mais curto
            'cnae_principal_id': random.choice(cnae_ids),
            'natureza_juridica': random.choice(['LTDA', 'EIRELI', 'SA']),
            'porte_empresa': random.choice(['EPP', 'ME', 'GRANDE']),
            'municipio_id': random.choice(municipio_ids),
            'cep': fake.postcode(),
            'logradouro': fake.street_name(),
            'numero': fake.building_number(),
            'complemento': random.choice([None, f"Apto {random.randint(1, 999)}", f"Sala {random.randint(1, 50)}", "Fundos"]),
            'bairro': fake.neighborhood(),
            'email': fake.email(),
            'telefone': fake.phone_number(),
            'situacao_cadastral': random.choice(['ATIVA', 'SUSPENSA', 'BAIXADA']),
            'data_situacao_cadastral': fake.date_between(start_date='-5y', end_date='today'),
            'motivo_situacao': random.choice(['Normal', 'Mudança de endereço', 'Outros']),
            'data_abertura': fake.date_between(start_date='-10y', end_date='today'),
            'created_at': pd.Timestamp.now()
        }
        estabelecimentos.append(estabelecimento)

    df = pd.DataFrame(estabelecimentos)
    inserir_dados(conn, df, 'establishments')
    print(f"{len(estabelecimentos)} estabelecimentos inseridos")