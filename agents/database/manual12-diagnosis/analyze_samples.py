"""Compute bounded monotonic counter deltas from public neutral telemetry only."""
import argparse,hashlib,json
from pathlib import Path
GAUGES={'Threads_connected','Threads_running','Max_used_connections','Innodb_row_lock_current_waits','Innodb_buffer_pool_pages_total','Innodb_buffer_pool_pages_data','Innodb_buffer_pool_pages_dirty','Innodb_buffer_pool_pages_free','Innodb_buffer_pool_bytes_data','Innodb_buffer_pool_bytes_dirty'}
def keyvalues(values):return dict(x.split() for x in values)
def block_io(values):
 result={}
 for line in values:
  device,*pairs=line.split();result[device]={k:int(v) for k,v in (p.split('=',1) for p in pairs)}
 return result
def digest_rows(value):return {x['digest_hash']:x for x in value['rows']} if value.get('available') else None
def difference(x,y):
 keys=x.keys()&y.keys();result={k:y[k]-x[k] for k in keys}
 if any(v<0 for v in result.values()):raise ValueError('COUNTER_RESET_OR_INCONSISTENT_SAMPLE')
 return result
def digests(x,y,dt):
 x,y=digest_rows(x),digest_rows(y)
 if x is None or y is None:return {'available':False,'reason':'missing is not zero'}
 rows=[]
 for h in x.keys()&y.keys():
  d=difference({k:v for k,v in x[h].items() if k!='digest_hash'},{k:v for k,v in y[h].items() if k!='digest_hash'});n=d['count_star']
  rows.append(dict(digest_hash=h,delta=d,calls_per_second=n/dt,mean_statement_ms=d['sum_timer_wait_ps']/1e9/n if n else None,rows_examined_per_call=d['sum_rows_examined']/n if n else None))
 return {'available':True,'common_rows':sorted(rows,key=lambda r:r['delta']['sum_timer_wait_ps'],reverse=True),'unmatched_hashes_not_assumed_zero':sorted(x.keys()^y.keys())}
def interval(x,y):
 dt=y['monotonic']-x['monotonic'];assert dt>0
 mysqlx=x['services']['mysql']['mysql'];mysqly=y['services']['mysql']['mysql']
 if abs((mysqly['status']['Uptime']-mysqlx['status']['Uptime'])-dt)>3:raise ValueError('MYSQL_UPTIME_DISCONTINUITY')
 result={'seconds':dt,'start_utc':x['utc'],'end_utc':y['utc'],'cpu':{}}
 for role,a in x['services'].items():
  b=y['services'][role];assert a['container_id']==b['container_id'] and a['image_id']==b['image_id']
  ca,cb=keyvalues(a['cgroup']['cpu.stat']),keyvalues(b['cgroup']['cpu.stat']);d=difference({k:int(v) for k,v in ca.items()},{k:int(v) for k,v in cb.items()})
  ix,iy=block_io(a['cgroup']['io.stat']),block_io(b['cgroup']['io.stat']);io={}
  for device in ix.keys()&iy.keys():
   delta=difference(ix[device],iy[device]);io[device]={'deltas':delta,'rates_per_second':{k:v/dt for k,v in delta.items()}}
  result.setdefault('kernel_block_io',{})[role]={'common_devices':io,'unmatched_devices_not_assumed_zero':sorted(ix.keys()^iy.keys()),'empty_projection_not_claimed_zero':not bool(ix) or not bool(iy)}
  result['cpu'][role]={'mean_cores':d['usage_usec']/dt/1e6,'throttled_usec_delta':d.get('throttled_usec'),'quota':b['cgroup']['cpu.max'],'oom_events_end':b['cgroup']['memory.events']}
 sx,sy=mysqlx['status'],mysqly['status'];counts=difference({k:v for k,v in sx.items() if k not in GAUGES},{k:v for k,v in sy.items() if k not in GAUGES});result['status_counter_deltas']=counts;result['status_rates_per_second']={k:v/dt for k,v in counts.items()};result['status_gauges']={k:{'start':sx[k],'end':sy[k]} for k in sx.keys()&sy.keys()&GAUGES}
 result['file_io_delta']=difference(mysqlx['aggregates']['FILE_IO_TOTAL'],mysqly['aggregates']['FILE_IO_TOTAL'])
 result['statement_total_delta']=difference(mysqlx['aggregates']['DIGEST_TOTAL'],mysqly['aggregates']['DIGEST_TOTAL'])
 result['top20_common_digest_deltas']=digests(mysqlx['top20_digests_by_count'],mysqly['top20_digests_by_count'],dt)
 result['confirmed_missing_digest_deltas']=digests(mysqlx['confirmed_missing_digest_candidates'],mysqly['confirmed_missing_digest_candidates'],dt)
 result['config_unchanged']=mysqlx['effective_global_config']==mysqly['effective_global_config'];result['effective_global_config']=mysqly['effective_global_config']
 return result
def main():
 p=argparse.ArgumentParser();p.add_argument('--early',type=Path,required=True);p.add_argument('--late',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();groups=[[json.loads(x) for x in path.read_text().splitlines()] for path in [a.early,a.late]];assert all(len(x)==12 for x in groups)
 out={'scope':'two bounded neutral snapshots, not all steady measurements; global counters include background and observer contribution','units':{'statement_timer':'picoseconds','cpu':'microseconds','innodb_row_lock_time':'milliseconds'},'inputs':{path.name:{'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'samples':12} for path in [a.early,a.late]},'intervals':{'early':interval(groups[0][0],groups[0][-1]),'late':interval(groups[1][0],groups[1][-1]),'between_groups':interval(groups[0][-1],groups[1][0])},'limitations':['statement waits sum concurrent calls and cannot be interpreted as one request duration','top20 set is truncated and may change; unmatched hashes are not zero','cgroup CPU is all container processes; api process projection lists only supervisor and does not prove one worker','no cloud actions, SUT requests or QA PRIVATE reads']}
 a.output.write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps({'status':'BOUNDED_COUNTER_ANALYSIS_COMPLETE','intervals':list(out['intervals']),'cloud_requests':0}))
if __name__=='__main__':main()
