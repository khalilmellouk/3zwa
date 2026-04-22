"""
Gestion de la base de données SQLite.
Modifiez ici le schéma ou les migrations.
"""
import sqlite3
from app.core.config import DATA_DIR, DB_PATH


def get_db():
    """Retourne une connexion SQLite avec row_factory."""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Crée les tables et applique les migrations de colonnes manquantes."""
    DATA_DIR.mkdir(exist_ok=True)
    with get_db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS fournisseurs (
            supplier_id            TEXT PRIMARY KEY,
            supplier_name          TEXT NOT NULL,
            supplier_type          TEXT DEFAULT 'Distributeur',
            category               TEXT,
            description            TEXT,
            country                TEXT DEFAULT 'Maroc',
            city                   TEXT,
            contact_person         TEXT,
            email                  TEXT,
            phone                  TEXT,
            products_sold          TEXT,
            price_level            TEXT DEFAULT 'moyen',
            rating                 REAL DEFAULT 4.0,
            delivery_time_days     INTEGER DEFAULT 14,
            minimum_order_quantity INTEGER DEFAULT 1,
            payment_terms          TEXT DEFAULT '30 jours net',
            status                 TEXT DEFAULT 'Actif',
            created_at             TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS demandes (
            demand_id              TEXT PRIMARY KEY,
            created_at             TEXT DEFAULT (datetime('now')),
            type_produit           TEXT,
            categorie              TEXT,
            quantite               INTEGER DEFAULT 1,
            budget_max             REAL,
            budget_alloue          REAL,
            delai_max_jours        INTEGER,
            localisation           TEXT,
            conditions             TEXT,
            commentaire_validation TEXT,
            demandeur              TEXT,
            service                TEXT,
            responsable            TEXT,
            date_demande           TEXT,
            confiance              REAL DEFAULT 0.5,
            processing_time        REAL DEFAULT 0.0,
            nb_candidates          INTEGER DEFAULT 0,
            rag_answer             TEXT,
            statut                 TEXT DEFAULT 'en_attente',
            top_suppliers          TEXT,
            conformite_statut      TEXT DEFAULT 'non_verifie',
            conformite_rapport     TEXT,
            conformite_date        TEXT
        );
        """)

        # ── Migrations automatiques (colonnes ajoutées après création initiale) ──
        existing = {row[1] for row in conn.execute("PRAGMA table_info(demandes)")}
        migrations = [
            ("conformite_statut",      "TEXT DEFAULT 'non_verifie'"),
            ("conformite_rapport",     "TEXT"),
            ("conformite_date",        "TEXT"),
            ("budget_alloue",          "REAL"),
            ("responsable",            "TEXT"),
            ("date_demande",           "TEXT"),
            ("commentaire_validation", "TEXT"),
        ]
        for col, definition in migrations:
            if col not in existing:
                conn.execute(f"ALTER TABLE demandes ADD COLUMN {col} {definition}")