import yaml
from scripts.utils.database import conectar_banco, carregar_config
from scripts.importers.municipios_importer import importar_municipios
from scripts.populators.dim_populators import (
    popular_dim_produtos,
    popular_dim_bandeiras,
    popular_dim_segmentos,
    popular_dim_cnae
)
from scripts.populators.entity_populators import popular_companies, popular_establishments
from scripts.populators.common import popular_se_vazio


def carregar_config_volumes():
    """Carrega configuração de volumes do arquivo YAML"""
    with open("config/data_volumes.yaml", "r") as file:
        return yaml.safe_load(file)


def carregar_business_rules():
    """Carrega regras de negócio do arquivo YAML"""
    with open("config/business_rules.yaml", "r") as file:
        return yaml.safe_load(file)

def populate_data():
    """Função principal que orquestra a população do banco de dados"""
    # Carrega configurações
    business_rules = carregar_business_rules()
    volumes = carregar_config_volumes()['volumes']

    # Conecta ao banco
    db_config = carregar_config()
    conn = conectar_banco(db_config)

    # Importa dados externos
    importar_municipios(conn)

    # Popula tabelas de dimensão
    _popular_dimensoes(conn, business_rules, volumes)

    # Popula tabelas de entidades
    _popular_entidades(conn, volumes)

    conn.close()


def _popular_dimensoes(conn, business_rules, volumes):
    """Popula todas as tabelas de dimensão"""

    popular_se_vazio(conn, "dim_produtos", popular_dim_produtos, business_rules)
    popular_se_vazio(conn, "dim_bandeiras", popular_dim_bandeiras, business_rules)
    popular_se_vazio(conn, "dim_segmentos", popular_dim_segmentos, volumes)
    popular_se_vazio(conn, "dim_cnae", popular_dim_cnae, volumes)


def _popular_entidades(conn, volumes):
    """Popula todas as tabelas de entidades principais"""

    popular_se_vazio(conn, "companies", popular_companies, volumes)
    popular_se_vazio(conn, "establishments", popular_establishments, volumes)


if __name__ == "__main__":
    populate_data()
