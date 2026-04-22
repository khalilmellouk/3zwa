"""
Routes API — Demandes d'achat.
Modifiez ici les endpoints de création, validation, PDF et export CSV.
"""
import csv
import io
import json
import uuid
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import Response

from app.core.database import get_db
from app.models.schemas import DemandeIn, StatutUpdate
from app.services.conformite import verifier_conformite
from app.services.extraction import extract_from_pdf
from app.services.pipeline import run_pipeline
from app.services.pdf_generator import generate_pdf

try:
    import fitz
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

router = APIRouter(prefix="/api/demandes", tags=["Demandes"])


def _read_pdf_text(pdf_bytes: bytes) -> str:
    if HAS_PDF:
        import fitz as _fitz
        doc  = _fitz.open(stream=pdf_bytes, filetype="pdf")
        text = "\n".join(p.get_text() for p in doc)
        doc.close()
        return text
    return pdf_bytes.decode("utf-8", errors="ignore")


# ── Vérification conformité seule ─────────────────────────────────────────────

@router.post("/verifier-conformite")
def check_conformite(d: DemandeIn):
    return verifier_conformite(d.model_dump())


# ── Création manuelle ─────────────────────────────────────────────────────────

@router.post("")
def create_demande(d: DemandeIn):
    data    = d.model_dump()
    rapport = verifier_conformite(data)
    if not rapport["conforme"]:
        return {"conforme": False, "rapport_conformite": rapport, "message": rapport["message_global"]}

    demand_id = f"DA-{uuid.uuid4().hex[:8].upper()}"
    demand = {
        "type_produit":    d.type_produit,
        "categorie":       d.categorie,
        "quantite":        d.quantite,
        "budget_max":      d.budget_max,
        "delai_max_jours": d.delai_max_jours,
        "localisation":    d.localisation,
        "conditions":      d.conditions,
        "demandeur":       d.demandeur,
        "service":         d.service,
        "responsable":     d.responsable,
        "date_demande":    d.date_demande,
        "budget_alloue":   d.budget_alloue,
        "confiance":       1.0,
    }
    text = (f"Demandeur:{d.demandeur}\nService:{d.service}\nResponsable:{d.responsable}\n"
            f"Produit:{d.type_produit}\nCategorie:{d.categorie}\nQuantite:{d.quantite}\n"
            f"Budget:{d.budget_max} DH\nDelai:{d.delai_max_jours} jours\n"
            f"Localisation:{d.localisation}\nConditions:{d.conditions}")

    result = run_pipeline(text, demand_id, demand_override=demand)

    with get_db() as conn:
        conn.execute(
            "UPDATE demandes SET conformite_statut=?, conformite_rapport=?, conformite_date=?, "
            "responsable=?, date_demande=?, budget_alloue=? WHERE demand_id=?",
            (rapport["statut"], json.dumps(rapport, ensure_ascii=False),
             rapport["date_verification"], d.responsable, d.date_demande, d.budget_alloue, demand_id)
        )
    result["conforme"]           = True
    result["rapport_conformite"] = rapport
    return result


# ── Création PDF — Étape 1 : extraction + conformité ─────────────────────────

@router.post("/pdf-extract")
async def extract_pdf_conformite(file: UploadFile = File(...)):
    """Extrait le texte du PDF et vérifie la conformité SANS lancer l'analyse."""
    pdf_bytes = await file.read()
    text      = _read_pdf_text(pdf_bytes)
    if not text.strip():
        raise HTTPException(400, "Impossible d'extraire le texte du PDF")

    extracted              = extract_from_pdf(text)
    extracted["filename"]  = file.filename
    extracted["text_extrait"] = text[:3000]
    rapport                = verifier_conformite(extracted)
    return {"extracted": extracted, "rapport_conformite": rapport, "text_length": len(text)}


# ── Création PDF — Étape 2 : confirmation + pipeline ─────────────────────────

