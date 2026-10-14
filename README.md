# duplicate-photo-scan

Script Python qui repère dans un dossier les photos en double : copies exactes, versions redimensionnées ou recompressées. Il produit une page `rapport.html` pour contrôler le résultat à l'œil.

**Le script ne supprime, ne déplace et ne modifie aucune photo.** Toute décision reste manuelle.

## Formats pris en compte

`.jpg`, `.jpeg`, `.png`, `.webp`, `.heic` (majuscules ou minuscules). Les sous-dossiers sont parcourus.

## Prérequis

- Python 3.10 ou plus récent
- Bibliothèques : `Pillow` et `pillow-heif`

```
pip install Pillow pillow-heif
```

## Utilisation

```
python3 dup.py chemin/du/dossier_de_photos
```

Résultat :

- la console affiche un lot par ligne (`Lot 1: photo_a.jpg photo_b.jpg ...`) ;
- le fichier `rapport.html` est créé dans le dossier d'où tu lances la commande. Ouvre-le dans un navigateur.

Si aucun doublon n'est trouvé, le rapport ne contient que son titre.

## Lire le rapport

Chaque lot regroupe des photos jugées identiques ou très proches. Pour chaque photo : miniature, chemin, dimensions, poids en Ko et début de l'empreinte `sha`.

- Même `sha` = copie exacte, octet pour octet.
- `sha` différents dans un même lot = versions proches (redimensionnée, recompressée).

## Réglage

Le seuil de ressemblance `thr` vaut 8 par défaut (dans `scan(folder, thr=8, ...)`).

- Trop de photos différentes dans un même lot : baisse-le (par exemple 5).
- Des recompressions agressives non détectées : monte-le (par exemple 10).

## Limites

- Ne détecte pas les rotations, recadrages ni miroirs.
- Le regroupement est transitif : si A ressemble à B et B à C, les trois sont dans le même lot, même si A et C diffèrent. Fréquent sur les rafales de photos très proches.
- Comparaison de toutes les paires : adapté à quelques milliers de photos, lent au-delà.
- Une photo illisible ou corrompue arrête le script avec une erreur.
- Le rapport peut devenir lourd s'il y a beaucoup de lots (miniatures intégrées dans le fichier).
- La lecture des fichiers HEIC n'a pas été testée.

## Fichiers

- `dup.py` : le script
- `README.md` : ce fichier
- `FONCTIONNEMENT.md` : explication détaillée du code, pour non-développeurs