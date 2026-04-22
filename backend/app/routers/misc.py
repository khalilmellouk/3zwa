"""
Routes API — Dashboard, Statut système et Q&A.
"""
from fastapi import APIRouter
from app.core.database import get_db
from app.core.embeddings import _get_chroma, HAS_CHROMA, HAS_ST
from app.models.schemas import QARequest
from app.services.qa import ask_rag

try:
    import ollama
    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False

try:
    import fitz
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

try:
    from reportlab.lib.pagesizes import A4
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

router = APIRouter(tags=["Système"])


@router.get("/api/status")
def get_status():
    col, _ = _get_chroma()
    return {
        "services": {
            "analyse_documentaire":  HAS_OLLAMA,
            "base_vectorielle":      HAS_CHROMA,
            "similarite_semantique": HAS_ST,
            "extraction_pdf":        HAS_PDF,
            "generation_pdf":        HAS_REPORTLAB,
            "base_donnees":          True,
        },
        "nb_fournisseurs_indexes": col.count() if col else 0,
    }


@router.get("/api/dashboard")
def get_dashboard():
    with get_db() as conn:
        nb_dem  = conn.execute("SELECT COUNT(*) FROM demandes").fetchone()[0]
        nb_four = conn.execute("SELECT COUNT(*) FROM fournisseurs WHERE status='Actif'").fetchone()[0]
        nb_val  = conn.execute("SELECT COUNT(*) FROM demandes WHERE statut='valide'").fetchone()[0]
        nb_att  = conn.execute("SELECT COUNT(*) FROM demandes WHERE statut='en_attente'").fetchone()[0]
        avg_t   = conn.execute("SELECT AVG(processing_time) FROM demandes").fetchone()[0] or 0
        recents = conn.execute(
            "SELECT demand_id, created_at, type_produit, categorie, demandeur, statut "
            "FROM demandes ORDER BY created_at DESC LIMIT 8"
        ).fetchall()
    return {
        "nb_demandes":   nb_dem,
        "nb_fournisseurs": nb_four,
        "nb_validees":   nb_val,
        "nb_en_attente": nb_att,
        "temps_moyen":   round(avg_t, 1),
        "recentes":      [dict(r) for r in recents],
    }


@router.post("/api/qa")
def qa_endpoint(body: QARequest):
    answer = ask_rag(body.question, body.demand_id)
    return {"question": body.question, "answer": answer}