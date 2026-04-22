"""
Moteur de Questions / Réponses (RAG).
Modifiez ici les règles directes ou le prompt envoyé au LLM.
"""
import json
import hashlib
import threading
from app.core.config import OLLAMA_MODEL, QA_CACHE_MAX
from app.core.database import get_db

# ── Dépendances optionnelles ──────────────────────────────────────────────────
try:
    import ollama as _ollama
    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False

# ── Cache en mémoire ──────────────────────────────────────────────────────────
_qa_cache: dict = {}


def _cache_key(question: str, demand_id: str | None) -> str:
    return hashlib.md5(f"{question}|{demand_id}".encode()).hexdigest()


# ── Construction du contexte RAG ──────────────────────────────────────────────

def _build_context(question: str, demand_id: str | None) -> str:
    q = question.lower()
    lines = []
    with get_db() as conn:
        if demand_id:
            row = conn.execute("SELECT * FROM demandes WHERE demand_id=?", (demand_id,)).fetchone()
            if row:
                d = dict(row)
                lines.append(f"=== Demande {d['demand_id']} ===")
                for k, v in [
                    ("Produit",       d.get("type_produit")),
                    ("Categorie",     d.get("categorie")),
                    ("Quantite",      d.get("quantite")),
                    ("Budget max",    str(d.get("budget_max") or "Non precise") + " DH"),
                    ("Budget alloue", str(d.get("budget_alloue") or "Non precise") + " DH"),
                    ("Delai max",     str(d.get("delai_max_jours") or "Non precise") + " jours"),
                    ("Demandeur",     d.get("demandeur")),
                    ("Responsable",   d.get("responsable")),
                    ("Service",       d.get("service")),
                    ("Date",          d.get("date_demande")),
                    ("Localisation",  d.get("localisation")),
                    ("Conditions",    d.get("conditions") or "Aucune"),
                    ("Statut",        d.get("statut")),
                    ("Conformite",    d.get("conformite_statut")),
                ]:
                    lines.append(f"{k} : {v or '—'}")
                try:
                    top = json.loads(d.get("top_suppliers") or "[]")
                    if top:
                        lines.append(f"Fournisseurs selectionnes ({len(top)}) :")
                        for s in top:
                            lines.append(
                                f"  Rang {s.get('rank')} - {s.get('supplier_name')} "
                                f"({s.get('score_percent')}%) : {s.get('justification', '')}"
                            )
                    else:
                        lines.append("Fournisseurs : aucun selectionne")
                except Exception:
                    pass
        else:
            rows = conn.execute("SELECT * FROM demandes ORDER BY created_at DESC LIMIT 20").fetchall()
            if rows:
                lines.append(f"=== {len(rows)} demande(s) ===")
                for r in rows:
                    d = dict(r)
                    sup_names = ""
                    try:
                        top = json.loads(d.get("top_suppliers") or "[]")
                        sup_names = ", ".join(s.get("supplier_name", "") for s in top)
                    except Exception:
                        pass
                    lines.append(
                        f"- {d['demand_id']} | {d.get('created_at', '')[:10]} | "
                        f"{d.get('type_produit', '?')} | Qte:{d.get('quantite', 1)} | "
                        f"Budget:{d.get('budget_max') or 'N/A'} DH | "
                        f"Statut:{d.get('statut', '?')} | Fournisseurs:{sup_names or '—'}"
                    )

        fkw = ["fournisseur", "supplier", "prestataire", "vendeur", "qui", "quel",
               "meilleur", "propose", "contact", "email", "pays", "prix", "delai", "note"]
        if any(k in q for k in fkw):
            rows_f = conn.execute(
                "SELECT * FROM fournisseurs WHERE status='Actif' ORDER BY rating DESC LIMIT 15"
            ).fetchall()
            if rows_f:
                lines.append(f"=== {len(rows_f)} fournisseur(s) actif(s) ===")
                for r in rows_f:
                    f = dict(r)
                    lines.append(
                        f"- {f.get('supplier_name', '—')} | {f.get('category', '—')} | "
                        f"Pays:{f.get('country', '—')} | Prix:{f.get('price_level', '—')} | "
                        f"Note:{f.get('rating', '—')}/5 | Delai:{f.get('delivery_time_days', '—')}j"
                    )
    return "\n".join(lines)


# ── Règles directes (sans LLM) ────────────────────────────────────────────────

