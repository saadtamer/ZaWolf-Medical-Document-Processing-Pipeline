import torch


def get_device(preference="auto"):
    if preference == "cpu":
        return "cpu"

    if preference == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA is not available.")
        return "cuda"

    return "cuda" if torch.cuda.is_available() else "cpu"