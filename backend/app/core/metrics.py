import time
from collections import defaultdict
from typing import Dict, Tuple

from app.db.session import get_db_pool_status


class MetricsRegistry:
    """
    In-memory Prometheus-compatible metrics registry for Enermax SaaS operations.
    Thread-safe and async-safe counters and duration accumulators.
    """

    def __init__(self):
        # (method, endpoint, status_code) -> count
        self._requests: Dict[Tuple[str, str, int], int] = defaultdict(int)
        # endpoint -> (total_seconds, count)
        self._durations: Dict[str, Tuple[float, int]] = defaultdict(lambda: (0.0, 0))
        # (error_code, status_code) -> count
        self._errors: Dict[Tuple[str, int], int] = defaultdict(int)
        # endpoint -> count
        self._rate_limits: Dict[str, int] = defaultdict(int)
        self._auth_failures: int = 0

    def record_request(self, method: str, endpoint: str, status_code: int, duration_sec: float) -> None:
        key = (method.upper(), endpoint, status_code)
        self._requests[key] += 1
        curr_total, curr_count = self._durations[endpoint]
        self._durations[endpoint] = (curr_total + duration_sec, curr_count + 1)

    def record_error(self, error_code: str, status_code: int) -> None:
        self._errors[(error_code, status_code)] += 1

    def record_rate_limit_hit(self, endpoint: str) -> None:
        self._rate_limits[endpoint] += 1

    def record_auth_failure(self) -> None:
        self._auth_failures += 1

    def generate_prometheus_text(self) -> str:
        """Emits standard Prometheus text representation."""
        lines = [
            "# HELP enermax_http_requests_total Total number of HTTP requests processed",
            "# TYPE enermax_http_requests_total counter",
        ]
        for (method, endpoint, code), count in self._requests.items():
            lines.append(
                f'enermax_http_requests_total{{method="{method}",endpoint="{endpoint}",status="{code}"}} {count}'
            )

        lines.extend([
            "",
            "# HELP enermax_http_request_duration_seconds Total execution time of HTTP requests in seconds",
            "# TYPE enermax_http_request_duration_seconds summary",
        ])
        for endpoint, (total, count) in self._durations.items():
            lines.append(f'enermax_http_request_duration_seconds_sum{{endpoint="{endpoint}"}} {total:.6f}')
            lines.append(f'enermax_http_request_duration_seconds_count{{endpoint="{endpoint}"}} {count}')

        lines.extend([
            "",
            "# HELP enermax_rate_limit_hits_total Number of requests rejected due to rate limits",
            "# TYPE enermax_rate_limit_hits_total counter",
        ])
        for endpoint, count in self._rate_limits.items():
            lines.append(f'enermax_rate_limit_hits_total{{endpoint="{endpoint}"}} {count}')

        lines.extend([
            "",
            "# HELP enermax_auth_failures_total Total failed authentication attempts",
            "# TYPE enermax_auth_failures_total counter",
            f"enermax_auth_failures_total {self._auth_failures}",
        ])

        # Database pool metrics
        pool = get_db_pool_status()
        lines.extend([
            "",
            "# HELP enermax_db_pool_size Total configured database connection pool size",
            "# TYPE enermax_db_pool_size gauge",
            f"enermax_db_pool_size {pool.get('size', 0)}",
            "# HELP enermax_db_pool_checked_in Idle connections in the database pool",
            "# TYPE enermax_db_pool_checked_in gauge",
            f"enermax_db_pool_checked_in {pool.get('checked_in', 0)}",
            "# HELP enermax_db_pool_checked_out Active checked-out connections in use",
            "# TYPE enermax_db_pool_checked_out gauge",
            f"enermax_db_pool_checked_out {pool.get('checked_out', 0)}",
            "# HELP enermax_db_pool_overflow Overflow connections in use beyond pool size",
            "# TYPE enermax_db_pool_overflow gauge",
            f"enermax_db_pool_overflow {pool.get('overflow', 0)}",
        ])

        return "\n".join(lines) + "\n"

    def get_summary(self) -> dict:
        """Returns JSON-serializable dictionary summary of operational metrics."""
        pool = get_db_pool_status()
        return {
            "total_requests": sum(self._requests.values()),
            "total_errors": sum(self._errors.values()),
            "total_rate_limit_hits": sum(self._rate_limits.values()),
            "auth_failures": self._auth_failures,
            "database_pool": pool,
        }


metrics_registry = MetricsRegistry()
