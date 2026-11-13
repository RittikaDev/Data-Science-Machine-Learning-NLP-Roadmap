"""Leakage-safe unsupervised Solar Plant Health Index (SPHI) pipeline.

The pipeline intentionally excludes reconstructed WS2 signals from model training.
They are retained in the exported data for auditability, but using deterministic
imputations as autoencoder inputs would make reconstruction performance optimistic.
"""

from __future__ import annotations

import json
import os
import random
import warnings
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.preprocessing import RobustScaler

try:
    import tensorflow as tf
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    from tensorflow.keras.layers import Dense, Input
    from tensorflow.keras.models import Model
    from tensorflow.keras.optimizers import Adam
except ImportError as exc:
    raise ImportError(
        "TensorFlow is required. Install it with: python -m pip install tensorflow"
    ) from exc


SEED = 42
CONTAMINATION = 0.10
CALIBRATION_QUANTILE = 0.95
DATA_FILE = "Kaptai_Solar_PV_Operational_Dataset_2020.xls"
RESULT_DIR_NAME = "SPHI_Research_Result"

np.random.seed(SEED)
random.seed(SEED)
tf.random.set_seed(SEED)
warnings.filterwarnings("ignore", category=FutureWarning)


def _resolve_base_dir() -> Path:
    """Work both from Jupyter and as a standalone script."""
    if "__file__" in globals():
        return Path(__file__).resolve().parent
    return Path.cwd()


BASE_DIR = _resolve_base_dir()
DATA_PATH = BASE_DIR / DATA_FILE
RESULT_DIR = BASE_DIR / RESULT_DIR_NAME
FIG_DIR = RESULT_DIR / "Figures"
TABLE_DIR = RESULT_DIR / "Tables"
for directory in (RESULT_DIR, FIG_DIR, TABLE_DIR):
    directory.mkdir(parents=True, exist_ok=True)


def require_columns(frame: pd.DataFrame, columns: list[str]) -> None:
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")


def reconstruct_sensor_with_validation(
    frame: pd.DataFrame,
    target: str,
    predictors: list[str],
) -> dict[str, float | int | str]:
    """Reconstruct only missing values and report out-of-fold accuracy.

    Recorded zeros are retained because zero may represent a genuine sensor or
    equipment state. Missing-value flags are exported so reconstructed records
    remain distinguishable from observations.
    """
    observed = frame[target].notna() & frame[predictors].notna().all(axis=1)
    missing = frame[target].isna() & frame[predictors].notna().all(axis=1)
    x_observed = frame.loc[observed, predictors]
    y_observed = frame.loc[observed, target]

    if len(y_observed) < 30:
        raise ValueError(f"Not enough observed values to reconstruct {target}")

    model = RandomForestRegressor(
        n_estimators=300,
        min_samples_leaf=3,
        random_state=SEED,
        n_jobs=-1,
    )
    folds = KFold(n_splits=5, shuffle=True, random_state=SEED)
    oof_prediction = cross_val_predict(model, x_observed, y_observed, cv=folds)
    model.fit(x_observed, y_observed)
    frame[f"{target}_WasMissing"] = frame[target].isna().astype(int)
    frame.loc[missing, target] = model.predict(frame.loc[missing, predictors])

    nonzero = np.abs(y_observed.to_numpy()) > 1e-9
    mape = np.mean(
        np.abs((y_observed.to_numpy()[nonzero] - oof_prediction[nonzero])
               / y_observed.to_numpy()[nonzero])
    ) * 100
    return {
        "Sensor": target,
        "Observed_rows": int(observed.sum()),
        "Reconstructed_rows": int(missing.sum()),
        "OOF_MAE": float(mean_absolute_error(y_observed, oof_prediction)),
        "OOF_RMSE": float(np.sqrt(mean_squared_error(y_observed, oof_prediction))),
        "OOF_R2": float(r2_score(y_observed, oof_prediction)),
        "OOF_MAPE_nonzero_percent": float(mape),
        "Used_by_autoencoder": "No",
    }


