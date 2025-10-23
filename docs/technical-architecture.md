# Technical Architecture

## Database Layer
- **OLTP**: PostgreSQL (operational transactions)
- **OLAP**: DuckDB (analytical queries)
- **Export**: Parquet files

## Data Flow
```
Config Files → Reference Data → PostgreSQL
     ↓
Transaction Simulation → Entity Creation → OLTP Tables
     ↓
ETL Process → DuckDB → Analytics
     ↓
Export → Parquet → Kaggle Dataset
```

## Key Dependencies
```python
companies → cardholders → cards → card_products
establishments → terminals
products + transaction_modalities → mcc_modalities
products + cnae_codes → cnae_products
