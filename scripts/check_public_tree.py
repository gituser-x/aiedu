"""Conservative checks; manual review of code and screenshots remains required."""
from pathlib import Path
import re
import sys

root = Path(__file__).resolve().parents[1]
forbidden_dirs = {'.venv', 'node_modules', 'backups', 'media', 'uploads', 'migrate'}
forbidden_extensions = {'.pem', '.key', '.p12', '.sql', '.dump', '.sqlite3', '.log', '.zip', '.tar', '.gz'}
patterns = [
    re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----'),
    re.compile(r'\bgh[pousr]_[A-Za-z0-9]{20,}\b'),
    re.compile(r'\bgithub_pat_[A-Za-z0-9_]{20,}\b'),
    re.compile(r'\bsk-[A-Za-z0-9_-]{20,}\b'),
    re.compile(r'\bLTAI[A-Za-z0-9]{12,}\b'),
    re.compile(r'(?i)(?:postgres(?:ql)?|redis)://[^\s:/]+:[^\s@]+@'),
    re.compile(r'(?i)[A-Z]:\\Users\\[^\s]+'),
]
failures = []
count = 0
for path in root.rglob('*'):
    rel = path.relative_to(root)
    if any(p in {'.git','__pycache__'} for p in rel.parts):
        continue
    if path.is_dir():
        if path.name in forbidden_dirs:
            failures.append(str(rel)+': forbidden directory')
        continue
    count += 1
    if path.name.startswith('.env') or path.suffix.lower() in forbidden_extensions:
        failures.append(str(rel)+': forbidden file')
    if path.suffix.lower() in {'.png','.jpg','.jpeg'}:
        continue
    text = path.read_text(encoding='utf-8')
    for pattern in patterns:
        if pattern.search(text):
            failures.append(str(rel)+': potential secret or private path (value hidden)')
            break
if failures:
    print('\n'.join(failures))
    sys.exit(1)
print(f'PASS: {count} public files checked; no matching forbidden files or secret patterns.')
