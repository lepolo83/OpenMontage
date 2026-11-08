# fetch/ — récupérer des images Wikimedia Commons via GitHub Actions

Les serveurs GitHub ont une IP que Commons ne limite pas, contrairement au conteneur de dev. Le workflow
`.github/workflows/fetch-assets.yml` lit `fetch/request.json`, télécharge les images et les commite.

## Utilisation pour une nouvelle vidéo
1. Éditer `fetch/request.json`, puis commiter et pousser sur n'importe quelle branche (pas de filtre de branche).
   Tout push touchant `fetch/**` (sauf ce README) lance le workflow ; il peut aussi être lancé à la main (`workflow_dispatch`).
2. Le workflow commite `assets_cache/<project>/` (images + `credits.json`) sur la branche qui l'a déclenché, avec `[skip ci]`.
   Attention : ne mettez jamais `[skip ci]` dans votre propre commit, le workflow ne démarrerait pas.
3. `git pull` puis utiliser les images ; `credits.json` sert à générer `CREDITS.md`.

## Format de `fetch/request.json`
```json
{
  "project": "psaume-23",                       // dossier de sortie : assets_cache/<project>/
  "width": 1920,                                // largeur de vignette demandée (px)
  "allowed_licenses": ["public domain", "pd", "cc0", "cc-0"],  // licences acceptées (début de LicenseShortName)
  "images": [
    {"id": "bon-berger-1", "title": "File:Nom exact.jpg"},                // fichier précis
    {"id": "bon-berger-2", "search": "Plockhorst Good Shepherd",          // ou recherche Commons
     "fallback_searches": ["Good Shepherd Murillo"],                      //   recherches de repli (facultatif)
     "exclude": ["plaque", "Lyon"]}                                       //   mots à exclure des titres (facultatif)
  ]
}
```
(Retirez les commentaires `//` : le JSON réel n'en accepte pas.)

- Pour chaque entrée, le premier candidat valide est retenu : licence autorisée, JPEG/PNG, ≥ 1000 px de large, pas déjà pris.
- Les recherches sont libres : **vérifiez qu'il s'agit bien d'une peinture** (utilisez `exclude`, ou `title` exact).
- Un fichier source plus petit que `width` est livré à sa taille d'origine.

## Sortie
`assets_cache/<project>/NN-<id>.jpg` et `credits.json` (id, fichier, titre, auteur, licence, `license_url`, `source_url`,
`image_url`, dimensions, taille). Politesse : User-Agent « OpenMontage-ZoneChretien/1.0 (https://zone-chretien.org) »,
3 s entre deux requêtes, `Retry-After` respecté sur 429. Les logs sont dans l'onglet Actions (`rejeté (...)` explique les refus).
