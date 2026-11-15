import time, os, csv, io, hashlib, json
from fastapi import HTTPException
from sqlalchemy import select
from src.models import Job, Report, Delivery
from src.config.settings import ARTIFACT_DIR
from src.services import approvals
def create(db, data):
    j=db.get(Job,data.job_id)
    if not j or j.status!='completed':
        raise HTTPException(409,'请先选择已完成的分析结果')
    if not approvals.released(db,j):
        raise HTTPException(409,'分析结果尚未凑齐双人会签，暂不能建立分发计划')
    r=Report(name=data.name, job_id=j.id, destination=data.destination, interval_seconds=data.interval_seconds, next_run=time.time()+data.delay_seconds, enabled=True)
    db.add(r); db.flush()
    return r
def deliver(db, report):
    j=db.get(Job,report.job_id)
    if not j or not approvals.released(db,j): return None  # 待复核期间暂停新一期分发，已归档简报保留
    out=io.StringIO()
    out.write('\ufeff')
    table=j.result.get('table',{})
    cols=table.get('columns',[])
    writer=csv.writer(out)
    def safe(v):
        if isinstance(v,(int,float)) and not isinstance(v,bool): return v
        text=str(v)
        return "'"+text if text.startswith(('=','+','-','@','\t','\r')) else text
    writer.writerow([safe(c['label']) for c in cols])
    for row in table.get('rows',[]): writer.writerow([safe(row.get(c['key'],'')) for c in cols])
    data=out.getvalue().encode('utf-8')
    delivery=Delivery(report_id=report.id, created_at=time.time(), checksum=hashlib.sha256(data).hexdigest(), filename='', destination=report.destination, basis=[])
    db.add(delivery); db.flush()
    delivery.filename=f'report-{report.id}-delivery-{delivery.id}.csv'
    path=os.path.join(ARTIFACT_DIR,delivery.filename)
    os.makedirs(ARTIFACT_DIR,exist_ok=True)
    with open(path,'wb') as f:f.write(data)
    # 终检：锁定任务行后复核会签仍有效；写文件期间被撤回的简报不进入收件箱
    locked=db.scalar(select(Job).where(Job.id==j.id).with_for_update())
    if not approvals.released(db,locked):
        try: os.remove(path)
        except OSError: pass
        return None
    snapshot=approvals.basis(db,locked)  # 以放行时刻的会签状态为准
    delivery.basis=snapshot
    with open(path+'.json','w') as f: json.dump({'job':j.name,'params':j.params,'result':j.result,'checksum':delivery.checksum,'basis':snapshot},f,ensure_ascii=False,allow_nan=False)
    report.next_run=time.time()+report.interval_seconds
    return delivery
