"""Run: PYTHONPATH=. .venv/bin/python scripts/benchmark_indexes.py

Uses only a temporary SQLite database; never touches data/app.db. Timings are
median warm-cache SELECT times, not API latency or a promise of fixed speedup.
The substring filter still scans; the indexes optimize ORDER BY + LIMIT.
"""

import argparse
import json
import statistics
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from time import perf_counter

from backend.app.indexes import ensure_query_indexes
from backend.app.models import Base, Note
from sqlalchemy import create_engine, func, insert, select, text


def benchmark(rows: int, repeats: int) -> dict:
    with tempfile.TemporaryDirectory() as directory:
        engine = create_engine(f"sqlite:///{Path(directory) / 'benchmark.db'}")
        try:
            Base.metadata.create_all(engine)
            with engine.begin() as connection:
                connection.execute(
                    insert(Note),
                    [
                        {
                            "id": i + 1,
                            "title": f"Title {(i * 37) % 10007:05d}",
                            "content": "MATCH body" if i % 3 == 0 else "other",
                            "created_at": datetime(2020, 1, 1) + timedelta(seconds=i % 1009),
                        }
                        for i in range(rows)
                    ],
                )
            queries = {}
            for name, ordering in [
                ("title_asc", (Note.title.asc(), Note.id.asc())),
                ("created_desc", (Note.created_at.desc(), Note.id.desc())),
            ]:
                for filtered in [False, True]:
                    query = select(Note)
                    if filtered:
                        query = query.where(
                            func.lower(Note.title).contains("match", autoescape=True)
                            | func.lower(Note.content).contains("match", autoescape=True)
                        )
                    queries[name + ("_filtered" if filtered else "")] = (
                        query.order_by(*ordering).limit(10).offset(100)
                    )

            def measure():
                measurements, results = {}, {}
                with engine.connect() as connection:
                    for name, query in queries.items():
                        sql = str(query.compile(engine, compile_kwargs={"literal_binds": True}))
                        plan = [
                            row[3] for row in connection.execute(text("EXPLAIN QUERY PLAN " + sql))
                        ]
                        results[name] = connection.execute(query).all()  # Warm up.
                        durations = []
                        for _ in range(repeats):
                            start = perf_counter()
                            connection.execute(query).all()
                            durations.append((perf_counter() - start) * 1000)
                        measurements[name] = {
                            "median_ms": round(statistics.median(durations), 4),
                            "plan": plan,
                        }
                return measurements, results

            before, before_results = measure()
            ensure_query_indexes(engine)
            after, after_results = measure()
            assert before_results == after_results, "Index changed query results"
            return {
                "rows": rows,
                "repeats": repeats,
                "results_identical": True,
                "before": before,
                "after": after,
            }
        finally:
            engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=50000)
    parser.add_argument("--repeats", type=int, default=20)
    args = parser.parse_args()
    if args.rows < 1 or args.repeats < 1:
        parser.error("--rows and --repeats must be positive")
    print(json.dumps(benchmark(args.rows, args.repeats), indent=2))
