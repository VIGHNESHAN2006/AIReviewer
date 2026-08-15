import pytest
from project.main import divide, calculate_average


def test_divide():
    assert divide(10, 2) == 5


def test_divide_by_zero():
    with pytest.raises(ValueError):
        divide(10, 0)


def test_average():
    assert calculate_average(100, 10) == 10


def test_average_with_zero_count():
    with pytest.raises(ValueError):
        calculate_average(100, 0)