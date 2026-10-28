# f7 P64 20:00新窗口：限定派生

操作者为后端AI；root于本轮明确新建窗口，称旧16:00包尚未执行业务。此项不续签旧grant/session，不延长已消费case。产品仍为f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f；无actual phase/grant/session输入，本岗不云操作。

输入为20eb4ae3已封的13运行文件、manifest1da8ff5e…feb1de8、两阶段grant/APP/LOAD模板、修复后的完整UI外层格式，以及部署岗新20:00 GEN（9edafbbff0586b5f77a701bd37f715685fba4169abaae510474343af75a8b427）。输出另置p64-f7-window2000，安装目的/root/t44-r9/p790-f7-2000-ui03。所有原16:00目录、3红失败和7回放原件保留。

运行文件允许差分仅为bootstrap/http/transfer三个datetime截止常量16→20、authority STOP字符串16→20及对应EXACT窗口错误标签；9个其余运行文件逐字相同。产品/source、seed44/04:00anchor、SQL、认证、600TTL、330/90秒、80/800/8000、400active/no-think、共享abort、锁→admit→SQL、GEN父锁外均不得变化。manifest只更新窗口/前链/派生文件哈希与实际新GEN pin；模板只更新窗口、安装路径和manifest pin，actual字段保持null、admitted=false。

生成器须对13输入核旧manifest，O_EXCL写新文件；复用已审原安装格式，raw≤12000，实际base64(raw)+300及完整UI命令+300都<18000。限定验证包括允许差分、Python3.10 AST、20Z截止及旧16Z/缺授权拒绝、完整外层安装回放和所有源SHA/权限，不重复无关整套产品测试。这里没有正式600秒/7角色授权；bootstrap先空表，再GEN idle和真实六角色核验，再root另给pressure grant的次序不变。
