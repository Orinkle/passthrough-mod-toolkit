"""schema_io.py — load a schema.yaml and select a vocabulary."""
import yaml


def load(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_vocab(schema, host=None, vocab_file=None):
    if vocab_file:
        with open(vocab_file, encoding="utf-8") as f:
            return yaml.safe_load(f)
    if host:
        return schema["vocabularies"][host]
    raise ValueError("need --host or --vocab")
