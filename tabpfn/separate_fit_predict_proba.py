import joblib
import modal
import openml
import tabpfn
import torch

from pathlib import Path
from sklearn.model_selection import train_test_split


app = modal.App("tabpfn-separate-fit-example")
image = (
    modal.Image.debian_slim()
    .uv_pip_install(["openml", "tabpfn"])
)
volume = modal.Volume.from_name("tabpfn-model-weights", create_if_missing=True)
MODEL_DIR = "/models"


@app.cls(
    env={"TABPFN_MODEL_CACHE_DIR": MODEL_DIR},
    image=image,
    gpu="A10",
    secrets=[modal.Secret.from_name("tabpfn")],
    volumes={MODEL_DIR: volume},
)
class TabPFNClassifier:

    @modal.method()
    def fit(self, X_train, y_train, categorical_indicator):
        if not (fit_id := joblib.hash([X_train, y_train])):
            raise RuntimeError("Cannot ID train dataset for state loading.")
        state_path = Path(MODEL_DIR) / fit_id / "state.tabpfn_fit"
        if state_path.exists():
            self.model = tabpfn.TabPFNClassifier.load_from_fit_state(state_path, device="cuda")
        else:
            self.model = tabpfn.TabPFNClassifier(fit_mode="fit_with_cache")
            self.model.categorical_features_indices = [i for i, x in enumerate(categorical_indicator) if x]
            self.model.fit(X_train, y_train)
            self.model.save_fit_state(state_path)

    @modal.method()
    def predict_proba(self, X_test):
        torch.cuda.reset_peak_memory_stats()

        probs = self.model.predict_proba(X_test)

        print(f"Peak allocated: {torch.cuda.max_memory_allocated() / 1e9:.2f} GB")
        print(f"Peak reserved:  {torch.cuda.max_memory_reserved() / 1e9:.2f} GB")

        return probs


@app.local_entrypoint()
def main():
    dataset = openml.datasets.get_dataset(dataset_id=1112)
    print(
        f"This is dataset '{dataset.name}', the target feature is "
        f"'{dataset.default_target_attribute}'"
    )
    print(f"URL: {dataset.url}")

    X, y, categorical_indicator, attribute_names = dataset.get_data(
        target=dataset.default_target_attribute
    )
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=2)

    # this is the modal class defined above, not the one from the tabpfn package
    model = TabPFNClassifier()
    model.fit.remote(X_train, y_train, categorical_indicator)
    probs = model.predict_proba.remote(X_test)
    print(probs)
    probs = model.predict_proba.remote(X_test)
    print(probs)
