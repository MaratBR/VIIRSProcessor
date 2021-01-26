import re
from pathlib import Path

path = Path(__file__).parent / 'config.py'
with path.open() as f:
    text = f.read()

regexp = re.compile(r"'xlim': \((.*), (.*)\),([\n\t ]*)'ylim': \((.*), (.*)\),")
text = regexp.sub(r"'xlim': (\1, \4),\3'ylim': (\2, \5),", text)

print(text)
