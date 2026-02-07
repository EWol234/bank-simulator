"""Application configuration."""

import os


class Config:
    DATA_DIR: str = os.environ.get(
        "BANK_SIM_DATA_DIR",
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "data"),
    )
