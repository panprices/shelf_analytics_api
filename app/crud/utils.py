from typing import List

from sqlalchemy.engine import Row


def convert_rows_to_dicts(rows: List[Row]):
    # As suggested here: https://stackoverflow.com/a/72126705/6760346
    return [dict(r._mapping) for r in rows]
