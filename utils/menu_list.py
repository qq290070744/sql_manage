instances = \
    {
        'cid': 10, 'title': '实例列表', 'path': '/instances', 'icon': 'el-icon-s-order'
    }
select = \
    {
        'cid': 20, 'title': 'SELECT', 'path': '/select', 'icon': 'iconfont icon-chaxun'
    }
inspect = \
    {
        'cid': 21, 'title': 'CRUD', 'path': '/inspect', 'icon': 'iconfont icon-zhihang1'
    }
roles = \
    {
        'cid': 30, 'title': '角色列表', 'path': '/roles', 'icon': 'iconfont icon-jiaoseguanli1'
    }
users = \
    {
        'cid': 31, 'title': '用户列表', 'path': '/user', 'icon': 'iconfont icon-yonghuguanli'
    }
pending = \
    {
        'cid': 40, 'title': '待审批', 'path': '/pending', 'icon': 'iconfont icon-daishenpi'
    }
workorder = \
    {
        'cid': 41, 'title': '我的SQL工单', 'path': '/workorder', 'icon': 'iconfont icon-order-mine'
    }
historyorder = \
    {
        'cid': 42, 'title': '历史SQL工单', 'path': '/historyorder/', 'icon': 'iconfont icon-lishi'
    }
workorder_data_export = \
    {
        'cid': 43, 'title': '我的数据导出工单', 'path': '/workorder_data_export/', 'icon': 'iconfont icon-lishi'
    }
historyorder_data_export = \
    {
        'cid': 44, 'title': '历史数据导出工单', 'path': '/historyorder_data_export', 'icon': 'iconfont icon-order-mine'
    }
get_query_log = \
    {
        'cid': 45, 'title': '历史查询记录', 'path': '/get_query_log', 'icon': 'iconfont icon-order-mine'
    }
inception_show_variables = \
    {
        'cid': 50, 'title': '审核规则', 'path': '/inception_show_variables', 'icon': 'iconfont icon-daishenpi'
    }
inception_show_levels = \
    {
        'cid': 51, 'title': '自定义审核级别', 'path': '/inception_show_levels', 'icon': 'iconfont icon-daishenpi'
    }

get_desensitization_info_list = \
    {
        'cid': 60, 'title': '获取脱敏字段列表', 'path': '/get_desensitization_info_list', 'icon': 'iconfont icon-daishenpi'
    }
get_slowlog_list = \
    {
        'cid': 70, 'title': '慢日志信息列表', 'path': '/get_slowlog_list', 'icon': 'iconfont icon-daishenpi'
    }
processlist = \
    {
        'cid': 80, 'title': '会话管理', 'path': '/processlist', 'icon': 'iconfont icon-daishenpi'
    }
tablesapce = \
    {
        'cid': 90, 'title': 'Top表空间', 'path': '/tablesapce', 'icon': 'iconfont icon-order-mine'
    }
innodb_trx = \
    {
        'cid': 100, 'title': '事务信息', 'path': '/innodb_trx', 'icon': 'iconfont icon-order-mine'
    }
trxandlocks = \
    {
        'cid': 110, 'title': '锁信息', 'path': '/trxandlocks', 'icon': 'iconfont icon-order-mine'
    }
instanceaccount = \
    {
        'cid': 120, 'title': '数据库账号管理', 'path': '/instanceaccount', 'icon': 'iconfont icon-order-mine'
    }
param_list = \
    {
        'cid': 130, 'title': '参数配置', 'path': '/param_list', 'icon': 'iconfont icon-order-mine'
    }
instance_monitor = \
    {
        'cid': 140, 'title': '实时监控', 'path': '/instance_monitor', 'icon': 'iconfont icon-order-mine'
    }
get_sales_order = \
    {
        'cid': 150, 'title': '销量查询', 'path': '/get_sales_order', 'icon': 'iconfont icon-order-mine'
    }
exec_shell = \
    {
        'cid': 160, 'title': '执行shell', 'path': '/exec_shell', 'icon': 'iconfont icon-order-mine'
    }
