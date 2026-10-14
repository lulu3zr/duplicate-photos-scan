# Fonctionnement détaillé de `dup.py`

Ce document explique le script ligne par ligne, sans prérequis en Python. Les numéros de ligne renvoient au fichier `dup.py`.

## 1. Le principe en 30 secondes

Le script répond à une question : « quelles photos de ce dossier sont la même image ? »

Il utilise deux empreintes pour chaque photo :

1. **Empreinte exacte (SHA-256)** : une suite de 64 caractères calculée à partir de tous les octets du fichier. Deux fichiers identiques donnent la même suite. Si un seul octet change, la suite est complètement différente. Elle détecte les copies exactes.
2. **Empreinte visuelle (dHash)** : un nombre de 64 bits qui résume l'allure de l'image (où elle est plus claire ou plus sombre). Une photo réduite ou recompressée garde presque la même empreinte. Elle détecte les versions retouchées.

Le script compare toutes les photos deux à deux, regroupe celles qui se ressemblent en **lots**, puis écrit une page web `rapport.html` pour que tu les vérifies à l'œil.

**Il ne supprime, ne déplace et ne modifie aucune photo.** Il ne fait que lire les fichiers et écrire `rapport.html`.

## 2. Mini-lexique Python

| Mot | Signification |
|---|---|
| `import` | Charger une boîte à outils déjà écrite par d'autres |
| variable | Une étiquette collée sur une valeur (`thr = 8` : « thr » désigne 8) |
| fonction (`def`) | Une recette nommée, qu'on peut appeler plusieurs fois |
| liste `[...]` | Une suite ordonnée de valeurs |
| dictionnaire `{clé: valeur}` | Un classeur : on retrouve une valeur à partir de sa clé |
| boucle `for` | Répéter une action pour chaque élément d'une liste |
| `if` | Faire une action seulement si une condition est vraie |
| `return` | La valeur que la fonction renvoie comme résultat |
| `f'...{x}...'` | Un texte où `{x}` est remplacé par la valeur de x |
| `p[:8]` | Les 8 premiers éléments (ici : 8 premiers caractères) |
| `a // b` | Division qui garde seulement la partie entière |

## 3. Lignes 1 à 5 : les outils chargés

```python
import base64, hashlib, html, io, sys
from pathlib import Path
from PIL import Image
from pillow_heif import register_heif_opener
register_heif_opener()
```

