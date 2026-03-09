"""
MiniQMT 连接管理模块
负责与 MiniQMT 终端的连接建立、维护和断开
"""
import time
import threading
from typing import Optional, Callable, List, Dict, Any
from datetime import datetime

from xtquant import xtdata
from xtquant.xttrader import XtQuantTrader, XtQuantTraderCallback
from xtquant.xttype import StockAccount

from app.utils.logging import log
from app.config import get_settings

settings = get_settings()


class MiniQMTConnectionManager:
    """
    MiniQMT 连接管理器
    单例模式，确保全局只有一个连接实例
    """
    _instance: Optional['MiniQMTConnectionManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'MiniQMTConnectionManager':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._connected = False
        self._trader: Optional[XtQuantTrader] = None
        self._account: Optional[StockAccount] = None
        self._callback: Optional[MiniQMTCallback] = None
        self._path: str = settings.minqmt_path or ""
        self._session_id: int = settings.minqmt_session_id or 0
        self._account_id: str = settings.minqmt_account_id or ""
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._stop_heartbeat = threading.Event()
        
    @property
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self._connected and self._trader is not None
    
    def connect(self, path: Optional[str] = None, 
                session_id: Optional[int] = None,
                account_id: Optional[str] = None) -> bool:
        """
        建立与 MiniQMT 的连接
        
        Args:
            path: MiniQMT 安装路径，如 "C:/国金证券QMT交易端/userdata_mini"
            session_id: 会话ID，用于区分不同的连接
            account_id: 资金账号
            
        Returns:
            bool: 连接是否成功
        """
        if self.is_connected:
            log.info("MiniQMT 已连接，无需重复连接")
            return True
        
        try:
            # 使用配置或传入的参数
            self._path = path or self._path
            self._session_id = session_id or self._session_id
            self._account_id = account_id or self._account_id
            
            if not self._path:
                log.error("MiniQMT 路径未配置")
                return False
            
            log.info(f"正在连接 MiniQMT: path={self._path}, session_id={self._session_id}")
            
            # 创建回调对象
            self._callback = MiniQMTCallback()
            
            # 创建交易对象
            self._trader = XtQuantTrader(self._path, self._session_id)
            self._trader.register_callback(self._callback)
            
            # 启动交易线程
            result = self._trader.start()
            if result != 0:
                log.error(f"MiniQMT 启动失败，错误码: {result}")
                return False
            
            # 创建资金账号对象
            if self._account_id:
                self._account = StockAccount(self._account_id)
                # 订阅账号
                self._trader.subscribe(self._account)
            
            self._connected = True
            log.info("MiniQMT 连接成功")
            
            # 启动心跳线程
            self._start_heartbeat()
            
            return True
            
        except Exception as e:
            log.error(f"MiniQMT 连接失败: {e}")
            self._cleanup()
            return False
    
    def disconnect(self) -> bool:
        """
        断开与 MiniQMT 的连接
        
        Returns:
            bool: 断开是否成功
        """
        try:
            # 停止心跳线程
            self._stop_heartbeat.set()
            if self._heartbeat_thread and self._heartbeat_thread.is_alive():
                self._heartbeat_thread.join(timeout=5)
            
            if self._trader:
                self._trader.stop()
                log.info("MiniQMT 已断开连接")
            
            self._cleanup()
            return True
            
        except Exception as e:
            log.error(f"MiniQMT 断开连接失败: {e}")
            return False
    
    def _cleanup(self):
        """清理资源"""
        self._connected = False
        self._trader = None
        self._account = None
        self._callback = None
        self._stop_heartbeat.clear()
    
    def _start_heartbeat(self):
        """启动心跳线程，保持连接活跃"""
        def heartbeat_loop():
            while not self._stop_heartbeat.wait(timeout=30):  # 每30秒执行一次
                try:
                    if self.is_connected and self._account:
                        # 查询资产作为心跳
                        self._trader.query_stock_asset(self._account)
                except Exception as e:
                    log.warning(f"MiniQMT 心跳异常: {e}")
        
        self._heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()
    
    def get_trader(self) -> Optional[XtQuantTrader]:
        """获取交易对象"""
        return self._trader if self.is_connected else None
    
    def get_account(self) -> Optional[StockAccount]:
        """获取资金账号对象"""
        return self._account if self.is_connected else None
    
    def reconnect(self) -> bool:
        """重新连接"""
        self.disconnect()
        time.sleep(1)
        return self.connect()


class MiniQMTCallback(XtQuantTraderCallback):
    """
    MiniQMT 回调处理类
    处理来自 MiniQMT 的各种异步消息
    """
    
    def on_disconnected(self):
        """连接断开回调"""
        log.warning("MiniQMT 连接已断开")
        manager = MiniQMTConnectionManager()
        manager._connected = False
    
    def on_stock_order(self, order):
        """委托回报回调"""
        log.debug(f"委托回报: {order}")
    
    def on_stock_trade(self, trade):
        """成交回报回调"""
        log.debug(f"成交回报: {trade}")
    
    def on_order_error(self, order_error):
        """委托失败回调"""
        log.error(f"委托失败: {order_error}")
    
    def on_cancel_error(self, cancel_error):
        """撤单失败回调"""
        log.error(f"撤单失败: {cancel_error}")
    
    def on_order_stock_async_response(self, response):
        """异步下单回调"""
        log.debug(f"异步下单响应: {response}")


class MiniQMTDataProvider:
    """
    MiniQMT 数据提供器
    封装 xtdata 接口，提供统一的数据获取方法
    """
    
    def __init__(self):
        self._connected = False
    
    def connect(self) -> bool:
        """
        连接行情服务
        """
        try:
            # xtdata 不需要显式连接，但我们可以检查是否能获取数据
            log.info("MiniQMT 行情服务初始化")
            self._connected = True
            return True
        except Exception as e:
            log.error(f"MiniQMT 行情服务初始化失败: {e}")
            return False
    
    def get_full_tick(self, stock_codes: List[str]) -> Dict[str, Any]:
        """
        获取全推行情数据
        
        Args:
            stock_codes: 股票代码列表，如 ['000001.SZ', '600000.SH']
            
        Returns:
            行情数据字典
        """
        try:
            return xtdata.get_full_tick(stock_codes)
        except Exception as e:
            log.error(f"获取全推行情失败: {e}")
            return {}
    
    def get_market_data(self, field_list: List[str], 
                       stock_list: List[str],
                       period: str = '1d',
                       start_time: str = '',
                       end_time: str = '',
                       count: int = -1) -> Dict[str, Any]:
        """
        获取历史行情数据
        
        Args:
            field_list: 字段列表，如 ['open', 'close', 'high', 'low', 'volume']
            stock_list: 股票代码列表
            period: 周期，如 '1d'(日线), '1m'(1分钟)
            start_time: 开始时间，格式 'YYYYMMDD' 或 'YYYYMMDDHHMMSS'
            end_time: 结束时间
            count: 获取条数，-1表示获取全部
            
        Returns:
            行情数据字典
        """
        try:
            return xtdata.get_market_data(
                field_list=field_list,
                stock_list=stock_list,
                period=period,
                start_time=start_time,
                end_time=end_time,
                count=count
            )
        except Exception as e:
            log.error(f"获取历史行情失败: {e}")
            return {}
    
    def get_local_data(self, field_list: List[str],
                      stock_list: List[str],
                      period: str = '1d',
                      start_time: str = '',
                      end_time: str = '',
                      count: int = -1) -> Dict[str, Any]:
        """
        获取本地历史数据（不请求服务器）
        """
        try:
            return xtdata.get_local_data(
                field_list=field_list,
                stock_list=stock_list,
                period=period,
                start_time=start_time,
                end_time=end_time,
                count=count
            )
        except Exception as e:
            log.error(f"获取本地数据失败: {e}")
            return {}
    
    def download_history_data(self, stock_code: str, 
                             period: str = '1d',
                             start_time: str = '',
                             end_time: str = '') -> bool:
        """
        下载历史数据到本地
        
        Args:
            stock_code: 股票代码
            period: 周期
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            bool: 是否成功
        """
        try:
            xtdata.download_history_data(
                stock_code=stock_code,
                period=period,
                start_time=start_time,
                end_time=end_time
            )
            return True
        except Exception as e:
            log.error(f"下载历史数据失败 {stock_code}: {e}")
            return False
    
    def get_stock_list(self, market: str = 'sh_sz') -> List[str]:
        """
        获取股票列表
        
        Args:
            market: 市场，'sh'(上海), 'sz'(深圳), 'sh_sz'(沪深)
            
        Returns:
            股票代码列表
        """
        try:
            return xtdata.get_stock_list_in_sector(market)
        except Exception as e:
            log.error(f"获取股票列表失败: {e}")
            return []
    
    def get_sector_list(self) -> List[str]:
        """
        获取板块列表
        
        Returns:
            板块名称列表
        """
        try:
            return xtdata.get_sector_list()
        except Exception as e:
            log.error(f"获取板块列表失败: {e}")
            return []
    
    def get_stock_list_in_sector(self, sector: str) -> List[str]:
        """
        获取板块成分股
        
        Args:
            sector: 板块名称，如 '沪深A股', '上证50'
            
        Returns:
            股票代码列表
        """
        try:
            return xtdata.get_stock_list_in_sector(sector)
        except Exception as e:
            log.error(f"获取板块成分股失败 {sector}: {e}")
            return []


# 全局实例
_connection_manager: Optional[MiniQMTConnectionManager] = None
_data_provider: Optional[MiniQMTDataProvider] = None


def get_connection_manager() -> MiniQMTConnectionManager:
    """获取连接管理器实例"""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = MiniQMTConnectionManager()
    return _connection_manager


def get_data_provider() -> MiniQMTDataProvider:
    """获取数据提供器实例"""
    global _data_provider
    if _data_provider is None:
        _data_provider = MiniQMTDataProvider()
    return _data_provider


def init_minqmt() -> bool:
    """
    初始化 MiniQMT 连接
    在应用启动时调用
    
    Returns:
        bool: 初始化是否成功
    """
    try:
        # 初始化行情服务
        data_provider = get_data_provider()
        if not data_provider.connect():
            log.warning("MiniQMT 行情服务初始化失败")
            return False
        
        # 初始化交易连接（如果配置了路径）
        manager = get_connection_manager()
        if settings.minqmt_path:
            if manager.connect():
                log.info("MiniQMT 交易连接成功")
            else:
                log.warning("MiniQMT 交易连接失败，仅使用行情服务")
        else:
            log.info("MiniQMT 路径未配置，仅使用行情服务")
        
        return True
        
    except Exception as e:
        log.error(f"MiniQMT 初始化失败: {e}")
        return False


def close_minqmt():
    """
    关闭 MiniQMT 连接
    在应用关闭时调用
    """
    global _connection_manager
    if _connection_manager:
        _connection_manager.disconnect()
        _connection_manager = None
    log.info("MiniQMT 已关闭")
