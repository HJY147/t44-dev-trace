# 恢复部署设计（先设计，后实现）

操作者为部署AI；来源是2026-10-28用户恢复指令及总协调实际派工，不是学生本人手写研究报告。只做本地准备，不云操作、启动、购机、CI或访问独立私有材料。

## 已核问题

原集成22f666e2、原部署fb0a4334核实。原935场景及generation-f4/resource-stream的绝对截止为2026-10-25T21:00Z，已失效；不能改原controller、binding、计时记录或日期以复用旧许可。原factory的Persistent timer只认冻结project/service和已证明镜像保卷停容器，重启时可能立即触发旧停止。先只读查旧timer/receipt，再使用全新namespace、数据库、CA、端口和窗口；不覆盖旧定时器。

旧798汇总程序先O_EXCL写入/fsync目标JSON，再因压缩base64>18000断言失败。本次不得重跑原程序或覆盖原JSON，改为只读提取该已封存文件。

## 只读汇总分块运输

- 输入固定为`/root/t44-r9/diag-summary-01.json`，66110字节、SHA256 d554caf63e38238ab1b3e75abc2823b670b078d60c84a9097b031c03044e3053，不能改成任意文件或容忍摘要不同。
- 通过O_RDONLY|O_NOFOLLOW单一FD打开；检查regular、长度及读前读后inode/size/mtime一致，完整bytes/SHA后才输出。无云端写入、无产品导入、无密码或会话读取。
- gzip(mtime=0)后base64每块最多12000字符，每次只输出一个指定index。每块携带原文及压缩SHA、总数、偏移、块SHA；输出有明确长度上界。
- 本机重组要求全块唯一、有序、连续、全部元数据一致，验证块/压缩/原文长度与SHA、gzip完整且无额外流，再固定FD独占写入0600新文件并fsync，不覆盖既有文件。
- 输出是开发观察汇总，不是独立验收或性能根因证明。首次失败日志和旧脚本原样保留。

## 新时间窗与源身份的派生工具

后续最终源由总协调明确，不能把f4当最终源。新增本地profile派生器，不改旧三个helper。输入是已审核原helper的精确SHA、完整Git源commit、新绝对UTC停止时间及不存在的新目录；时间必须至少未来30分钟、至多12小时。先用实际Git完整文件集和旧builder等价检查验证依赖、两REST、DDL、前端和支持文件仍同字节，若本轮改了这些则拒绝，交总协调另行设计，不放宽冻结。

输出为目标commit专用builder、generator、resource-stream及明确派生清单：新builder SHA被新generator pin，新generator SHA被新resource-stream pin，新源全量文件数量取真实Git清单（允许真实增删文件，不能固定假53），新截止写入新helper与binding。每个替换均验证精确旧前像/次数，编译后写入O_EXCL新文件；旧935/f4原件、旧截止、旧成绩不改变。原非root、网络none、完整实际文件字节/模式、TLS CA+IP、独占新namespace、保卷stop、尾部采样等保护均保留。

本地保护验证包括源/模板/时间/前像错误拒绝、全SHA链、真实文件数量、旧件未变、输出拒覆盖和运输的缺块/重块/篡改/超限/符号链接。无真实云build、cgroup、跨VM采样或新独立验收结论；只有root之后真实云回执才能补执行状态。
