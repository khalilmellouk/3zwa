"""
Scoring et matching des fournisseurs.
Modifiez ici les poids de scoring ou les critères d'élimination.
"""
import re
from app.core.config import PRICE_SCORE, SCORE_WEIGHTS
from app.core.embeddings import search_suppliers_chroma
from app.core.database import get_db


# ── Justification textuelle ───────────────────────────────────────────────────

def _build_justification(s: dict, s_sem: float) -> str:
    parts = []
    cat = s.get("category", "")
    if s_sem >= 0.70 and cat:
        parts.append(f"specialise en {cat}")
    r = float(s.get("rating", 0) or 0)
    if r >= 4.5:
        parts.append(f"note {r}/5")
    elif r >= 4.0:
        parts.append(f"bonne note {r}/5")
    pl = str(s.get("price_level", "")).lower()
    if pl == "bas":
        parts.append("prix bas")
    elif pl == "moyen":
        parts.append("prix competitif")
    d = s.get("delivery_time_days")
    if d and int(float(d)) <= 7:
        parts.append(f"livraison rapide ({d}j)")
    elif d:
        parts.append(f"delai {d}j")
    if s.get("country"):
        parts.append(f"base en {s['country']}")
    if not parts:
        parts.append("profil correspondant")
    return f"{s.get('supplier_name', '')} : {', '.join(parts[:3])}."


# ── Calcul de score ───────────────────────────────────────────────────────────

def _compute_score(s: dict, demand: dict, max_del: int) -> dict:
    """Calcule les sous-scores et le score global."""
    s_sem    = float(s.get("_similarity", 0.0))
    pl       = str(s.get("price_level", "moyen")).lower()
    s_prix   = PRICE_SCORE.get(pl, 0.5)
    rating   = max(3.0, min(5.0, float(s.get("rating", 4.0) or 4.0)))
    s_rating = (rating - 3.0) / 2.0
    delivery = int(float(s.get("delivery_time_days", 14) or 14))
    s_delai  = max(0.0, 1.0 - delivery / max_del) if max_del else 1.0
    moq      = int(float(s.get("minimum_order_quantity", 1) or 1))
    s_qte    = 1.0 if (moq <= 0 or demand.get("quantite", 1) >= moq) else demand.get("quantite", 1) / moq
    loc      = str(demand.get("localisation") or "").lower()
    sc       = str(s.get("country", "")).lower()
    s_geo    = (1.0 if sc == loc else
                0.75 if sc in ("maroc", "algérie", "tunisie") and loc in ("maroc", "algérie", "tunisie") else
                0.5  if not loc else 0.30)

    w = SCORE_WEIGHTS
    score = (w["semantique"] * s_sem + w["prix"]     * s_prix   +
             w["rating"]     * s_rating + w["delai"] * s_delai  +
             w["quantite"]   * s_qte   + w["geo"]    * s_geo)

    return {
        **s,
        "score_global":  round(score, 4),
        "score_percent": round(score * 100),
        "s_sem":   round(s_sem, 3),   "s_prix":   round(s_prix, 3),
        "s_rating":round(s_rating, 3),"s_delai":  round(s_delai, 3),
        "s_qte":   round(s_qte, 3),   "s_geo":    round(s_geo, 3),
        "justification": _build_justification(s, s_sem),
        "niveau": ("Tres pertinent" if score >= 0.75 else
                   "Pertinent"      if score >= 0.55 else
                   "Acceptable"     if score >= 0.35 else "Faible"),
    }


def _score_with_filters(s: dict, demand: dict, max_del: int) -> dict | None:
    """Score avec critères éliminatoires (délai, MOQ)."""
    if str(s.get("status", "Actif")).lower() not in ("actif", "active", "1", "true", ""):
        return None
    delivery = int(float(s.get("delivery_time_days", 14) or 14))
    moq      = int(float(s.get("minimum_order_quantity", 1) or 1))
    if demand.get("delai_max_jours") and delivery > demand["delai_max_jours"]:
        return None
    if moq > 0 and demand.get("quantite", 1) and moq > demand["quantite"] * 3:
        return None
    return _compute_score(s, demand, max_del)


def _score_no_filter(s: dict, demand: dict, max_del: int) -> dict | None:
    """Score sans critères éliminatoires — garantit au moins 3 résultats."""
    if str(s.get("status", "Actif")).lower() not in ("actif", "active", "1", "true", ""):
        return None
    return _compute_score(s, demand, max_del)


# ── Similarité par mots-clés (fallback sans ChromaDB) ────────────────────────

def _keyword_similarity(query: str, supplier: dict) -> float:
    q_words = set(w for w in re.split(r'\W+', query.lower()) if len(w) > 2)
    text = " ".join([
        str(supplier.get("supplier_name", "")),
        str(supplier.get("category", "")),
        str(supplier.get("description", "")),
        str(supplier.get("products_sold", "")),
        str(supplier.get("supplier_type", "")),
    ]).lower()
    if not q_words:
        return 0.5
    matches  = sum(1 for w in q_words if w in text)
    kw_score = matches / len(q_words)
    sup_cat  = str(supplier.get("category", "")).lower()
    if sup_cat and any(w in query.lower() for w in sup_cat.split()):
        kw_score = min(1.0, kw_score + 0.3)
    return round(min(1.0, kw_score), 4)


# ── Pipeline de matching principal ────────────────────────────────────────────

def match_suppliers(demand: dict) -> list:
    """
    Retourne les 3 meilleurs fournisseurs pour une demande donnée.
    1. Recherche sémantique ChromaDB (si disponible)
    2. Fallback : similarité par mots-clés sur la BDD SQLite
    3. Score avec filtres → fallback sans filtres si < 3 résultats
    """
    query      = f"{demand['type_produit']} {demand['categorie']} {demand.get('conditions', '')}"
    candidates = search_suppliers_chroma(query)

    # Fallback SQLite
    if not candidates:
        with get_db() as conn:
            rows = conn.execute("SELECT * FROM fournisseurs WHERE status='Actif'").fetchall()
        for row in rows:
            d   = dict(row)
            sim = _keyword_similarity(query, d)
            candidates.append({**d, "_similarity": sim})

    if not candidates:
        return []

    max_del = max(int(float(c.get("delivery_time_days", 14) or 14)) for c in candidates)
    scored  = [r for r in (_score_with_filters(c, demand, max_del) for c in candidates) if r]

    # Fallback sans filtres éliminatoires
    if len(scored) < 3:
        scored = [r for r in (_score_no_filter(c, demand, max_del) for c in candidates) if r]

    scored.sort(key=lambda x: x["score_global"], reverse=True)
    for i, s in enumerate(scored):
        s["rank"] = i + 1
    return scored[:3]


def build_summary(demand: dict, top: list) -> str:
    """Résumé textuel de la sélection fournisseurs."""
    if not top:
        return "Aucun fournisseur eligible identifie."
    lines = [f"Demande : {demand['type_produit']} — {demand['categorie']} — Qte : {demand['quantite']}."]
    if demand.get("budget_max"):
        lines.append(f"Budget : {demand['budget_max']:.0f} DH.")
    lines.append(f"{len(top)} fournisseur(s) selectionne(s) :")
    for s in top:
        lines.append(f"  Rang {s['rank']} — {s['supplier_name']} ({s['score_percent']}%) : {s.get('justification', '')}")
    return "\n".join(lines)