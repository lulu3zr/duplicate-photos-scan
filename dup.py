import base64, hashlib, html, io, sys
from pathlib import Path
from PIL import Image
from pillow_heif import register_heif_opener
register_heif_opener()

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def dhash(p):
    im = Image.open(p).convert("L").resize((9, 8), Image.LANCZOS)
    px = list(im.getdata())
    return sum((px[r*9+c] > px[r*9+c+1]) << (r*8+c) for r in range(8) for c in range(8))

def card(p, h):
    im = Image.open(p)
    w, ht = im.size
    im.thumbnail((300, 300)); b = io.BytesIO(); im.convert("RGB").save(b, "JPEG")
    return (f'<div><img src="data:image/jpeg;base64,{base64.b64encode(b.getvalue()).decode()}"><br>'
            f'{html.escape(str(p))}<br>{w}x{ht} - {Path(p).stat().st_size // 1024} Ko<br>sha {h[:8]}</div>')

def scan(folder, thr=8, out="rapport.html"):
    files = [p for p in Path(folder).rglob("*") if p.suffix.lower() in {".jpg",".jpeg",".png",".webp",".heic"}]
    info = [(p, sha(p), dhash(p)) for p in files]
    root = list(range(len(info)))
    def find(i):
        while root[i] != i: root[i] = root[root[i]]; i = root[i]
        return i
    for i in range(len(info)):
        for j in range(i + 1, len(info)):
            if info[i][1] == info[j][1] or (info[i][2] ^ info[j][2]).bit_count() <= thr:
                root[find(j)] = find(i)
    lots = {}
    for i in range(len(info)): lots.setdefault(find(i), []).append(info[i])
    rows = []
    for n, lot in enumerate((l for l in lots.values() if len(l) > 1), 1):
        print(f"Lot {n}:", *[p for p, _, _ in lot])
        rows.append(f'<h3>Lot {n} ({len(lot)} photos)</h3><div style="display:flex;flex-wrap:wrap;gap:16px">'
                    + "".join(card(p, h) for p, h, _ in lot) + "</div><hr>")
    Path(out).write_text('<meta charset="utf-8"><body style="font-family:sans-serif">'
                         '<h2>Contrôle visuel - aucune suppression effectuée</h2>' + "".join(rows))

if __name__ == "__main__": scan(sys.argv[1])