# evo-search Skill

## Description
Ce skill effectue des recherches web ultra-rapides et robustes en interrogeant **DuckDuckGo Lite** (version HTML pure). Il est conçu pour éviter les CAPTCHAs et les blocages liés aux bots, tout en restant léger (pas de navigateur complet requis en exécution standard).

## Fonctionnalités
- **Recherche Instantanée** : Utilise `curl` pour interroger directement `html.duckduckgo.com`.
- **Anonymat & Robustesse** : Simule un navigateur standard via User-Agent et utilise des requêtes POST pour minimiser la détection.
- **Sortie JSON Propre** : Retourne une liste structurée de résultats (`title`, `url`, `snippet`).
- **Nettoyage automatique** : Convertit les liens de redirection DuckDuckGo en URLs directes.

## Utilisation

### Commande
```bash
python3 skills/evo-search/search.py "votre requête de recherche"
```

### Exemple de Sortie
```json
[
  {
    "title": "Météo Drummondville - MétéoMédia",
    "url": "https://www.meteomedia.com/ca/meteo/quebec/drummondville",
    "snippet": "Obtenez les prévisions météo 14 jours, les cartes radar, et l'heure lever/coucher du soleil..."
  }
]
```

## Structure
- `search.py` : Script Python autonome (dépendances standard + `curl` système).
- `venv/` : Environnement virtuel (optionnel pour ce script, mais conservé pour évolutions futures).

## Notes Techniques
- Le script parse le HTML brut via Regex pour une vitesse maximale.
- En cas de changement de structure HTML chez DuckDuckGo, le script devra être ajusté.
