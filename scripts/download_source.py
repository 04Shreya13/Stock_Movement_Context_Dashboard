"""Download only the pinned three source tables; verify before saving.

If access is gated, first accept the dataset access conditions on Hugging Face
and set HF_TOKEN in your environment. Never commit or print the token.
"""
import hashlib
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from dso576_python.cleaning import RAW_SHA256

REVISION = '52d3ecb97e490a2392717935402cde283e8fa36e'


def main():
    destination = Path('data/raw')
    destination.mkdir(parents=True, exist_ok=True)
    for table, expected in RAW_SHA256.items():
        path = destination / f'{table}.parquet'
        if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == expected:
            print(f'{table}: existing pinned bytes verified')
            continue
        url = f'https://huggingface.co/datasets/TheFinAI/Herculean/resolve/{REVISION}/data/{table}.parquet'
        request = urllib.request.Request(url)
        token = os.environ.get('HF_TOKEN')
        if token:
            request.add_header('Authorization', f'Bearer {token}')
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                content = response.read()
        except urllib.error.HTTPError as error:
            if error.code in (401, 403):
                raise SystemExit('Source access required. Accept dataset conditions on Hugging Face and set HF_TOKEN, or place the three pinned Parquet files in data/raw/. No token was printed.') from None
            raise SystemExit(f'Source HTTP error {error.code}; no files substituted.') from None
        except urllib.error.URLError:
            raise SystemExit('Source network request failed; use the pinned local files described in README.md.') from None
        if hashlib.sha256(content).hexdigest() != expected:
            raise SystemExit(f'{table}: checksum mismatch; refusing changed source')
        temporary = path.with_suffix('.part')
        temporary.write_bytes(content)
        temporary.replace(path)
        print(f'{table}: downloaded and checksum verified')


if __name__ == '__main__':
    main()
