# 身份语义修正设计与证据界限

先root设计checkpoint：保原manifest/CIID/archive；classic.actualId==configId照旧。fresh Docker29 containerd actual.Id是OCI manifest Descriptor digest时，仅在原已核archive内取相同digest的真实blob并重新SHA/size，config descriptor必须等于原CIConfigID的真实configBlob，所有OCI layer原bytes SHA/size和解压diffID按序等于rootfs.diff_ids；实际labels/os/arch/rootfs同源全核。未知mediaType、缺blob、改变config/Env、layer、labels、descriptor任一拒绝。没有把两个ID当随意互换、没有重tag覆盖或跳过任何身份检查；旧0a1 helper和3c599/7905数据保持。

05私有原raw24587bytes只含2个完整alias、破损中间行、末tag/config与complete marker，明确中间截断，末marker不证明全7。新47b50 proof程序先O_EXCL raw JSONL再执行，完整原件与stdout<3KB摘要分离；没有打印Config.Env/Cmd。13项离线正负0.05s通过，首lintunusedstat/TypeError和testunusedhashlib均已修并保过程说明。

root真实双目标官方云助手回执两节点exit0/summary complete/all7 oci-descriptor-to-original-config，50297bytes/rawSHA30b1ca48f152cae797862319cdda80c0a0b65ed5af32acf4b18ea55d531cc8d0。部署只读root授权两summary原文件，未云操作、未取完整raw；两个相同输入的raw同bytes不代替节点liveness证明，节点对应靠root实际双目标云助手回执。原始50k待后续完整回收，不冒已逐页审完整raw。V2wrapper只接受fresh全7证明后写新overlay/receipt，不再Dockerload、不替换旧别名。

官方依据（2026-10-25浏览）：Docker https://docs.docker.com/engine/storage/containerd 说明fresh29默认containerd；OCI https://github.com/opencontainers/image-spec/blob/main/config.md 区分configID和uncompressedDiffID，https://github.com/opencontainers/image-spec/blob/main/manifest.md 定义manifest/config/layer descriptor。文档解释不是本机通过证据，实链由真实blob计算。