menu_list = {
    'admin': [
        {'id': 0, 'title': '实例管理', 'icon': 'el-icon-s-cooperation', 'children': [
            instances, instance_monitor, processlist, tablesapce, innodb_trx, trxandlocks, instanceaccount, param_list
        ]},
        {'id': 1, 'title': 'SQL 执行', 'icon': 'el-icon-s-promotion', 'children': [
            select, inspect, get_sales_order, exec_shell
        ]},
        {'id': 2, 'title': '权限管理', 'icon': 'iconfont icon-quanxianguanli', 'children': [
            roles, users
        ]},
        {'id': 3, 'title': '工单管理', 'icon': 'iconfont icon-gongdanguanli', 'children': [
            pending, workorder, historyorder, workorder_data_export, historyorder_data_export, get_query_log
        ]},
        {'id': 4, 'title': 'goInception配置管理', 'icon': 'el-icon-s-cooperation', 'children': [
            inception_show_variables, inception_show_levels
        ]},
        {'id': 5, 'title': '脱敏字段管理', 'icon': 'el-icon-s-cooperation', 'children': [
            get_desensitization_info_list
        ]},
        {'id': 6, 'title': '慢日志管理', 'icon': 'el-icon-s-cooperation', 'children': [
            get_slowlog_list
        ]},
    ],
    'DBA': [
        {'id': 0, 'title': '实例管理', 'icon': 'el-icon-s-cooperation', 'children': [
            instances, instance_monitor, processlist, tablesapce, innodb_trx, trxandlocks, instanceaccount, param_list
        ]},
        {'id': 1, 'title': 'SQL 执行', 'icon': 'el-icon-s-promotion', 'children': [
            select, inspect, get_sales_order, exec_shell
        ]},
        {'id': 2, 'title': '权限管理', 'icon': 'iconfont icon-quanxianguanli', 'children': [
            roles, users
        ]},
        {'id': 3, 'title': '工单管理', 'icon': 'iconfont icon-gongdanguanli', 'children': [
            pending, workorder, historyorder, workorder_data_export, historyorder_data_export, get_query_log
        ]},
        {'id': 4, 'title': 'goInception配置管理', 'icon': 'el-icon-s-cooperation', 'children': [
            inception_show_variables, inception_show_levels
        ]},
        {'id': 5, 'title': '脱敏字段管理', 'icon': 'el-icon-s-cooperation', 'children': [
            get_desensitization_info_list
        ]},
        {'id': 6, 'title': '慢日志管理', 'icon': 'el-icon-s-cooperation', 'children': [
            get_slowlog_list
        ]},
    ],
    '主管': [
        {'id': 0, 'title': '实例管理', 'icon': 'el-icon-s-cooperation', 'children': [
            instance_monitor
        ]},
        {'id': 1, 'title': 'SQL 执行', 'icon': 'el-icon-s-promotion', 'children': [
            select, inspect, get_sales_order
        ]},
        {'id': 3, 'title': '工单管理', 'icon': 'iconfont icon-gongdanguanli', 'children': [
            pending, workorder, historyorder, workorder_data_export, historyorder_data_export
        ]},
        {'id': 6, 'title': '慢日志管理', 'icon': 'el-icon-s-cooperation', 'children': [
            get_slowlog_list
        ]},
    ],
    '员工': [
        {'id': 0, 'title': '实例管理', 'icon': 'el-icon-s-cooperation', 'children': [
            instance_monitor
        ]},
        {'id': 1, 'title': 'SQL 执行', 'icon': 'el-icon-s-promotion', 'children': [
            select, inspect, get_sales_order
        ]},
        {'id': 3, 'title': '工单管理', 'icon': 'iconfont icon-gongdanguanli', 'children': [
            workorder, workorder_data_export
        ]},
        {'id': 6, 'title': '慢日志管理', 'icon': 'el-icon-s-cooperation', 'children': [
            get_slowlog_list
        ]},
    ],
}
