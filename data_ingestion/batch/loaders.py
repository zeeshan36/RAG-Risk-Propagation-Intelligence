"""CSV/JSON batch loaders that normalize rows into canonical models."""
import csv
import json
from pathlib import Path
from typing import List, Type, TypeVar

from pydantic import BaseModel, ValidationError

from common.exceptions import RepositoryError

T = TypeVar("T", bound=BaseModel)


def load_json(path: Path, model_cls: Type[T]) -> List[T]:
    """Load a JSON array of objects and validate as model_cls."""
    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    if not isinstance(raw, list):
        raise RepositoryError(f"Expected JSON array in {path}")
    return [_parse_record(item, model_cls) for item in raw]


def load_csv(path: Path, model_cls: Type[T]) -> List[T]:
    """Load a CSV file and validate each row as model_cls."""
    records: List[T] = []
    with open(path, "r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if None in row:
                raise RepositoryError(f"Malformed CSV row in {path}: {row}")
            records.append(_parse_record(row, model_cls))
    return records


def load_records(records: List[dict], model_cls: Type[T]) -> List[T]:
    """Validate a list of dicts as model_cls."""
    return [_parse_record(r, model_cls) for r in records]


def _parse_record(raw: dict, model_cls: Type[T]) -> T:
    cleaned = {k: v for k, v in raw.items() if v is not None and v != ""}
    try:
        return model_cls.model_validate(cleaned)
    except ValidationError as exc:
        raise RepositoryError(
            f"Failed to validate {model_cls.__name__} record: {raw}"
        ) from exc
