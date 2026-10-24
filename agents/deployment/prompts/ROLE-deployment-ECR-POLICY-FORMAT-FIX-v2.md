# ROLE-deployment-ECR-POLICY-FORMAT-FIX-v2

本岗为本轮实际root派工建立归档ID；原文如下。

实云ECR build已失败：14:52:56，1秒，exit1；未到网络层，末DENY命中原nginx完整引用（与原FROM标签摘要字面完全相同）：could not resolve image due to policy: source "docker-image://docker.io/library/nginx:stable-alpine@sha256:479..." denied by policy。policy生成hash已核502...bed5，原全文UI一致。请暂停overlay编码，优先定位官方BuildKit实际版本/JSON schema为何EXACT CONVERT未生效：可能默认输入字串转换、match_type JSON编码enum/Buildx预处理。不要移除deny盲重试，不云动作。Root保留真实失败。可产新精确修正版但必须解释依据，不能改image摘要。

root和审核岗已定位确因：官方v0.25.1 sourcepolicy/formatter.go https://raw.githubusercontent.com/moby/buildkit/v0.25.1/sourcepolicy/formatter.go EXACT分支return s.Identifier而不是updates目标！故mutated=false继续DENY。请仅将3个selector match_type改WILDCARD但identifier仍完整literal、不得加*，保持末DENY；增加官方engine离线反例验证或严谨官方Format路径guard，不盲删DENY。这是受控最小修正，新helper/policy需新hash和文件名v2避免覆盖已云文件；保留原失败。优先修正提交，overlay后续继续。
