# F7 新campaign：provider、watcher与精确功能授权限定审

## 1. 精确对象与读取边界

固定AI审核岗，非独立验收。root source commit3f51350ae1e5d89983dab69edebe3641804f54b3，八个明确source/测试/public binding/draft/preflight文件逐字同该commit，hash留证；root tree存在无关untracked文件，不宣称全树干净，也未打开它们。仅读root明列公开/环境实现源码及记录，不读private suite/env/token/build/CA值、独立Git/log/key，不联系testing agent或向其注入开发结果。

## 2. Provider修正与原门禁

provider SHA75de2979c378d091d6e533bb85ca6af6197485e52cc0b5af8580680a749f40b4。phase_request_anchor取真实supervisor.launch_clock.utc，validate仍原早2秒容差、未来2秒、expiry、exact supervisor nonce/context/source/runtime/resource/functional、单positive int project、固定scope/48hex请求nonce。故合法请求可先于provider晚启动，不用放松到无phase起点。load/private_json/instant/remaining/validate五函数整体AST同已审d7a；改变的是传入下界，原拒绝记录不改。

新增精确私有config经mode/非symlink、grant绑定bytes SHA、四字段集合、functional campaign run直父/非symlink、buildmanifest parent、runtime/source/CLI binding/controllerhash检查；这些私有实际值由root已核信任，本岗只核明列公开binding f61cca313a8c2b3371c70d24d465ba27064e34c09b821e640a93aa9e90dc78f2和源码约束。不是恶意同用户filesystem隔离证明。

fresh target在原approved/provisioned/functional-v7-<supervisorNonce>/<requestNonce>，父与子mode0700/拒symlink/排他fresh创建，私有JSON原O_EXCL|O_NOFOLLOW不变。双截止取UTC+mono及receipt最早、inner40cap、CLI/apply/seal三个remaining timeout、private staged后复查到期+不覆盖link、失败保留无自动retry均保持。新增stage标签不打印token。check→syscall正常调度间隙/已提交token不保证撤销的既有限制保持。

## 3. Bootstrap的职责和限制

watcher SHA6a6df2a8416c1ddb30b811205a53de3234d07bbc41c96d4145725fbfad5fddbc，仅在固定v7 PUBLIC/runtime寻找非symlink/<=32768的receipt，同freeze、同expiry及父子kill0存活后exec同目录821_provider_v7.py，provider随后严格检查路径/nonce、配置/source/runtime和后续requestcontext。按root本轮single fresh receipt流程可用，不把它称作任意stale坏JSON容错或PID防复用机制。

watcher等待仅UTC、最多600s与grant expiry取早，本身不构成monotonic hardstop证明；它不发HTTP/SQL/CLI，真正SUT sideeffect仍由provider+supervisor双截止约束。root在独立operator前起watcher是调度选择，不承诺完全没有OS调度延迟、120s handoff必成功或自动重试。

## 4. 两项测试与真实组件预检的边界

final JUnit实读tests2/failure0/error0/skip0/time0.015s，本岗仅机械复算不重跑。延迟provider测试实调用phase_request_anchor/validate并保留旧晚启动anchor拒绝对照；目录case只比较Path.is_relative_to的纯路径性质，不是对实际controller的集成执行证明。

PUBLIC root预检记录：09:34:51真实root strictTLS请求1/完整201，neutral project1、sourcebound CLI、单P1 scope/escalation:write/TTL3600、owned scheduler76376成功；09:36:05 own-key sealer记录同b957 helper、auth cipher roundtrip。这里只读root公开credential-free摘要，未读原HTTPbody/token/RSAkey，没有亲跑或验证私有raw。这是root组件预检，不是14个独立case通过；保留root已明确not_independent_acceptance身份。

## 5. 精确授权变换

draft实际bytes SHA692b8edfb21d6ba52a00840e52a4498bf3034d0ab8442b4b999105777dc9cc21；新文件仅admitted false→true，其余逐值不变。canonical内容SHA5234b21e5abdf2761dcde5bde861adb4f24b85a58c631865b3ab770de4764d8c（UTF8/ensure_ascii=false/sort_keys=true/无分隔空格），root另记实际输出bytes hash，本岗不写激活grant。

v7freeze9e247e8、sourcec8/archivec393、nativebuild8f7ac784852f46d68c5a33b3780f620e4c76f07118562047246c2f7a295260c7、runtimeb19411de213ef12f345011966c3cbf58eb4280033075b40a63cc73805e7d8d3d、明确新CA/localhost18096 pin127/新t44_f817 schema/vhost资源绑定。功能only，100000req/400concurrency/RSS4GiB/原2GiB压缩3GiB密文32GiB明文/faults空/cost0。非空1preflight project、tasks0/5human，原数据不清理、initialscheduler[1]，实际每新project再替换；单scheduler替换旧project停扫/旧token不自动撤销如实。root私有config同bytes600、新session09:17:15签发TTL3600只沿已核元数据不读secret。

## 6. 时间与未证明项

工具09:42:05.724195 UTC距09:50余474.275805秒，实际wall=min(900,剩余UTC及supervisor deadline)，不承诺所有计划case能完成。新campaign09:50不是把旧09:22 grant改写延期；root spawncap10:00/appguardian10:20:30为环境边界元数据，不使phase越过09:50，也不授权stop共享MySQL或改无关资源。当前技术准入先发root，行政不阻塞启动。

本岗0新test/probe/HTTP/SQL/CLI/provider/watcher/supervisor/SUT执行，实际功能结果/receipt时序/输出完整性由独立operator另归档，本scope不读取。既有.01s时钟采样/真实OSlag、RSS单runner每1s而非aggregate/OS硬分配保持，门禁失败或neutral setup失败须保留NOT_PROVEN，不删原HTTP事实或改业务预期。

## 7. 十项判定

| 项 | 判定 | 依据 |
|---|---|---|
| 1 exact source | 匹配 | 8文件字节同3f51350 |
| 2 source/binding | 限定通过 | publicf61cca与grant同，私有由root核 |
| 3 phase下界 | 闭环 | supervisor.launch_clock.utc，无晚启动误拒 |
| 4 namespace | 静态闭环 | approved父内双nonce/fresh0700，不冒controller测试 |
| 5 剩余门禁 | 保持 | 双截止/40/精确nonce/remaining/staged排他 |
| 6 watcher | 本流程可用 | 固定PUBLIC/live同freeze+expiry后provider复核；UTC等待限制披露 |
| 7 验证证据 | 限定自洽 | JUnit2机械复算；root组件预检非独立case |
| 8 grant | 一次准入 | 新文件单admitted字段；canonical5234b21e |
| 9 时间与资源 | 相容不保证完成 |09:50/max900取早，新campaign旧grant不改 |
| 10 结果 | 未验收 | 0本岗SUT；无business/perf/product/global/main/merge通过 |

## 8. 结论

未见本scope具体阻断，精确3f51350的新F7 campaign可按上述单字段变换准入一次functional-only，由独立operator生成实际新receipt并衔接watcher/provider。技术结论已先给root；本报告不等业务、独立验收、性能、产品或全局通过，任何其它source/draft/期限变化另做准确影响审查。
