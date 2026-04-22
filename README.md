# Novec — Gestion des Achats
## FastAPI Backend + React Frontend

---

## Structure

```
novec/
├── backend/
│   ├── main.py           # API FastAPI complète
│   ├── requirements.txt
│   └── data/             # SQLite + ChromaDB (créé auto)
└── frontend/
    ├── src/
    │   ├── App.jsx       # Router + Navbar
    │   ├── api.js        # Client API
    │   ├── index.css     # Design Novec
    │   └── pages/
    │       ├── Dashboard.jsx
    │       ├── Fournisseurs.jsx
    │       ├── NouvelleDemande.jsx
    │       ├── Resultats.jsx
    │       ├── Historique.jsx
    │       └── QA.jsx
    ├── index.html
    ├── package.json
    └── vite.config.js
```

---

## Démarrage

### Backend

```bash
cd backend

# Installer les dépendances
pip install -r requirements.txt

# (Optionnel) Modèle spaCy français
python -m spacy download fr_core_news_lg

# Lancer
python main.py
# API disponible sur http://localhost:8000
# Docs Swagger : http://localhost:8000/docs
```

### Frontend

```bash
cd frontend

# Installer
npm install

# Développement
npm run dev
# App disponible sur http://localhost:3000

# Build production
npm run build
```

---

## API Endpoints

| Méthode | Route | Description |
|---------|-------|-------------|
| GET  | /api/status | Etat des services |
| GET  | /api/dashboard | KPIs et demandes récentes |
| GET  | /api/fournisseurs | Liste fournisseurs |
| POST | /api/fournisseurs | Ajouter un fournisseur |
| POST | /api/fournisseurs/import-csv | Importer CSV |
| POST | /api/fournisseurs/reindex | Réindexer dans ChromaDB |
| POST | /api/demandes | Créer une demande (formulaire) |
| POST | /api/demandes/pdf | Créer depuis un PDF |
| GET  | /api/demandes | Liste des demandes |
| GET  | /api/demandes/{id} | Détail d'une demande |
| PATCH| /api/demandes/{id}/statut | Changer le statut |
| GET  | /api/demandes/{id}/pdf | Télécharger la fiche PDF |
| GET  | /api/demandes/export/csv | Exporter l'historique |
| POST | /api/qa | Question-Réponse RAG |

---

## Dépendances optionnelles

L'application fonctionne sans IA si les modules ne sont pas installés :

| Module | Rôle | Fallback |
|--------|------|---------|
| ollama | Analyse LLM | Résumé automatique |
| chromadb | Base vectorielle | Recherche SQLite |
| sentence-transformers | Embeddings | Vecteur déterministe |
| pymupdf | Extraction PDF | Décodage UTF-8 |
