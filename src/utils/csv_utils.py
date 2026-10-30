from pathlib import Path

import polars as pl


def save_df_to_csv(
    df: pl.DataFrame,
    file_path: str | Path,
    separator: str = ",",
    include_header: bool = True,
    quote_char: str = '"',
    batch_size: int = 1024,
    datetime_format: str = "%Y-%m-%d %H:%M:%S",
    date_format: str = "%Y-%m-%d",
    time_format: str = "%H:%M:%S",
    float_precision: int = 6,
    null_value: str = "",
) -> None:
    """
    Save a Polars DataFrame as CSV with ISO formats.

    Args:
        df: DataFrame to save
        file_path: Destination file; parent folders are created
        separator: Field separator (comma by default)
        include_header: Write the header row
        quote_char: Quote character
        batch_size: Rows written per batch
        datetime_format: ISO 8601 format for datetimes
        date_format: ISO 8601 format for dates
        time_format: ISO 8601 format for times
        float_precision: Decimal places for floats
        null_value: How NULL is written
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
        null_value=null_value,
    )
