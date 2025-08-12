# Dashboard Marchés et Idées d'Investissement

Application légère pour:
- Scraper des données financières (actions, ETF, crypto, indices, matières premières, forex) via des sources publiques et APIs gratuites
- Calculer les plus hauts/bas 52 semaines, top gagnants/perdants, momentum
- Agréger des actualités (NewsAPI si clé dispo, sinon flux RSS) et évaluer le sentiment (VADER)
- Proposer des idées d'investissement basées sur règles simples: momentum, distance aux extrêmes, sentiment, surprises de résultats

## Installation

1) Python 3.10+ recommandé
2) Installer les dépendances:

```bash
pip install -r requirements.txt
```

3) Variables d'environnement (facultatif mais recommandé):

- `NEWSAPI_KEY` (https://newsapi.org/) pour l'actualité ciblée
- `FMP_API_KEY` (https://financialmodelingprep.com/) pour récupérer les surprises de résultats

Créer un fichier `.env` à la racine:

```
NEWSAPI_KEY=...
FMP_API_KEY=...
```

## Lancer le dashboard

```bash
streamlit run src/dashboard.py
```

## Lancer en CLI (idées d'investissement rapides)

```bash
python src/main.py --asset-class equities --top-n 10
```

## Notes
- Les données de prix proviennent principalement de `yfinance` (Yahoo Finance). Respectez les conditions d'utilisation des fournisseurs de données.
- Les suggestions ne sont pas des conseils financiers; utilisez-les à vos risques et périls.
- Adapter les univers de titres dans `src/config.py`.
