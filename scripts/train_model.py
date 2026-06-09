import csv
import sys
from pathlib import Path

import joblib
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from phishguard.ml import build_pipeline


def load_dataset(dataset_path: Path) -> tuple[list[str], list[int]]:
    texts: list[str] = []
    labels: list[int] = []
    with dataset_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            texts.append(row["text"])
            labels.append(int(row["label"]))
    return texts, labels


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    dataset_path = PROJECT_ROOT / "data" / "mock_hebrew_messages.csv"
    model_output = PROJECT_ROOT / "models" / "phishguard_model.joblib"
    model_output.parent.mkdir(parents=True, exist_ok=True)

    texts, labels = load_dataset(dataset_path)
    x_train, x_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.30, random_state=42, stratify=labels
    )

    pipeline = build_pipeline()
    pipeline.fit(x_train, y_train)
    y_pred = pipeline.predict(x_test)

    print("=== Baseline Evaluation ===")
    print(classification_report(y_test, y_pred, digits=3))

    payload = {"pipeline": pipeline, "classes": ["legit", "phishing"]}
    joblib.dump(payload, model_output)
    print("Model saved successfully to models/phishguard_model.joblib")


if __name__ == "__main__":
    main()

