"""ROLE-reviewer-PRODUCT-v1: isolated Inspector double, never an actual MySQL alteration."""
import copy
import json
from unittest.mock import patch

from t44.persistence.migrations import check_schema
from t44.persistence.schema import TABLES


class InspectorDouble:
    def __init__(self, drift):
        self.drift = drift

    def get_table_names(self):
        return list(TABLES)

    def get_columns(self, name):
        return [dict(name=c.name, type=copy.copy(c.type), nullable=c.nullable,
                     default=str(c.server_default.arg) if c.server_default is not None else None)
                for c in TABLES[name].c]

    def get_pk_constraint(self, name):
        return dict(constrained_columns=['id'])

    def get_indexes(self, name):
        return [dict(name=i.name, column_names=['id'] if self.drift else [c.name for c in i.columns],
                     unique=self.drift) for i in TABLES[name].indexes]

    def get_unique_constraints(self, name):
        return [dict(name=c.name, column_names=['id'] if self.drift else [x.name for x in c.columns])
                for c in TABLES[name].constraints if c.__class__.__name__ == 'UniqueConstraint']

    def get_foreign_keys(self, name):
        return [dict(name=c.name,
                     constrained_columns=['id'] if self.drift else [e.parent.name for e in c.elements],
                     referred_table='users' if self.drift else c.elements[0].column.table.name,
                     referred_columns=['id'] if self.drift else [e.column.name for e in c.elements])
                for c in TABLES[name].constraints if c.__class__.__name__ == 'ForeignKeyConstraint']

    def get_check_constraints(self, name):
        return [dict(name=c.name, sqltext='1 = 1' if self.drift else str(c.sqltext))
                for c in TABLES[name].constraints if c.__class__.__name__ == 'CheckConstraint']


with patch('t44.persistence.migrations.inspect', return_value=InspectorDouble(False)):
    baseline = check_schema(object())
assert baseline['passed'], baseline
with patch('t44.persistence.migrations.inspect', return_value=InspectorDouble(True)):
    drifted = check_schema(object())
print(json.dumps(dict(scope='Inspector-double only; no live MySQL schema changed',
                      baseline=baseline, semantically_changed_same_names=drifted), indent=2))
assert not drifted['passed'], 'Same names with changed index columns/uniqueness, FK targets and CHECK expressions must fail schema compatibility'
