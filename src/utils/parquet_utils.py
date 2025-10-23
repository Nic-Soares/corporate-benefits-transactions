import polars as pl
from pathlib import Path
from typing import Optional, Dict, Any, Union


def save_df_to_parquet(
    df: pl.DataFrame,
    file_path: Union[str, Path],
    compression: str = "snappy",
    compression_level: Optional[int] = None,
    statistics: bool = True,
    row_group_size: Optional[int] = None,
    data_page_size: Optional[int] = None,
    use_pyarrow: bool = False,
    pyarrow_options: Optional[Dict[str, Any]] = None,
    **kwargs
) -> None:
    """
    Salva um DataFrame Polars em formato Parquet com todos os parâmetros possíveis.
    
    Args:
        df: DataFrame Polars para salvar
        file_path: Caminho do arquivo (str ou Path)
        compression: Algoritmo de compressão ("snappy", "gzip", "brotli", "lz4", "zstd")
        compression_level: Nível de compressão (específico do algoritmo)
        statistics: Se deve calcular estatísticas das colunas
        row_group_size: Número de linhas por grupo
        data_page_size: Tamanho da página de dados em bytes
        use_pyarrow: Se deve usar PyArrow em vez do writer nativo
        pyarrow_options: Opções específicas do PyArrow
        **kwargs: Argumentos adicionais passados para write_parquet()
    
    Examples:
        # Uso básico
        save_df_to_parquet(df, "data.parquet")
        
        # Com compressão específica
        save_df_to_parquet(df, "data.parquet", compression="zstd", compression_level=3)
        
        # Para arquivos grandes
        save_df_to_parquet(df, "data.parquet", row_group_size=50000, data_page_size=1024*1024)
        
        # Com PyArrow
        save_df_to_parquet(df, "data.parquet", use_pyarrow=True, 
                          pyarrow_options={"coerce_timestamps": "ms"})
    """
    
    # Converte para Path se necessário
    file_path = Path(file_path)
    
    # Cria diretório se não existir
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepara argumentos base
    write_args = {
        "compression": compression,
        "statistics": statistics,
        **kwargs
    }
    
    # Adiciona argumentos opcionais se fornecidos
    if compression_level is not None:
        write_args["compression_level"] = compression_level
    
    if row_group_size is not None:
        write_args["row_group_size"] = row_group_size
    
    if data_page_size is not None:
        write_args["data_page_size"] = data_page_size
    
    if use_pyarrow and pyarrow_options:
        write_args.update(pyarrow_options)
    
    # Salva o arquivo
    try:
        if use_pyarrow:
            df.write_parquet(file_path, use_pyarrow=True, **write_args)
        else:
            df.write_parquet(file_path, **write_args)
        
        print(f"✅ DataFrame salvo em: {file_path}")
        print(f"   Linhas: {len(df):,}")
        print(f"   Colunas: {len(df.columns)}")
        print(f"   Tamanho: {file_path.stat().st_size / 1024 / 1024:.2f} MB")
        
    except Exception as e:
        print(f"❌ Erro ao salvar {file_path}: {e}")
        raise


def save_multiple_dfs_to_parquet(
    dataframes: Dict[str, pl.DataFrame],
    base_path: Union[str, Path],
    **parquet_options
) -> None:
    """
    Salva múltiplos DataFrames em arquivos Parquet.
    
    Args:
        dataframes: Dicionário {nome_arquivo: dataframe}
        base_path: Diretório base onde salvar
        **parquet_options: Opções passadas para save_df_to_parquet()
    
    Example:
        dfs = {
            "products": products_df,
            "companies": companies_df,
            "cards": cards_df
        }
        save_multiple_dfs_to_parquet(dfs, "data/master/", compression="zstd")
    """
    base_path = Path(base_path)
    
    print(f"💾 Salvando {len(dataframes)} DataFrames em {base_path}")
    
    for name, df in dataframes.items():
        file_path = base_path / f"{name}.parquet"
        save_df_to_parquet(df, file_path, **parquet_options)
    
    print(f"\n✅ Todos os DataFrames salvos em {base_path}")