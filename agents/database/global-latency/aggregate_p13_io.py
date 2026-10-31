"""Read only two previously published P13 neutral windows; no SQL text or server access."""
from pathlib import Path
import json,hashlib,statistics
BASE=Path('/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/.runtime/p13-app07-live-20261031')
OUT=Path(__file__).parent
allout={}
for phase in ['early','late']:
 p=BASE/f't44-p13-material07-observe-{phase}.PUBLIC.jsonl';raw=p.read_bytes();rs=[json.loads(x)for x in raw.splitlines()];ms=[r['services']['mysql']['mysql']for r in rs];ss=[m['status']for m in ms];dt=rs[-1]['monotonic']-rs[0]['monotonic'];first,last=ss[0],ss[-1]
 assert len(rs)==12 and all(ss[i]['Uptime']<ss[i+1]['Uptime']for i in range(11))
 rates={};delta={}
 counters=['Com_commit','Com_rollback','Handler_commit','Innodb_buffer_pool_pages_flushed','Innodb_buffer_pool_read_requests','Innodb_buffer_pool_reads','Innodb_buffer_pool_wait_free','Innodb_data_fsyncs','Innodb_data_read','Innodb_data_reads','Innodb_data_writes','Innodb_data_written','Innodb_log_waits','Innodb_log_writes','Innodb_os_log_fsyncs','Innodb_os_log_written','Innodb_redo_log_current_lsn','Innodb_redo_log_checkpoint_lsn','Innodb_row_lock_time','Innodb_row_lock_waits','Connections']
 assert all(m['effective_global_config']['values']==ms[0]['effective_global_config']['values'] for m in ms)
 for key in counters:
  assert all(ss[i+1][key]>=ss[i][key] for i in range(11)),key
  delta[key]=last[key]-first[key];assert delta[key]>=0;rates[key]=delta[key]/dt
 age=[m['checkpoint_age']['bytes']for m in ms];cap=ms[0]['effective_global_config']['values']['innodb_redo_log_capacity'];redo_rate=rates['Innodb_redo_log_current_lsn']
 agg={}
 for group in ['FILE_IO_TOTAL','DIGEST_TOTAL']:
  a=ms[0]['aggregates'][group];b=ms[-1]['aggregates'][group];agg[group]={k:b[k]-a[k] for k in a if k!='digest_rows'}
 waits=[]
 a={x['event_name']:x for x in ms[0]['global_waits']['top20_by_cumulative_timer']};b={x['event_name']:x for x in ms[-1]['global_waits']['top20_by_cumulative_timer']}
 for k in sorted(a.keys()&b.keys()):
  if a[k]['timed'] and a[k]['enabled']:
   n=b[k]['count_star']-a[k]['count_star'];ps=b[k]['sum_timer_wait_ps']-a[k]['sum_timer_wait_ps'];waits.append({'event':k,'delta_calls':n,'delta_aggregate_seconds':ps/1e12,'mean_ms_per_event':ps/1e9/n if n else None})
 digs=[];a={x['digest_hash']:x for x in ms[0]['top20_digests_by_count']['rows']};b={x['digest_hash']:x for x in ms[-1]['top20_digests_by_count']['rows']}
 for k in sorted(a.keys()&b.keys()):
  n=b[k]['count_star']-a[k]['count_star'];t=b[k]['sum_timer_wait_ps']-a[k]['sum_timer_wait_ps'];digs.append({'digest_hash':k,'calls':n,'aggregate_seconds':t/1e12,'mean_ms':t/1e9/n if n else None})
 out={'source_path':str(p),'source_sha256':hashlib.sha256(raw).hexdigest(),'source_bytes':len(raw),'samples':len(rs),'seconds':dt,'utc_start':rs[0]['utc'] if 'utc'in rs[0]else rs[0].get('observed_utc'),'utc_end':rs[-1].get('utc',rs[-1].get('observed_utc')),'config':ms[0]['effective_global_config']['values'],'counters_delta':delta,'rates_per_second':rates,'checkpoint_age_bytes':{'first':age[0],'last':age[-1],'min':min(age),'max':max(age),'fraction_capacity_min':min(age)/cap,'fraction_capacity_max':max(age)/cap},'nominal_capacity_seconds_at_observed_redo_rate':cap/redo_rate,'age_seconds_at_observed_redo_rate_range':[min(age)/redo_rate,max(age)/redo_rate],'aggregate_deltas':agg,'wait_deltas':sorted(waits,key=lambda x:-x['delta_aggregate_seconds']),'common_top20_digest_deltas':sorted(digs,key=lambda x:-x['aggregate_seconds']),'buffer_free_fraction_range':[min(s['Innodb_buffer_pool_pages_free']/s['Innodb_buffer_pool_pages_total']for s in ss),max(s['Innodb_buffer_pool_pages_free']/s['Innodb_buffer_pool_pages_total']for s in ss)],'threads_connected_range':[min(s['Threads_connected']for s in ss),max(s['Threads_connected']for s in ss)]}
 allout[phase]=out
(OUT/'P13_IO_DELTAS.PUBLIC.json').write_text(json.dumps(allout,indent=2)+'\n')
for k,o in allout.items():print(k,json.dumps({x:o[x]for x in ['seconds','rates_per_second','checkpoint_age_bytes','nominal_capacity_seconds_at_observed_redo_rate','age_seconds_at_observed_redo_rate_range','wait_deltas','buffer_free_fraction_range','threads_connected_range']}))
