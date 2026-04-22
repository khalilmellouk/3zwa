"""
Routes API — Fournisseurs.
Modifiez ici les endpoints CRUD ou ajoutez de nouvelles routes fournisseurs.
"""
import csv
import io
import uuid
from fastapi import APIRouter, HTTPException, UploadFile, File
from app.core.database import get_db
from app.core.embeddings import index_supplier
from app.models.schemas import SupplierIn

router = APIRouter(prefix="/api/fournisseurs", tags=["Fournisseurs"])

_INSERT_SQL = """
    INSERT OR REPLACE INTO fournisseurs
    (supplier_id, supplier_name, supplier_type, category, description, country, city,
     contact_person, email, phone, products_sold, price_level, rating,
     delivery_time_days, minimum_order_quantity, payment_terms, status)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
"""


def _supplier_values(s: dict) -> list:
    return [
        s["supplier_id"], s["supplier_name"], s["supplier_type"],
        s["category"], s["description"], s["country"], s["city"],
        s["contact_person"], s["email"], s["phone"], s["products_sold"],
        s["price_level"], s["rating"], s["delivery_time_days"],
        s["minimum_order_quantity"], s["payment_terms"], s["status"],
    ]


@router.get("")
def list_fournisseurs(search: str = "", category: str = ""):
    with get_db() as conn:
        q, args = "SELECT * FROM fournisseurs WHERE 1=1", []
        if search:
            q += " AND (supplier_name LIKE ? OR city LIKE ? OR products_sold LIKE ?)"
            args += [f"%{search}%"] * 3
        if category:
            q += " AND category=?"
            args.append(category)
        q += " ORDER BY supplier_name"
        rows = conn.execute(q, args).fetchall()
    return [dict(r) for r in rows]


@router.get("/{supplier_id}")
def get_fournisseur(supplier_id: str):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM fournisseurs WHERE supplier_id=?", (supplier_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Fournisseur non trouve")
    return dict(row)


@router.post("")
def create_fournisseur(s: SupplierIn):
    data = s.model_dump()
    with get_db() as conn:
        conn.execute(_INSERT_SQL, _supplier_values(data))
    index_supplier(data)
    return {"ok": True, "supplier_id": s.supplier_id}


@router.post("/import-csv")
async def import_csv(file: UploadFile = File(...)):
    raw     = await file.read()
    rows_ok = rows_err = 0

    for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            reader = csv.DictReader(io.StringIO(raw.decode(enc)))
            rows   = list(reader)
            break
        except Exception:
            continue
    else:
        raise HTTPException(400, "Impossible de decoder le CSV")

    for row in rows:
        try:
            s = {
                "supplier_id":            str(row.get("supplier_id", "")).strip() or str(uuid.uuid4())[:8],
                "supplier_name":          str(row.get("supplier_name", "")).strip(),
                "supplier_type":          str(row.get("supplier_type", "Distributeur")).strip(),
                "category":               str(row.get("category", "")).strip(),
                "description":            str(row.get("description", "")).strip(),
                "country":                str(row.get("country", "Maroc")).strip(),
                "city":                   str(row.get("city", "")).strip(),
                "contact_person":         str(row.get("contact_person", "")).strip(),
                "email":                  str(row.get("email", "")).strip(),
                "phone":                  str(row.get("phone", "")).strip(),
                "products_sold":          str(row.get("products_sold", "")).strip(),
                "price_level":            str(row.get("price_level", "moyen")).strip().lower(),
                "rating":                 float(row.get("rating", 4.0) or 4.0),
                "delivery_time_days":     int(float(row.get("delivery_time_days", 14) or 14)),
                "minimum_order_quantity": int(float(row.get("minimum_order_quantity", 1) or 1)),
                "payment_terms":          str(row.get("payment_terms", "30 jours net")).strip(),
                "status":                 str(row.get("status", "Actif")).strip(),
            }
            if not s["supplier_name"]:
                continue
            with get_db() as conn:
                conn.execute(_INSERT_SQL, _supplier_values(s))
            index_supplier(s)
            rows_ok += 1
        except Exception:
            rows_err += 1

    return {"imported": rows_ok, "errors": rows_err}


@router.post("/reindex")
def reindex_all():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM fournisseurs").fetchall()
    for r in rows:
        index_supplier(dict(r))
    return {"reindexed": len(rows)}