# 935独立TLS修复（真实云执行由root完成）

原nginx只指定client/proxy temp到/tmp，未显式指定fastcgi/uwsgi/scgi。root实际限定stderr捕获 `mkdir() "/var/cache/nginx/fastcgi_temp" failed (30: Read-only file system)`，TLS Restarting/Pid0/Exit1非OOM；原失败10140 bytes/SHA673e2018c64280b29f9606477f924fa1177d59c9418702f46142962b5a233076保留，本岗不读raw或猜整改。

新 tls-repair.py 12987 bytes/SHA c3459c2213b628829fd3f865007ef1b1931ba4284c77ee6a92e9fa0cdbb5dd9c。10项本地guard0.04s与Ruff绿，不是云证明。原770d/diag56d78/controller daaf/94caf严格核SHA；nginx preimage==原生成器，再复制到新目录只新增3个/tmp temp。新Overlay只替TLS nginx RO文件，原证书/UID101/readonly/capdrop/ports/networks/image/DB/API保持；memory-only完整Compose config核，不把含Env的全config写日志。保旧21Z stop锚，原文件不改。

```sh
python3 /root/t44-r9/tls-repair.py \
  --base-phase /root/t44-r9/campaign-935/p \
  --diagnostic-profile /root/t44-r9/diag-profile-935-01 \
  --output /root/t44-r9/tls-repair-935-01
```

nginx -t用同UID/RO/tmpfs/网络的一次--rm无端口容器实际检查，完整stdout/stderr保存0600。只up --no-deps tls-gateway，不启动其他服务；host Python stdlib HTTPSConnection用原CA+IP SAN校验，无代理/重定向/Token，实际GET/api/v1/projects必须401，bounded重试每次原件保留，失败不能把API running当可用。

root实际报告此命令成功：nginx-t passed，严格CA+IP 401，attempt1且no credentials；新binding SHA546e3c1bace95d9fff9809f2fbf7df4bee67abc013324e79cb55c64c7ef32e9d，旧770d/56d78/stop未变，onlyTLSup=true。本岗未执行云操作、未独立读取云raw；root保JSON与页面证据。此结果是TLS连通门禁，不是业务、吞吐或400/600验收通过。

后续新campaign生成器须在新模板直接设置client/proxy/fastcgi/uwsgi/scgi全部/tmp temp，并在up后真实host CA+IP HTTPS门禁；旧app-campaign.py/770d只保历史，不可为了新generation覆写旧controller或stop lease。