def _rule_based_answer(question: str, demand_id: str | None) -> str | None:
    """
    Répond instantanément aux questions fréquentes via SQL.
    Ajouter/modifier des règles ici pour enrichir les réponses sans LLM.
    """
    q = question.lower().strip()
    with get_db() as conn:

        if any(k in q for k in ["combien", "nombre", "total", "statistique"]):
            nb_dem  = conn.execute("SELECT COUNT(*) FROM demandes").fetchone()[0]
            nb_four = conn.execute("SELECT COUNT(*) FROM fournisseurs WHERE status='Actif'").fetchone()[0]
            nb_val  = conn.execute("SELECT COUNT(*) FROM demandes WHERE statut='valide'").fetchone()[0]
            nb_att  = conn.execute("SELECT COUNT(*) FROM demandes WHERE statut='en_attente'").fetchone()[0]
            return (f"Statistiques :\n  - {nb_dem} demande(s)\n"
                    f"  - {nb_val} validee(s), {nb_att} en attente\n"
                    f"  - {nb_four} fournisseur(s) actif(s)")

        if any(k in q for k in ["dernier", "derniere", "recent", "nouveau"]):
            row = conn.execute("SELECT * FROM demandes ORDER BY created_at DESC LIMIT 1").fetchone()
            if row:
                d = dict(row)
                top = []
                try: top = json.loads(d.get("top_suppliers") or "[]")
                except: pass
                rep = (f"Derniere demande : {d['demand_id']}\n"
                       f"  - Produit : {d.get('type_produit', '?')}\n"
                       f"  - Budget : {d.get('budget_max') or 'Non precise'} DH\n"
                       f"  - Statut : {d.get('statut', '?')}")
                if top:
                    rep += "\nFournisseurs :"
                    for s in top:
                        rep += f"\n  - Rang {s.get('rank')} : {s.get('supplier_name')} ({s.get('score_percent')}%)"
                return rep

        if any(k in q for k in ["budget", "montant", "cout"]):
            if demand_id:
                row = conn.execute("SELECT type_produit, budget_max FROM demandes WHERE demand_id=?", (demand_id,)).fetchone()
                if row:
                    b = row["budget_max"]
                    return f"Budget de '{row['type_produit']}' : {str(round(b, 2)) + ' DH' if b else 'non precise'}."
            row = conn.execute(
                "SELECT demand_id, type_produit, budget_max, demandeur FROM demandes "
                "WHERE budget_max IS NOT NULL ORDER BY budget_max DESC LIMIT 1"
            ).fetchone()
            if row:
                return (f"Budget le plus eleve : '{row['type_produit']}' ({row['demand_id']}) — "
                        f"{row['budget_max']:.2f} DH.")

        if any(k in q for k in ["en attente", "attente", "a valider"]):
            rows = conn.execute(
                "SELECT demand_id, type_produit, created_at FROM demandes WHERE statut='en_attente' ORDER BY created_at DESC"
            ).fetchall()
            if rows:
                rep = f"{len(rows)} demande(s) en attente :\n"
                for r in rows:
                    rep += f"  - {r['demand_id']} — {r['type_produit']} — {r['created_at'][:10]}\n"
                return rep.strip()
            return "Aucune demande en attente."

        if any(k in q for k in ["statut", "status", "etat"]):
            if demand_id:
                row = conn.execute("SELECT type_produit, statut FROM demandes WHERE demand_id=?", (demand_id,)).fetchone()
                if row:
                    return f"Statut de '{row['type_produit']}' : {row['statut'].upper()}"

        if any(k in q for k in ["meilleur fournisseur", "top fournisseur", "mieux note"]):
            rows = conn.execute(
                "SELECT * FROM fournisseurs WHERE status='Actif' ORDER BY rating DESC LIMIT 3"
            ).fetchall()
            if rows:
                rep = "Fournisseurs les mieux notes :\n"
                for i, r in enumerate(rows, 1):
                    f = dict(r)
                    rep += f"  {i}. {f['supplier_name']} — {f.get('category', chr(8212))} — Note:{f['rating']}/5\n"
                return rep.strip()

    return None


# ── Point d'entrée Q&A ────────────────────────────────────────────────────────

def ask_rag(question: str, demand_id: str | None = None) -> str:
    """
    Pipeline Q&A :
    1. Cache mémoire (instantané)
    2. Règles directes SQL (instantané)
    3. Contexte RAG → LLM Ollama (avec timeout 20s)
    4. Fallback : contexte brut si timeout
    """
    # 1. Cache
    key = _cache_key(question, demand_id)
    if key in _qa_cache:
        return _qa_cache[key]

    # 2. Règles directes
    direct = _rule_based_answer(question, demand_id)
    if direct:
        _qa_cache[key] = direct
        return direct

    # 3. Contexte RAG
    context = _build_context(question, demand_id)
    if not context.strip():
        return "Aucune donnee disponible."

    if not HAS_OLLAMA:
        return f"Informations disponibles :\n\n{context}"

    context_court = context[:800] + ("..." if len(context) > 800 else "")
    prompt = (
        f"Données:\n{context_court}\n\n"
        f"Question: {question}\n\n"
        f"Réponds en français en 2-3 phrases max en utilisant UNIQUEMENT les données ci-dessus. "
        f"Si l'info n'est pas dans les données, dis-le clairement.\nRéponse:"
    )

    result = [None]

    def _call():
        try:
            resp = _ollama.chat(
                model=OLLAMA_MODEL,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.0, "num_predict": 150, "num_ctx": 1024, "top_k": 10, "top_p": 0.5},
            )
            result[0] = resp["message"]["content"].strip()
        except Exception as e:
            print(f"[QA] Ollama error: {e}")

    t = threading.Thread(target=_call, daemon=True)
    t.start()
    t.join(timeout=20)

    if result[0]:
        if len(_qa_cache) >= QA_CACHE_MAX:
            _qa_cache.pop(next(iter(_qa_cache)))
        _qa_cache[key] = result[0]
        return result[0]

    return f"Informations disponibles :\n\n{context}"