# v5 定点复核（先于实现/执行）

保留v4反例原文件不改，另建822_v5_scope_return_recheck.py，使用同一纯fake配置对精确PUBLIC control08ac2373重放两个输入：UTC+20/mono0/expiry10应在transport前拒绝；HTTP15/run120、0s完整201后20s合法neutral handoff应保留HTTP complete/status/body，setup单独READY，HTTP elapsed仍0。只改复核源hash和已审修复后的相反判定，不运行36或私有bundle。

真实Gate构造与request、synthetic receipt/container身份、内存journal、假clock/transport/handoff；自有tmp822临时文件。0socket/真实SUT，不调系统钟/启动supervisor/provider，不读实际native grant/env/build/token。此probe只验证先前控制边界反例关闭，不形成业务oracle或实际HTTP验收。
