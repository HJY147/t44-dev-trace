# Direct P17 独立可搬运PUBLIC

本目录已复制冻结v1.2必需PUBLIC字节、胶囊和新CLI补件，直接按本目录manifest搬运，无需动态拼旧目录。RUN=r30posttools17，W=/root/t44-final-20261101/QA753_POSTTOOLS_V12_P17，REMOTE=/root/t44-direct-p17。INSTALL与BOOT不要求旧TARGET_PROFILE/APPROVAL/grant；两份新profile/approval仅兼容打包器、默认false，不得提升为旧准入批准。DIRECT不读取它们。新binding含新nonce及未消费material名，当前无真实五件输入/会话，不是已生成packet或现场批准。下一次必须新producer材料/新CMS五件SHA绑定，不能改名复用旧packet。

源五件和胶囊保持原冻结SHA；INSTALL固定W/public工具与密文SHA，接收显式绝对W。压测400/60+600及后置40s，combined不完整非零退出，非零也先封存回收。观察仅投影phase，不读PRIVATE。所有detach外部日志放W外。当前没有云操作或新run触发。Linux8CPU/8GiB验证正在本地可行性检查；本机24GiB不能实际承诺运行28GiB封存容器，须明确区分本地小备份认证与云侧后处理资源。
