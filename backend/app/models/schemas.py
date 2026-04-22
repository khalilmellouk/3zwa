"""
Schémas Pydantic — modifiez ici les champs des requêtes/réponses API.
"""
from pydantic import BaseModel
from typing import Optional


class SupplierIn(BaseModel):
    supplier_id: str
    supplier_name: str
    supplier_type: str = "Distributeur"
    category: str = ""
    description: str = ""
    country: str = "Maroc"
    city: str = ""
    contact_person: str = ""
    email: str = ""
    phone: str = ""
    products_sold: str = ""
    price_level: str = "moyen"
    rating: float = 4.0
    delivery_time_days: int = 14
    minimum_order_quantity: int = 1
    payment_terms: str = "30 jours net"
    status: str = "Actif"


class DemandeIn(BaseModel):
    demandeur: str
    responsable: Optional[str] = None
    service: Optional[str] = None
    date_demande: Optional[str] = None
    type_produit: str
    categorie: str
    quantite: int = 1
    budget_max: Optional[float] = None
    budget_alloue: Optional[float] = None
    delai_max_jours: Optional[int] = None
    localisation: Optional[str] = "Maroc"
    conditions: Optional[str] = None


class StatutUpdate(BaseModel):
    statut: str
    commentaire: Optional[str] = ""
    validated_by: Optional[str] = ""


class QARequest(BaseModel):
    question: str
    demand_id: Optional[str] = None