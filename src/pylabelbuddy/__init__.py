import warnings
from pathlib import Path

warnings.simplefilter("always", DeprecationWarning)
warnings.warn(
    "pylabelbuddy is not maitained anymore. it has been superceded "
    "by the C++ application labelbuddy: "
    "https://jeromedockes.github.io/labelbuddy/",
    DeprecationWarning,
)

__version__ = (
    Path(__file__)
    .parent.joinpath("_data", "VERSION.txt")
    .read_text(encoding="utf-8")
    .strip()
)
