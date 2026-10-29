# ROLE-deployment-ECR-SOURCE-POLICY-v1

本岗为本轮实际root派工/后续澄清建立归档ID。以下是实际派工，不冒充已执行云动作。

## root研究转实现派工

五个精确digest在ECR官方docker/library已实际逐项imagetools inspect成功（Python/node/nginx/mysql/rabbitmq，14:45:29，13秒exit0）；不是只tag匹配。官方Docker变量页https://docs.docker.com/build/building/variables/现列正确变量EXPERIMENTAL_BUILDKIT_SOURCE_POLICY（不是BUILDX_SOURCE_POLICY），CONVERT例子有规则JSON。请立即给出精确政策JSON/有时限build步骤，优先在不改tracked源/daemon/DNS配置下EXACT remap3个FROM，尾加DENY docker.io* fail-closed。Compose默认实际调用Bake。若需要脚本由你在自己新worktree基于563/fe6完成代码/文档，root待审核后UI运行；不做云动作。MySQL/RabbitMQ后续显式ECR同digest pull+单独Compose delivery overlay保持原compose不变，先别启动。

## root范围与时限补充

需要尽快拿到policy helper可审版本（不需要长篇研究）。root当前已merge563为e084?（请gitrev当前读取基点或仍563即可），云时限17:00，现约14:50。helper可只productiondeployment/ecr-build-policy.py生成JSON到明确私有runtimefile，不带新deps、无cloudIP/ID，不改C源码/.env，不启动服务；后续root用已校验全文的CloudAssistant relay。记录已知原build失败，ECRmetadata成功不同于实际层下载/构建成功。

审核岗快速结论已核CONVERT后重评估可行，注意JSON selector.match_type="EXACT"（snake_case，不是matchType）。官方BuildKit转换成功短路本轮以ECR新identifier重评估，不误触docker.io/*DENY。root已真实失败+两个probe安全投影记录提交6d57999，代码未变；你docs不要覆盖rootrecords，build还未重试。请尽快交付脚本可审。

## root审查反馈

root已全文读helper/md，未见实质阻断，已发审核岗实际文件检查。请完成必要校验提交返回commit（不运行云）。记toolcommit与产品C分开。生成policy后root只把已审helper原文UIrelay到/run，hash比对后单独调用build。
