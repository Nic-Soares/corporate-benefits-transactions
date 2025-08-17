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

## 🚀 Como Executar

### Pré-requisitos
- Python 3.9+
- Docker & Docker Compose
- Git

### Instalação Rápida

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/corporate-benefits-transactions.git
cd corporate-benefits-transactions

# 2. Configure o ambiente
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 3. Instale dependências
pip install -r requirements.txt

# 4. Configure variáveis de ambiente
cp .env.example .env
# Edite o arquivo .env com suas configurações

# 5. Inicie a infraestrutura
docker-compose up -d

# 6. Execute o sistema
python main.py
```

## 🏢 Contexto de Negócio: Benefícios Corporativos no Brasil

### O que são Benefícios Corporativos?

No Brasil, empresas fornecem aos funcionários cartões de benefícios que oferecem vantagens fiscais e maior qualidade de vida:

- **💰 Vale Refeição (VR)**: Refeições em restaurantes, lanchonetes
- **🛒 Vale Alimentação (VA)**: Compras em supermercados, mercearias  
- **💊 Vale Farmácia**: Medicamentos e produtos farmacêuticos
- **🎁 Cartões Premium**: Benefícios multipropósito

O sistema reproduz a complexidade real do mercado, incluindo validações por MCC (Merchant Category Code) para redes bandeiradas e CNAE (Classificação Nacional de Atividades Econômicas) para redes fechadas.

## 📈 Roadmap do Projeto

### Fase 1: Fundação ✅
- [x] Modelo de dados OLTP
- [x] Infraestrutura Docker
- [x] Geradores de dados sintéticos

### Fase 2: Simulação 🚧
- [x] Lógica de autorização
- [x] Regras de negócio (MCC/CNAE)
- [ ] Cenários de fraude
- [ ] Validações de performance

### Fase 3: Analytics 📋
- [ ] Modelo OLAP (DuckDB)
- [ ] Views analíticas
- [ ] Métricas de qualidade
- [ ] Exportação Parquet

### Fase 4: Distribuição 🎯
- [ ] Dataset consolidado
- [ ] Documentação Kaggle
- [ ] Notebooks de exemplo
- [ ] Publicação pública

## 🤝 Contribuindo

Contribuições são bem-vindas! Este projeto visa se tornar um recurso valioso para a comunidade:

1. **Fork** o repositório
2. **Create** uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. **Push** para a branch (`git push origin feature/AmazingFeature`)
5. **Open** um Pull Request

## 📄 Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 👨‍💻 Autor

Desenvolvido com ❤️ para a comunidade de Data Science e Engenharia de Dados.

---

**🎯 Objetivo Final**: Transformar este trabalho em um dataset público no Kaggle, fornecendo à comunidade uma base de dados realista e abrangente para estudos sobre o mercado brasileiro de benefícios corporativos.

*"Dados de qualidade são a fundação de insights valiosos."*