def build_autoencoder(number_of_features: int) -> Model:
    inputs = Input(shape=(number_of_features,), name="operational_features")
    encoded = Dense(8, activation="relu")(inputs)
    bottleneck = Dense(2, activation="relu", name="bottleneck")(encoded)
    decoded = Dense(8, activation="relu")(bottleneck)
    outputs = Dense(number_of_features, activation="linear")(decoded)
    model = Model(inputs, outputs, name="SPHI_autoencoder")
    model.compile(optimizer=Adam(learning_rate=5e-4), loss="mse")
    return model


def row_mse(actual: np.ndarray, predicted: np.ndarray) -> np.ndarray:
    return np.mean(np.square(actual - predicted), axis=1)


def calculate_sphi(error: np.ndarray, threshold: float) -> np.ndarray:
    """Map zero error to 100 and the calibrated anomaly threshold to 60."""
    if not np.isfinite(threshold) or threshold <= 0:
        raise ValueError("The calibrated reconstruction threshold must be positive")
    scale = -threshold / np.log(0.60)
    return np.clip(100.0 * np.exp(-error / scale), 0.0, 100.0)


def health_class(sphi: pd.Series) -> np.ndarray:
    return np.select(
        [sphi >= 80, sphi >= 60],
        ["Healthy", "Warning"],
        default="Degraded",
    )


