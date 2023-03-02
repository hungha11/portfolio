import numpy as np
import pandas as pd
from empyrical import (
    sharpe_ratio,
    calmar_ratio,
    sortino_ratio,
    max_drawdown,
    downside_risk,
    annual_return,
    annual_volatility,
    roll_beta,
)



def calc_sharpe_by_year(data: pd.DataFrame, suffix: str = None) -> dict:
    """Sharpe ratio for each year in dataframe

    Args:
        data (pd.DataFrame): dataframe containing captured returns, indexed by date

    Returns:
        dict: dictionary of Sharpe by year
    """
    if not suffix:
        suffix = ""

    data = data.copy()
    data["year"] = data.index.year

    # mean of year is year for same date
    sharpes = (
        data.dropna()[["year", "captured_returns"]]
        .groupby(level=0)
        .mean()
        .groupby("year")
        .apply(lambda y: sharpe_ratio(y["captured_returns"]))
    )

    sharpes.index = "sharpe_ratio_" + sharpes.index.map(int).map(str) + suffix

    return sharpes.to_dict()


def calc_performance_metrics_subset(srs: pd.Series, metric_suffix="") -> dict:
    """Performance metrics for evaluating strategy

    Args:
        captured_returns (pd.Series): series containing captured returns, aggregated by date

    Returns:
        dict: dictionary of performance metrics
    """
    return {
        f"annual_return{metric_suffix}": annual_return(srs),
        f"annual_volatility{metric_suffix}": annual_volatility(srs),
        f"downside_risk{metric_suffix}": downside_risk(srs),
        f"max_drawdown{metric_suffix}": -max_drawdown(srs),
    }