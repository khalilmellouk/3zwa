"""
Gestion des embeddings vectoriels et de ChromaDB.
Modifiez ici le modèle d'embedding ou le backend vectoriel.
"""
import math
import hashlib
from app.core.config import DATA_DIR

# ── Dépendances optionnelles ──────────────────────────────────────────────────
try:
    import chromadb
    HAS_CHROMA = True
except ImportError:
    HAS_CHROMA = False

try:
    from sentence_transformers import SentenceTransformer
    _ST_MODEL = SentenceTransformer(
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    HAS_ST = True
except ImportError:
    _ST_MODEL = None
    HAS_ST = False

# ── Singletons ChromaDB ───────────────────────────────────────────────────────
_chroma_client = None
_col_suppliers = None
_col_docs      = None


def _get_chroma():
    """Retourne (collection_fournisseurs, collection_docs) — lazy init."""
    global _chroma_client, _col_suppliers, _col_docs
    if not HAS_CHROMA:
        return None, None
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=str(DATA_DIR / "chroma_db"))
        _col_suppliers = _chroma_client.get_or_create_collection(
            "fournisseurs", metadata={"hnsw:space": "cosine"})
        _col_docs = _chroma_client.get_or_create_collection(
            "demandes_docs", metadata={"hnsw:space": "cosine"})
    return _col_suppliers, _col_docs


def embed(text: str) -> list:
    """Transforme un texte en vecteur d'embedding (384 dimensions)."""
    if HAS_ST and _ST_MODEL:
        v = _ST_MODEL.encode(str(text)[:1000], normalize_embeddings=True)
        return v.tolist()
    # Fallback déterministe (sans sentence-transformers)
    seed = int(hashlib.md5(str(text)[:500].encode()).hexdigest(), 16)
    vec  = [math.sin(seed * (i + 1) * 0.001) for i in range(384)]
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def index_supplier(s: dict):
    """Indexe ou met à jour un fournisseur dans ChromaDB."""
    col, _ = _get_chroma()
    if not col:
        return
    text = (f"{s.get('supplier_name','')} {s.get('category','')} "
            f"{s.get('description','')} {s.get('products_sold','')}")
    col.upsert(
        ids=[str(s["supplier_id"])],
        embeddings=[embed(text)],
        documents=[text],
        metadatas=[{k: str(v) for k, v in s.items() if v is not None}],
    )


def index_document(demand_id: str, text: str, filename: str = ""):
    """Indexe un document PDF par chunks dans ChromaDB."""
    _, col = _get_chroma()
    if not col or not text.strip():
        return
    size, overlap, i, j = 400, 40, 0, 0
    while i < len(text):
        chunk = text[i:i + size]
        col.upsert(
            ids=[f"{demand_id}_c{j}"],
            embeddings=[embed(chunk)],
            documents=[chunk],
            metadatas=[{"demand_id": demand_id, "filename": filename, "chunk": j}],
        )
        i += size - overlap
        j += 1


def search_suppliers_chroma(query: str, n: int = 20) -> list:
    """Recherche sémantique dans ChromaDB. Retourne [] si indisponible."""
    col, _ = _get_chroma()
    if not col or col.count() == 0:
        return []
    try:
        res = col.query(
            query_embeddings=[embed(query)],
            n_results=min(n, col.count()),
            include=["metadatas", "distances"],
        )
        if res["ids"] and res["ids"][0]:
            return [
                {**res["metadatas"][0][i],
                 "_similarity": round(max(0.0, 1.0 - res["distances"][0][i]), 4)}
                for i in range(len(res["ids"][0]))
            ]
    except Exception:
        pass
    return []