"""Derive bounded native redo results from saved public 2-second samples."""
import json
from pathlib import Path
HERE=Path(__file__).parent
rows=[]
for cap in (104857600,1073741824):
 v=json.loads((HERE/f'redo-{cap}.PUBLIC.json').read_text());all_samples=v['samples'];s=[x for x in all_samples if x['monotonic']>=all_samples[0]['monotonic']+v['warmup_seconds']];a,b=s[0],s[-1];dt=b['monotonic']-a['monotonic'];ages=[x['innodb_log']['LSN']-x['innodb_log']['LSN_checkpoint'] for x in s];dx={x['digest']:x for x in a['digests']};dy={x['digest']:x for x in b['digests']}
 deltas={h:{'calls':dy[h]['count']-dx[h]['count'],'mean_ms':(dy[h]['timer_ps']-dx[h]['timer_ps'])/1e9/(dy[h]['count']-dx[h]['count'])} for h in dx.keys()&dy.keys() if dy[h]['count']>dx[h]['count']}
 delta=lambda k:b['status'][k]-a['status'][k]
 rows.append({'capacity':cap,'sample_seconds':dt,'redo_lsn_delta':b['innodb_log']['LSN']-a['innodb_log']['LSN'],'redo_turnover_of_config_capacity':(b['innodb_log']['LSN']-a['innodb_log']['LSN'])/cap,'checkpoint_age_range':[min(ages),max(ages)],'checkpoint_advancements':len({x['innodb_log']['LSN_checkpoint'] for x in s}),'log_waits_delta':delta('Innodb_log_waits'),'data_written_delta':delta('Innodb_data_written'),'data_written_bytes_per_second':delta('Innodb_data_written')/dt,'redo_fsync_per_second':delta('Innodb_os_log_fsyncs')/dt,'dirty_bytes_range':[min(x['status']['Innodb_buffer_pool_bytes_dirty'] for x in s),max(x['status']['Innodb_buffer_pool_bytes_dirty'] for x in s)],'digests':deltas})
v={'status':'LOCAL_REDO_COMPARISON_COMPLETE_NO_BENEFIT_OBSERVED','phases':rows,'recommendation':'Do not adopt a redo-size change as an established fix; native baseline already lacked capacity pressure and cloud wait was not reproduced. Need actual block-device await/queue/limits and P_S wait evidence.','own_socket_exists_after':Path('/tmp/t44-manual12-digest.sock').exists()}
(HERE/'native-redo-derived.PUBLIC.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
