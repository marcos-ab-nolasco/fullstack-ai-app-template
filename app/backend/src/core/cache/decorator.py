from typing import Any, Callable, Optional, TypeVar, Union, TypedDict, cast
from src.core.cache.client import get_redis_sync_client
from functools import wraps
import pickle
from redis import Redis
import copy
from src.core.config import get_settings
import hashlib
from collections import OrderedDict
import time
import math
settings = get_settings()

class CacheResponse(TypedDict):
    timestamp: Union[float, int]
    value: Any
    parameters: Any

_DEFAULT_CONCURRENT_CHECK_INTERVAL: float = 0.05
KeySerializer = Callable[[tuple[Any, ...], dict[str, Any]], str]
ValidationFunction = Callable[[tuple[Any, ...], dict[str, Any], CacheResponse], bool]
    


FuncType = TypeVar("FuncType", bound=Callable[..., Any])

def _gen_key(obj: Any) -> str:
    return f"{type(obj)}_{obj}"

def _sorted_by_keys(dict_: dict[Any, Any]) -> dict[Any, Any]:
    sorted_keys = sorted(dict_.keys(), key=_gen_key)
    return {key: dict_[key] for key in sorted_keys}

def _sort_dicts(
    obj: Any,
) -> None:
    if isinstance(obj, (list, tuple)):
        for item in obj:
            _sort_dicts(item)

    if isinstance(obj, dict):
        for value in obj.values():
            _sort_dicts(value)

    if isinstance(obj, dict) and not isinstance(obj, OrderedDict):
        tmp = _sorted_by_keys(obj)
        obj.clear()
        obj.update(tmp)

def sorted_dicts_args(args: tuple[Any, ...]) -> tuple[Any, ...]:
    args_copy = copy.deepcopy(args)
    for arg in args_copy:
        _sort_dicts(arg)
    return args_copy

def sorted_dicts(dict_: dict[str, Any]) -> dict[str, Any]:
    sorted_dict = _sorted_by_keys(copy.deepcopy(dict_))
    for value in sorted_dict.values():
        _sort_dicts(value)
    return sorted_dict

