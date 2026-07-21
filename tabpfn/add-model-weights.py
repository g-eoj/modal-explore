import modal
import tabpfn
from pathlib import Path
from typing import Literal, cast


app = modal.App("tabpfn-model-weights")
image = (
    modal.Image.debian_slim()
    .uv_pip_install("tabpfn")
)
volume = modal.Volume.from_name("tabpfn-model-weights", create_if_missing=True)
MODEL_DIR = Path("/models")


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("tabpfn")],
    volumes={MODEL_DIR: volume}
)
def download_v3_models():
    """Download v3 classifier and regressor model weights."""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    for model_version, model_source, model_type in [
        (tabpfn.model_loading.ModelVersion.V3, tabpfn.model_loading.ModelSource.get_classifier_v3(), "classifier"),
        (tabpfn.model_loading.ModelVersion.V3, tabpfn.model_loading.ModelSource.get_regressor_v3(), "regressor"),
    ]:
        for ckpt_name in model_source.filenames:
            path = MODEL_DIR / ckpt_name
            if path.exists():
                print(
                    f"Skipping download of checkpoint that already exists: {path}"
                )
                continue
            result = tabpfn.model_loading.download_model(
                to=path,
                version=model_version,
                which=cast("Literal['classifier', 'regressor']", model_type),
                model_name=ckpt_name,
            )
            if result != "ok":
                print(f"Errors downloading model {model_version}: {result}")
