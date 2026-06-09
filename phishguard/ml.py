from dataclasses import dataclass
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from phishguard.types import MLResult


@dataclass
class TrainedModel:
    pipeline: Pipeline
    labels: dict[int, str]


def build_pipeline() -> Pipeline:
    return Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    analyzer="char_wb",
                    ngram_range=(3, 5),
                    min_df=1,
                    lowercase=True,
                ),
            ),
            ("clf", LogisticRegression(max_iter=600, class_weight="balanced")),
        ]
    )


class MLClassifier:
    def __init__(self, model_path: Path) -> None:
        self.model_path = model_path
        self.pipeline: Pipeline | None = None

    def load(self) -> None:
        payload = joblib.load(self.model_path)
        self.pipeline = payload["pipeline"]

    def predict(self, text: str) -> MLResult:
        if self.pipeline is None:
            raise RuntimeError("Model not loaded. Run training first.")
        proba = self.pipeline.predict_proba([text])[0]
        phishing_probability = float(proba[1])
        predicted_label = int(self.pipeline.predict([text])[0])
        return MLResult(
            phishing_probability=phishing_probability, predicted_label=predicted_label
        )

