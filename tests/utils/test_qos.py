import pandas as pd
from deepdiff import DeepDiff

from depc.utils.qos import OperationTypes
from depc.utils.qos import _compute_qos

DEFAULT_ARGS = {"agg_op": OperationTypes.AND, "auto_fill": True, "float_decimal": 3}


def test_compute_qos_empty():
    expected = {
        "qos": None,
        "bools_dps": {},
        "periods": {"ok": 0, "ko": 0},
    }
    actual = _compute_qos([], start=0, end=1, **DEFAULT_ARGS)
    assert DeepDiff(expected, actual, ignore_order=True) == {}


def test_compute_qos_good_values():
    data = pd.Series({1595980800: True, 1595994060: True})
    expected = {
        "bools_dps": {1595980800: True, 1596067199: True},
        "periods": {"ko": 0, "ok": 86399},
        "qos": 100.0,
    }
    actual = _compute_qos([data], start=1595980800, end=1596067199, **DEFAULT_ARGS)
    assert DeepDiff(expected, actual, ignore_order=True) == {}


def test_compute_qos_one_minute_downtime():
    data = pd.Series({1595980800: True, 1595994000: False, 1595994060: True})
    expected = {
        "bools_dps": {
            1595980800: True,
            1595994000: False,
            1595994060: True,
            1596067199: True,
        },
        "periods": {"ko": 60, "ok": 86339},
        "qos": 99.931,
    }
    actual = _compute_qos([data], start=1595980800, end=1596067199, **DEFAULT_ARGS)
    assert DeepDiff(expected, actual, ignore_order=True) == {}


def test_compute_qos_two_series():
    s1 = pd.Series({1595980800: True, 1595994000: False, 1595994060: True})
    s2 = pd.Series({1595980800: True, 1595994001: True, 1595994060: True})
    expected = {
        "bools_dps": {
            1595980800: True,
            1595994000: False,
            1595994060: True,
            1596067199: True,
        },
        "periods": {"ko": 60, "ok": 86339},
        "qos": 99.931,
    }
    actual = _compute_qos([s1, s2], start=1595980800, end=1596067199, **DEFAULT_ARGS)
    assert DeepDiff(expected, actual, ignore_order=True) == {}


def test_compute_qos_two_series_bad_values():
    s1 = pd.Series({1595980800: True, 1595994000: False, 1595994060: True})
    s2 = pd.Series({1595980800: False, 1595994000: False, 1595994060: False})
    expected = {
        "bools_dps": {1595980800: False, 1596067199: False},
        "periods": {"ko": 86399, "ok": 0},
        "qos": 0.0,
    }
    actual = _compute_qos([s1, s2], start=1595980800, end=1596067199, **DEFAULT_ARGS)
    assert DeepDiff(expected, actual, ignore_order=True) == {}


def test_compute_qos_two_series_good_values():
    s1 = pd.Series({1595980800: True, 1595994000: True, 1595994060: True})
    s2 = pd.Series({1595980800: True, 1595994000: True, 1595994060: True})
    expected = {
        "bools_dps": {1595980800: True, 1596067199: True},
        "periods": {"ko": 0, "ok": 86399},
        "qos": 100.0,
    }
    actual = _compute_qos([s1, s2], start=1595980800, end=1596067199, **DEFAULT_ARGS)
    assert DeepDiff(expected, actual, ignore_order=True) == {}
