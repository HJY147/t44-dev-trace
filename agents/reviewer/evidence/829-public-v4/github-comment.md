Agent-Role: reviewer
Prompt-Ref: ROLE-reviewer-FUNCTIONAL-PROVIDER-v1; ROLE-reviewer-829-PUBLIC-v4-v1

本阶段两个scope分开记录；都不是业务验收，不含私有用例或secret。

一、根环境provider：
原HEAD a6c96c5599a9dd7db60eb618a40f9acbaf49817b/source6d09d2e51bd574258f55d778b9bdd83cdc54c96a，静态发现PROVIDER-EXPIRY-01（validate后CLI/apply/seal无重查且timeout不裁）、PROVIDER-CAP-01（inner可超过40）、supervisor nonce仅truthy缺活跃来源。没有实际红test，不把旧7绿说成覆盖这些main分支。
修订49ef08a7e726fa163106647b96e415213f2aae8f已限定闭环：paired UTC/mono+receipt deadline、inner每path40/时间、三阶段remaining、私有staged回复+最后复查+os.link不覆盖、root明确当前PUBLIC receipt/freeze/semantic expiry/两livePID/48hexnonce/request精确nonce。11guard与Ruff是root报告，未重跑。根托管source/env/controller按已核信任，不读private值；没有CLI/DB/HTTP。check到syscall调度间隙、已提交token不自动撤销/进程树不保证全回滚、单scheduler替换后旧项目不再周期扫描均明示，不要求新功能。该provider本身未见剩余具体阻断，但不单独授权控制器/SUT。

二、829 PUBLIC v4控制器：
精确freeze2996e1e71f1c1160282520b7273ac85c42f4b75acc5042e74836841d75bf1424，control SHA ac50e3a92ff46181d056410d632b19f1050e04483db4794b63a3d16377fe1b99。16 PUBLIC项目hash同；opaque仅wholehash。旧UTC已闭环：paired保守anchor、多阶段dual check、supervisor实际.01s双查+monoTimer/lag，receipt与provider兼容。29源码方法/29绿公开报告与28error1失败保留，本岗不重跑。

新P2 829-HANDOFF-DEADLINE-01阻断functional：HTTP完成/已记录后进入最长120s且排除请求延迟的neutral handoff，之后return_clock却仍拿原HTTP deadline。一次新822纯fake复现HTTP15/run120、POST/projects201在0s完整记录，再20s合法假handoff；run仍live/HTTP record complete，却返回complete=false/return DeadlineExceeded。同次小probe确认旧UTC+20/mono0在transport前已拒。0socket/SUT、无private、无实际provider/supervisor/系统调钟，不是业务case或29重跑。

最小修正是分离HTTP完成/持久化的原截止与120s neutral handoff/run双截止，timer在HTTP完成取消，不放宽HTTP，不删body；handoff失败另作setup不证明。已先经root转PUBLIC中性问题，审核岗不联系独立agent、不用开发结果作oracle。

中性draft SHA01fb722a181c73f9c592ab22c942e40e186da51b1b27161de5daee19c221bf9a保持admitted=false；仅functional/localhost18096/pinloopback、固定native身份、新schema/vhost/5人0projects、08:15UTC/1800s/100000req/4GiB/faults空/cost0及单scheduler限制。未读取private build/CA/env值，不能仅false→true激活当前v4。

技术报告/原件已push 7ec719f0282f3ff00d95a546801764d7df818ce7：
[Provider原阻断](https://github.com/HJY147/t44-dev-trace/blob/7ec719f0282f3ff00d95a546801764d7df818ce7/reports/reviews/functional-provider-a6c96c5599a9dd7db60eb618a40f9acbaf49817b.md)
[Provider49ef限定闭环](https://github.com/HJY147/t44-dev-trace/blob/7ec719f0282f3ff00d95a546801764d7df818ce7/reports/reviews/functional-provider-49ef08a7e726fa163106647b96e415213f2aae8f.md)
[v4 PUBLIC阻断报告](https://github.com/HJY147/t44-dev-trace/blob/7ec719f0282f3ff00d95a546801764d7df818ce7/reports/reviews/829-public-v4-2996e1e71f1c1160282520b7273ac85c42f4b75acc5042e74836841d75bf1424.md)

无APPROVE、main/global、fault/performance/产品放行。root下一新freeze另审，旧源/反例不追改。
