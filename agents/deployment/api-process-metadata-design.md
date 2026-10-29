# API进程只读采集：合成反例设计

先记录后执行。假设：旧API_SCRIPT以argv成员出现uvicorn和t44.api:app判断supervisor，可能同时计入init wrapper及真正Python模块进程。该假设尚不代表stage05实际原因。

仅在953以pytest临时目录构造fake /proc：docker-init/tini wrapper、真实形态python -m uvicorn t44.api:app --workers 4与四个spawn_main条目。脚本中的Path('/proc')必须mock至该临时目录；不启动应用、子业务进程或Docker，不读真实/proc、独立私密输入或旧raw。

先对原脚本要求supervisor_count=1/configured_workers=[4]/spawn_main_process_count=4并保留红。若证实，只把supervisor识别改成明确Python module argv前缀；继续严格拒绝零个或多个supervisor，不修改投影数量容忍、worker资源或产品。然后同例green，加两个真实supervisor仍被拒绝的守卫，保留原API projection守卫。

历史b3ee/H11 incomplete与已封存正式结果不改，合成复现只说明该采集器对所构造进程树有缺陷，不推定实际runner具备同一进程树。

## 实际结果

原脚本对docker-init/tini两个fake进程树均红：supervisor_count=2、workers=[4,4]，spawn=4。仅修成Python可执行文件名及紧邻-m uvicorn t44.api:app形态，strict count==1不变。相关四项（两wrapper反例、双真实supervisor拒绝、原投影守卫）green；首green暴露字符串内正则转义SyntaxWarning，保留原件，改[.]后同四项无warning通过。仅API_SCRIPT以外AST完全一致。

所有结果仅为合成边界，未观察真实容器/进程或stage05原始输出；不能把本反例认定为stage05实际原因。b3ee/H11等历史incomplete和封存正式失败结果保持。
