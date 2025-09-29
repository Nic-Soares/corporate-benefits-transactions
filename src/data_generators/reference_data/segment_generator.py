import polars as pl
from datetime import datetime


def generate_segments(config_files_updated):
    """Generate segments DataFrame from business rules"""
    segments_list = config_files_updated['segments']
    segments = pl.DataFrame(segments_list)
    segments = segments.with_columns([
        pl.lit(datetime.now()).alias('created_at'),
        pl.col('name').cast(pl.Categorical),
        pl.col('category').cast(pl.Categorical)
    ])
    return segments