@router.post("/pdf-confirm")
async def confirm_pdf_demande(body: dict):
    """Lance le pipeline complet si la demande est conforme (après vérification étape 1)."""
    data    = body.get("data", {})
    text    = body.get("text_extrait", "")
    fname   = body.get("filename", "")
    rapport = verifier_conformite(data)

    if not rapport["conforme"]:
        return {"conforme": False, "rapport_conformite": rapport, "message": rapport["message_global"]}

    demand_id = f"DA-{uuid.uuid4().hex[:8].upper()}"
    demand = {
        "type_produit":    data.get("type_produit", ""),
        "categorie":       data.get("categorie", "Autre"),
        "quantite":        int(data.get("quantite", 1) or 1),
        "budget_max":      float(data["budget_max"])      if data.get("budget_max")      else None,
        "delai_max_jours": int(data["delai_max_jours"])   if data.get("delai_max_jours") else None,
        "localisation":    data.get("localisation"),
        "conditions":      data.get("conditions"),
        "demandeur":       data.get("demandeur"),
        "service":         data.get("service"),
        "responsable":     data.get("responsable"),
        "date_demande":    data.get("date_demande"),
        "budget_alloue":   float(data["budget_alloue"])   if data.get("budget_alloue")   else None,
        "confiance":       float(data.get("confiance", 0.5)),
    }
    result = run_pipeline(text or str(demand), demand_id, fname, demand_override=demand)

    with get_db() as conn:
        conn.execute(
            "UPDATE demandes SET conformite_statut=?, conformite_rapport=?, conformite_date=?, "
            "responsable=?, date_demande=?, budget_alloue=? WHERE demand_id=?",
            (rapport["statut"], json.dumps(rapport, ensure_ascii=False),
             rapport["date_verification"], demand.get("responsable"),
             demand.get("date_demande"), demand.get("budget_alloue"), demand_id)
        )
    result["conforme"]           = True
    result["rapport_conformite"] = rapport
    return result


# ── Création PDF legacy (1 étape) ─────────────────────────────────────────────

@router.post("/pdf")
async def create_demande_pdf(file: UploadFile = File(...)):
    """Route legacy — extraction + pipeline en une seule étape, sans vérification conformité."""
    pdf_bytes = await file.read()
    text      = _read_pdf_text(pdf_bytes)
    if not text.strip():
        raise HTTPException(400, "Impossible d'extraire le texte du PDF")
    demand_id = f"DA-{uuid.uuid4().hex[:8].upper()}"
    return run_pipeline(text, demand_id, file.filename)


# ── Liste des demandes ────────────────────────────────────────────────────────

@router.get("")
def list_demandes(statut: str = "", categorie: str = "", limit: int = 100):
    with get_db() as conn:
        q, args = "SELECT * FROM demandes WHERE 1=1", []
        if statut:    q += " AND statut=?";    args.append(statut)
        if categorie: q += " AND categorie=?"; args.append(categorie)
        q += " ORDER BY created_at DESC LIMIT ?"; args.append(limit)
        rows = conn.execute(q, args).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        try:    d["top_suppliers"] = json.loads(d.get("top_suppliers") or "[]")
        except: d["top_suppliers"] = []
        result.append(d)
    return result


@router.get("/export/csv")
def export_csv():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM demandes ORDER BY created_at DESC").fetchall()
    if not rows:
        return Response(content="", media_type="text/csv")
    keys = [k for k in dict(rows[0]).keys() if k != "top_suppliers"]
    buf  = io.StringIO()
    w    = csv.DictWriter(buf, fieldnames=keys, extrasaction="ignore")
    w.writeheader()
    w.writerows([dict(r) for r in rows])
    return Response(content=buf.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=historique.csv"})


@router.get("/{demand_id}")
def get_demande(demand_id: str):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM demandes WHERE demand_id=?", (demand_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Demande non trouvee")
    d = dict(row)
    try:    d["top_suppliers"] = json.loads(d.get("top_suppliers") or "[]")
    except: d["top_suppliers"] = []
    return d


# ── Mise à jour du statut ─────────────────────────────────────────────────────

@router.patch("/{demand_id}/statut")
def update_statut(demand_id: str, body: StatutUpdate):
    """
    Met à jour uniquement statut + commentaire_validation.
    Ne touche PAS aux champs originaux (conditions, type_produit, etc.).
    """
    with get_db() as conn:
        row = conn.execute("SELECT demand_id FROM demandes WHERE demand_id=?", (demand_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Demande non trouvee")
        conn.execute(
            "UPDATE demandes SET statut=?, commentaire_validation=? WHERE demand_id=?",
            (body.statut, body.commentaire or "", demand_id)
        )
    return {"ok": True, "demand_id": demand_id, "statut": body.statut}


# ── Téléchargement Bon de Commande PDF ───────────────────────────────────────

@router.get("/{demand_id}/pdf")
def get_pdf(demand_id: str):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM demandes WHERE demand_id=?", (demand_id,)).fetchone()
    if not row:
        raise HTTPException(404)
    d = dict(row)
    try:    top = json.loads(d.get("top_suppliers") or "[]")
    except: top = []
    pdf = generate_pdf(d, top, demand_id)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="BonCommande_{demand_id}.pdf"'},
    )