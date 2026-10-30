from pathlib import Path
from typing import Any

import polars as pl


def save_df_to_parquet(
    df: pl.DataFrame,
    file_path: str | Path,
    compression: str = "snappy",
    compression_level: int | None = None,
    statistics: bool = True,
    row_group_size: int | None = None,
    data_page_size: int | None = None,
    use_pyarrow: bool = False,
    pyarrow_options: dict[str, Any] | None = None,
    **kwargs,
) -> None:
    """
    Save a Polars DataFrame as Parquet.

    Args:
        df: DataFrame to save
        file_path: Destination file; parent folders are created
        compression: "snappy", "gzip", "brotli", "lz4" or "zstd"
        compression_level: Algorithm-specific compression level
        statistics: Write column statistics
        row_group_size: Rows per row group
        data_page_size: Data page size in bytes
        use_pyarrow: Use PyArrow instead of the native writer
        pyarrow_options: PyArrow-specific options
        **kwargs: Passed on to write_parquet()

    Examples:
        # Basic
        save_df_to_parquet(df, "data.parquet")

        # Specific compression
        save_df_to_parquet(df, "data.parquet", compression="zstd", compression_level=3)

        # Large files
        save_df_to_parquet(df, "data.parquet", row_group_size=50000, data_page_size=1024*1024)

        # With PyArrow
        save_df_to_parquet(df, "data.parquet", use_pyarrow=True,
                          pyarrow_options={"coerce_timestamps": "ms"})
    """

    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    write_args = {"compression": compression, "statistics": statistics, **kwargs}
    if compression_level is not None:
        write_args["compression_level"] = compression_level

    if row_group_size is not None:
        write_args["row_group_size"] = row_group_size

    if data_page_size is not None:
        write_args["data_page_size"] = data_page_size

    if use_pyarrow and pyarrow_options:
        write_args.update(pyarrow_options)

    try:
        if use_pyarrow:
            df.write_parquet(file_path, use_pyarrow=True, **write_args)
        else:
            df.write_parquet(file_path, **write_args)

        print(f"✅ DataFrame saved to: {file_path}")
        print(f"   Rows: {len(df):,}")
        print(f"   Columns: {len(df.columns)}")
        print(f"   Size: {file_path.stat().st_size / 1024 / 1024:.2f} MB")

    except Exception as e:
        print(f"❌ Failed to save {file_path}: {e}")
        raise


def save_multiple_dfs_to_parquet(
    dataframes: dict[str, pl.DataFrame], base_path: str | Path, **parquet_options
) -> None:
    """
    Save several DataFrames as Parquet files, one per name.

    Args:
        dataframes: {file_name: dataframe}
        base_path: Destination folder
        **parquet_options: Passed on to save_df_to_parquet()

    Example:
        dfs = {
            "products": products_df,
            "companies": companies_df,
            "cards": cards_df
        }
        save_multiple_dfs_to_parquet(dfs, "data/master/", compression="zstd")
    """
    base_path = Path(base_path)

    print(f"💾 Saving {len(dataframes)} DataFrames to {base_path}")

    for name, df in dataframes.items():
        file_path = base_path / f"{name}.parquet"
        save_df_to_parquet(df, file_path, **parquet_options)

    print(f"\n✅ All DataFrames saved to {base_path}")
