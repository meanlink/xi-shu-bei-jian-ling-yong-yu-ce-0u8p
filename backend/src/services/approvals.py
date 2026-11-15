"""双人会签：两名不同负责人同意才放行分发；创建人不计票；意见可撤回，按生效顺序裁决。"""
import time
from fastapi import HTTPException
from sqlalchemy import select
from src.models import Approval

REQUIRED = 2  # 放行所需的不同负责人会签数


def _group_events(db, job_ids):
    rows = db.scalars(select(Approval).where(Approval.job_id.in_(job_ids)).order_by(Approval.id)).all() if job_ids else []
    grouped = {i: [] for i in job_ids}
    for row in rows:
        grouped[row.job_id].append(row)
    return grouped


def _view(job, events):
    latest, legacy = {}, []
    for e in events:
        if e.action == 'legacy':
            legacy.append(e)  # 旧版批准记录只作历史凭据，不参与计票
        else:
            latest[e.reviewer_id] = e  # 同一复核人按实际生效顺序取最后一条
    valid = [e for e in latest.values() if e.action == 'approve' and e.reviewer_id != job.created_by]
    return {
        'required': REQUIRED,
        'released': len(valid) >= REQUIRED,
        'valid_count': len(valid),
        'opinions': [{'reviewer_id': e.reviewer_id, 'reviewer': e.reviewer_name, 'email': e.reviewer_email,
                      'action': e.action, 'at': e.created_at} for e in sorted(latest.values(), key=lambda x: x.created_at)],
        'valid': [{'reviewer': e.reviewer_name, 'email': e.reviewer_email, 'at': e.created_at}
                  for e in sorted(valid, key=lambda x: x.created_at)],
        'legacy': [{'reviewer': e.reviewer_name, 'at': e.created_at} for e in legacy],
    }


def views(db, jobs):
    grouped = _group_events(db, [j.id for j in jobs])
    return {j.id: _view(j, grouped[j.id]) for j in jobs}


def view(db, job):
    return views(db, [job])[job.id]


def released(db, job):
    return view(db, job)['released']


def basis(db, job):
    """本期分发采用的会签依据快照。"""
    return view(db, job)['valid']


def approve(db, job, user):
    """记录会签同意。幂等：同一复核人重复提交或失败重试不重复计票。返回 (视图, 是否新计票)。"""
    if job.status != 'completed':
        raise HTTPException(409, '仅已完成结果可以会签')
    if job.created_by == user.id:
        raise HTTPException(409, '创建人不参与会签计票，请由其他负责人复核')
    current = view(db, job)
    mine = next((o for o in current['opinions'] if o['reviewer_id'] == user.id), None)
    if mine and mine['action'] == 'approve':
        return current, False
    db.add(Approval(job_id=job.id, reviewer_id=user.id, reviewer_name=user.name,
                    reviewer_email=user.email, action='approve', created_at=time.time()))
    db.flush()
    return view(db, job), True


def withdraw(db, job, user):
    """撤回自己的会签意见。只能撤回当前生效的同意。返回 (视图, 是否有撤回发生)。"""
    current = view(db, job)
    mine = next((o for o in current['opinions'] if o['reviewer_id'] == user.id), None)
    if not mine or mine['action'] != 'approve':
        raise HTTPException(409, '没有可撤回的会签意见')
    db.add(Approval(job_id=job.id, reviewer_id=user.id, reviewer_name=user.name,
                    reviewer_email=user.email, action='withdraw', created_at=time.time()))
    db.flush()
    return view(db, job), True
