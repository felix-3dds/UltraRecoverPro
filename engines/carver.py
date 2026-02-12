import ahocorasick


class DeepCarver:
    def __init__(self, signatures: dict):
        # Automaton que acepta secuencias
        self.automaton = ahocorasick.Automaton(
            ahocorasick.STORE_ANY,
            ahocorasick.KEY_SEQUENCE
        )

        for name, sig in signatures.items():
            header = sig['header']

            if not isinstance(header, (bytes, bytearray)):
                raise TypeError(f"Header for {name} must be bytes")

            # Convertimos bytes a secuencia de enteros
            key = tuple(header)

            self.automaton.add_word(key, (name, sig))

        self.automaton.make_automaton()

    def scan_buffer(self, data: bytes):
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("scan_buffer expects bytes")

        matches = []

        # Convertimos buffer completo a secuencia
        sequence = tuple(data)

        for end_index, (name, sig) in self.automaton.iter(sequence):
            start_index = end_index - len(sig['header']) + 1
            matches.append({
                "type": name,
                "offset": start_index,
                "signature": sig
            })

        return matches
