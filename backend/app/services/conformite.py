"""
Vérification de conformité des demandes d'achat.
Modifiez ici les règles de validation (champs obligatoires, seuils budget, etc.).
"""
from datetime import datetime


def verifier_conformite(data: dict) -> dict:
    """
    Vérifie la conformité avant analyse IA.
    Retourne un rapport complet avec problèmes bloquants et avertissements.
    """
    problemes      = []
    avertissements = []

    # ── Règles bloquantes ─────────────────────────────────────────────────────

    if not str(data.get("demandeur") or "").strip():
        problemes.append({
            "code":    "SIGNATURE_MANQUANTE",
            "type":    "bloquant",
            "champ":   "demandeur",
            "message": "La demande n'est pas signee : le nom du demandeur est absent.",
        })

    if not str(data.get("responsable") or "").strip():
        problemes.append({
            "code":    "VISA_MANQUANT",
            "type":    "bloquant",
            "champ":   "responsable",
            "message": "Le visa du responsable hierarchique est absent.",
        })

    if not str(data.get("type_produit") or "").strip():
        problemes.append({
            "code":    "PRODUIT_MANQUANT",
            "type":    "bloquant",
            "champ":   "type_produit",
            "message": "La designation du produit ou de la prestation est absente.",
        })

    try:
        if int(data.get("quantite", 1)) <= 0:
            raise ValueError
    except (ValueError, TypeError):
        problemes.append({
            "code":    "QUANTITE_INVALIDE",
            "type":    "bloquant",
            "champ":   "quantite",
            "message": "La quantite demandee doit etre superieure a zero.",
        })

    # ── Dépassement de budget ─────────────────────────────────────────────────
    budget_max    = data.get("budget_max")
    budget_alloue = data.get("budget_alloue")
    if budget_max and budget_alloue:
        try:
            bm  = float(budget_max)
            ba  = float(budget_alloue)
            if bm > ba:
                dep = bm - ba
                pct = round((dep / ba) * 100, 1)
                entry = {
                    "champ":       "budget_max",
                    "depassement": dep,
                    "pourcentage": pct,
                    "message": (
                        f"Depassement de budget : {bm:,.0f} DH demandes pour "
                        f"{ba:,.0f} DH alloues (depassement de {dep:,.0f} DH soit +{pct}%)."
                    ),
                }
                if pct > 20:
                    entry["code"] = "DEPASSEMENT_BUDGET_CRITIQUE"
                    entry["type"] = "bloquant"
                    entry["message"] += " Autorisation speciale requise."
                    problemes.append(entry)
                else:
                    entry["code"] = "DEPASSEMENT_BUDGET_MINEUR"
                    entry["type"] = "avertissement"
                    entry["message"] += " Validation recommandee."
                    avertissements.append(entry)
        except (ValueError, TypeError):
            pass

    # ── Avertissements ────────────────────────────────────────────────────────

    if not str(data.get("service") or "").strip():
        avertissements.append({
            "code":    "SERVICE_MANQUANT",
            "type":    "avertissement",
            "champ":   "service",
            "message": "Le service emetteur n'est pas renseigne.",
        })

    if not data.get("date_demande"):
        avertissements.append({
            "code":    "DATE_MANQUANTE",
            "type":    "avertissement",
            "champ":   "date_demande",
            "message": "La date de la demande n'est pas renseignee.",
        })

    # ── Résultat ──────────────────────────────────────────────────────────────
    conforme = len(problemes) == 0
    return {
        "conforme":          conforme,
        "statut":            "conforme" if conforme else "non_conforme",
        "nb_problemes":      len(problemes),
        "nb_avertissements": len(avertissements),
        "problemes":         problemes,
        "avertissements":    avertissements,
        "date_verification": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "message_global": (
            "La demande est conforme et peut etre transmise a l'analyse."
            if conforme else
            f"La demande presente {len(problemes)} probleme(s) bloquant(s) et ne peut pas etre traitee."
        ),
    }