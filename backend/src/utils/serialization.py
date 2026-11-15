import hashlib, json
def checksum(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()
def dataset_dict(d):
    return {'id':d.id, 'name':d.name, 'source':d.source, 'rows':len(d.records), 'checksum':d.checksum, 'created_at':d.created_at}
def job_dict(j, cosign=None):
    d={k:getattr(j,k) for k in ['id','name','dataset_id','params','status','result','error','approved','created_by','created_at','finished_at']}
    d['legacy_approved']=bool(j.approved)  # 旧版批准记录仅作历史凭据
    d['cosign']=cosign or {'required':2,'released':False,'valid_count':0,'opinions':[],'valid':[],'legacy':[]}
    return d
def report_dict(r, released=None):
    d={k:getattr(r,k) for k in ['id','name','job_id','destination','interval_seconds','next_run','enabled']}
    d['released']=bool(released)  # 已放行 / 待复核
    return d
def delivery_dict(d):
    return {k:getattr(d,k) for k in ['id','report_id','created_at','checksum','filename','destination','basis']}
