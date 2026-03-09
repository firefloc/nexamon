# Nexamon Pack — Guide de contribution

## Architecture

```
nexamon/
├── mods/                  # Sources .pw.toml (mods)
├── resourcepacks/         # Sources .pw.toml (resource packs)
├── shaderpacks/           # Fichiers shaders (non .pw.toml)
├── configs/               # Configs source, organisees par tier
│   ├── core/config/       #   → inclus dans low + base + ultra
│   ├── base/config/       #   → inclus dans base + ultra
│   ├── base/shaderpacks/  #   → shaders base + ultra
│   └── ultra/config/      #   → inclus dans ultra uniquement
├── build_packs.py         # Script de build (genere low/, base/, ultra/)
├── low/                   # GENERE — ne pas editer
├── base/                  # GENERE — ne pas editer
└── ultra/                 # GENERE — ne pas editer
```

## Systeme de tiers

Chaque `.pw.toml` doit avoir un champ `tier`:

| Tier     | Inclus dans         | Usage                                     |
|----------|---------------------|--------------------------------------------|
| `core`   | low + base + ultra  | Mods serveur, perf, essentiels             |
| `base`   | base + ultra        | Mods client QoL, RP cosmetiques            |
| `ultra`  | ultra seulement     | Shaders, mods lourds optionnels            |

Si un `.pw.toml` n'a pas de champ `tier`, le defaut est:
- `side = "both"` → `core`
- `side = "client"` → `base`

Pour auto-tagger tous les fichiers: `python3 build_packs.py --tag`

## Regles absolues

1. **JAMAIS editer `low/`, `base/`, `ultra/` directement** — ces dossiers sont regeneres par `build_packs.py` et ecrases a chaque build. Toute modif manuelle sera perdue.

2. **Editer uniquement les sources:**
   - Mods → `mods/<nom>.pw.toml`
   - Resource packs → `resourcepacks/<nom>.pw.toml`
   - Configs → `configs/<tier>/config/...`
   - Shaders → `configs/base/shaderpacks/...` ou `shaderpacks/`

3. **Chaque `.pw.toml` doit avoir un `tier`** — la CI echouera sinon.

4. **Configs extras tolerees** — dans les dossiers `config/`, les fichiers supplementaires (non geres par build_packs.py) sont acceptes. Ils seront copies tels quels dans les packs generes.

## Workflow: ajouter un mod

```bash
# 1. Creer le .pw.toml dans mods/
#    Champs requis: name, filename, side, tier, [download] url + hash

# 2. Choisir le tier
tier = "core"    # mod serveur ou perf essentiel
tier = "base"    # mod client QoL
tier = "ultra"   # mod lourd optionnel

# 3. Rebuild local pour verifier
python3 build_packs.py

# 4. Commit + push
git add mods/mon-mod.pw.toml
git commit -m "add: mon-mod (tier base)"
git push
```

## Workflow: modifier une config

```bash
# 1. Identifier le tier de la config
#    - Config serveur/essentielle → configs/core/config/
#    - Config client QoL → configs/base/config/
#    - Config ultra only → configs/ultra/config/

# 2. Editer le fichier source
vim configs/core/config/resourcepackoverrides.json

# 3. Rebuild local
python3 build_packs.py

# 4. Commit + push
git add configs/core/config/resourcepackoverrides.json
git commit -m "fix: update resource pack overrides"
git push
```

## Workflow: retirer un mod

```bash
# 1. Supprimer le .pw.toml (ou mv vers .agenttrash/)
mv mods/mon-mod.pw.toml .agenttrash/

# 2. Rebuild
python3 build_packs.py

# 3. Commit
git add -u mods/mon-mod.pw.toml
git commit -m "remove: mon-mod"
git push
```

## Workflow: ajouter un resource pack

```bash
# 1. Creer le .pw.toml dans resourcepacks/
#    Avec tier = "core" ou "base"

# 2. Si le RP doit etre active par defaut, ajouter dans:
#    - configs/core/config/resourcepackoverrides.json → default_packs[]
#    - configs/core/config/defaultoptions/options.txt → resourcePacks[]

# 3. Rebuild + commit + push
python3 build_packs.py
git add resourcepacks/mon-rp.pw.toml configs/core/config/resourcepackoverrides.json
git commit -m "add: mon-rp resource pack"
git push
```

## Hebergement des fichiers custom (NON-Modrinth)

**REGLE CRITIQUE** : les URL dans les `.pw.toml` doivent etre **accessibles publiquement**.
Si packwiz ne peut pas telecharger un fichier, **TOUT le pack echoue** pour TOUS les joueurs.

### Sources de fichiers

| Source | URL | Exemple |
|--------|-----|---------|
| Modrinth | `https://cdn.modrinth.com/data/...` | Automatique via `index_resourcepacks.py` |
| Custom (nous) | GitHub Releases `v1.0.0-custom` | `https://github.com/firefloc/nexamon/releases/download/v1.0.0-custom/MonFichier.zip` |

