import polars as pl
from typing import List
from typing_extensions import TypedDict

class SegmentTypes(TypedDict):
  id: str
  name: str
  category: str

class PrePopulatedReference(TypedDict):
  segments: List[SegmentTypes]

def load_segments(pre_populate_reference: PrePopulatedReference) -> pl.DataFrame:
    """Load segments DataFrame from business rules"""
    segments = [
        {
            'id': segment['id'],
            'name': segment['name'],
            'category': segment['category'],
            'active': True
        }
        for segment in pre_populate_reference['segments']
    ]

    return pl.DataFrame(segments).with_columns([
        pl.col('id').cast(pl.Utf8),
        pl.col('name').cast(pl.Categorical),
        pl.col('category').cast(pl.Categorical),
        pl.col('active').cast(pl.Boolean)
    ])
