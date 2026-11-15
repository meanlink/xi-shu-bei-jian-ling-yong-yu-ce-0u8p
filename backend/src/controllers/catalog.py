from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from src.config.database import get_db
from src.middlewares.auth import current_user
from src.models import Dataset, Job, Report, Audit
from src.services.business import metadata
from src.services import approvals
router=APIRouter()
@router.get('/meta')
def meta():return metadata()
@router.get('/overview')
def overview(db=Depends(get_db),user=Depends(current_user)):
    jobs=db.scalars(select(Job)).all()
    released=sum(1 for v in approvals.views(db,jobs).values() if v['released'])
    return {'datasets':db.scalar(select(func.count()).select_from(Dataset)), 'records':sum(len(d.records) for d in db.scalars(select(Dataset))), 'jobs':len(jobs), 'released':released, 'reports':db.scalar(select(func.count()).select_from(Report))}
@router.get('/audits')
def audits(db=Depends(get_db),user=Depends(current_user)):
    return [{'id':a.id,'actor':a.actor,'action':a.action,'detail':a.detail,'at':a.at} for a in db.scalars(select(Audit).order_by(Audit.id.desc()).limit(50))]
