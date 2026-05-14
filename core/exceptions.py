"""自定义异常类"""


class FinanceAllInOneError(Exception):
    """基础异常"""
    pass


class DataFetchError(FinanceAllInOneError):
    """数据获取失败"""
    pass


class SourceUnavailableError(FinanceAllInOneError):
    """某个数据源临时不可用"""
    pass


class SourceExhaustedError(FinanceAllInOneError):
    """所有数据源均不可用"""
    pass


class InsufficientDataError(FinanceAllInOneError):
    """返回数据条数不足"""
    pass


class InvalidSymbolError(FinanceAllInOneError):
    """代码格式错误或不存在"""
    pass


class RateLimitError(FinanceAllInOneError):
    """触发源速率限制"""
    pass
