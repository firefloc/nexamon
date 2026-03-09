# Nexamon — Feuille de passage agents

Chaque agent (humain ou IA) qui modifie le pack ou le launcher inscrit son passage ici.
Format: date, identifiant, action, resultat.

---

## 2026-03-09

| Heure | Agent | Action | Resultat |
|-------|-------|--------|----------|
| ~18:15 | Claude Opus 4.6 (session inconnue) | remove: RRLS mod (`9aa3cab`) | OK — commit + push, CI deploie |
| ~18:28 | Claude Opus 4.6 (session inconnue) | add: servers.dat (`a992932`) | OK |
| ~18:33 | Claude Opus 4.6 (session inconnue) | add: CI pages.yml + CONTRIBUTING.md (`49ab71c`) | OK |
| ~21:39 | Claude Opus 4.6 (session inconnue) | add: Nexamon Overrides RP + cutil-nerf hash update (`2f7aa73`) | **CASSE** — URL locale `http://90.73.30.60:9457/` inexistante. Packwiz 404 pour tous les joueurs. Zip pas uploade sur GitHub Releases. |
| ~22:25 | Claude Opus 4.6 (`59e4507a`) | fix: URL custom RPs → GitHub Releases (`d06968b`) | OK — uploade les 2 zips sur v1.0.0-custom, corrige URLs, verifie HTTP 200 |
| ~22:25 | Claude Opus 4.6 (`59e4507a`) | fix: launcher — erreur silencieuse packwiz | OK — dialog erreur visible, `finally` block pour refreshPackStatuses, timeout 5min→15min |
| ~22:25 | Claude Opus 4.6 (`59e4507a`) | doc: CONTRIBUTING.md + procedure hebergement custom | OK — ajout section complete GitHub Releases |
