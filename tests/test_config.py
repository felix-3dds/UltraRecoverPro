import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from utils.config_loader import get_runtime_signatures, load_config


def test_load_config_rejects_invalid_hex_header(tmp_path: Path) -> None:
    config_file = tmp_path / "bad_header.json"
    config_file.write_text(
        json.dumps(
            {
                "signatures": {
                    "JPEG": {"header": "zz11", "max_size": 1024},
                },
                "profiles": {
                    "fast": {"max_size_factor": 0.5, "validate_entropy": False, "validate_structure": False},
                    "balanced": {"max_size_factor": 1.0, "validate_entropy": True, "validate_structure": True},
                    "deep": {"max_size_factor": 2.0, "validate_entropy": True, "validate_structure": True},
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Invalid header"):
        load_config(str(config_file))


def test_load_config_rejects_non_positive_max_size(tmp_path: Path) -> None:
    config_file = tmp_path / "bad_size.json"
    config_file.write_text(
        json.dumps(
            {
                "signatures": {
                    "JPEG": {"header": "ffd8ff", "max_size": 0},
                },
                "profiles": {
                    "fast": {"max_size_factor": 0.5, "validate_entropy": False, "validate_structure": False},
                    "balanced": {"max_size_factor": 1.0, "validate_entropy": True, "validate_structure": True},
                    "deep": {"max_size_factor": 2.0, "validate_entropy": True, "validate_structure": True},
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="max_size"):
        load_config(str(config_file))


def test_profile_adjusts_signature_max_size(tmp_path: Path) -> None:
    config_file = tmp_path / "good.json"
    config_file.write_text(
        json.dumps(
            {
                "signatures": {
                    "JPEG": {"header": "ffd8ff", "max_size": 100},
                },
                "profiles": {
                    "fast": {"max_size_factor": 0.5, "validate_entropy": False, "validate_structure": False},
                    "balanced": {"max_size_factor": 1.0, "validate_entropy": True, "validate_structure": True},
                    "deep": {"max_size_factor": 2.0, "validate_entropy": True, "validate_structure": True},
                },
            }
        ),
        encoding="utf-8",
    )

    config = load_config(str(config_file))
    signatures, profile = get_runtime_signatures(config, "deep")

    assert signatures["JPEG"]["header"] == b"\xff\xd8\xff"
    assert signatures["JPEG"]["max_size"] == 200
    assert profile["validate_structure"] is True
