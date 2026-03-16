"""
实用装饰器
- 重试机制（带指数退避）
- 超时控制
- 异常捕获与日志
"""

import time
import logging
from functools import wraps
from typing import Callable, Tuple, Any, Optional, Type
from signal import signal, SIGALRM, alarm
import signal as signal_module


logger = logging.getLogger(__name__)


def retry(
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    initial_delay: float = 1.0,
) -> Callable:
    """
    重试装饰器（带指数退避）
    
    Args:
        max_attempts: 最大尝试次数
        backoff_factor: 退避因子（等待时间 = initial_delay * (backoff_factor ^ 尝试次数)）
        exceptions: 要捕获的异常类型元组
        initial_delay: 初始延迟（秒）
    
    Example:
        @retry(max_attempts=3, backoff_factor=2.0, exceptions=(APIError, ConnectionError))
        def call_api():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    logger.debug(f"[{func.__name__}] 第 {attempt}/{max_attempts} 次尝试")
                    return func(*args, **kwargs)
                
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        logger.error(
                            f"[{func.__name__}] 已达最大重试次数({max_attempts})，"
                            f"最后错误: {str(e)}"
                        )
                        raise
                    
                    # 计算延迟（指数退避）
                    delay = initial_delay * (backoff_factor ** (attempt - 1))
                    logger.warning(
                        f"[{func.__name__}] 尝试 {attempt} 失败: {str(e)}, "
                        f"{delay:.1f}秒后重试..."
                    )
                    time.sleep(delay)
            
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


def timeout(seconds: int) -> Callable:
    """
    超时装饰器（仅在 Unix/Linux 系统上有效）
    
    Args:
        seconds: 超时秒数
    
    Example:
        @timeout(10)
        def long_running_task():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 仅在支持 SIGALRM 的系统上使用
            if not hasattr(signal_module, 'SIGALRM'):
                logger.warning(f"[{func.__name__}] 当前系统不支持超时控制")
                return func(*args, **kwargs)
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"函数 {func.__name__} 执行超时（{seconds}秒）")
            
            # 设置信号处理器
            old_handler = signal(SIGALRM, timeout_handler)
            alarm(seconds)
            
            try:
                result = func(*args, **kwargs)
                alarm(0)  # 取消闹钟
                return result
            
            finally:
                alarm(0)  # 确保闹钟被取消
                signal(SIGALRM, old_handler)
        
        return wrapper
    return decorator


def log_execution(
    log_level: str = "INFO",
    log_result: bool = True,
    log_args: bool = False,
) -> Callable:
    """
    执行日志装饰器
    自动记录函数执行时间和结果
    
    Args:
        log_level: 日志级别（DEBUG/INFO/WARNING/ERROR）
        log_result: 是否记录返回值
        log_args: 是否记录输入参数
    
    Example:
        @log_execution(log_level="INFO", log_result=True)
        def process_data(data: dict) -> dict:
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            log_func = getattr(logger, log_level.lower(), logger.info)
            
            # 记录开始
            msg = f"[{func.__name__}] 开始执行"
            if log_args:
                msg += f" (args: {args}, kwargs: {kwargs})"
            log_func(msg)
            
            # 执行函数并记录时间
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                
                msg = f"[{func.__name__}] 执行成功 ({elapsed:.2f}秒)"
                if log_result and result is not None:
                    msg += f" | 返回值类型: {type(result).__name__}"
                log_func(msg)
                
                return result
            
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"[{func.__name__}] 执行失败 ({elapsed:.2f}秒): {str(e)}")
                raise
        
        return wrapper
    return decorator


def safe_execute(
    default_return: Any = None,
    log_errors: bool = True,
) -> Callable:
    """
    安全执行装饰器
    捕获所有异常，返回默认值或继续
    
    Args:
        default_return: 异常时的返回值
        log_errors: 是否记录错误日志
    
    Example:
        @safe_execute(default_return=[], log_errors=True)
        def fetch_data() -> list:
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger.error(f"[{func.__name__}] 异常捕获: {str(e)}", exc_info=True)
                return default_return
        
        return wrapper
    return decorator

