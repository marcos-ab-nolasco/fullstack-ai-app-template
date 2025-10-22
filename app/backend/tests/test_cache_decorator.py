import threading
import time
from typing import Any, Callable, Generator

import pytest

from src.core.cache.client import get_redis_sync_client
from src.core.cache.decorator import RedisCache, hash_key


@pytest.fixture
def redis_client() -> Generator[Any, None, None]:
    client = get_redis_sync_client()
    client.flushall()
    yield client
    client.flushall()


@pytest.fixture
def redis_cache(redis_client: Any) -> RedisCache:
    return RedisCache(redis_client, prefix="tcache")


def collect_call_counter() -> dict[str, int]:
    return {"count": 0}


def decode_keys(redis_client: Any, pattern: str = "*") -> set[str]:
    return {key.decode() if isinstance(key, bytes) else key for key in redis_client.scan_iter(pattern)}


def test_cache_returns_cached_value(redis_cache: RedisCache, redis_client: Any) -> None:
    counter = collect_call_counter()

    @redis_cache.cache()
    def add(a: int, b: int) -> int:
        counter["count"] += 1
        return a + b

    assert add(1, 2) == 3
    assert add(1, 2) == 3
    assert counter["count"] == 1
    assert len(decode_keys(redis_client)) == 1


def test_cache_ignores_selected_positionals(redis_cache: RedisCache) -> None:
    counter = collect_call_counter()

    @redis_cache.cache(ignore_positionals=[0])
    def combine(_ignored: str, value: int) -> int:
        counter["count"] += 1
        return value * 2

    assert combine("first", 3) == 6
    assert combine("second", 3) == 6
    assert counter["count"] == 1


def test_cache_ignores_selected_keywords(redis_cache: RedisCache) -> None:
    counter = collect_call_counter()

    @redis_cache.cache(ignore_kw=["noise"])
    def operate(value: int, *, noise: int, scale: int) -> int:
        counter["count"] += 1
        return value * scale

    assert operate(5, noise=1, scale=2) == 10
    assert operate(5, noise=999, scale=2) == 10
    assert counter["count"] == 1


