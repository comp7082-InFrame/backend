from datetime import datetime
from uuid import UUID
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.term import Term
from app.schemas.term import TermResponse

router = APIRouter()



@router.get("/by_date/", response_model=List[TermResponse])
def get_terms(
    date: datetime,
    db: Session = Depends(get_db)
):
    terms = (db.query(Term).filter(
        Term.start_date <= date,
        Term.end_date >= date
    ))


    return terms.all()

@router.get("/", response_model=List[TermResponse])
def get_terms(
    term_id: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Term)

    if term_id:
        query = query.filter(Term.id == term_id)

    return query.all()
