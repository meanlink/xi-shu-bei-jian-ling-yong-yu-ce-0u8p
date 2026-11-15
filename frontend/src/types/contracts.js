/** @typedef {{id:number,name:string,source:string,rows:number,checksum:string}} Dataset */
/** @typedef {{reviewer:string,email:string,action:'approve'|'withdraw',at:number}} CosignOpinion */
/** @typedef {{required:number,released:boolean,valid_count:number,opinions:CosignOpinion[],valid:Array<{reviewer:string,email:string,at:number}>,legacy:Array<{reviewer:string,at:number}>}} CosignState */
/** @typedef {{id:number,name:string,dataset_id:number,status:string,result:Object,approved:boolean,created_by:number,cosign:CosignState}} AnalysisJob */
/** @typedef {{id:number,name:string,job_id:number,destination:string,next_run:number,enabled:boolean,released:boolean}} ReportSchedule */
/** @typedef {{id:number,report_id:number,created_at:number,checksum:string,filename:string,destination:string,basis:Array<{reviewer:string,email:string,at:number}>}} DeliveryArchive */
export {};