def test_cache_custom_key_serializer_receives_filtered_arguments(redis_cache: RedisCache) -> None:
    seen: dict[str, Any] = {}

    def serializer(args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
        seen["args"] = args
        seen["kwargs"] = kwargs
        return "static"

    @redis_cache.cache(ignore_positionals=[0], ignore_kw=["debug"], key_serializer=serializer)
    def target(_noise: str, value: int, *, debug: bool, flag: str) -> str:
        return f"{value}:{flag}"

    assert target("ignored", 7, debug=True, flag="ok") == "7:ok"
    assert seen["args"] == (7,)
    assert seen["kwargs"] == {"flag": "ok"}


def test_cache_uses_custom_namespace(redis_cache: RedisCache, redis_client: Any) -> None:

    @redis_cache.cache(namespace="custom")
    def work(value: int) -> int:
        return value + 1

    assert work(4) == 5
    key = next(iter(decode_keys(redis_client)))
    assert key.startswith("tcache:custom:")


def test_cache_defaults_namespace_to_module_and_qualname(redis_cache: RedisCache, redis_client: Any) -> None:

    @redis_cache.cache()
    def sample(value: int) -> int:
        return value - 1

    assert sample(10) == 9
    key = next(iter(decode_keys(redis_client)))
    expected_namespace = f"{sample.__module__}.{sample.__qualname__}"
    assert key.startswith(f"tcache:{expected_namespace}:")


def test_cache_uses_validation_function(redis_cache: RedisCache) -> None:
    counter = collect_call_counter()
    validation_calls: list[tuple[tuple[Any, ...], dict[str, Any], Any]] = []

    def validation(args: tuple[Any, ...], kwargs: dict[str, Any], response: dict[str, Any]) -> bool:
        validation_calls.append((args, kwargs, response["value"]))
        return True

    @redis_cache.cache(validation_func=validation)
    def compute(value: int) -> int:
        counter["count"] += 1
        return value * value

    assert compute(3) == 9
    assert compute(3) == 9
    assert counter["count"] == 1
    assert len(validation_calls) == 1


def test_cache_recomputes_when_validation_returns_false(redis_cache: RedisCache) -> None:
    counter = collect_call_counter()

    def validation(*_: Any) -> bool:
        return False

    @redis_cache.cache(validation_func=validation)
    def produce() -> int:
        counter["count"] += 1
        return counter["count"]

    assert produce() == 1
    assert produce() == 2
    assert counter["count"] == 2


def test_cache_validation_errors_respected_when_not_ignored(redis_cache: RedisCache) -> None:

    def validation(*_: Any) -> bool:
        raise RuntimeError("invalid")

    @redis_cache.cache(validation_func=validation, ignore_validation_error=False)
    def creator() -> int:
        return 1

    assert creator() == 1
    with pytest.raises(RuntimeError):
        creator()


def test_cache_validation_errors_suppressed_by_default(redis_cache: RedisCache) -> None:
    counter = collect_call_counter()

    def validation(*_: Any) -> bool:
        raise RuntimeError("validation failed")

    @redis_cache.cache(validation_func=validation)
    def generator() -> int:
        counter["count"] += 1
        return counter["count"]

    assert generator() == 1
    assert generator() == 2
    assert counter["count"] == 2


def test_cache_respects_positive_ttl(redis_cache: RedisCache, redis_client: Any) -> None:
    counter = collect_call_counter()

    @redis_cache.cache(ttl=1.0)
    def target() -> int:
        counter["count"] += 1
        return counter["count"]

    assert target() == 1
    key = target.cache_key_for()
    ttl_value = redis_client.ttl(key)
    assert ttl_value is not None and ttl_value > 0
    assert target() == 1
    time.sleep(1.2)
    assert target() == 2


def test_cache_skips_storage_when_ttl_non_positive(redis_cache: RedisCache, redis_client: Any) -> None:
    counter = collect_call_counter()

    @redis_cache.cache(ttl=0)
    def target() -> int:
        counter["count"] += 1
        return counter["count"]

    assert target() == 1
    assert target() == 2
    assert counter["count"] == 2
    assert not decode_keys(redis_client)


def test_cache_accepts_custom_serializer(redis_cache: RedisCache) -> None:
    dumps_calls = {"count": 0}
    loads_calls = {"count": 0}

    def dumps(value: Any) -> bytes:
        dumps_calls["count"] += 1
        import json

        return json.dumps(value).encode()

    def loads(blob: bytes) -> Any:
        loads_calls["count"] += 1
        import json

        return json.loads(blob.decode())

    @redis_cache.cache(serializer=dumps, deserializer=loads)
    def echo(value: int) -> int:
        return value

    assert echo(8) == 8
    assert echo(8) == 8
    assert dumps_calls["count"] == 1
    assert loads_calls["count"] == 1


def test_cache_recomputes_when_serializer_returns_non_bytes(redis_cache: RedisCache) -> None:
    counter = collect_call_counter()

    def bad_serializer(_: Any) -> str:
        return "not-bytes"

    @redis_cache.cache(serializer=bad_serializer)
    def value() -> int:
        counter["count"] += 1
        return counter["count"]

    assert value() == 1
    assert value() == 2
    assert counter["count"] == 2


def test_cache_helper_methods_expose_cache_controls(redis_cache: RedisCache, redis_client: Any) -> None:

    @redis_cache.cache()
    def work(value: int) -> int:
        return value * 3

    result = work(5)
    assert result == 15

    assert work.is_cached(5)
    assert work.has_valid_value(5)
    timestamp = work.get_cached_timestamp(5)
    assert isinstance(timestamp, float)

    assert work.invalidate(5) == 1
    assert not work.is_cached(5)
    assert work.invalidate_all() == 0

    assert work.cache_instance is redis_cache
    key = work.cache_key_for(5)
    expected_hash = hash_key((5,), {})
    expected_namespace = f"{work.__module__}.{work.__qualname__}"
    assert key == f"tcache:{expected_namespace}:{expected_hash}"
    assert work.cache_namespace == expected_namespace


def test_cache_invalidate_all_removes_each_entry(redis_cache: RedisCache, redis_client: Any) -> None:

    @redis_cache.cache(namespace="batch")
    def fn(value: int) -> int:
        return value * 10

    assert fn(1) == 10
    assert fn(2) == 20
    assert len(decode_keys(redis_client)) == 2
    assert fn.invalidate_all() == 2
    assert not decode_keys(redis_client)


def test_cache_concurrent_calls_share_computation(redis_cache: RedisCache) -> None:
    counter = collect_call_counter()
    started = threading.Event()
    release = threading.Event()
    results: list[int] = []
    errors: list[Exception] = []

    @redis_cache.cache(concurrent_max_wait_time=1.0, concurrent_check_interval=0.01)
    def slow(value: int) -> int:
        counter["count"] += 1
        started.set()
        release.wait(timeout=1)
        return value * 4

    def worker() -> None:
        try:
            results.append(slow(5))
        except Exception as exc:  # pragma: no cover - defensive branch
            errors.append(exc)

    first = threading.Thread(target=worker)
    second = threading.Thread(target=worker)
    first.start()
    started.wait(timeout=0.2)
    second.start()
    time.sleep(0.05)
    release.set()
    first.join()
    second.join()

    assert not errors
    assert counter["count"] == 1
    assert len(results) == 2
    assert all(value == 20 for value in results)


def test_cache_key_for_matches_storage(redis_cache: RedisCache, redis_client: Any) -> None:

    @redis_cache.cache(namespace="keys")
    def fn(value: int, *, flag: str) -> str:
        return f"{value}:{flag}"

    assert fn(3, flag="on") == "3:on"
    key = fn.cache_key_for(3, flag="on")
    stored_keys = decode_keys(redis_client)
    assert key in stored_keys
