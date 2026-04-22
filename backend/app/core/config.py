"""
Configuration globale — modifiez ici les paramètres de l'application.
"""
from pathlib import Path

# ── Chemins ───────────────────────────────────────────────────────────────────
DATA_DIR = Path("data")
DB_PATH  = DATA_DIR / "procurement.db"
CHROMA_PATH = DATA_DIR / "chroma_db"

# ── Modèle LLM local ──────────────────────────────────────────────────────────
OLLAMA_MODEL = "qwen2.5:3b"

# ── Cache Q&A ─────────────────────────────────────────────────────────────────
QA_CACHE_MAX = 100

# ── Catégories produits ───────────────────────────────────────────────────────
CATEGORIES = [
    "Informatique", "Fournitures de bureau", "Mobilier",
    "Electronique", "Hygiene et Entretien", "Logiciels",
    "Emballage", "Equipements industriels", "Services", "Autre",
]

# ── Mots-clés par catégorie (extraction automatique) ─────────────────────────
CATEGORY_KEYWORDS = {
    "Mobilier":               ["mobilier de bureau", "mobilier", "fauteuil ergonomique",
                               "armoire de rangement", "bureau en l"],
    "Fournitures de bureau":  ["fournitures de bureau", "papeterie", "stylo", "papier",
                               "classeur", "ramette", "agrafeuse", "post-it"],
    "Informatique":           ["informatique", "ordinateur", "laptop", "pc", "ecran",
                               "imprimante", "serveur"],
    "Electronique":           ["electronique", "telephone", "tablette", "cable"],
    "Logiciels":              ["logiciel", "licence", "abonnement", "software"],
    "Hygiene et Entretien":   ["hygiene", "nettoyage", "desinfectant"],
    "Equipements industriels":["machine", "outillage", "pompe", "moteur"],
    "Services":               ["prestation", "formation", "maintenance", "audit"],
}

# ── Scoring fournisseurs — poids ──────────────────────────────────────────────
SCORE_WEIGHTS = {
    "semantique": 0.30,
    "prix":       0.20,
    "rating":     0.20,
    "delai":      0.15,
    "quantite":   0.10,
    "geo":        0.05,
}

PRICE_SCORE = {"bas": 1.0, "moyen": 0.65, "eleve": 0.30, "élevé": 0.30}