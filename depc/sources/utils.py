import pandas as pd

from depc.utils.qos import compute_qos_from_bools


def compute_threshold(data, start, end, threshold):
    """
    This method lowers the QOS for every values strictly
    superior to a threshold.
    """
    bool_per_ts = [pd.Series(ts["dps"]).apply(lambda x: x <= threshold) for ts in data]
    return compute_qos_from_bools(bool_per_ts, start, end)


def compute_interval(data, start, end, bottom, top):
    """
    This method lowers the QOS for every values not included
    between a bottom and a top thresholds.
    """
    bool_per_ts = [
        pd.Series(ts["dps"]).apply(lambda x: bottom <= x <= top) for ts in data
    ]
    return compute_qos_from_bools(bool_per_ts, start, end)
