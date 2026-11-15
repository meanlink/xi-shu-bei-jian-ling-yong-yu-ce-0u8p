import time
from sqlalchemy import select, text, inspect
from src.config.database import Base, engine, Session
from src import models
from src.models import Job, Approval, Audit
def migrate():
    Base.metadata.create_all(engine)
    if 'basis' not in [c['name'] for c in inspect(engine).get_columns('deliveries')]:  # 存量库补充新列；新库由 create_all 自带
        with engine.begin() as conn:
            conn.execute(text('ALTER TABLE deliveries ADD COLUMN basis JSON'))
    with Session() as db:  # 旧批准记录转为历史凭据，存量计划待凑齐双人会签后恢复分发
        upgraded=[]
        for j in db.scalars(select(Job).where(Job.approved==True)):
            if not db.scalar(select(Approval.id).where(Approval.job_id==j.id,Approval.action=='legacy')):
                db.add(Approval(job_id=j.id,reviewer_id=j.created_by,reviewer_name='旧版批准凭据',reviewer_email='legacy@migration',action='legacy',created_at=j.finished_at or time.time()))
                upgraded.append(j.id)
        if upgraded:
            db.add(Audit(actor='system',action='migrate.legacy_approval',detail={'jobs':upgraded,'note':'旧批准记录转为历史凭据，存量计划待双人会签后恢复分发'},at=time.time()))
        db.commit()
if __name__=='__main__':migrate()
