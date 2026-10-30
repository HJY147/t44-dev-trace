from pathlib import Path
from PIL import Image
import ast,json,hashlib
BASE=Path(__file__).parent
source='90b734f65ce6ee9f5c217e885bc7ea4857e32b48'
source_sets={
'srs1':['docs/collaboration/implementation-layout.md'],
'srs2':['backend/t44/domain/state_machine.py','backend/t44/services/projects.py'],
'srs3':['backend/t44/domain/models.py','backend/t44/services/workflow.py'],
'srs4':['backend/t44/services/tasks.py','backend/t44/services/projects.py'],
'srs5':['backend/t44/services/workflow.py','backend/t44/domain/state_machine.py'],
'srs6':['backend/t44/domain/state_machine.py'],
'srs7':['backend/t44/scheduling/scanner.py','backend/t44/messaging/worker.py'],
'srs8':['records/spec-freezes/','docs/reports/'],
'sdd1':['docs/collaboration/implementation-layout.md','backend/t44/services/runtime.py'],
'sdd2':['backend/t44/services/runtime.py','backend/t44/services/workflow.py','backend/t44/domain/state_machine.py'],
'sdd3':['backend/t44/persistence/schema_v1.sql','backend/t44/persistence/rows.py','backend/t44/domain/models.py'],
'sdd4':['backend/t44/domain/state_machine.py','backend/t44/services/workflow.py'],
'sdd5':['backend/t44/services/runtime.py','backend/t44/services/workflow.py'],
'sdd6':['backend/t44/services/runtime.py'],
'sdd7':['frontend/src/'],
'sdd8':['backend/t44/services/runtime.py','backend/t44/services/tasks.py','backend/t44/services/projects.py'],
'sdd9':['backend/t44/scheduling/scanner.py','backend/t44/persistence/scans.py','backend/t44/messaging/worker.py','backend/t44/persistence/delivery.py'],
'sdd10':['docs/collaboration/implementation-layout.md','用户手动停机与证据回收要求']}
limits={
'srs1':'范围图只列主要业务角色；数据库和MQ为基础设施。',
'srs2':'主要用例而非完整权限矩阵；跨线不表示关联节点。',
'srs3':'业务关联，不替代技术ER或数据库完整约束。',
'srs4':'A/B/C/D为无真实数据的规则示例；人力变更的成员保护与工时保护须区分。',
'srs5':'D008只细化原批准引用不匹配分支；匹配分支的领域顺序不变。',
'srs6':'进入阻塞的示意线代表1/2/4/5；恢复字段动态指向四者之一。',
'srs7':'202为可靠受理；站内通知完成不等于任务迁移。',
'srs8':'只表达证据出口；开发CI不等于独立验收。图中NP为本轮公开状态。',
'sdd1':'进程均可部署同一APP；消息确认细节见sdd9。',
'sdd2':'组合根边为装配，其余边为调用；纯函数与事务适配边界分开。',
'sdd3':'主要关联摘录；成员/迭代/评估/审计等支撑实体完整ER及字段见正文DDL。',
'sdd4':'准入概览；真实函数签名、输入、错误见设计正文。',
'sdd5':'仅幂等保护写请求；不是所有失败均可声称业务未写。',
'sdd6':'幂等业务结果重放不要求HTTP元数据逐字节重放。',
'sdd7':'会话代次为浏览器隔离机制；不撤销已发送服务端写事务。',
'sdd8':'N任务、E依赖、K新增前驱；数据库成本另计；并非候选优化设计。',
'sdd9':'上下两阶段不表示DB/MQ分布式原子提交；旧run保留started与cursor。',
'sdd10':'仅部署及证据回收概览；正式测试前备份恢复完整性校验仍须完成；无自动云停机。'}
figs=[]
for n in ast.walk(ast.parse((BASE/'draw.py').read_text())):
 if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='Fig':
  id,title,subtitle=[ast.literal_eval(x) for x in n.args[:3]]
  row={'id':id,'title':title,'subtitle':subtitle,'sources':source_sets[id],'scope_note':limits[id],'legend':'海军蓝=正文与组件；蓝绿=正常关系或主路径；琥珀=拒绝、故障或特殊约束；箭头含义以图题和边标签为准','visual_check':'PNG individually opened and inspected; no product or cloud test performed','files':{}}
  for ext in ['png','svg']:
   p=BASE/'assets'/f'{id}.{ext}';row['files'][ext]={'path':f'assets/{id}.{ext}','sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
  with Image.open(BASE/'assets'/f'{id}.png') as im:row['size_px']=list(im.size)
  figs.append(row)
(BASE/'MANIFEST.PUBLIC.json').write_text(json.dumps({'schema_version':1,'source_commit':source,'spec':'v1.2','generator':'draw.py (bundled Python + Pillow)','not_adopted':'INSERT-first optimization candidate','figures':sorted(figs,key=lambda x:(x['id'][:3],int(x['id'][3:])))},ensure_ascii=False,indent=2)+'\n')
print(f'{len(figs)} figures, PNG/SVG hashes recorded')