def main() -> None:
    df = pd.read_excel(DATA_PATH, engine="xlrd")
    required = [
        "Date", "Month", "Month_Number", "WS1_East", "WS2_East", "WS1_West", "WS2_West",
        "Radiation_kWh", "Input_Energy", "Output_Energy", "PR",
    ]
    require_columns(df, required)
    df["Date"] = pd.to_datetime(df["Date"], errors="raise")
    df = df.sort_values("Date").drop_duplicates("Date").reset_index(drop=True)
    df.replace([np.inf, -np.inf], np.nan, inplace=True)

    # PR is a defined physical ratio in this dataset; fill it only where missing.
    valid_pr = df["Output_Energy"].notna() & df["Input_Energy"].gt(0)
    df["PR_WasMissing"] = df["PR"].isna().astype(int)
    fill_pr = df["PR"].isna() & valid_pr
    df.loc[fill_pr, "PR"] = (
        df.loc[fill_pr, "Output_Energy"] / df.loc[fill_pr, "Input_Energy"]
    )

    # Cyclical variables improve the auxiliary sensor reconstruction across seasons.
    day = df["Date"].dt.dayofyear
    df["Day_Sin"] = np.sin(2 * np.pi * day / 366.0)
    df["Day_Cos"] = np.cos(2 * np.pi * day / 366.0)
    sensor_reports = []
    sensor_reports.append(
        reconstruct_sensor_with_validation(
            df,
            "WS2_East",
            ["WS1_East", "WS1_West", "Radiation_kWh", "Day_Sin", "Day_Cos"],
        )
    )
    sensor_reports.append(
        reconstruct_sensor_with_validation(
            df,
            "WS2_West",
            ["WS1_West", "WS1_East", "Radiation_kWh", "Day_Sin", "Day_Cos"],
        )
    )
    pd.DataFrame(sensor_reports).to_excel(
        TABLE_DIR / "Table_01_Reconstruction_Validation.xlsx", index=False
    )

    # Exclude redundant Input_Energy and reconstructed WS2 channels. These five
    # observed variables capture weather, delivered energy, and conversion quality.
    model_features = [
        "WS1_East", "WS1_West", "Radiation_kWh", "Output_Energy", "PR"
    ]
    complete = df[model_features].notna().all(axis=1)
    if not complete.all():
        raise ValueError(
            "Unresolved missing values in model features: "
            f"{df.loc[:, model_features].isna().sum().to_dict()}"
        )

    # Chronological, non-overlapping partitions prevent future leakage.
    n = len(df)
    train_end = int(n * 0.60)
    calibration_end = int(n * 0.80)
    partition = np.full(n, "Test", dtype=object)
    partition[:train_end] = "Train"
    partition[train_end:calibration_end] = "Calibration"
    df["Partition"] = partition

    x_train_raw = df.loc[df["Partition"] == "Train", model_features]
    x_calibration_raw = df.loc[df["Partition"] == "Calibration", model_features]
    x_test_raw = df.loc[df["Partition"] == "Test", model_features]

    # Robust unsupervised screening limits contamination of the normal reference.
    screening_scaler = RobustScaler().fit(x_train_raw)
    screening_model = IsolationForest(
        n_estimators=500,
        contamination=CONTAMINATION,
        random_state=SEED,
        n_jobs=-1,
    )
    train_screen = screening_model.fit_predict(screening_scaler.transform(x_train_raw))
    reference_train = x_train_raw.iloc[train_screen == 1]

    scaler = RobustScaler().fit(reference_train)
    x_train = scaler.transform(reference_train)
    x_calibration = scaler.transform(x_calibration_raw)
    x_test = scaler.transform(x_test_raw)
    x_all = scaler.transform(df[model_features])

    autoencoder = build_autoencoder(len(model_features))
    callbacks = [
        EarlyStopping(monitor="val_loss", patience=40, restore_best_weights=True),
        ReduceLROnPlateau(monitor="val_loss", patience=15, factor=0.5, min_lr=1e-7),
    ]
    history = autoencoder.fit(
        x_train,
        x_train,
        validation_data=(x_calibration, x_calibration),
        epochs=400,
        batch_size=16,
        shuffle=True,
        callbacks=callbacks,
        verbose=0,
    )

    calibration_prediction = autoencoder.predict(x_calibration, verbose=0)
    calibration_error = row_mse(x_calibration, calibration_prediction)
    threshold = float(np.quantile(calibration_error, CALIBRATION_QUANTILE))

    all_prediction = autoencoder.predict(x_all, verbose=0)
    all_error = row_mse(x_all, all_prediction)
    df["Reconstruction_Error"] = all_error
    df["AE_Deviation"] = all_error > threshold
    df["SPHI"] = calculate_sphi(all_error, threshold)
    df["Health_Status"] = health_class(df["SPHI"])

    # Independent baseline: agreement strengthens evidence that results are not
    # simply an artifact of one neural-network architecture.
    baseline = IsolationForest(
        n_estimators=500,
        contamination=1.0 - CALIBRATION_QUANTILE,
        random_state=SEED,
        n_jobs=-1,
    ).fit(x_train)
    df["IF_Deviation"] = baseline.predict(x_all) == -1
    df["Model_Agreement"] = df["AE_Deviation"] == df["IF_Deviation"]

    # Feature-wise squared errors make every health score explainable.
    squared_error = np.square(x_all - all_prediction)
    for index, feature in enumerate(model_features):
        df[f"Error_{feature}"] = squared_error[:, index]
    error_columns = [f"Error_{feature}" for feature in model_features]
    df["Dominant_Error_Feature"] = df[error_columns].idxmax(axis=1).str.removeprefix(
        "Error_"
    )

    # Synthetic underperformance test: reduce delivered energy and corresponding
    # PR by 20% in the untouched test period, then measure detection sensitivity.
    synthetic = x_test_raw.copy()
    synthetic["Output_Energy"] *= 0.80
    synthetic["PR"] *= 0.80
    synthetic_scaled = scaler.transform(synthetic)
    synthetic_error = row_mse(
        synthetic_scaled, autoencoder.predict(synthetic_scaled, verbose=0)
    )
    synthetic_detection_rate = float(np.mean(synthetic_error > threshold))

    test_mask = df["Partition"] == "Test"
    test_agreement = float(df.loc[test_mask, "Model_Agreement"].mean())
    test_deviation_rate = float(df.loc[test_mask, "AE_Deviation"].mean())
    metrics = {
        "rows": n,
        "train_rows_before_screening": len(x_train_raw),
        "reference_train_rows": len(reference_train),
        "calibration_rows": len(x_calibration_raw),
        "test_rows": len(x_test_raw),
        "calibration_quantile": CALIBRATION_QUANTILE,
        "reconstruction_threshold": threshold,
        "test_deviation_rate": test_deviation_rate,
        "test_autoencoder_isolationforest_agreement": test_agreement,
        "synthetic_20pct_underperformance_detection_rate": synthetic_detection_rate,
        "minimum_validation_loss": float(min(history.history["val_loss"])),
    }

    pd.DataFrame(
        {"Parameter": list(metrics), "Value": list(metrics.values())}
    ).to_excel(TABLE_DIR / "Table_02_Method_Validation.xlsx", index=False)
    pd.DataFrame(
        {
            "Feature": model_features,
            "Mean_Squared_Error": squared_error[test_mask].mean(axis=0),
        }
    ).to_excel(TABLE_DIR / "Table_03_Test_Feature_Errors.xlsx", index=False)

    monthly = (
        df.groupby(["Month", "Month_Number"], as_index=False)
        .agg(
            Mean_SPHI=("SPHI", "mean"),
            Mean_PR=("PR", "mean"),
            Deviation_Days=("AE_Deviation", "sum"),
            Model_Agreement=("Model_Agreement", "mean"),
        )
        .sort_values("Month_Number")
    )
    monthly.to_excel(TABLE_DIR / "Table_04_Monthly_Assessment.xlsx", index=False)

    plt.figure(figsize=(11, 5), dpi=200)
    plt.plot(df["Date"], df["SPHI"], label="SPHI", linewidth=1.6)
    plt.axhline(80, linestyle="--", color="tab:orange", label="Healthy/Warning")
    plt.axhline(60, linestyle="--", color="tab:red", label="Warning/Degraded")
    degraded = df["Health_Status"] == "Degraded"
    plt.scatter(df.loc[degraded, "Date"], df.loc[degraded, "SPHI"], s=18,
                color="tab:red", label="Degraded")
    plt.xlabel("Date")
    plt.ylabel("Solar Plant Health Index (0–100)")
    plt.title("Leakage-safe unsupervised operational health assessment")
    plt.grid(alpha=0.25)
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG_DIR / "Figure_01_SPHI_Time_Series.png", bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(8, 4.5), dpi=200)
    plt.plot(history.history["loss"], label="Training")
    plt.plot(history.history["val_loss"], label="Calibration")
    plt.xlabel("Epoch")
    plt.ylabel("MSE")
    plt.title("Autoencoder learning curve")
    plt.grid(alpha=0.25)
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG_DIR / "Figure_02_Learning_Curve.png", bbox_inches="tight")
    plt.close()

    df.drop(columns=["Day_Sin", "Day_Cos"]).to_excel(
        RESULT_DIR / "FINAL_SPHI_RESULTS.xlsx", index=False
    )
    autoencoder.save(RESULT_DIR / "SPHI_Autoencoder.keras")
    joblib.dump(scaler, RESULT_DIR / "RobustScaler.joblib")
    joblib.dump(baseline, RESULT_DIR / "IsolationForest_Baseline.joblib")
    with open(RESULT_DIR / "run_metadata.json", "w", encoding="utf-8") as file:
        json.dump(
            {
                **metrics,
                "features": model_features,
                "split": "chronological 60/20/20",
                "sphi_calibration": "100 at zero error; 60 at 95th-percentile calibration error",
                "limitations": (
                    "Single-site daily data; no inverter alarms, temperatures, DC signals, "
                    "maintenance labels, or multi-site external validation."
                ),
            },
            file,
            indent=2,
        )

    print("SPHI research pipeline completed.")
    print(pd.Series(metrics).to_string())
    print(f"Results: {RESULT_DIR}")


if __name__ == "__main__":
    main()
