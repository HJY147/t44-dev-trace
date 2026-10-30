"""Real local SQLAlchemy/SQLite DBAPI lifecycle probe; no server or secrets.

The product UoW is unchanged. Pool reset is varied only in isolated local engines,
not in production settings. Counts show network command opportunities, not cloud
latency savings or durable MySQL behavior.
"""
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
from t44.persistence.uow import SqlAlchemyUnitOfWorkFactory


def probe(reset):
    counts = Counter()

    class Tracked(sqlite3.Connection):
        def commit(self):
            counts['dbapi_commit'] += 1
            return super().commit()

        def rollback(self):
            counts['dbapi_rollback'] += 1
            return super().rollback()

    engine = create_engine('sqlite://', creator=lambda: sqlite3.connect(':memory:', factory=Tracked),
                           poolclass=QueuePool, pool_size=1, max_overflow=0,
                           pool_reset_on_return=reset)
    with engine.begin() as conn:
        conn.exec_driver_sql('CREATE TABLE probe (id INTEGER PRIMARY KEY)')
    factory = SqlAlchemyUnitOfWorkFactory(engine)
    cases = {}
    for name in ['successful_read', 'successful_write', 'failed_uow', 'unclosed_connection_transaction', 'unclosed_session_transaction']:
        counts.clear()
        if name in ['successful_read', 'successful_write']:
            with factory() as uow:
                session = uow._require_active()
                session.execute(text('SELECT 1') if name.endswith('read') else text('INSERT INTO probe VALUES (1)'))
        elif name == 'failed_uow':
            try:
                with factory() as uow:
                    uow._require_active().execute(text('INSERT INTO probe VALUES (2)'))
                    raise RuntimeError('synthetic failure')
            except RuntimeError:
                pass
        elif name == 'unclosed_connection_transaction':
            conn = engine.connect()
            conn.exec_driver_sql('INSERT INTO probe VALUES (3)')
            conn.close()
        else:
            session = factory._sessions()
            session.execute(text('INSERT INTO probe VALUES (4)'))
            session.close()
        observed = dict(counts)
        with engine.connect() as conn:
            durable_ids = list(conn.exec_driver_sql('SELECT id FROM probe ORDER BY id').scalars())
        cases[name] = dict(dbapi_calls=observed, durable_ids=durable_ids)
    engine.dispose()
    return cases


if __name__ == '__main__':
    result = dict(scope='local_sqlalchemy_sqlite_lifecycle_only_no_cloud_latency_claim',
                  source='90b734f65ce6ee9f5c217e885bc7ea4857e32b48',
                  sqlalchemy_version=sqlalchemy.__version__, variants={
                      'rollback': probe('rollback'), 'none': probe(None)})
    for variant in result['variants'].values():
        assert variant['successful_write']['durable_ids'] == [1]
        for name in ['failed_uow', 'unclosed_connection_transaction', 'unclosed_session_transaction']:
            assert variant[name]['durable_ids'] == [1]
    Path(sys.argv[1]).write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
