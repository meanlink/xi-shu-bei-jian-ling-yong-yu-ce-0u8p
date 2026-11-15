from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from src.config.database import get_db
from src.models import Job
from src.schemas.job import JobInput
from src.middlewares.auth import current_user, can_write, admin_only
from src.services import jobs, approvals
from src.services.audit import record
from src.utils.serialization import job_dict
router=APIRouter(prefix='/jobs')
@router.get('')
def listing(db=Depends(get_db),u=Depends(current_user)):
    rows=db.scalars(select(Job).order_by(Job.id.desc()).limit(100)).all()
    vs=approvals.views(db,rows)
    return [job_dict(j,vs[j.id]) for j in rows]
@router.post('',status_code=201)
def create(data:JobInput,db=Depends(get_db),u=Depends(can_write)):
    j=jobs.create(db,data,u); record(db,u.email,'job.create',{'id':j.id,'params':j.params})
    db.commit(); jobs.enqueue(j.id); return job_dict(j,approvals.view(db,j))
@router.get('/{id}')
def detail(id:int,db=Depends(get_db),u=Depends(current_user)):
    j=db.get(Job,id)
    if not j: raise HTTPException(404,'分析任务不存在')
    return job_dict(j,approvals.view(db,j))
@router.post('/{id}/approve')
def approve(id:int,db=Depends(get_db),u=Depends(admin_only)):
    j=db.scalar(select(Job).where(Job.id==id).with_for_update())
    if not j: raise HTTPException(404,'分析任务不存在')
    v,changed=approvals.approve(db,j,u)
    if changed: record(db,u.email,'job.approve',{'id':id,'valid':v['valid_count'],'released':v['released']})
    db.commit()
    return job_dict(j,v)
@router.post('/{id}/withdraw')
def withdraw(id:int,db=Depends(get_db),u=Depends(admin_only)):
    j=db.scalar(select(Job).where(Job.id==id).with_for_update())
    if not j: raise HTTPException(404,'分析任务不存在')
    v,changed=approvals.withdraw(db,j,u)
    if changed: record(db,u.email,'job.withdraw',{'id':id,'valid':v['valid_count'],'released':v['released']})
    db.commit()
    return job_dict(j,v)
