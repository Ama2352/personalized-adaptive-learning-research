"""Small, explicit boundary around the installed CAHLR/pyBKT API."""

from importlib import metadata
import platform

import numpy as np
import pandas as pd
from pyBKT.models import Model


MODEL_COLUMNS = ["user_id", "skill_name", "correct", "order_id"]


def verify_runtime() -> dict:
    version = metadata.version("pyBKT")
    if version != "1.4.3":
        raise RuntimeError(f"Expected pyBKT 1.4.3, found {version}")
    return {
        "pyBKT_version": version,
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "pandas_version": pd.__version__,
    }


def fit_skill(train_df: pd.DataFrame, skill: str, num_fits: int, seed: int) -> Model:
    if train_df.empty or set(train_df["skill_name"]) != {skill}:
        raise ValueError("train_df must contain exactly the requested skill")
    data = train_df.loc[:, MODEL_COLUMNS].copy()
    data["correct"] = data["correct"].astype("int64")
    model = Model(seed=seed, num_fits=num_fits, parallel=False)
    model.fit(data=data, forgets=False)
    if skill not in model.coef_:
        raise RuntimeError(f"pyBKT did not fit {skill}")
    for name, values in model.coef_[skill].items():
        if not np.isfinite(np.asarray(values, dtype=float)).all():
            raise FloatingPointError(f"pyBKT produced non-finite {name} parameters for {skill}")
    return model


def predict_skill(model: Model, eval_df: pd.DataFrame) -> pd.DataFrame:
    if eval_df.empty:
        return pd.DataFrame(columns=["source_row", "prediction"])
    if eval_df["source_row"].duplicated().any():
        raise ValueError("source_row must uniquely identify evaluation rows")
    skill = eval_df["skill_name"].iloc[0]
    if set(eval_df["skill_name"]) != {skill} or skill not in model.coef_:
        raise ValueError("evaluation skill must be fitted")
    data = eval_df.loc[:, MODEL_COLUMNS + ["source_row"]].copy()
    data["correct"] = data["correct"].astype("int64")
    result = model.predict(data=data)
    out = result.loc[:, ["source_row", "correct_predictions"]].rename(
        columns={"correct_predictions": "prediction"}
    )
    if not np.isfinite(out["prediction"].to_numpy(dtype=float)).all():
        raise FloatingPointError(f"pyBKT produced non-finite predictions for {skill}")
    return out.sort_values("source_row", kind="stable").reset_index(drop=True)
