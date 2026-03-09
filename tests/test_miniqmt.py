"""
MiniQMT 连接测试脚本
直接运行: python tests/test_miniqmt.py
"""
import sys
from datetime import datetime, timedelta

sys.path.insert(0, r'e:\zhouxiaozhu\ai-deep-stock')

from app.stock.miniqmt import (
    get_connection_manager,
    get_data_provider,
    init_minqmt,
    close_minqmt
)
from app.config import get_settings


def test_market_data():
    """测试行情数据获取"""
    print("\n【行情数据测试】")
    provider = get_data_provider()
    
    # 初始化
    if not provider.connect():
        print("  ✗ 初始化失败")
        return False
    print("  ✓ 初始化成功")
    
    # 获取板块列表
    sectors = provider.get_sector_list()
    print(f"  ✓ 板块数量: {len(sectors)}")
    
    # 获取实时行情
    tick = provider.get_full_tick(['000001.SZ', '600000.SH'])
    print(f"  ✓ 实时行情: {len(tick)} 只股票")
    for code, data in list(tick.items())[:1]:
        print(f"    {code}: {data.get('lastPrice', 'N/A')}")
    
    return True


def test_trading_connection():
    """测试交易连接"""
    print("\n【交易连接测试】")
    settings = get_settings()
    
    if not settings.minqmt_path:
        print("  ! 未配置路径，跳过")
        return None
    
    manager = get_connection_manager()
    
    if not manager.connect():
        print("  ✗ 连接失败（MiniQMT 可能未启动）")
        return False
    
    print("  ✓ 连接成功")
    
    if manager.get_account():
        print(f"  ✓ 资金账号: {manager.get_account().account_id}")
    
    manager.disconnect()
    print("  ✓ 已断开")
    return True


def main():
    """主测试函数"""
    print("=" * 50)
    print("MiniQMT 连接测试")
    print("=" * 50)
    
    settings = get_settings()
    print(f"\n配置: path={settings.minqmt_path or '未配置'}, enabled={settings.minqmt_enabled}")
    
    # 运行测试
    test_market_data()
    test_trading_connection()
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)


if __name__ == "__main__":
    main()
