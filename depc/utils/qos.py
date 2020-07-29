import logging
from datetime import datetime

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class OperationTypes:
    @staticmethod
    def AND(df_timeseries):
        return df_timeseries.all(axis=1)

    @staticmethod
    def OR(df_timeseries):
        return df_timeseries.any(axis=1)

    @staticmethod
    def ATLEAST(n):
        def op(df_timeseries):
            return df_timeseries.sum(axis=1) >= n

        return op

    @staticmethod
    def RATIO(r):
        def op(df_timeseries):
            return (df_timeseries.sum(axis=1) / df_timeseries.count(axis=1)) >= r

        return op


class AggregationTypes:
    @staticmethod
    def AVERAGE(values):
        return np.average(values)

    @staticmethod
    def MIN(values):
        return min(values)

    @staticmethod
    def MAX(values):
        return max(values)


def compute_qos_from_bools(
    booleans, start=None, end=None, agg_op=OperationTypes.AND, auto_fill=True
):
    from flask import current_app as app
    float_decimal = app.config.get("FLOAT_DECIMAL", 3)

    return _compute_qos(booleans, start, end, agg_op, auto_fill, float_decimal)


def _compute_qos(booleans, start, end, agg_op, auto_fill, float_decimal):
    if not booleans:
        return {"qos": None, "bools_dps": {}, "periods": {"ok": 0, "ko": 0}}

    # Create the DataFrame
    merged_ts = pd.DataFrame(
        {"TS_{}".format(i + 1): ts for i, ts in enumerate(booleans)}
    )

    if auto_fill:
        if start or end:
            # Ensure the QOS is computed between the start and the end specified by the user
            idx = merged_ts.index.tolist()
            if start:
                idx.insert(0, start)
            if end:
                idx.append(end)

            # Using a Set to ensure there is no redundant values
            s = sorted(set(idx))

            merged_ts = merged_ts.reindex(s)

        # Replacing NaN values created during the merge and/or reindex process
        merged_ts = merged_ts.fillna(method="ffill").fillna(method="bfill")
    else:
        s = sorted(set(merged_ts.index.tolist()))
        merged_ts = merged_ts.reindex(s)

    # Apply an aggregation between all series
    merged_ts["Results"] = agg_op(merged_ts)

    # If we just have 1 timestamp,
    # the QOS is this value
    if merged_ts.Results.size == 1:
        return 100.0 if merged_ts.Results.bool() else 0.0

    # Only keep the changes to reduce the size
    normalized_results = merged_ts.Results[
        merged_ts.Results.shift(1) != merged_ts.Results
    ].dropna()

    # Last tick has been removed in the process,
    # so append it again by copying last state
    normalized_results = normalized_results.append(merged_ts.Results[-1:])

    # Add the datetime column
    dates_results = pd.DataFrame(
        {
            "Dates": [
                datetime.fromtimestamp(float(timestamp_string))
                for timestamp_string in normalized_results.index.values
            ],
            "Results": normalized_results,
        }
    )

    # Compute the duration of a change in new column
    dates_results["Periods"] = dates_results.Dates - dates_results.shift(1).Dates

    # shift back to correct position (not required, 0 and 1 will just be inverted)
    dates_results["Periods"] = dates_results["Periods"].shift(-1)

    # Sum the periods
    grouped_states = dates_results.groupby(["Results"]).sum()

    # Handle the case where there is only false or true ticks
    periods_false = pd.Timedelta(0)
    if False in grouped_states.index.tolist():
        periods_false = grouped_states.loc[False].Periods

    periods_true = pd.Timedelta(0)
    if True in grouped_states.index.tolist():
        periods_true = grouped_states.loc[True].Periods

    try:
        qos = periods_true / (periods_false + periods_true)
        qos = round(qos * 100, float_decimal)
    except ZeroDivisionError:
        logger.warning(
            "Catching a division by zero (ZeroDivisionError) during the Pandas compute (periods_"
            "true={}, periods_false={})".format(periods_true, periods_false)
        )
        qos = None

    return {
        "qos": qos,
        "bools_dps": normalized_results.to_dict(),
        "periods": {"ok": periods_true.seconds, "ko": periods_false.seconds},
    }


def check_enable_auto_fill(*ids):
    """
    Check if one or multiple IDs are blacklisted for the regular QoS computing method
    :param ids: the IDs (UUID v4) to check
    :return: False if one of the ID is in the list specified with EXCLUDE_FROM_AUTO_FILL
    """
    from flask import current_app as app

    excluded_ids = app.config.get("EXCLUDE_FROM_AUTO_FILL")
    if len(excluded_ids) == 0:
        return True
    return all([_id not in excluded_ids for _id in ids])
