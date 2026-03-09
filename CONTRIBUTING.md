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

## Bonnes pratiques

- Toujours `python3 build_packs.py` en local avant de push
- Verifier le nombre de mods/RP dans la sortie du script
- Ne jamais `git add low/ base/ ultra/` — ils sont dans `.gitignore`
- Commit messages: `add:`, `remove:`, `fix:`, `update:` + nom du mod/config
