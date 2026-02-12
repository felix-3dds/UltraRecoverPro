from __future__ import annotations

from typing import Any

import ahocorasick


class DeepCarver:
    """Motor de detección de firmas basado en Aho-Corasick."""

    def __init__(self, signatures: dict[str, dict[str, Any]]):
        self.automaton = ahocorasick.Automaton(ahocorasick.STORE_ANY, ahocorasick.KEY_SEQUENCE)
        self.max_header_size = 0

        for name, sig in signatures.items():
            header = sig["header"]
            if not isinstance(header, (bytes, bytearray)):
                raise TypeError(f"Header for {name} must be bytes")

            key = tuple(header)
            self.automaton.add_word(key, (name, sig))
            self.max_header_size = max(self.max_header_size, len(header))

        self.automaton.make_automaton()

    def scan_buffer(self, data: bytes | bytearray | memoryview) -> list[dict[str, Any]]:
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise TypeError("scan_buffer expects bytes-like data")

        matches: list[dict[str, Any]] = []
        sequence = tuple(data)
        for end_index, (name, sig) in self.automaton.iter(sequence):
            start_index = end_index - len(sig["header"]) + 1
            matches.append({"type": name, "offset": start_index, "signature": sig})

        return matches
