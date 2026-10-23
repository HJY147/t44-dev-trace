-- T44 schema v1 frozen; MySQL 8.4 / InnoDB.
-- Per-table design review and C1-C4 re-review passed; D004 adopted by user.
-- Frozen specification only: execution/migration results are recorded separately.
-- Run only in an explicitly selected empty schema after per-table approval.
-- No DROP, seed data, database creation, triggers, or implicit application state machine.
-- All connections must use UTC and strict SQL mode; set by runtime connection bootstrap.

CREATE TABLE users (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    username VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    active TINYINT UNSIGNED NOT NULL DEFAULT 1,
    created_at DATETIME(6) NOT NULL,
    updated_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_users_username (username),
    CONSTRAINT ck_users_active CHECK (active IN (0,1)),
    CONSTRAINT ck_users_hash_shape CHECK (LEFT(password_hash,10) = '$argon2id$' AND CHAR_LENGTH(password_hash) > 30)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE service_accounts (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    active TINYINT UNSIGNED NOT NULL DEFAULT 1,
    created_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_service_accounts_name (name),
    CONSTRAINT ck_service_accounts_active CHECK (active IN (0,1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE auth_sessions (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    actor_kind TINYINT UNSIGNED NOT NULL,
    user_id INT UNSIGNED NULL,
    service_account_id INT UNSIGNED NULL,
    token_hash BINARY(32) NOT NULL,
    project_ids JSON NOT NULL,
    scopes JSON NOT NULL,
    expires_at DATETIME(6) NOT NULL,
    revoked_at DATETIME(6) NULL,
    created_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_auth_sessions_token_hash (token_hash),
    KEY ix_auth_sessions_user (user_id,revoked_at,id),
    KEY ix_auth_sessions_service (service_account_id,revoked_at,id),
    CONSTRAINT fk_auth_sessions_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_auth_sessions_service FOREIGN KEY (service_account_id) REFERENCES service_accounts(id),
    CONSTRAINT ck_auth_sessions_actor CHECK (
        (actor_kind = 1 AND user_id IS NOT NULL AND service_account_id IS NULL)
        OR (actor_kind = 2 AND user_id IS NULL AND service_account_id IS NOT NULL)
    ),
    CONSTRAINT ck_auth_sessions_scopes CHECK (
        JSON_TYPE(project_ids) = 'ARRAY' AND JSON_TYPE(scopes) = 'ARRAY' AND
        (actor_kind = 2 OR (JSON_LENGTH(project_ids) = 0 AND JSON_LENGTH(scopes) = 0))
    ),
    CONSTRAINT ck_auth_sessions_expiry CHECK (expires_at > created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE projects (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(2000) NOT NULL,
    version INT UNSIGNED NOT NULL DEFAULT 1,
    created_by INT UNSIGNED NOT NULL,
    created_at DATETIME(6) NOT NULL,
    updated_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    KEY ix_projects_creator (created_by,id),
    CONSTRAINT fk_projects_creator FOREIGN KEY (created_by) REFERENCES users(id),
    CONSTRAINT ck_projects_version CHECK (version BETWEEN 1 AND 2147483647)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE project_members (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    project_id INT UNSIGNED NOT NULL,
    user_id INT UNSIGNED NOT NULL,
    roles_mask TINYINT UNSIGNED NOT NULL,
    active TINYINT UNSIGNED NOT NULL DEFAULT 1,
    version INT UNSIGNED NOT NULL DEFAULT 1,
    created_at DATETIME(6) NOT NULL,
    updated_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_members_project_user (project_id,user_id),
    KEY ix_members_user_active (user_id,active,project_id),
    CONSTRAINT fk_members_project FOREIGN KEY (project_id) REFERENCES projects(id),
    CONSTRAINT fk_members_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT ck_members_roles CHECK (roles_mask BETWEEN 1 AND 7),
    CONSTRAINT ck_members_active CHECK (active IN (0,1)),
    CONSTRAINT ck_members_version CHECK (version BETWEEN 1 AND 2147483647)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE iterations (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    project_id INT UNSIGNED NOT NULL,
    name VARCHAR(100) NOT NULL,
    planned_start DATETIME(6) NOT NULL,
    planned_end DATETIME(6) NOT NULL,
    capacity JSON NOT NULL,
    buffer_quarters SMALLINT UNSIGNED NOT NULL,
    delay_contingency VARCHAR(2000) NOT NULL,
    version INT UNSIGNED NOT NULL DEFAULT 1,
    plan_version INT UNSIGNED NOT NULL DEFAULT 1,
    created_at DATETIME(6) NOT NULL,
    updated_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_iterations_project_id (project_id,id),
    KEY ix_iterations_project_time (project_id,planned_start,id),
    CONSTRAINT fk_iterations_project FOREIGN KEY (project_id) REFERENCES projects(id),
    CONSTRAINT ck_iterations_time CHECK (planned_end > planned_start),
    CONSTRAINT ck_iterations_capacity CHECK (JSON_TYPE(capacity) = 'ARRAY' AND JSON_LENGTH(capacity) BETWEEN 1 AND 100),
    CONSTRAINT ck_iterations_buffer CHECK (buffer_quarters <= 40000),
    CONSTRAINT ck_iterations_versions CHECK (version BETWEEN 1 AND 2147483647 AND plan_version BETWEEN 1 AND 2147483647)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE tasks (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    project_id INT UNSIGNED NOT NULL,
    iteration_id INT UNSIGNED NOT NULL,
    title VARCHAR(200) NOT NULL,
    description VARCHAR(4000) NOT NULL,
    owner_id INT UNSIGNED NOT NULL,
    state TINYINT UNSIGNED NOT NULL DEFAULT 1,
    version INT UNSIGNED NOT NULL DEFAULT 1,
    schedule_version INT UNSIGNED NOT NULL DEFAULT 1,
    delivery_cycle INT UNSIGNED NOT NULL DEFAULT 1,
    review_cycle INT UNSIGNED NOT NULL DEFAULT 1,
    planned_start DATETIME(6) NOT NULL,
    planned_end DATETIME(6) NOT NULL,
    estimated_quarters MEDIUMINT UNSIGNED NOT NULL,
    buffer_quarters SMALLINT UNSIGNED NOT NULL,
    delay_contingency VARCHAR(2000) NOT NULL,
    blocked_from_state TINYINT UNSIGNED NULL,
    block_reason VARCHAR(2000) NULL,
    responsibility_stage TINYINT UNSIGNED NULL,
    artifact_revision CHAR(40) CHARACTER SET ascii COLLATE ascii_bin NULL,
    latest_review_id INT UNSIGNED NULL,
    approved_review_id INT UNSIGNED NULL,
    approved_assessment_id INT UNSIGNED NULL,
    approved_assessment_version INT UNSIGNED NULL,
    escalation_count INT UNSIGNED NOT NULL DEFAULT 0,
    created_at DATETIME(6) NOT NULL,
    updated_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_tasks_project_id (project_id,id),
    KEY ix_tasks_project_state (project_id,state,id),
    KEY ix_tasks_owner_state (project_id,owner_id,state,id),
    KEY ix_tasks_iteration (project_id,iteration_id,id),
    KEY ix_tasks_scan (state,planned_end,id),
    CONSTRAINT fk_tasks_project FOREIGN KEY (project_id) REFERENCES projects(id),
    CONSTRAINT fk_tasks_iteration FOREIGN KEY (project_id,iteration_id) REFERENCES iterations(project_id,id),
    CONSTRAINT fk_tasks_owner FOREIGN KEY (project_id,owner_id) REFERENCES project_members(project_id,user_id),
    CONSTRAINT ck_tasks_state CHECK (state BETWEEN 1 AND 7),
    CONSTRAINT ck_tasks_versions CHECK (version BETWEEN 1 AND 2147483647 AND schedule_version BETWEEN 1 AND 2147483647 AND delivery_cycle BETWEEN 1 AND 2147483647 AND review_cycle BETWEEN 1 AND 2147483647),
    CONSTRAINT ck_tasks_time CHECK (planned_end > planned_start),
    CONSTRAINT ck_tasks_hours CHECK (estimated_quarters BETWEEN 1 AND 400000 AND buffer_quarters <= 40000),
    CONSTRAINT ck_tasks_block CHECK (
        (state = 3 AND blocked_from_state IS NOT NULL AND blocked_from_state IN (1,2,4,5) AND block_reason IS NOT NULL AND CHAR_LENGTH(TRIM(block_reason)) > 0 AND responsibility_stage IS NOT NULL AND responsibility_stage BETWEEN 1 AND 5)
        OR (state <> 3 AND blocked_from_state IS NULL AND block_reason IS NULL AND responsibility_stage IS NULL)
    ),
    CONSTRAINT ck_tasks_assessment_pair CHECK (
        (approved_assessment_id IS NULL AND approved_assessment_version IS NULL)
        OR (approved_assessment_id IS NOT NULL AND approved_assessment_version IS NOT NULL AND approved_assessment_version BETWEEN 1 AND 2147483647)
    ),
    CONSTRAINT ck_tasks_escalations CHECK (escalation_count <= 2147483647)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE task_dependencies (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    project_id INT UNSIGNED NOT NULL,
    task_id INT UNSIGNED NOT NULL,
    depends_on_task_id INT UNSIGNED NOT NULL,
    created_by INT UNSIGNED NOT NULL,
    created_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_dependencies_edge (project_id,task_id,depends_on_task_id),
    KEY ix_dependencies_reverse (project_id,depends_on_task_id,task_id),
    KEY ix_dependencies_creator (created_by),
    CONSTRAINT fk_dependencies_task FOREIGN KEY (project_id,task_id) REFERENCES tasks(project_id,id),
    CONSTRAINT fk_dependencies_predecessor FOREIGN KEY (project_id,depends_on_task_id) REFERENCES tasks(project_id,id),
    CONSTRAINT fk_dependencies_creator FOREIGN KEY (created_by) REFERENCES users(id),
    CONSTRAINT ck_dependencies_not_self CHECK (task_id <> depends_on_task_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE reviews (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    project_id INT UNSIGNED NOT NULL,
    task_id INT UNSIGNED NOT NULL,
    version INT UNSIGNED NOT NULL DEFAULT 1,
    delivery_cycle INT UNSIGNED NOT NULL,
    review_cycle INT UNSIGNED NOT NULL,
    template_version INT UNSIGNED NOT NULL,
    template_hash BINARY(32) NOT NULL,
    artifact_revision CHAR(40) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    sections JSON NOT NULL,
    checklist JSON NOT NULL,
    verdict TINYINT UNSIGNED NOT NULL,
    reviewer_id INT UNSIGNED NOT NULL,
    created_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_reviews_task_id (task_id,id),
    KEY ix_reviews_task_cycle (project_id,task_id,delivery_cycle,review_cycle,id),
    KEY ix_reviews_reviewer (reviewer_id,id),
    CONSTRAINT fk_reviews_task FOREIGN KEY (project_id,task_id) REFERENCES tasks(project_id,id),
    CONSTRAINT fk_reviews_reviewer FOREIGN KEY (reviewer_id) REFERENCES users(id),
    CONSTRAINT ck_reviews_versions CHECK (version = 1 AND delivery_cycle BETWEEN 1 AND 2147483647 AND review_cycle BETWEEN 1 AND 2147483647 AND template_version BETWEEN 1 AND 2147483647),
    CONSTRAINT ck_reviews_sections CHECK (JSON_TYPE(sections) = 'ARRAY' AND JSON_LENGTH(sections) = 8),
    CONSTRAINT ck_reviews_checklist CHECK (JSON_TYPE(checklist) = 'ARRAY' AND JSON_LENGTH(checklist) BETWEEN 10 AND 100),
    CONSTRAINT ck_reviews_verdict CHECK (verdict IN (1,2))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE release_assessments (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    project_id INT UNSIGNED NOT NULL,
    task_id INT UNSIGNED NOT NULL,
    version INT UNSIGNED NOT NULL DEFAULT 1,
    schedule_version INT UNSIGNED NOT NULL,
    delivery_cycle INT UNSIGNED NOT NULL,
    status TINYINT UNSIGNED NOT NULL DEFAULT 1,
    risks JSON NOT NULL,
    rollback_plan_version INT UNSIGNED NOT NULL,
    rollback_plan JSON NOT NULL,
    created_by INT UNSIGNED NOT NULL,
    reviewed_by INT UNSIGNED NULL,
    reviewed_at DATETIME(6) NULL,
    review_reason VARCHAR(2000) NULL,
    review_evidence JSON NOT NULL,
    created_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_assessments_task_id (task_id,id),
    UNIQUE KEY uq_assessments_plan_version (task_id,rollback_plan_version),
    KEY ix_assessments_current (project_id,task_id,delivery_cycle,schedule_version,status,id),
    KEY ix_assessments_creator (created_by),
    KEY ix_assessments_reviewer (reviewed_by),
    CONSTRAINT fk_assessments_task FOREIGN KEY (project_id,task_id) REFERENCES tasks(project_id,id),
    CONSTRAINT fk_assessments_creator FOREIGN KEY (created_by) REFERENCES users(id),
    CONSTRAINT fk_assessments_reviewer FOREIGN KEY (reviewed_by) REFERENCES users(id),
    CONSTRAINT ck_assessments_versions CHECK (version BETWEEN 1 AND 2147483647 AND schedule_version BETWEEN 1 AND 2147483647 AND delivery_cycle BETWEEN 1 AND 2147483647 AND rollback_plan_version BETWEEN 1 AND 2147483647),
    CONSTRAINT ck_assessments_status CHECK (status IN (1,2,3)),
    CONSTRAINT ck_assessments_risks CHECK (JSON_TYPE(risks) = 'ARRAY' AND JSON_LENGTH(risks) = 4),
    CONSTRAINT ck_assessments_plan CHECK (JSON_TYPE(rollback_plan) = 'OBJECT'),
    CONSTRAINT ck_assessments_review CHECK (
        JSON_TYPE(review_evidence) = 'ARRAY' AND
        ((status = 1 AND reviewed_by IS NULL AND reviewed_at IS NULL AND review_reason IS NULL AND JSON_LENGTH(review_evidence) = 0)
        OR (status IN (2,3) AND reviewed_by IS NOT NULL AND reviewed_at IS NOT NULL AND review_reason IS NOT NULL AND CHAR_LENGTH(TRIM(review_reason)) > 0 AND JSON_LENGTH(review_evidence) BETWEEN 1 AND 30))
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

ALTER TABLE tasks
    ADD CONSTRAINT fk_tasks_latest_review FOREIGN KEY (id,latest_review_id) REFERENCES reviews(task_id,id),
    ADD CONSTRAINT fk_tasks_approved_review FOREIGN KEY (id,approved_review_id) REFERENCES reviews(task_id,id),
    ADD CONSTRAINT fk_tasks_approved_assessment FOREIGN KEY (id,approved_assessment_id) REFERENCES release_assessments(task_id,id);

CREATE TABLE decisions (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    project_id INT UNSIGNED NOT NULL,
    task_id INT UNSIGNED NOT NULL,
    type TINYINT UNSIGNED NOT NULL,
    decided_by INT UNSIGNED NOT NULL,
    delivery_cycle INT UNSIGNED NOT NULL,
    reason VARCHAR(2000) NOT NULL,
    impact VARCHAR(3000) NULL,
    target_version VARCHAR(128) NULL,
    assessment_id INT UNSIGNED NULL,
    rollback_plan_version INT UNSIGNED NULL,
    evidence JSON NOT NULL,
    decided_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_decisions_cycle_type (task_id,delivery_cycle,type),
    KEY ix_decisions_project_task (project_id,task_id,id),
    KEY ix_decisions_actor (decided_by,id),
    KEY ix_decisions_assessment (task_id,assessment_id),
    CONSTRAINT fk_decisions_task FOREIGN KEY (project_id,task_id) REFERENCES tasks(project_id,id),
    CONSTRAINT fk_decisions_actor FOREIGN KEY (decided_by) REFERENCES users(id),
    CONSTRAINT fk_decisions_assessment FOREIGN KEY (task_id,assessment_id) REFERENCES release_assessments(task_id,id),
    CONSTRAINT ck_decisions_type CHECK (type IN (1,2,3)),
    CONSTRAINT ck_decisions_cycle CHECK (delivery_cycle BETWEEN 1 AND 2147483647 AND (rollback_plan_version IS NULL OR rollback_plan_version BETWEEN 1 AND 2147483647)),
    CONSTRAINT ck_decisions_reason CHECK (CHAR_LENGTH(TRIM(reason)) > 0),
    CONSTRAINT ck_decisions_evidence CHECK (JSON_TYPE(evidence) = 'ARRAY' AND JSON_LENGTH(evidence) BETWEEN 1 AND 30),
    CONSTRAINT ck_decisions_payload CHECK (
        (type = 1 AND target_version IS NOT NULL AND CHAR_LENGTH(TRIM(target_version)) > 0 AND assessment_id IS NOT NULL AND rollback_plan_version IS NOT NULL)
        OR (type = 2 AND impact IS NOT NULL AND CHAR_LENGTH(TRIM(impact)) > 0 AND target_version IS NOT NULL AND CHAR_LENGTH(TRIM(target_version)) > 0 AND assessment_id IS NOT NULL AND rollback_plan_version IS NOT NULL)
        OR (type = 3 AND impact IS NULL AND target_version IS NULL AND assessment_id IS NULL AND rollback_plan_version IS NULL)
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE schedule_changes (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    project_id INT UNSIGNED NOT NULL,
    task_id INT UNSIGNED NULL,
    iteration_id INT UNSIGNED NULL,
    from_version INT UNSIGNED NOT NULL,
    to_version INT UNSIGNED NOT NULL,
    before_plan JSON NOT NULL,
    after_plan JSON NOT NULL,
    reason VARCHAR(2000) NOT NULL,
    evidence JSON NOT NULL,
    changed_by INT UNSIGNED NOT NULL,
    changed_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_schedule_task_version (task_id,to_version),
    UNIQUE KEY uq_schedule_iteration_version (iteration_id,to_version),
    KEY ix_schedule_project (project_id,id),
    CONSTRAINT fk_schedule_task FOREIGN KEY (project_id,task_id) REFERENCES tasks(project_id,id),
    CONSTRAINT fk_schedule_iteration FOREIGN KEY (project_id,iteration_id) REFERENCES iterations(project_id,id),
    CONSTRAINT fk_schedule_actor FOREIGN KEY (changed_by) REFERENCES users(id),
    CONSTRAINT ck_schedule_target CHECK ((task_id IS NOT NULL AND iteration_id IS NULL) OR (task_id IS NULL AND iteration_id IS NOT NULL)),
    CONSTRAINT ck_schedule_versions CHECK (from_version BETWEEN 1 AND 2147483646 AND to_version = from_version + 1),
    CONSTRAINT ck_schedule_json CHECK (JSON_TYPE(before_plan) = 'OBJECT' AND JSON_TYPE(after_plan) = 'OBJECT' AND JSON_TYPE(evidence) = 'ARRAY' AND JSON_LENGTH(evidence) BETWEEN 1 AND 30),
    CONSTRAINT ck_schedule_reason CHECK (CHAR_LENGTH(TRIM(reason)) > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE audit_events (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    project_id INT UNSIGNED NULL,
    task_id INT UNSIGNED NULL,
    attempted_project_id INT UNSIGNED NULL,
    attempted_task_id INT UNSIGNED NULL,
    actor_kind TINYINT UNSIGNED NOT NULL,
    actor_id INT UNSIGNED NULL,
    request_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    operation_id VARCHAR(100) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    outcome TINYINT UNSIGNED NOT NULL,
    reason_code TINYINT UNSIGNED NULL,
    expected_version INT UNSIGNED NULL,
    observed_version INT UNSIGNED NULL,
    before_values JSON NOT NULL,
    after_values JSON NOT NULL,
    evidence JSON NOT NULL,
    created_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    KEY ix_audit_project_task (project_id,task_id,id),
    KEY ix_audit_request (request_id,id),
    KEY ix_audit_actor (actor_kind,actor_id,id),
    CONSTRAINT fk_audit_project FOREIGN KEY (project_id) REFERENCES projects(id),
    CONSTRAINT fk_audit_task FOREIGN KEY (project_id,task_id) REFERENCES tasks(project_id,id),
    CONSTRAINT ck_audit_actor CHECK (actor_kind IN (1,2,3) AND (actor_kind = 3 OR actor_id IS NOT NULL)),
    CONSTRAINT ck_audit_outcome CHECK ((outcome = 1 AND reason_code IS NULL) OR (outcome = 2 AND reason_code IS NOT NULL AND reason_code BETWEEN 1 AND 255)),
    CONSTRAINT ck_audit_arrays CHECK (JSON_TYPE(before_values) = 'ARRAY' AND JSON_TYPE(after_values) = 'ARRAY' AND JSON_TYPE(evidence) = 'ARRAY'),
    CONSTRAINT ck_audit_project_task CHECK (task_id IS NULL OR project_id IS NOT NULL)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE idempotency_requests (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    actor_kind TINYINT UNSIGNED NOT NULL,
    actor_id INT UNSIGNED NOT NULL,
    operation_id VARCHAR(100) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    idempotency_key VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    request_hash BINARY(32) NOT NULL,
    status TINYINT UNSIGNED NOT NULL,
    owner_token BINARY(16) NOT NULL,
    lease_until DATETIME(6) NOT NULL,
    response_status SMALLINT UNSIGNED NULL,
    response_body JSON NULL,
    response_request_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NULL,
    created_at DATETIME(6) NOT NULL,
    completed_at DATETIME(6) NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_idempotency_scope (actor_kind,actor_id,operation_id,idempotency_key),
    KEY ix_idempotency_recovery (status,lease_until,id),
    CONSTRAINT ck_idempotency_actor CHECK (actor_kind IN (1,2)),
    CONSTRAINT ck_idempotency_state CHECK (
        (status = 1 AND response_status IS NULL AND response_body IS NULL AND response_request_id IS NULL AND completed_at IS NULL)
        OR (status = 2 AND response_status IS NOT NULL AND response_status BETWEEN 200 AND 499 AND response_body IS NOT NULL AND response_request_id IS NOT NULL AND CHAR_LENGTH(TRIM(response_request_id)) > 0 AND completed_at IS NOT NULL)
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE outbox_events (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    event_type TINYINT UNSIGNED NOT NULL,
    schema_version TINYINT UNSIGNED NOT NULL DEFAULT 1,
    project_id INT UNSIGNED NOT NULL,
    task_id INT UNSIGNED NULL,
    payload JSON NOT NULL,
    recipients JSON NOT NULL,
    status TINYINT UNSIGNED NOT NULL DEFAULT 1,
    attempts SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    next_attempt_at DATETIME(6) NOT NULL,
    lease_token BINARY(16) NULL,
    lease_until DATETIME(6) NULL,
    confirmed_at DATETIME(6) NULL,
    fallback_at DATETIME(6) NULL,
    last_error_code VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin NULL,
    created_at DATETIME(6) NOT NULL,
    updated_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_outbox_project_task_id (project_id,task_id,id),
    KEY ix_outbox_dispatch (status,next_attempt_at,id),
    KEY ix_outbox_recovery (status,lease_until,id),
    CONSTRAINT fk_outbox_project FOREIGN KEY (project_id) REFERENCES projects(id),
    CONSTRAINT fk_outbox_task FOREIGN KEY (project_id,task_id) REFERENCES tasks(project_id,id),
    CONSTRAINT ck_outbox_type CHECK (event_type IN (1,2) AND schema_version = 1),
    CONSTRAINT ck_outbox_payload CHECK (JSON_TYPE(payload) = 'OBJECT' AND JSON_TYPE(recipients) = 'ARRAY'),
    CONSTRAINT ck_outbox_state CHECK (
        (status = 1 AND lease_token IS NULL AND lease_until IS NULL AND confirmed_at IS NULL AND fallback_at IS NULL)
        OR (status = 2 AND lease_token IS NOT NULL AND lease_until IS NOT NULL AND confirmed_at IS NULL AND fallback_at IS NULL)
        OR (status = 3 AND lease_token IS NULL AND lease_until IS NULL AND confirmed_at IS NOT NULL AND fallback_at IS NULL)
        OR (status = 4 AND lease_token IS NULL AND lease_until IS NULL AND fallback_at IS NOT NULL)
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE escalation_events (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    project_id INT UNSIGNED NOT NULL,
    task_id INT UNSIGNED NOT NULL,
    schedule_version INT UNSIGNED NOT NULL,
    level TINYINT UNSIGNED NOT NULL,
    rule_version INT UNSIGNED NOT NULL,
    rule_snapshot JSON NOT NULL,
    rule_hash BINARY(32) NOT NULL,
    scan_run_id INT UNSIGNED NOT NULL,
    planned_end DATETIME(6) NOT NULL,
    observed_at DATETIME(6) NOT NULL,
    event_id INT UNSIGNED NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_escalation_once (task_id,schedule_version,level),
    UNIQUE KEY uq_escalation_event (event_id),
    KEY ix_escalation_project_task (project_id,task_id,id),
    KEY ix_escalation_scan (scan_run_id,id),
    CONSTRAINT fk_escalation_task FOREIGN KEY (project_id,task_id) REFERENCES tasks(project_id,id),
    CONSTRAINT fk_escalation_outbox FOREIGN KEY (project_id,task_id,event_id) REFERENCES outbox_events(project_id,task_id,id),
    CONSTRAINT ck_escalation_level CHECK (level BETWEEN 1 AND 255),
    CONSTRAINT ck_escalation_versions CHECK (schedule_version BETWEEN 1 AND 2147483647 AND rule_version BETWEEN 1 AND 2147483647),
    CONSTRAINT ck_escalation_rules CHECK (JSON_TYPE(rule_snapshot) = 'OBJECT')
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE notifications (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    project_id INT UNSIGNED NOT NULL,
    task_id INT UNSIGNED NOT NULL,
    event_id INT UNSIGNED NOT NULL,
    recipient_id INT UNSIGNED NOT NULL,
    version INT UNSIGNED NOT NULL DEFAULT 1,
    level TINYINT UNSIGNED NOT NULL,
    title VARCHAR(200) NOT NULL,
    message VARCHAR(2000) NOT NULL,
    fallback TINYINT UNSIGNED NOT NULL,
    read_at DATETIME(6) NULL,
    handled_at DATETIME(6) NULL,
    handling_note VARCHAR(2000) NULL,
    handling_evidence JSON NOT NULL,
    created_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_notifications_consumer (event_id,recipient_id),
    KEY ix_notifications_recipient (recipient_id,project_id,id),
    KEY ix_notifications_unread (recipient_id,read_at,id),
    KEY ix_notifications_unhandled (recipient_id,handled_at,id),
    CONSTRAINT fk_notifications_event FOREIGN KEY (project_id,task_id,event_id) REFERENCES outbox_events(project_id,task_id,id),
    CONSTRAINT fk_notifications_recipient FOREIGN KEY (recipient_id) REFERENCES users(id),
    CONSTRAINT ck_notifications_version CHECK (version BETWEEN 1 AND 2147483647),
    CONSTRAINT ck_notifications_level CHECK (level BETWEEN 1 AND 255),
    CONSTRAINT ck_notifications_fallback CHECK (fallback IN (0,1)),
    CONSTRAINT ck_notifications_handling CHECK (
        JSON_TYPE(handling_evidence) = 'ARRAY' AND
        ((handled_at IS NULL AND handling_note IS NULL AND JSON_LENGTH(handling_evidence) = 0)
        OR (handled_at IS NOT NULL AND handling_note IS NOT NULL AND CHAR_LENGTH(TRIM(handling_note)) > 0 AND JSON_LENGTH(handling_evidence) BETWEEN 1 AND 30))
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE scan_runs (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    run_key BINARY(16) NOT NULL,
    rule_version INT UNSIGNED NOT NULL,
    rule_snapshot JSON NOT NULL,
    rule_hash BINARY(32) NOT NULL,
    cutoff_at DATETIME(6) NOT NULL,
    status TINYINT UNSIGNED NOT NULL,
    last_task_id INT UNSIGNED NOT NULL DEFAULT 0,
    scanned_count INT UNSIGNED NOT NULL DEFAULT 0,
    created_count INT UNSIGNED NOT NULL DEFAULT 0,
    duplicate_count INT UNSIGNED NOT NULL DEFAULT 0,
    started_at DATETIME(6) NOT NULL,
    heartbeat_at DATETIME(6) NOT NULL,
    finished_at DATETIME(6) NULL,
    error_code VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_scan_run_key (run_key),
    KEY ix_scan_runs_recovery (status,heartbeat_at,id),
    CONSTRAINT ck_scan_runs_version CHECK (rule_version BETWEEN 1 AND 2147483647),
    CONSTRAINT ck_scan_runs_rules CHECK (JSON_TYPE(rule_snapshot) = 'OBJECT'),
    CONSTRAINT ck_scan_runs_state CHECK ((status = 1 AND finished_at IS NULL) OR (status IN (2,3) AND finished_at IS NOT NULL))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

ALTER TABLE escalation_events
    ADD CONSTRAINT fk_escalation_scan FOREIGN KEY (scan_run_id) REFERENCES scan_runs(id);
