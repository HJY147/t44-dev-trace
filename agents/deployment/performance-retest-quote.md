# 短时性能复测报价（待用户批准，不执行）

截至2026-10-24 03:31UTC（北京11:31）核价；用户截止 **11月28日**，尚未授权付费。建议先做独立 **0元发压器校准**，只用合成目标、不触SUT，当前尚未执行。

方案：AWS us-east-1，两台普通Linux按需实例，同账户、同AZ-ID、私网发压。应用c7i.2xlarge **8vCPU/16GiB**，独立发压c7i.xlarge **4vCPU/8GiB**，gp3盘80+40GiB。规格是工程建议，非已确认教师硬门槛；默认shared tenancy共享宿主，vCPU不当作独占物理核，也不是Dedicated Instance/Host（本表不含其额外费用）。[规格](https://aws.amazon.com/ec2/instance-types/c7i/)、[租用隔离说明](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/dedicated-instance.html)

| 项目 / 原始单价USD | 1小时 | 2小时 |
| --- | ---: | ---: |
| 应用 $0.357/小时 | 0.3570 | 0.7140 |
| 发压 $0.1785/小时 | 0.1785 | 0.3570 |
| gp3共120GiB，$0.08/GiB月，按秒折算 | 0.01290 | 0.02581 |
| 公网IPv4两个，各$0.005/小时 | 0.0100 | 0.0200 |
| **小计，未含税/需收费的公网流出** | **约0.56** | **约1.12** |

计算：计算资源(0.357+0.1785)×h；磁盘0.08×120×(h×3600)/(31×86400)，按10月31天示例，保留到实际删除；IPv4 2×0.005×h。计算实例采用官方直接小时价，**没有月价÷730**。价格源是[官方当前小时价数据](<https://b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/ec2/USD/current/ec2-ondemand-without-sec-sel/US%20East%20(N.%20Virginia)/Linux/index.json>)（发布2026-10-23T22:13:55Z）；[gp3区域单价](https://docs.aws.amazon.com/en_en/emr/latest/ManagementGuide/emr-plan-storage-compare-volume-types.html)、[按秒规则](https://aws.amazon.com/ebs/pricing/)、[IPv4](https://aws.amazon.com/vpc/pricing/)。不加IOPS/吞吐、快照、NAT网关或负载均衡器。

建议计划2小时：准备/数据/接线60分钟、正式窗10分钟、核对导出清理及余量50分钟；不是完成保证。**供用户考虑的审批上限USD3**，不是云厂商硬封顶，批准前不创建资源/充值；不足则报告，不自动续费。价格不保证、不含人工；税费、支付/开户验证或充值门槛、实例配额/库存及账户免费额度均未核实，不换算人民币、不承诺270ms。

流量：[同AZ-ID私网流量免费](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-share-billing.html)，发压不走公网；公网出流量另计，账户聚合100GB/月免费额度剩余未知，不在本表抵扣。[EC2计费/流量](https://aws.amazon.com/ec2/pricing/on-demand/) 停机只停计算费，[保留EBS仍收费](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-lifecycle.html)，闲置EIP也收费。获准运行后须导出所需证据，再终止两实例、核实删除全部测试盘/遗留快照并释放EIP；只关机不算完成删除，[终止规则](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/terminating-instances.html)。本报价未改部署代码/live/demo/旧包或automation。
