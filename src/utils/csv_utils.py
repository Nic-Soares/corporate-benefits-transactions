import polars as pl
from pathlib import Path
from typing import Union


def save_df_to_csv(
    df: pl.DataFrame,
    file_path: Union[str, Path],
    separator: str = ",",
    include_header: bool = True,
    quote_char: str = '"',
    batch_size: int = 1024,
    datetime_format: str = "%Y-%m-%d %H:%M:%S",
    date_format: str = "%Y-%m-%d",
    time_format: str = "%H:%M:%S",
    float_precision: int = 6,
    null_value: str = ""
) -> None:
    """
    Salva um DataFrame Polars em formato CSV seguindo padrões ISO.
    
    Args:
        df: DataFrame Polars para salvar
        file_path: Caminho do arquivo
        separator: Separador de campos (padrão ISO: vírgula)
        include_header: Incluir cabeçalho
        quote_char: Caractere de aspas
        batch_size: Tamanho do batch para escrita
        datetime_format: Formato ISO 8601 para datetime
        date_format: Formato ISO 8601 para date
        time_format: Formato ISO 8601 para time
        float_precision: Precisão para números decimais
        null_value: Valor para representar NULL
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.write_csv(
        file_path,
        separator=separator,
        include_header=include_header,
        quote_char=quote_char,
        batch_size=batch_size,
        datetime_format=datetime_format,
        date_format=date_format,
        time_format=time_format,
        float_precision=float_precision,
        null_value=null_value
    )
