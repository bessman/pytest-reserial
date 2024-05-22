"""Convert log files created by pytest-reserial<0.4.0 to the new format."""

import base64
import json
import sys
from pathlib import Path

old = Path(sys.argv[1])
new = Path(old.stem + ".jsonl")

with old.open() as fin:
    records = json.load(fin)

with new.open("w") as fout:
    for test_name, data in records.items():
        rx = base64.b64encode(bytes(data["rx"])).decode("ascii")
        tx = base64.b64encode(bytes(data["tx"])).decode("ascii")
        fout.write(json.dumps({test_name: {"rx": rx, "tx": tx}}) + "\n")
