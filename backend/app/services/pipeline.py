"""
Pipeline principal de traitement des demandes d'achat.
Modifiez ici la logique d'orchestration extraction → scoring → sauvegarde.
"""
import json
import time
from app.core.database import get_db
from app.core.embeddings import index_document
from app.services.extraction import extract_from_text
from app.services.scoring import match_suppliers, build_summary


def run_pipeline(text: str, demand_id: str,
                 pdf_filename: str = "",
                 demand_override: dict | None = None) -> dict:
    """
    Pipeline complet :
    1. Extraction des données (texte ou override manuel)
    2. Indexation dans ChromaDB
    3. Matching fournisseurs + scoring
    4. Sauvegarde en base SQLite

    Retourne le résultat complet avec top_suppliers et rag_answer.
    """
    t0     = time.time()
    demand = demand_override or extract_from_text(text)

    if text.strip():
        index_document(demand_id, text, pdf_filename)

    top    = match_suppliers(demand)
    answer = build_summary(demand, top)
    dur    = round(time.time() - t0, 2)

    with get_db() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO demandes
            (demand_id, type_produit, categorie, quantite, budget_max,
             delai_max_jours, localisation, conditions, demandeur, service,
             confiance, processing_time, nb_candidates, rag_answer, top_suppliers)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            demand_id,
            demand["type_produit"],
            demand["categorie"],
            demand["quantite"],
            demand.get("budget_max"),
            demand.get("delai_max_jours"),
            demand.get("localisation"),
            demand.get("conditions"),
            demand.get("demandeur"),
            demand.get("service"),
            demand.get("confiance", 0.5),
            dur,
            len(top),
            answer,
            json.dumps(top, ensure_ascii=False),
        ))

    return {
        "demand_id":       demand_id,
        "demand":          demand,
        "top_suppliers":   top,
        "rag_answer":      answer,
        "processing_time": dur,
    }