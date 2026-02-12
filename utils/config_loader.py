import json
import re
from pathlib import Path

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "signatures.json"
HEX_RE = re.compile(r"^[0-9a-fA-F]+$")
REQUIRED_PROFILES = {"fast", "balanced", "deep"}


def _validate_signatures(signatures: dict) -> None:
    if not isinstance(signatures, dict) or not signatures:
        raise ValueError("Config must define at least one signature")

    for name, signature in signatures.items():
        header = signature.get("header")
        max_size = signature.get("max_size")

        if not isinstance(header, str) or not header:
            raise ValueError(f"Invalid header for signature '{name}': expected non-empty hex string")
        if len(header) % 2 != 0 or HEX_RE.fullmatch(header) is None:
            raise ValueError(f"Invalid header for signature '{name}': must be valid even-length hex")
        if not isinstance(max_size, int) or max_size <= 0:
            raise ValueError(f"Invalid max_size for signature '{name}': must be > 0")


def _validate_profiles(profiles: dict) -> None:
    if not isinstance(profiles, dict):
        raise ValueError("Config 'profiles' must be a dictionary")

    missing = REQUIRED_PROFILES - set(profiles.keys())
    if missing:
        raise ValueError(f"Missing required profiles: {', '.join(sorted(missing))}")

    for profile_name, profile in profiles.items():
        factor = profile.get("max_size_factor")
        validate_entropy = profile.get("validate_entropy")
        validate_structure = profile.get("validate_structure")

        if not isinstance(factor, (int, float)) or factor <= 0:
            raise ValueError(f"Profile '{profile_name}' has invalid max_size_factor (must be > 0)")
        if not isinstance(validate_entropy, bool):
            raise ValueError(f"Profile '{profile_name}' has invalid validate_entropy (must be bool)")
        if not isinstance(validate_structure, bool):
            raise ValueError(f"Profile '{profile_name}' has invalid validate_structure (must be bool)")


def load_config(signatures_file: str | None = None) -> dict:
    config_path = Path(signatures_file) if signatures_file else DEFAULT_CONFIG_PATH
    config = json.loads(config_path.read_text(encoding="utf-8"))

    signatures = config.get("signatures", {})
    profiles = config.get("profiles", {})

    _validate_signatures(signatures)
    _validate_profiles(profiles)

    return config


def get_runtime_signatures(config: dict, profile_name: str) -> tuple[dict, dict]:
    profiles = config["profiles"]
    if profile_name not in profiles:
        available = ", ".join(sorted(profiles.keys()))
        raise ValueError(f"Unknown profile '{profile_name}'. Available: {available}")

    profile = profiles[profile_name]
    signatures = {}
    for name, signature in config["signatures"].items():
        adjusted_max_size = max(1, int(signature["max_size"] * profile["max_size_factor"]))
        signatures[name] = {
            "header": bytes.fromhex(signature["header"]),
            "max_size": adjusted_max_size,
        }

    return signatures, profile
