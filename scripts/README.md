# Scripts - Estrutura Modular

Este diretório contém scripts organizados de forma modular para facilitar a manutenção e reutilização do código.

## Estrutura

```
scripts/
├── populators/           # Populadores de dados
│   ├── __init__.py
│   ├── common.py        # Utilitários comuns
│   ├── dim_populators.py    # Populadores de tabelas de dimensão
│   └── entity_populators.py # Populadores de entidades principais
├── importers/           # Importadores de dados externos
│   ├── __init__.py
│   └── municipios_importer.py
├── queries/             # Consultas e acesso a dados
│   ├── __init__.py
│   └── data_queries.py  # Funções get_* para buscar IDs e dados
├── utils/               # Utilitários gerais
│   ├── database.py
│   └── read_shapefile.py
├── populate_data.py     # Script principal orquestrador
├── create_schema.py
├── export_parquet.py
├── test.py
└── validade_data.py
```

## Módulos

### `populators/`
Contém funções especializadas para popular diferentes tipos de tabelas:

- **`common.py`**: Funções utilitárias compartilhadas
  - `inserir_dados()`: Insere DataFrame no DuckDB
  - `verificar_tabela_vazia()`: Verifica se tabela está vazia
  - `popular_se_vazio()`: Popula apenas se tabela estiver vazia

- **`dim_populators.py`**: Populadores para tabelas de dimensão
  - `popular_dim_produtos()`
  - `popular_dim_bandeiras()`
  - `popular_dim_segmentos()`
  - `popular_dim_cnae()`

- **`entity_populators.py`**: Populadores para entidades principais
  - `popular_companies()`
  - `popular_establishments()`

### `importers/`
Contém importadores de dados externos:

- **`municipios_importer.py`**: Importa dados de municípios do shapefile
  - `importar_municipios()`: Processa e importa dados geográficos

### `queries/`
Contém funções de consulta e acesso a dados:

- **`data_queries.py`**: Funções para buscar IDs e dados do banco
  - `get_municipio_ids()`: Busca IDs de municípios
  - `get_cnae_ids()`: Busca IDs de CNAEs
  - `get_segmento_ids()`: Busca IDs de segmentos
  - `get_produto_ids()`: Busca IDs de produtos
  - `get_bandeira_ids()`: Busca IDs de bandeiras
  - `get_company_ids()`: Busca IDs de empresas
  - `get_establishment_ids()`: Busca IDs de estabelecimentos
  - `contar_registros()`: Conta registros em uma tabela
  - `verificar_tabela_possui_dados()`: Verifica se tabela tem dados

### Arquivo Principal
- **`populate_data.py`**: Orquestra todo o processo de população
  - `populate_data()`: Função principal
  - `_popular_dimensoes()`: Coordena população das dimensões
  - `_popular_entidades()`: Coordena população das entidades

## Vantagens da Estrutura Modular

1. **Separação de Responsabilidades**: Cada módulo tem uma função específica
2. **Reutilização**: Funções podem ser importadas e reutilizadas
3. **Manutenibilidade**: Código mais fácil de localizar e modificar
4. **Testabilidade**: Módulos podem ser testados independentemente
5. **Legibilidade**: Arquivo principal mais limpo e focado na orquestração

## Uso

```python
# Executar população completa
python scripts/populate_data.py

# Importar funções específicas para uso customizado
from scripts.populators.dim_populators import popular_dim_produtos
from scripts.importers.municipios_importer import importar_municipios
from scripts.queries.data_queries import get_municipio_ids, get_cnae_ids
```
