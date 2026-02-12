import ahocorasick


class DeepCarver:
    def __init__(self, signatures: dict):
        # Automaton que acepta strings; usamos codificación latin-1 para mapear bytes 1:1.
        self.automaton = ahocorasick.Automaton(
            ahocorasick.STORE_ANY,
            ahocorasick.KEY_STRING,
        )

        for name, sig in signatures.items():
            header = sig['header']

            if not isinstance(header, (bytes, bytearray)):
                raise TypeError(f"Header for {name} must be bytes")

            key = header.decode("latin-1")

            self.automaton.add_word(key, (name, sig))

        self.automaton.make_automaton()

    def scan_buffer(self, data: bytes | bytearray | memoryview):
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise TypeError("scan_buffer expects a bytes-like object")

        matches = []

        # Mapeo 1:1 de bytes a string para evitar materializar tuplas enormes.
        # Si ya es bytes evitamos una copia extra.
        sequence = data.decode("latin-1") if isinstance(data, bytes) else bytes(data).decode("latin-1")

        for end_index, (name, sig) in self.automaton.iter(sequence):
            start_index = end_index - len(sig['header']) + 1
            matches.append({
                "type": name,
                "offset": start_index,
                "signature": sig
            })

        return matches
