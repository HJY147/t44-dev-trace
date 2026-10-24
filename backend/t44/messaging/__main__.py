"""Run with DATABASE_URL, matching T44_DATABASE and AMQP_URL; no API-worker startup."""

import argparse
import logging
import os
import signal
from threading import Event

from t44.persistence import SqlAlchemyUnitOfWorkFactory, create_mysql_engine
from t44.persistence.delivery import OutboxStore
from t44.settings import Settings

from .broker import BrokerSettings, PikaBroker
from .worker import DeliveryWorker


def main():
    parser = argparse.ArgumentParser(description="T44 durable notification publisher/consumer")
    parser.add_argument("--once", action="store_true", help="process one bounded delivery cycle")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    logging.getLogger("pika").setLevel(logging.CRITICAL)
    engine = None
    try:
        if not os.environ.get("DATABASE_URL") or not os.environ.get("T44_DATABASE"):
            raise ValueError("Explicit project database configuration required")
        settings = BrokerSettings(os.environ.get("AMQP_URL", ""))
        engine = create_mysql_engine(Settings.from_env().mysql_settings())
        publisher, consumer = PikaBroker(settings, publisher=True), PikaBroker(settings)
        worker = DeliveryWorker(
            OutboxStore(SqlAlchemyUnitOfWorkFactory(engine)), publisher, consumer
        )
        stop = Event()
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, lambda _signum, _frame: stop.set())
        if args.once:
            try:
                counts = worker.cycle()
                logging.info("delivery_cycle %s", counts)
                return 2 if counts["errors"] else 0
            finally:
                publisher.close()
                consumer.close()
        worker.run(stop)
        return 0
    except Exception:
        logging.error(
            "Messaging process failed; check configuration/database (credentials omitted)"
        )
        return 1
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
