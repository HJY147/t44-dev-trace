# 失败现场密封：FORENSIC ONLY

原正常SEAL_P14_V52.sh保留不改。新增独立取证入口SEAL_FORENSIC_P14_V52.sh，用于运行失败、result缺失/损坏或writer_finalized=false时保存停止后的现有现场。它不读result，不要求raw/footer完整，不把false补true，也不删除或改写任何旧文件。原正式测量与验收门禁完全保留。

使用前必须独立记录真实进程已退出、所有producer及内外部writer停止（含operator-channel/evidence-neutral写者）、对应run/W及观察时间。docker容器不在列表只能作为已移除容器现象，不能单独证明进程退出；显式全停声明必须由实际退出与所有writer检查支持。进程仍活/仍可能写入时不得封存；需要先等待/停止相应本次进程，不能伪造全停。脚本本身没有通用办法穷尽全部外部写者，不能将该限制隐藏为已自动核实。

以后获准执行时，先将本PUBLIC helper和wrapper放入同一个新W/public；不改tool-manifest、原backup.py或新backup.key：
```sh
sh SEAL_FORENSIC_P14_V52.sh /root/t44-final-20261031/QA753_NEXT_V52 r30manualp14 /root/t44-sealed-p14/r30manualp14.failure01.forensic.753backup FORENSIC_ONLY_EXITED_ALL_PRODUCERS_AND_WRITERS_STOPPED
```

外部输出父目录必须已存在。路径与receipt不得存在，必须在W外并以.forensic.753backup结尾；失败留部分产物，不覆盖/删除或自动重跑。wrapper拒绝非p14/不正确声明、目标容器仍处活动状态、Docker枚举失败、镜像错误；只读挂载W，network none，并在容器内核原v5.2 manifest及每件安装工具/新key SHA，同时核PUBLIC helper自身SHA。root不读密钥或private工具内容。

PUBLIC FORENSIC_BACKUP_P14.py只在容器内导入已核runtime.Seal与本W的新backup.key，流式保存原backup.py同样六个证据目录及内部文件hash manifest，64GiB封存密文上限不变。它专门流式核cipher SHA，避免将整个大密文一次读入内存；发现单文件size/mtime/ino在复制间变化即失败。该检查不代替全停事实检查。未观察到或未记录的失败交换无法补造；归档完整只表示保存现有文件。

成功receipt明确purpose=FORENSIC_ONLY，writer_complete_asserted/cohort_complete_asserted/acceptance_pass_asserted全部false，不表达实际writer一定不完整，只表示没有作完整断言。原失败result及raw原样保存。密文footer沿用753-backup-complete仅代表归档容器完成，不代表测量raw完整。

root仅搬密文和同名.receipt.json，可在LOAD本机及下载后各运行：
```sh
python3 CHECK_FORENSIC_RECEIPT.py /本地/r30manualp14.failure01.forensic.753backup /本地/r30manualp14.failure01.forensic.753backup.receipt.json
```
它只核目的标记、文件名、bytes及流式SHA；不是认证解密。独立测试岗随后用本轮新backup.key和冻结verify_backup.py核认证解密、压缩tar流及全部内部文件hash，不要求raw本身完整才能接受归档。若raw损坏/缺footer/后置缺失，按原门禁判NP并保留原失败，不影响保存现场。

密文与receipt成功生成、已停止所有写者且至少一份本地下载bytes/SHA匹配、密文本地保存可持续访问后，就可让用户及时手动保留磁盘停机；无需等待P95/业务/测量raw判定通过。独立认证解密可在本地停机后继续；若下载/传输校验失败必须明确尚未回收，不能谎称证据安全。若封存/磁盘/工具hash失败，原W保留，不强行绕过hash或伪造receipt；汇报失败并区分保留云盘现场与已回收本地。

本轮4项参数/default拒绝与静态自检通过；新增1个正向往返测试覆盖两种合成W（缺result及writer_finalized=false），使用本轮本地新生成临时key执行真实Seal编码→原verify_backup认证解密/压缩流/全部文件hash核验→逐字比较恢复文件。PUBLIC receipt checker亦在这两个合成归档上核bytes/SHA通过。原false/missing及不完整合成raw保留不变，证明归档兼容性不依赖测量完整。原verify_backup字节SHA保持382fe87d...；没有调用Docker、旧PRIVATE或任何实际服务器/key/结果。成功格式兼容已离线验证，当前LOAD能力尚未现场验证。本PUBLIC路径不构成执行、环境身份或grant授权。
