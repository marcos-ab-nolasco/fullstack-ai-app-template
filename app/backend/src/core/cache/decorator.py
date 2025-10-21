from typing import Any, Callable, Optional, TypeVar, Union, TypedDict
from src.core.cache.client import get_redis_sync_client
from functools import wraps
import pickle
from redis import Redis
import copy
from src.core.config import get_settings
import hashlib
from collections import OrderedDict
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
    ):
        # TODO: Implement caching logic here; maybe returns an instance of another class with
        pass

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


