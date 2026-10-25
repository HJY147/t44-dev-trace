# root中性新库命名适配（实施前）

root明确指定本次新VM、私有容器MySQL:3306的全新一次性诊断库精确`t44c_r9diag935_p`，准该字面值作为第二允许项；原`t44_diag810_*`保留，不放宽`t44_`或旧正式P/F。DSN库、T44_DATABASE、T44_DIAG_DATABASE仍须逐字同，host/port/user显式声明仍同且13306仍禁止。prepare尚无账户/数据，必须另收root sessionpacket才能执行；本岗不连接。

新增允许精确字面/拒near-match/旧t44_p816/13306的owned gate测试，允许路径仅证明到达create_engine桩，不建连接。此授权仅本轮935诊断，不套未来组合正式F/P库。工具metadata同时把通用Probe的product标成reference，只有app_factory校验过的关键源指纹另记source_binding；不把owned stub记录冒成源935运行或完整镜像证明。
