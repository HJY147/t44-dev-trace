# Projection candidate

Use the existing `services.common.model` in `EscalationFacade.event`; do not introduce
an additional mapper, mutate contract/DDL, alter queries, or remove computed fields.
The ordinary RowsGateway contract returns complete plain dictionaries. On that contract,
expand the schema projection into per-field AST expressions and compare its entire ordered
field-expression map against the original wire(dict(...)). All preceding statements stay
unchanged. This proof does not cover incomplete/malicious custom Mapping inputs or their
exception evaluation order, external monkeypatch consumers, response validation, or DB runs.
Compile syntax and count original/replacement whole facade including the new imported name.
The evidence is a temporary candidate, never a production reduction.
