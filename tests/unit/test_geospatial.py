"""Tests for geospatial mapper adapters."""
import pytest

from data_ingestion.mappers.geospatial import NoOpGeoMapper, ShapelyGeoMapper


def test_no_op_mapper_returns_false():
    mapper = NoOpGeoMapper()
    assert mapper.point_in_circle(0.0, 0.0, 0.0, 0.0, 10.0) is False
    assert mapper.haversine_km(0.0, 0.0, 1.0, 1.0) == 0.0


def test_shapely_mapper_point_in_circle():
    try:
        import shapely  # noqa: F401
    except ImportError:
        pytest.skip("shapely not installed")
    mapper = ShapelyGeoMapper()
    assert mapper.point_in_circle(0.0, 0.0, 0.0, 0.0, 1.0) is True
    assert mapper.point_in_circle(None, None, 0.0, 0.0, 1.0) is False
    assert mapper.haversine_km(0.0, 0.0, 1.0, 0.0) > 0


def test_shapely_mapper_requires_dependency():
    try:
        import shapely  # noqa: F401
    except ImportError:
        with pytest.raises(ImportError):
            ShapelyGeoMapper()