**JAMAIS** utiliser d'URL locale (`http://192.168...`, `http://90.73...`, `localhost`, IP privee).

### Procedure pour ajouter un fichier custom

```bash
# 1. Avoir le fichier .zip pret localement

# 2. Calculer le hash SHA256
sha256sum mon-fichier.zip

# 3. Uploader sur la release GitHub v1.0.0-custom
#    ATTENTION: GitHub remplace les espaces par des points dans le nom
gh release upload v1.0.0-custom mon-fichier.zip --clobber

# 4. Verifier le nom exact sur la release (espaces → points)
gh release view v1.0.0-custom --json assets --jq '.assets[].name' | grep -i "mon-fichier"

# 5. Verifier que le telechargement fonctionne (HTTP 200)
curl -sL -o /dev/null -w "%{http_code}" "https://github.com/firefloc/nexamon/releases/download/v1.0.0-custom/Mon.Fichier.zip"
# Doit retourner 200. Si 404 → le nom est incorrect.

# 6. Creer le .pw.toml avec la bonne URL et le bon hash
cat > resourcepacks/mon-fichier.pw.toml << 'TOML'
name = "Mon Fichier"
filename = "Mon Fichier.zip"
side = "both"
tier = "core"

[download]
url = "https://github.com/firefloc/nexamon/releases/download/v1.0.0-custom/Mon.Fichier.zip"
hash-format = "sha256"
hash = "<sha256 de l'etape 2>"
TOML

# 7. Tester le build
python3 build_packs.py

# 8. Commit + push
git add resourcepacks/mon-fichier.pw.toml
git commit -m "add: Mon Fichier resource pack"
git push
```

### Mise a jour d'un fichier custom existant

```bash
# 1. Recreer le .zip avec les nouvelles modifications
# 2. Recalculer le hash: sha256sum mon-fichier.zip
# 3. Re-uploader: gh release upload v1.0.0-custom mon-fichier.zip --clobber
# 4. Verifier le download (curl HTTP 200)
# 5. Mettre a jour le hash dans le .pw.toml
# 6. Commit + push
```

### Checklist avant commit (OBLIGATOIRE)

- [ ] Le hash SHA256 dans le `.pw.toml` correspond au fichier uploade
- [ ] L'URL retourne HTTP 200 (`curl -sL -o /dev/null -w "%{http_code}" <url>`)
- [ ] `python3 build_packs.py` reussit sans erreur
- [ ] Aucune URL locale/privee dans les fichiers modifies

## CI / Verification

Le workflow GitHub Actions (`.github/workflows/pages.yml`) execute:

1. **verify** (sur push et PR):
   - Run `build_packs.py`
   - Verifie que `pack.toml` et `index.toml` existent pour chaque variante
   - Verifie que tous les `.pw.toml` ont un champ `tier` valide
   - Verifie la structure des configs

2. **deploy** (sur push main seulement):
   - Rebuild les packs
   - Deploie sur GitHub Pages

### URLs de distribution

| Variante | URL pack.toml                                         |
|----------|-------------------------------------------------------|
| Low      | `https://firefloc.github.io/nexamon/low/pack.toml`    |
| Base     | `https://firefloc.github.io/nexamon/base/pack.toml`   |
| Ultra    | `https://firefloc.github.io/nexamon/ultra/pack.toml`  |

## Fichiers cles

| Fichier | Role |
|---------|------|
| `configs/core/config/defaultoptions/options.txt` | Options MC par defaut (resourcePacks, guiScale, etc.) |
| `configs/core/config/defaultoptions/servers.dat` | Serveur par defaut (NBT) |
| `configs/core/config/resourcepackoverrides.json` | Liste des RP actives par defaut (default_packs) |
| `build_packs.py` | Script de generation des 3 variantes |

## Feuille de passage agent (AGENT_LOG.md)

**OBLIGATOIRE** pour tout agent (IA ou humain) qui modifie le repo.

Apres chaque intervention, ajouter une ligne dans `AGENT_LOG.md` :

```
| HH:MM | Modele (session-id 8 chars) | action courte (hash commit) | OK / CASSE — raison |
```

- **Modele** : `Claude Opus 4.6`, `Claude Sonnet 4.6`, `humain`, etc.
- **Session-id** : 8 premiers chars de l'ID de conversation/session
- **Resultat** : `OK`, `CASSE — impact`, ou `EN COURS`
- Si ca casse, decrire l'impact clairement (ex: "packwiz 404 pour tous les joueurs")

## Bonnes pratiques

- Toujours `python3 build_packs.py` en local avant de push
- Verifier le nombre de mods/RP dans la sortie du script
- Ne jamais `git add low/ base/ ultra/` — ils sont dans `.gitignore`
- Commit messages: `add:`, `remove:`, `fix:`, `update:` + nom du mod/config
- **Toujours verifier les URLs avant de commit** (`curl -sL -o /dev/null -w "%{http_code}" <url>`)
- **Jamais d'URL locale/privee** dans les `.pw.toml`
- **Toujours signer le AGENT_LOG.md** apres intervention
