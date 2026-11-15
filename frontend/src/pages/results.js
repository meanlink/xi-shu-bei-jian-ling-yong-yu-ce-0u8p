import {jobs} from '../api/entities.js';
import {workspace} from '../stores/workspace.js';
import {session} from '../stores/session.js';
import {heading} from '../components/common/shell.js';
import {chart} from '../components/common/chart.js';
import {table} from '../components/common/table.js';
import {status} from '../components/common/status.js';
import {CosignAction} from '../constants/enums.js';
import {esc,fmt,date,notify} from '../utils/dom.js';
function cosignPanel(j){
 const me=session.user,cos=j.cosign||{required:2,released:false,valid_count:0,opinions:[],valid:[],legacy:[]};
 const mine=cos.opinions.find(o=>o.email===me.email),isCreator=me.id===j.created_by,canCosign=me.role==='admin'&&!isCreator;
 const badge=cos.released?'已放行 · 会签 '+cos.valid_count+'/'+cos.required:'待复核 · 会签 '+cos.valid_count+'/'+cos.required;
 const opinions=cos.opinions.length?cos.opinions.map(o=>'<li><strong>'+esc(o.reviewer)+'</strong><span>'+esc(CosignAction[o.action]||o.action)+' · '+date(o.at)+'</span></li>').join(''):'<li class="empty">尚无会签意见，等待负责人复核。</li>';
 const legacy=cos.legacy.length?'<p class="hint">历史凭据：'+cos.legacy.map(l=>esc(l.reviewer)+' · '+date(l.at)).join('；')+'（旧版批准记录，仅留痕不计票）。</p>':'';
 let action='';
 if(canCosign)action=mine&&mine.action==='approve'?'<button class="button" id="cosign-withdraw">撤回我的会签</button>':'<button class="primary" id="cosign-approve">会签同意</button>';
 const note=me.role!=='admin'?'<p class="hint">分析员与观察员无会签权限，仅业务负责人可会签。</p>':isCreator?'<p class="hint">你是该分析的创建人，创建人不参与会签计票。</p>':'';
 return '<section class="panel cosign-panel"><div class="section-title"><h2>双人会签</h2><span class="'+(cos.released?'approval':'pending')+'">'+badge+'</span></div><ul class="opinions">'+opinions+'</ul>'+legacy+'<div class="cosign-actions">'+action+'</div>'+note+'<p class="hint">两名不同负责人同意后放行分发；任一复核人撤回即暂停新一期分发，已归档简报保留。</p></section>';
}
export async function results(id){
 workspace.jobs=await jobs.list();const j=id?await jobs.get(id):(workspace.jobs.find(j=>j.id===workspace.selectedJob)||workspace.jobs[0]);
 if(j&&!workspace.jobs.some(x=>x.id===j.id))workspace.jobs.push(j);
 if(!j)return heading('04 / REVIEW','结果复核','尚无分析结果。')+'<div class="empty">先到分析工作台，选择批次并提交一次计算。<a href="#/workbench">前往工作台 ↗</a></div>';
 workspace.selectedJob=j.id;const r=j.result||{};const cos=j.cosign||{required:2,released:false,valid_count:0};
 return heading('04 / REVIEW','结果复核与业务解释',j.name,'<button class="button" id="refresh-results">刷新结果 ↻</button>')+'<div class="result-selector"><label>分析记录<select id="select-job">'+workspace.jobs.map(x=>'<option value="'+x.id+'" '+(x.id===j.id?'selected':'')+'>'+esc(x.name)+' · '+esc(x.status)+'</option>').join('')+'</select></label>'+status(j.status)+'<span>'+date(j.created_at)+'</span><span class="'+(cos.released?'approval':'pending')+'">'+(cos.released?'已放行 · 双人会签齐':'待复核 · 会签 '+cos.valid_count+'/'+cos.required)+'</span></div>'+(j.status==='completed'?'<section class="result-lead"><p class="eyebrow">COMPUTED FINDING</p><h2>'+esc(r.summary)+'</h2><div class="metrics">'+(r.metrics||[]).map(m=>'<div><span>'+esc(m.label)+'</span><strong>'+esc(fmt(m.value))+'<small>'+esc(m.unit||'')+'</small></strong></div>').join('')+'</div></section><section class="panel">'+chart(r.chart)+'</section><div class="two-columns"><section class="panel"><div class="section-title"><h2>业务解释</h2><span>由计算结果生成</span></div><ol class="questions">'+(r.findings||[]).map(v=>'<li>'+esc(v)+'</li>').join('')+'</ol>'+(r.warnings||[]).map(v=>'<p class="warning">'+esc(v)+'</p>').join('')+'</section><section class="method-sheet compact"><p class="eyebrow">REPRODUCIBILITY</p><h3>计算口径与参数</h3><p>'+esc(r.method)+'</p><pre>'+esc(JSON.stringify(j.params,null,2))+'</pre><p class="hint">凑齐双人会签后，结果才能进入定时分发档案。</p></section></div>'+cosignPanel(j)+'<section class="panel"><div class="section-title"><h2>结果明细</h2><span>'+(r.table?.rows?.length||0)+' 行</span></div>'+table(r.table?.columns||[],r.table?.rows||[])+'</section>':'<section class="panel empty">'+(j.status==='failed'?'计算失败：'+esc(j.error)+'。请返回工作台调整参数或数据。':'后台正在执行计算。点击刷新结果查看最新进展。')+'<a href="#/workbench">返回工作台 ↗</a></section>');
}
export function bindResults(refresh){document.querySelector('#refresh-results')?.addEventListener('click',refresh);document.querySelector('#select-job')?.addEventListener('change',e=>{workspace.selectedJob=Number(e.target.value);location.hash='#/results/'+e.target.value;});document.querySelector('#cosign-approve')?.addEventListener('click',async()=>{try{await jobs.approve(workspace.selectedJob);notify('会签已记录');await refresh();}catch(e){notify(e.message,true);}});document.querySelector('#cosign-withdraw')?.addEventListener('click',async()=>{try{await jobs.withdraw(workspace.selectedJob);notify('已撤回会签，新一期分发将暂停');await refresh();}catch(e){notify(e.message,true);}});}
