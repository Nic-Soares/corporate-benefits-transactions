import pandas as pd
import random
from faker import Faker
from .common import inserir_dados

fake = Faker('pt_BR')


def popular_dim_produtos(conn, business_rules):
    """Popula a tabela dim_produtos com base nas regras de negócio"""
    print("Populando dim_produtos...")

    produtos = []
    for codigo, dados in business_rules['tipos_produto'].items():
        produto = {
            'produto_id': f"PROD_{codigo.upper()}",
            'codigo_produto': dados['codigo'],
            'nome_produto': dados['nome'],
            'categoria': codigo,
            'descricao': f"Produto de {dados['nome']}",
            'created_at': pd.Timestamp.now()
        }
        produtos.append(produto)

    df = pd.DataFrame(produtos)
    inserir_dados(conn, df, 'dim_produtos')
    print(f"{len(produtos)} produtos inseridos")


def popular_dim_bandeiras(conn, business_rules):
    """Popula a tabela dim_bandeiras com base nas regras de negócio"""
    print("Populando dim_bandeiras")

    bandeiras = []
    for codigo, dados in business_rules['bandeiras'].items():
        bandeira = {
            'bandeira_id': f"BAND_{codigo.upper()}",
            'codigo_bandeira': codigo,
            'nome_bandeira': dados['nome'],
            'created_at': pd.Timestamp.now()
        }
        bandeiras.append(bandeira)

    df = pd.DataFrame(bandeiras)
    inserir_dados(conn, df, 'dim_bandeiras')
    print(f"{len(bandeiras)} bandeiras inseridas")


def popular_dim_segmentos(conn, volumes):
    """Popula a tabela dim_segmentos com base no volume especificado."""
    print("📊 Populando dim_segmentos...")

    segmentos_base = [
        ("Tecnologia", "Tecnologia e Comunicação"),
        ("Varejo", "Comércio"),
        ("Indústria", "Manufatura e Indústria"),
        ("Serviços Financeiros", "Serviços"),
        ("Saúde", "Saúde e Bem-estar"),
        ("Educação", "Serviços"),
        ("Alimentação", "Comércio"),
        ("Construção", "Indústria e Construção"),
        ("Agronegócio", "Setor Primário"),
        ("Energia", "Infraestrutura"),
        ("Transporte e Logística", "Serviços"),
        ("Consultoria", "Serviços"),
        ("Turismo e Hotelaria", "Serviços"),
        ("Mídia e Entretenimento", "Tecnologia e Comunicação"),
        ("Setor Público", "Governo")
    ]

    segmentos = []
    for i in range(volumes['segmentos']):
        nome, categoria = random.choice(segmentos_base)
        segmentos.append({
            "segmento_id": f"SEG_{i+1:03d}",  # Segue o padrão dos outros IDs
            "segmento_nome": nome,
            "categoria_segmento": categoria,
            "created_at": pd.Timestamp.now()
        })

    df = pd.DataFrame(segmentos)
    inserir_dados(conn, df, "dim_segmentos")
    print(f"{len(segmentos)} segmentos inseridos com sucesso.")


def popular_dim_cnae(conn, volumes):
    """Popula a tabela dim_cnae com CNAEs realistas"""
    print("📋 Populando dim_cnae...")

    # CNAEs realistas para o projeto de benefícios
    cnaes_base = [
        ("5611-2", "Restaurantes e similares", "G", "56", "561", "5611"),
        ("5612-1", "Serviços ambulantes de alimentação", "G", "56", "561", "5612"),
        ("4711-3", "Comércio varejista de mercadorias em geral", "G", "47", "471", "4711"),
        ("4731-8", "Comércio varejista de combustíveis", "G", "47", "473", "4731"),
        ("4729-6", "Comércio varejista de produtos alimentícios", "G", "47", "472", "4729"),
        ("4751-2", "Comércio varejista de eletrodomésticos", "G", "47", "475", "4751"),
        ("4761-0", "Comércio varejista de livros", "G", "47", "476", "4761"),
        ("4771-7", "Comércio varejista de roupas", "G", "47", "477", "4771"),
        ("4781-4", "Comércio varejista de artigos do lar", "G", "47", "478", "4781"),
        ("4930-2", "Transporte rodoviário de passageiros", "H", "49", "493", "4930"),
        ("4923-0", "Transporte rodoviário de cargas", "H", "49", "492", "4923"),
        ("5510-8", "Hotéis e similares", "I", "55", "551", "5510"),
        ("5613-8", "Bares e outros estabelecimentos especializados em servir bebidas", "G", "56", "561", "5613"),
        ("8690-9", "Atividades de atenção à saúde humana", "Q", "86", "869", "8690"),
        ("8550-1", "Educação profissional de nível técnico", "P", "85", "855", "8550"),
        ("8011-1", "Atividades de vigilância e segurança privada", "N", "80", "801", "8011"),
        ("6201-5", "Desenvolvimento de programas de computador", "J", "62", "620", "6201"),
        ("4712-1", "Comércio varejista de mercadorias em geral com predominância de produtos alimentícios", "G", "47", "471", "4712"),
        ("4752-1", "Comércio varejista de móveis", "G", "47", "475", "4752"),
        ("4782-2", "Comércio varejista de artigos de papelaria", "G", "47", "478", "4782"),
    ]

    cnaes = []
    for i, (codigo, descricao, secao, divisao, grupo, classe) in enumerate(cnaes_base):
        cnae = {
            'cnae_id': f"CNAE_{i+1:04d}",
            'codigo_cnae': codigo,
            'descricao_cnae': descricao,
            'secao': secao,
            'divisao': divisao,
            'grupo': grupo,
            'classe': classe,
            'subclasse': None,
            'created_at': pd.Timestamp.now()
        }
        cnaes.append(cnae)

    df = pd.DataFrame(cnaes)
    inserir_dados(conn, df, 'dim_cnae')
    print(f"{len(cnaes)} cnaes inseridos")