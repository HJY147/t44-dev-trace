# 第二原生环境实际派工与root技术选择

部署AI过程素材，不是学生本人研究报告。root要求在functional验收环境不被打断的前提下，为精确产品c8cea7e82805de5283ce67501769fa9a4efc1047准备第二个performance原生runtime；只准读取指定新performance-db/appenv，只准新t44_p829_20261025、新端口18097/25697/24397/35697/45716–45725、新CA/目录/用户/vhost。先设计，硬绑工具只能显式旧新SHA/次数派生；不得宽泛放库名、不读admin/独立目录、不改旧run、初始build或受保护MySQL配置。08:46:30/08:47/08:50停止窗不延长。DB夹具由数据库岗负责，部署不猜IDs、不seed；只有root确认functional结束且旧连接停止后才可启动新应用。

最初root明确8worker。本岗只读实际MySQL元数据得到151上限、3连接含probe、历史峰值70；说明8*15+两个辅助engine30+其他2的最坏模型152高于151，不能将当前低连接当容量保证。root随后明确选择保守7worker（105+30+其他2=137模型）。这是root协调AI作出的技术选择，不冒充用户本人操作。

实际实施：先4b27fde以固定53d五件公开模板和精确functional/performance两配置派生W8；prepare/broker/c8绑定成功，未启动任何新API/consumer/scheduler。再3c4ed19分层派生W7，只变worker有效配置及新的-w7文件/目录命名空间；旧W8控制器、预备build和artifact在原路径逐字保持。W7在08:14:46前准备好，实际启动和正式性能结果仍等root phase准入，不自动延长时限或先开跑。每层差量和6项合成guard、真实源/档案/证书/连接元数据留公开记录；不编造测试或停机结果。