def hash_key(
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> str:
    sorted_args = sorted_dicts_args(args)
    sorted_kwargs = sorted_dicts(kwargs)

    s = f"{sorted_args}, {sorted_kwargs}"
    return hashlib.sha256(s.encode()).hexdigest()



class RedisCache:
    def __init__(
        self,
        redis_client: "Redis[Any]",
        *,
        prefix: str = "rc",
    ) -> None:
        self.client = redis_client
        self.prefix = prefix

    def cache(
        self,
        *,
        ignore_positionals: Optional[list[int]] = None,
        ignore_kw: Optional[list[str]] = None,
        validation_func: Optional[ValidationFunction] = None,
        ttl: Optional[float] = None,
        serializer: Callable[[Any], bytes] = pickle.dumps,
        deserializer: Callable[[bytes], Any] = pickle.loads,
        key_serializer: KeySerializer = hash_key,
        namespace: Optional[str] = None,
        ignore_validation_error: bool = True,
        concurrent_max_wait_time: float = 0,
        concurrent_check_interval: float = _DEFAULT_CONCURRENT_CHECK_INTERVAL,
    ) -> Callable[[FuncType], FuncType]:
        ignore_positionals_set = set(ignore_positionals or [])
        ignore_kw_set = set(ignore_kw or [])
        effective_check_interval = (
            concurrent_check_interval if concurrent_check_interval > 0 else _DEFAULT_CONCURRENT_CHECK_INTERVAL
        )

        def decorator(func: FuncType) -> FuncType:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                key_args = tuple(
                    value for index, value in enumerate(args) if index not in ignore_positionals_set
                )
                key_kwargs = {key: value for key, value in kwargs.items() if key not in ignore_kw_set}

                key_components = [self.prefix]
                if namespace:
                    key_components.append(namespace)
                key_components.append(key_serializer(key_args, key_kwargs))
                cache_key = ":".join(component for component in key_components if component)
                lock_key = f"{cache_key}:lock"

                def _load_cached_response() -> Optional[CacheResponse]:
                    try:
                        raw_value = self.client.get(cache_key)
                    except Exception:
                        return None

                    if raw_value is None:
                        return None

                    try:
                        cached_value = deserializer(raw_value)
                    except Exception:
                        if ignore_validation_error:
                            return None
                        raise

                    if not isinstance(cached_value, dict):
                        return None

                    if "value" not in cached_value:
                        return None

                    return cast(CacheResponse, cached_value)

                def _resolve_cached_value() -> Optional[Any]:
                    cached_response = _load_cached_response()
                    if cached_response is None:
                        return None

                    try:
                        if validation_func is None or validation_func(args, kwargs, cached_response):
                            return cached_response["value"]
                    except Exception:
                        if not ignore_validation_error:
                            raise
                        return None

                    return None

                cached_result = _resolve_cached_value()
                if cached_result is not None:
                    return cached_result

                have_lock = False

                if concurrent_max_wait_time > 0:
                    deadline = time.monotonic() + concurrent_max_wait_time
                    lock_ttl = max(int(math.ceil(concurrent_max_wait_time)), 1)

                    while time.monotonic() < deadline:
                        cached_result = _resolve_cached_value()
                        if cached_result is not None:
                            return cached_result

                        try:
                            acquired = self.client.set(lock_key, b"1", nx=True, ex=lock_ttl)
                        except Exception:
                            acquired = False

                        if acquired:
                            have_lock = True
                            break

                        time.sleep(effective_check_interval)

                    if not have_lock:
                        cached_result = _resolve_cached_value()
                        if cached_result is not None:
                            return cached_result

                try:
                    result = func(*args, **kwargs)
                except Exception:
                    if have_lock:
                        try:
                            self.client.delete(lock_key)
                        except Exception:
                            pass
                    raise

                ttl_kwargs: dict[str, Any] = {}
                if ttl is not None:
                    ttl_seconds = float(ttl)
                    if ttl_seconds <= 0:
                        if have_lock:
                            try:
                                self.client.delete(lock_key)
                            except Exception:
                                pass
                        return result

                    if ttl_seconds.is_integer():
                        ttl_kwargs["ex"] = int(ttl_seconds)
                    else:
                        ttl_kwargs["px"] = max(int(ttl_seconds * 1000), 1)

                cache_payload: CacheResponse = {
                    "timestamp": time.time(),
                    "value": result,
                    "parameters": {"args": key_args, "kwargs": key_kwargs},
                }

                try:
                    serialized = serializer(cache_payload)
                    if isinstance(serialized, bytearray):
                        serialized = bytes(serialized)
                    if not isinstance(serialized, (bytes, bytearray)):
                        raise TypeError("Serializer must return bytes-like object.")

                    self.client.set(cache_key, serialized, **ttl_kwargs)
                except Exception:
                    if not ignore_validation_error:
                        raise
                finally:
                    if have_lock:
                        try:
                            self.client.delete(lock_key)
                        except Exception:
                            pass

                return result

            return cast(FuncType, wrapper)

        return decorator

def get_local_redis_cache() -> RedisCache:
    return RedisCache(get_redis_sync_client(), prefix=settings.CACHE_PREFIX)


def redis_cache_decorator(
    ignore_positionals: Optional[list[int]] = None,
    ignore_kw: Optional[list[str]] = None,
    validation_func: Optional[ValidationFunction] = None,
    ttl: Optional[float] = None,
    serializer: Callable[[Any], bytes] = pickle.dumps,
    deserializer: Callable[[bytes], Any] = pickle.loads,
    key_serializer: KeySerializer = hash_key,
    namespace: Optional[str] = None,
    ignore_validation_error: bool = True,
    concurrent_max_wait_time: float = 0,
    concurrent_check_interval: float = _DEFAULT_CONCURRENT_CHECK_INTERVAL,
) -> Callable[[FuncType], FuncType]:
    """
    Usage example:
        ```
        ...
        
        @classmethod
        @redis_cache_decorator(
            # key_serializer=helpers.consume_key_serializer, #  situacional
            ttl=settings.CACHE_TTL_RATE_LIMITS,
            namespace=settings.CACHE_NAMESPACE_RATE_LIMITS,
            validation_func=validation_limits,
            serializer=custom_serializer,
            ignore_positionals=[0],
            ignore_kw=["cls"],
        )
        def read_rate_limit(cls, request_data: ConsumeParameters) -> schemas.GetRateLimitsResponse:
        ...
    """
    def decorator(func: FuncType) -> FuncType:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            cache = get_local_redis_cache()
            cached_func = cache.cache(
                ignore_positionals=ignore_positionals,
                ignore_kw=ignore_kw,
                validation_func=validation_func,
                ttl=ttl,
                serializer=serializer,
                deserializer=deserializer,
                key_serializer=key_serializer,
                namespace=namespace,
                ignore_validation_error=ignore_validation_error,
                concurrent_max_wait_time=concurrent_max_wait_time,
                concurrent_check_interval=concurrent_check_interval,
            )(func)
            return cached_func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator
