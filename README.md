# Sistema Central de Transações de Benefícios Corporativos 🍽️💳

## 📋 Visão Geral

Este projeto implementa uma **base de dados central** para gerenciar e processar transações de cartões de benefícios corporativos, como Vale Refeição (VR), Vale Alimentação (VA) e outros produtos Premium. O sistema simula o fluxo completo de uma transação financeira, desde a tentativa de compra até a aprovação final, garantindo integridade e rastreabilidade completa dos dados.

### 🎯 Objetivo Principal

Desenvolver um ecossistema de dados robusto que reproduza fielmente o comportamento do mercado brasileiro de benefícios corporativos, preparando um dataset consolidado para análise avançada que será disponibilizado publicamente no Kaggle em breve.

## 🏗️ Arquitetura do Sistema

### Modelo de Dados (Backend)

O projeto implementa um modelo de banco de dados **OLTP (Online Transaction Processing)** robusto e bem-normalizado, otimizado para operações diárias de alta frequência:

- **Tabelas de Apoio**: Produtos, empresas, estabelecimentos, modalidades transacionais
- **Tabelas Principais**: Transações, histórico de saldos, autorizações
- **Integridade Referencial**: Chaves primárias compostas e estrangeiras
- **Auditabilidade**: Campos `created_at` e `updated_at` em todas as entidades

### Infraestrutura Híbrida

**Arquitetura Moderna e Flexível:**
- 🐳 **Docker**: Ambiente isolado e replicável
- 🐘 **PostgreSQL**: Base transacional (OLTP) - confiabilidade e robustez
- 🦆 **DuckDB**: Base analítica (OLAP) - performance em consultas complexas
- 📊 **Parquet**: Formato final para distribuição

### Lógica de Negócio

**Complexidade Real do Mercado:**
- **Redes Bandeiradas**: Autorização baseada em MCC (Merchant Category Code)
- **Redes Fechadas**: Autorização baseada em CNAE (Classificação Nacional de Atividades Econômicas)
- **Multi-adquirentes**: Cielo, Rede, Stone, GetNet
- **Validações de Saldo**: Controle em tempo real
- **Cenários de Fraude**: Simulação de tentativas suspeitas

## 🗂️ Estrutura do Projeto

```
corporate-benefits-transactions/
├── 📁 src/                    # Código-fonte principal
│   ├── 🔧 generators/         # Geradores de dados sintéticos
│   ├── 📤 exporters/          # Exportação para formatos analíticos
│   ├── 🔍 extractors/         # Extração de dados externos
│   ├── ✅ validators/         # Validações de regras de negócio
│   └── 🛠️ common/            # Utilitários compartilhados
├── 💾 database/               # Modelos de dados e migrações
│   ├── 📊 oltp/              # Scripts SQL para PostgreSQL (transacional)
│   ├── 📈 olap/              # Scripts SQL para DuckDB (analítico)
│   └── 🏗️ model/             # Documentação DBML do modelo
├── 📁 data/                   # Datasets e arquivos de apoio
├── 🧪 tests/                  # Testes automatizados
├── ⚙️ config/                # Configurações do sistema
└── 🐳 docker-compose.yaml    # PostgreSQL containerizado
```

## 🚀 How to run

### Prerequisites
- [uv](https://docs.astral.sh/uv/) (installs Python 3.14 if needed)
- Docker with Docker Compose

### Setup

```bash
# 1. Install the dependencies (creates .venv from uv.lock)
uv sync

# 2. Database credentials
cp .env.example .env   # then set DB_PASSWORD

# 3. Start PostgreSQL 18
docker compose up -d
```

There is no single entrypoint yet: `src/main.py` is planned in `EP-06` of the
[roadmap](docs/planning/ROADMAP.md).

## 🏢 Contexto de Negócio: Benefícios Corporativos no Brasil

### O que são Benefícios Corporativos?

No Brasil, empresas fornecem aos funcionários cartões de benefícios que oferecem vantagens fiscais e maior qualidade de vida:

- **💰 Vale Refeição (VR)**: Refeições em restaurantes, lanchonetes
- **🛒 Vale Alimentação (VA)**: Compras em supermercados, mercearias  
- **💊 Vale Farmácia**: Medicamentos e produtos farmacêuticos
- **🎁 Cartões Premium**: Benefícios multipropósito

O sistema reproduz a complexidade real do mercado, incluindo validações por MCC (Merchant Category Code) para redes bandeiradas e CNAE (Classificação Nacional de Atividades Econômicas) para redes fechadas.

## 📈 Roadmap

The development roadmap, its status board, and the decisions behind it live in
[`docs/planning/ROADMAP.md`](docs/planning/ROADMAP.md).

## 🔀 Development workflow

- `main` = released code. `develop` = integration; every epic or story is merged into it with a `merge(<scope>): …` commit.
- One branch per epic/story, cut from `develop`: `<type>/ep-XX-<slug>` or `<type>/st-XX.Y-<slug>`, where `<type>` is the conventional-commit type (`feat`, `fix`, `chore`, `docs`, `test`, `ci`, `refactor`).
- Commits follow [Conventional Commits](https://www.conventionalcommits.org/) (`chore(deps): …`, `docs(roadmap): …`).
- Lint and format with `uv run ruff check` and `uv run ruff format`.

## 📄 Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 👨‍💻 Autor

Desenvolvido com ❤️ para a comunidade de Data Science e Engenharia de Dados.

---

**🎯 Objetivo Final**: Transformar este trabalho em um dataset público no Kaggle, fornecendo à comunidade uma base de dados realista e abrangente para estudos sobre o mercado brasileiro de benefícios corporativos.

*"Dados de qualidade são a fundação de insights valiosos."*