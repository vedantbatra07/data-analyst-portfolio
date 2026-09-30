"""Download the exact public input used by this portfolio; verify its hash."""
from pathlib import Path
import hashlib,json,urllib.request,tempfile,os
root=Path(__file__).resolve().parents[2]
info=json.loads((root/'02-ai-adoption/SOURCE.json').read_text())
target=root/'02-ai-adoption/data/stackoverflow_2025.csv'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()
if target.exists():
    if sha(target)!=info['sha256']:raise SystemExit('Existing input does not match the recorded hash; preserved without overwriting.')
    print('Verified existing public input.')
else:
    fd,tmp=tempfile.mkstemp(dir=target.parent,suffix='.download');os.close(fd);tmp=Path(tmp)
    try:
        with urllib.request.urlopen(info['download_url'],timeout=120) as response,tmp.open('wb') as dest:
            while chunk:=response.read(1024*1024):dest.write(chunk)
        if sha(tmp)!=info['sha256']:raise SystemExit('Publisher file changed: hash mismatch. Do not silently substitute data.')
        tmp.replace(target);print('Downloaded and verified the original public input.')
    finally:
        if tmp.exists():tmp.unlink()
