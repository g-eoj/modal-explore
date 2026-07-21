import modal
import openml
import torch

from tabpfn import TabPFNClassifier
from sklearn.model_selection import train_test_split


app = modal.App("tabpfn-basic-example")
image = (
    modal.Image.debian_slim()
    .uv_pip_install(["openml", "tabpfn"])
)


@app.function(
    image=image,
    gpu="A10",
    secrets=[modal.Secret.from_name("tabpfn")],
)
def fit_predict_proba(X_train, X_test, y_train, categorical_indicator):
    torch.cuda.reset_peak_memory_stats()

    model = TabPFNClassifier()
    model.categorical_features_indices = [i for i, x in enumerate(categorical_indicator) if x]
    model.fit(X_train, y_train)
    probs = model.predict_proba(X_test)

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
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=1)

    probs = fit_predict_proba.remote(X_train, X_test, y_train, categorical_indicator)
    print(probs)