- `hashlib` : calcule le SHA-256.
- `base64` : transforme une image en texte pour l'intégrer dans la page web.
- `html` : protège les caractères spéciaux dans les noms de fichiers (par exemple `<` ou `&`) pour qu'ils ne cassent pas la page.
- `io` : permet de garder un fichier en mémoire sans l'écrire sur le disque.
- `sys` : donne accès à ce qu'on tape après le nom du script dans la commande.
- `Path` : manipule des chemins de fichiers et de dossiers.
- `Image` (bibliothèque Pillow) : ouvre et transforme les images.
- Lignes 4-5 : activent la lecture des fichiers `.heic` (photos d'iPhone). Sans elles, Pillow ne sait pas ouvrir ce format.

## 4. Ligne 7 : `sha(p)` — l'empreinte exacte

```python
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
```

De l'intérieur vers l'extérieur :

1. `Path(p)` : le chemin de la photo `p`.
2. `.read_bytes()` : lit tout le contenu du fichier, octet par octet.
3. `hashlib.sha256(...)` : calcule l'empreinte de ces octets.
4. `.hexdigest()` : l'écrit sous forme de 64 caractères lisibles (chiffres et lettres a-f).

Résultat : deux copies exactes ont la même suite, quel que soit leur nom ou leur dossier.

## 5. Lignes 9 à 12 : `dhash(p)` — l'empreinte visuelle

```python
def dhash(p):
    im = Image.open(p).convert("L").resize((9, 8), Image.LANCZOS)
    px = list(im.getdata())
    return sum((px[r*9+c] > px[r*9+c+1]) << (r*8+c) for r in range(8) for c in range(8))
```

**Ligne 10 :**
- `Image.open(p)` ouvre la photo.
- `.convert("L")` la passe en niveaux de gris (on ignore la couleur).
- `.resize((9, 8), ...)` la réduit à une minuscule image de 9 pixels de large sur 8 de haut. Cette réduction efface les détails (compression, taille d'origine) et ne garde que la structure générale. `LANCZOS` est une méthode de réduction de bonne qualité.

**Ligne 11 :** `px` devient la liste des 72 valeurs de luminosité (9 × 8), ligne par ligne, de 0 (noir) à 255 (blanc).

**Ligne 12 :** pour chacune des 8 lignes (`r`) et chacune des 8 colonnes (`c`), on compare un pixel avec son voisin de droite :

- `px[r*9+c]` : le pixel courant (la ligne `r` commence à la position `r*9` car chaque ligne a 9 pixels).
- `px[r*9+c+1]` : son voisin de droite.
- `>` donne « vrai » (1) si le pixel courant est plus clair que son voisin, « faux » (0) sinon.
- `<< (r*8+c)` place ce 0 ou 1 à une position différente (0 à 63) dans un grand nombre.
- `sum(...)` additionne les 64 morceaux : on obtient un nombre de 64 bits, dont chaque bit dit « plus clair vers la droite ? » à un endroit de l'image.

Pourquoi 9 colonnes et pas 8 ? Comparer des voisins donne une comparaison de moins que de pixels : 9 pixels par ligne donnent exactement 8 comparaisons par ligne.

Une photo réduite ou légèrement recompressée a presque les mêmes zones claires et sombres au même endroit, donc presque les mêmes 64 bits.

## 6. Lignes 14 à 19 : `card(p, h)` — la fiche d'une photo dans le rapport

```python
def card(p, h):
    im = Image.open(p)
    w, ht = im.size
    im.thumbnail((300, 300)); b = io.BytesIO(); im.convert("RGB").save(b, "JPEG")
    return (f'<div><img src="data:image/jpeg;base64,...">...</div>')
```

Cette fonction produit le morceau de page web (HTML) qui affiche une photo. `p` est le chemin, `h` son empreinte exacte.

- Ligne 16 : `w, ht` reçoit la largeur et la hauteur d'origine, pour les afficher.
- Ligne 17 :
  - `im.thumbnail((300, 300))` réduit l'image pour qu'elle tienne dans 300 × 300 pixels, en gardant ses proportions.
  - `b = io.BytesIO()` crée un « fichier » vide en mémoire.
  - `.convert("RGB").save(b, "JPEG")` y enregistre la miniature au format JPEG (le passage en RGB évite les erreurs avec certains formats, par exemple les PNG transparents).
- Lignes 18-19 : construisent le texte HTML :
  - `base64.b64encode(...)` transforme la miniature en texte, qu'on intègre directement dans la page. Le rapport est ainsi un fichier unique, qui s'affiche même pour les `.heic` que les navigateurs ne savent pas lire.
  - `html.escape(str(p))` écrit le chemin en le protégeant des caractères spéciaux.
  - `Path(p).stat().st_size // 1024` donne le poids du fichier en Ko.
  - `h[:8]` affiche les 8 premiers caractères du SHA-256 : deux photos avec le même début sont des copies exactes.

## 7. Lignes 21 à 40 : `scan(...)` — le programme principal

```python
def scan(folder, thr=8, out="rapport.html"):
```

Paramètres :
- `folder` : le dossier à analyser (donné à l'exécution).
- `thr=8` : le seuil de ressemblance (voir plus bas). 8 est la valeur par défaut.
- `out="rapport.html"` : le nom du fichier rapport.

### Étape A, ligne 22 : lister les photos

```python
files = [p for p in Path(folder).rglob("*") if p.suffix.lower() in {".jpg",".jpeg",".png",".webp",".heic"}]
```

- `rglob("*")` parcourt le dossier et tous ses sous-dossiers.
- `p.suffix.lower()` prend l'extension du fichier en minuscules (`.JPG` devient `.jpg`).
- Seuls les fichiers dont l'extension est dans la liste sont gardés.

### Étape B, ligne 23 : calculer les empreintes

```python
info = [(p, sha(p), dhash(p)) for p in files]
```

Pour chaque photo, on stocke un triplet : (chemin, empreinte exacte, empreinte visuelle). `info` est la liste de tous ces triplets. C'est l'étape la plus longue : chaque photo est lue en entier.

### Étape C, lignes 24 à 31 : repérer et regrouper les ressemblances

C'est la partie la plus technique. Le but : former des lots. Si A ressemble à B, et B à C, alors A, B et C forment un seul lot.

**Ligne 24 :** `root = list(range(len(info)))`. Chaque photo reçoit un numéro (0, 1, 2...). `root` note, pour chaque photo, le « chef » de son groupe. Au départ, chaque photo est son propre chef : `root = [0, 1, 2, ...]`.

**Lignes 25-27 : `find(i)`.** Cette petite fonction retrouve le chef d'une photo : tant que le chef noté n'est pas la photo elle-même, on remonte au chef du chef. Au passage, la ligne `root[i] = root[root[i]]` raccourcit les chaînes pour accélérer les recherches suivantes.

**Lignes 28-31 : comparer toutes les paires.**

```python
for i in range(len(info)):
    for j in range(i + 1, len(info)):
        if info[i][1] == info[j][1] or (info[i][2] ^ info[j][2]).bit_count() <= thr:
            root[find(j)] = find(i)
```

- Deux boucles imbriquées : chaque photo `i` est comparée à toutes les suivantes `j`. Chaque paire n'est vue qu'une fois.
- `info[i][1] == info[j][1]` : les empreintes exactes sont égales (copie exacte).
- `info[i][2] ^ info[j][2]` : l'opérateur `^` (« ou exclusif ») compare les deux nombres de 64 bits et ne garde que les bits différents. `.bit_count()` les compte : c'est la **distance de Hamming**, le nombre de bits qui diffèrent sur 64.
- `<= thr` : si cette distance est de 8 ou moins, les photos sont jugées proches. 0 veut dire « même allure », 64 « totalement opposées ».
- `or` : une seule des deux conditions suffit.
- `root[find(j)] = find(i)` : les deux photos sont fusionnées dans le même groupe (le chef de `j` devient le chef de `i`).

### Étape D, lignes 32 à 33 : constituer les lots

```python
lots = {}
for i in range(len(info)): lots.setdefault(find(i), []).append(info[i])
```

On range chaque photo dans une « boîte » portant le numéro de son chef. `setdefault(chef, [])` crée la boîte si elle n'existe pas encore, et `.append(...)` y ajoute la photo. À la fin, `lots` contient une boîte par groupe.

### Étape E, lignes 34 à 38 : préparer l'affichage

```python
rows = []
for n, lot in enumerate((l for l in lots.values() if len(l) > 1), 1):
```

- `len(l) > 1` : on ignore les boîtes d'une seule photo (photo sans doublon).
- `enumerate(..., 1)` numérote les lots à partir de 1.
- Ligne 36 : affiche le lot dans la console (`Lot 1: photo_a.jpg photo_b.jpg`).
- Lignes 37-38 : ajoute à `rows` le titre du lot et la fiche de chaque photo (via `card`), côte à côte.

### Étape F, lignes 39 à 40 : écrire le rapport

```python
Path(out).write_text('<meta charset="utf-8">...' + "".join(rows))
```

Écrit le fichier `rapport.html` avec le titre « Contrôle visuel - aucune suppression effectuée » suivi de tous les lots. Si un `rapport.html` existe déjà à cet endroit, il est remplacé. Les accents sont gérés grâce à `utf-8`.

## 8. Ligne 42 : le déclencheur

```python
if __name__ == "__main__": scan(sys.argv[1])
```

Cette ligne lance `scan` seulement quand on exécute le fichier directement (`python3 dup.py dossier`). `sys.argv[1]` est le premier mot tapé après `dup.py` : le dossier à analyser. Si on oublie de le donner, le script s'arrête avec une erreur.

## 9. Exemple concret

Dossier contenant : `a.jpg`, `a_copie.jpg` (copie exacte de `a.jpg`), `a_petite.jpg` (même photo réduite et recompressée), `b.jpg` (autre photo).

1. Le script calcule les empreintes des 4 fichiers.
2. `a.jpg` et `a_copie.jpg` ont le même SHA-256 : ils sont regroupés.
3. `a_petite.jpg` a un SHA différent, mais un dHash à distance 0 de `a.jpg` : elle rejoint le même groupe.
4. `b.jpg` est trop différente : elle reste seule et n'apparaît pas dans le rapport.
5. `rapport.html` contient « Lot 1 (3 photos) » avec les 3 miniatures. Tu les compares à l'œil et tu décides toi-même de ce que tu fais.

## 10. Points d'attention

- **Seuil `thr`** : plus il est haut, plus le script regroupe de photos (au risque de mélanger des photos différentes). Plus il est bas, plus il est strict (au risque de rater des recompressions fortes).
- **Regroupement en chaîne** : A proche de B et B proche de C met A, B et C dans le même lot, même si A et C diffèrent. Vérifie toujours visuellement.
- **Ce qui n'est pas détecté** : rotations, recadrages, miroirs.
- **Photo illisible** : le script s'arrête avec une erreur.
- **Volume** : toutes les paires sont comparées, donc le temps augmente vite avec le nombre de photos.
- **HEIC** : la lecture n'a pas été testée.