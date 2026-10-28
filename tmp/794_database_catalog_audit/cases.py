"""Published owner mutation recipes, corrected split-FK setup; no independent cases."""


def cases(reference, actual):
    index = "ALTER TABLE tasks DROP INDEX ix_tasks_project_state, ADD {} ix_tasks_project_state ({}){}"
    foreign = "ALTER TABLE projects DROP FOREIGN KEY fk_projects_creator, ADD CONSTRAINT fk_projects_creator FOREIGN KEY(created_by) REFERENCES {}(id){}"
    check = "ALTER TABLE users DROP CHECK ck_users_active, ADD CONSTRAINT ck_users_active CHECK ({})"
    values = [
        ("counter_growth", True, "ALTER TABLE users AUTO_INCREMENT=1234"),
        ("redundant_parentheses", True, check.format("((`active` IN (0,1)))")),
        (
            "utf8mb4_introducer",
            True,
            "ALTER TABLE users DROP CHECK ck_users_hash_shape, ADD CONSTRAINT ck_users_hash_shape CHECK ((LEFT(`password_hash`,10)=_utf8mb4'$argon2id$') AND (CHAR_LENGTH(`password_hash`)>30))",
        ),
        (
            "ascii_introducer",
            True,
            "ALTER TABLE users DROP CHECK ck_users_hash_shape, ADD CONSTRAINT ck_users_hash_shape CHECK ((left(`password_hash`,10)=_ascii'$argon2id$') AND (char_length(`password_hash`)>30))",
        ),
        (
            "foreign_noaction_restrict",
            True,
            foreign.format("users", " ON DELETE NO ACTION ON UPDATE RESTRICT"),
        ),
        ("foreign_qualified_self", True, foreign.format(f"`{actual}`.`users`", "")),
        (
            "index_asc_btree",
            True,
            index.format("KEY", "project_id ASC,state ASC,id ASC", " USING BTREE"),
        ),
        (
            "index_rebuild_same_definition",
            True,
            index.format("KEY", "project_id,state,id", ""),
        ),
        ("index_order", False, index.format("KEY", "state,project_id,id", "")),
        ("index_unique", False, index.format("UNIQUE KEY", "project_id,state,id", "")),
        ("index_desc", False, index.format("KEY", "project_id,state DESC,id", "")),
        (
            "unique_to_nonunique",
            False,
            "ALTER TABLE users DROP INDEX uq_users_username, ADD KEY uq_users_username(username)",
        ),
        (
            "unique_column_order",
            False,
            "ALTER TABLE task_dependencies ADD KEY probe_support(project_id,task_id), DROP INDEX uq_dependencies_edge, ADD UNIQUE KEY uq_dependencies_edge(project_id,depends_on_task_id,task_id)",
        ),
        ("foreign_target_table", False, foreign.format("service_accounts", "")),
        ("foreign_target_schema", False, foreign.format(f"`{reference}`.`users`", "")),
        (
            "foreign_source_order",
            False,
            "ALTER TABLE task_dependencies DROP FOREIGN KEY fk_dependencies_task, ADD CONSTRAINT fk_dependencies_task FOREIGN KEY(task_id,project_id) REFERENCES tasks(project_id,id)",
        ),
        (
            "foreign_target_order",
            False,
            [
                "ALTER TABLE tasks ADD UNIQUE KEY probe_target(id,project_id)",
                "ALTER TABLE task_dependencies DROP FOREIGN KEY fk_dependencies_task, ADD CONSTRAINT fk_dependencies_task FOREIGN KEY(project_id,task_id) REFERENCES tasks(id,project_id)",
            ],
        ),
        ("foreign_cascade", False, foreign.format("users", " ON DELETE CASCADE")),
        ("check_true", False, check.format("1=1")),
        ("check_expanded_in", False, check.format("active IN (0,1,2)")),
        ("check_or_true", False, check.format("active IN (0,1) OR 1=1")),
        (
            "column_type",
            None,
            "ALTER TABLE users MODIFY active SMALLINT UNSIGNED NOT NULL DEFAULT 1",
        ),
        (
            "column_nullable",
            None,
            "ALTER TABLE users MODIFY active TINYINT UNSIGNED NULL DEFAULT 1",
        ),
        ("column_default", None, "ALTER TABLE users ALTER active SET DEFAULT 0"),
        (
            "column_auto_increment",
            None,
            "ALTER TABLE notifications MODIFY id INT UNSIGNED NOT NULL",
        ),
        (
            "index_prefix",
            None,
            "ALTER TABLE users DROP INDEX uq_users_username, ADD UNIQUE KEY uq_users_username(username(8))",
        ),
        ("engine", None, "ALTER TABLE idempotency_requests ENGINE=MyISAM"),
        ("table_collation", None, "ALTER TABLE projects DEFAULT COLLATE=utf8mb4_bin"),
        (
            "column_collation",
            None,
            "ALTER TABLE users MODIFY password_hash VARCHAR(255) CHARACTER SET ascii COLLATE ascii_general_ci NOT NULL",
        ),
        (
            "check_enforcement",
            None,
            "ALTER TABLE users ALTER CHECK ck_users_active NOT ENFORCED",
        ),
    ]

    result = []
    for name, expected, changes in values:
        statements = [changes] if isinstance(changes, str) else changes
        split = []
        for statement in statements:
            if " DROP FOREIGN KEY " in statement and ", ADD CONSTRAINT " in statement:
                drop, add = statement.split(", ADD CONSTRAINT ", 1)
                split.extend(
                    [
                        drop,
                        drop.split(" DROP FOREIGN KEY ", 1)[0]
                        + " ADD CONSTRAINT "
                        + add,
                    ]
                )
            else:
                split.append(statement)
        result.append((name, expected is True, split))
    result.append(
        (
            "index_invisible",
            False,
            ["ALTER TABLE tasks ALTER INDEX ix_tasks_project_state INVISIBLE"],
        )
    )
    return result
