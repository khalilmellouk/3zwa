"""
Novec — Gestion des Achats
Point d'entrée FastAPI.

Pour démarrer :
    uvicorn main:app --reload --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import init_db
from app.routers import fournisseurs, demandes, misc

init_db()

app = FastAPI(title="Novec Procurement API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://stagesimo.netlify.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(fournisseurs.router)
app.include_router(demandes.router)
app.include_router(misc.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)