CREATE TABLE `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'id',
  `username` varchar(32) DEFAULT '' COMMENT '用户名',
  `email` varchar(100) DEFAULT '' COMMENT '邮箱',
  `password` varchar(64) DEFAULT '' COMMENT '密码',
  `status` enum('正常','锁定') DEFAULT '正常' COMMENT '状态',
  `role_id` int(11) DEFAULT 0 COMMENT '角色',
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_username` (`username`)
) COMMENT='用户表';

INSERT INTO `users` VALUES (1,'admin','','$2b$12$3OCr4M1JAk0v0bXJ6q1FH.6eqNGSg/AbP/5wNA82H.F7QvAp4h3/C','正常',1);

CREATE TABLE `roles` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `role` enum('admin','DBA','主管','员工') DEFAULT '员工',
  `department` varchar(32) DEFAULT '',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uni_idx_role_department` (`role`,`department`)
)COMMENT='角色表';

INSERT INTO `roles` VALUES (1,'admin','管理员');

CREATE TABLE `privilege` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `role_id` int(11) DEFAULT 0,
  `instance_id` int(11) DEFAULT 0,
  `privileges` varchar(64) DEFAULT '',
  PRIMARY KEY (`id`),
  KEY `role_id` (`role_id`),
  KEY `instanse_id` (`instance_id`)
) COMMENT='权限表';

CREATE TABLE `instance` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ins_name` varchar(32) DEFAULT '',
  `type` enum('master','slave') DEFAULT 'master',
  `host` varchar(16) DEFAULT '',
  `port` int(11) DEFAULT 0,
  `user` varchar(32) DEFAULT '',
  `password` varchar(500) DEFAULT '',
  `db_type` enum('mysql','cassandra','pgsql','mongodb','redis') DEFAULT 'mysql' COMMENT '数据库类型字段 ',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ins_name` (`ins_name`)
) COMMENT='机器表';

CREATE TABLE `workorder` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `sponsor` int(11) DEFAULT 0,
  `approver_manager` int(11) DEFAULT 0,
  `approver_dba` int(11) DEFAULT 0,
  `instance_id` int(11) DEFAULT 0,
  `dbname` varchar(32) DEFAULT '',
  `remark` varchar(255)  DEFAULT '',
   `is_check` int(11) DEFAULT '0' COMMENT '是否检查',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `end_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
)COMMENT='工单表';

CREATE TABLE `sqlrecord` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `content` text,
  `status_code` int(11) DEFAULT 0,
  `approved` int(11) DEFAULT 0,
  `remark` text,
  `sequence` varchar(50) DEFAULT '',
  `wkodid` int(11) DEFAULT 0,
  `affected_rows` varchar(100) DEFAULT '' COMMENT ' 影响行数',
  `execute_time` varchar(100) DEFAULT '' COMMENT ' 执行时间',
   `backup_dbname` varchar(255) DEFAULT NULL COMMENT '备份库',
  PRIMARY KEY (`id`)
)COMMENT='sql记录表';

CREATE TABLE `workorder_data_export` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `sponsor` int(11) DEFAULT NULL,
  `approver_manager` int(11) DEFAULT 0,
  `approver_dba` int(11) DEFAULT 0,
  `instance_id` int(11) DEFAULT 0,
  `dbname` varchar(32) DEFAULT '',
  `sql` text ,
  `status` int(11) DEFAULT '0',
  `path` varchar(255)  DEFAULT '',
  `remark` varchar(255)  DEFAULT '',
   `is_check` int(11) DEFAULT '0' COMMENT '是否检查',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `approve_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `download_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `end_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
)  COMMENT='数据导出工单表' ;

CREATE TABLE `desensitization_info` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `instance_id` int(11) DEFAULT 0,
  `dbname` varchar(32) DEFAULT '',
   `field` varchar(32) DEFAULT '',
  PRIMARY KEY (`id`)
) COMMENT='脱敏信息表' ;

CREATE TABLE `slowlogs` (
    `id` bigint(11) NOT NULL AUTO_INCREMENT,
    `dbid` int(11) DEFAULT 0,
    `db_user` varchar(32) DEFAULT '',
    `app_ip` varchar(32) DEFAULT '',
    `thread_id` int(11) DEFAULT 0,
    `exec_duration` varchar(32) DEFAULT '',
    `rows_sent` int(11) DEFAULT 0,
    `rows_examined` int(11) DEFAULT 0,
    `start_time` int(11) DEFAULT 0,
    `sql_pattern` text,
    `orig_sql` text,
    `fingerprint` varchar(50) DEFAULT '',
    `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `index_time` (`create_time`)
) COMMENT='慢日志表' ;

CREATE TABLE `query_log` (
    `id` bigint(11) NOT NULL AUTO_INCREMENT,
    `sponsor` int(11) DEFAULT 0,
    `instance_id` int(11) DEFAULT 0,
     `dbname` varchar(32) DEFAULT '',
     `sql` text,
    `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `index_time` (`create_time`)
) COMMENT='查询记录表' ;

CREATE TABLE `exec_shell_log` (
  `id` bigint(11) NOT NULL AUTO_INCREMENT COMMENT ' ',
  `log_name` varchar(32)   DEFAULT NULL COMMENT ' ',
  `cmd` text   COMMENT ' ',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT ' ',
  PRIMARY KEY (`id`)
) COMMENT='shell记录表'