# 历史交易记录管理模块
import datetime
import csv
import os
from typing import List, Dict, Any, Optional
from .execution_engine import execution_engine

# 模拟历史交易数据
simulated_trades = [
    {
        'id': 1,
        'orderId': 1,
        'symbol': '600519',
        'name': '贵州茅台',
        'type': 'buy',
        'quantity': 50,
        'price': 1720.00,
        'amount': 86000.00,
        'fee': 25.80,
        'timestamp': datetime.datetime.now().timestamp() - 3600,
        'accountId': 'A001',
        'assetType': 'stock',
        'status': 'completed'
    },
    {
        'id': 2,
        'orderId': 2,
        'symbol': '000001',
        'name': '平安银行',
        'type': 'sell',
        'quantity': 300,
        'price': 11.85,
        'amount': 3555.00,
        'fee': 1.07,
        'timestamp': datetime.datetime.now().timestamp() - 7200,
        'accountId': 'A001',
        'assetType': 'stock',
        'status': 'completed'
    },
    {
        'id': 3,
        'orderId': 0,
        'symbol': '600036',
        'name': '招商银行',
        'type': 'buy',
        'quantity': 500,
        'price': 35.20,
        'amount': 17600.00,
        'fee': 5.28,
        'timestamp': datetime.datetime.now().timestamp() - 86400 * 5,
        'accountId': 'A001',
        'assetType': 'stock',
        'status': 'completed'
    },
    {
        'id': 4,
        'orderId': 0,
        'symbol': '000001',
        'name': '平安银行',
        'type': 'buy',
        'quantity': 1000,
        'price': 12.50,
        'amount': 12500.00,
        'fee': 3.75,
        'timestamp': datetime.datetime.now().timestamp() - 86400 * 10,
        'accountId': 'A001',
        'assetType': 'stock',
        'status': 'completed'
    }
]

# 交易ID计数器
next_trade_id = 5

class TradeHistoryManager:
    """历史交易记录管理类，负责记录和查询交易历史"""
    
    def __init__(self):
        self.trades = simulated_trades.copy()
    
    def record_trade(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """记录一笔交易
        
        Args:
            order: 订单信息
        
        Returns:
            交易记录
        """
        global next_trade_id
        
        # 计算交易金额和费用
        amount = order['filledQuantity'] * order['price']
        fee = execution_engine.calculate_transaction_fee(order)
        
        trade = {
            'id': next_trade_id,
            'orderId': order['id'],
            'symbol': order['symbol'],
            'name': order['name'],
            'type': order['type'],
            'quantity': order['filledQuantity'],
            'price': order['price'],
            'amount': amount,
            'fee': fee,
            'timestamp': order['timestamp'],
            'accountId': order['accountId'],
            'assetType': order['assetType'],
            'status': 'completed' if order['status'] == 'filled' else 'failed'
        }
        
        self.trades.append(trade)
        next_trade_id += 1
        return trade
    
    def get_trades(self, 
                   account_id: str = None, 
                   symbol: str = None, 
                   trade_type: str = None, 
                   asset_type: str = None, 
                   start_date: Optional[float] = None, 
                   end_date: Optional[float] = None) -> List[Dict[str, Any]]:
        """查询历史交易记录
        
        Args:
            account_id: 账户ID，可选
            symbol: 交易标的，可选
            trade_type: 交易类型（buy/sell），可选
            asset_type: 资产类型，可选
            start_date: 开始时间戳，可选
            end_date: 结束时间戳，可选
        
        Returns:
            交易记录列表
        """
        filtered_trades = self.trades.copy()
        
        # 按账户ID过滤
        if account_id:
            filtered_trades = [trade for trade in filtered_trades if trade['accountId'] == account_id]
        
        # 按交易标的过滤
        if symbol:
            filtered_trades = [trade for trade in filtered_trades if trade['symbol'] == symbol]
        
        # 按交易类型过滤
        if trade_type:
            filtered_trades = [trade for trade in filtered_trades if trade['type'] == trade_type]
        
        # 按资产类型过滤
        if asset_type:
            filtered_trades = [trade for trade in filtered_trades if trade['assetType'] == asset_type]
        
        # 按时间范围过滤
        if start_date:
            filtered_trades = [trade for trade in filtered_trades if trade['timestamp'] >= start_date]
        
        if end_date:
            filtered_trades = [trade for trade in filtered_trades if trade['timestamp'] <= end_date]
        
        # 按时间戳排序（最新的在前）
        filtered_trades.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return filtered_trades
    
    def get_trade_by_id(self, trade_id: int) -> Dict[str, Any]:
        """根据ID获取单个交易记录
        
        Args:
            trade_id: 交易记录ID
        
        Returns:
            交易记录
        """
        for trade in self.trades:
            if trade['id'] == trade_id:
                return trade
        return None
    
    def export_trades_to_csv(self, file_path: str, 
                             account_id: str = None, 
                             start_date: Optional[float] = None, 
                             end_date: Optional[float] = None) -> str:
        """导出交易记录到CSV文件
        
        Args:
            file_path: 文件路径
            account_id: 账户ID，可选
            start_date: 开始时间戳，可选
            end_date: 结束时间戳，可选
        
        Returns:
            导出的文件路径
        """
        # 获取要导出的交易记录
        trades_to_export = self.get_trades(account_id=account_id, start_date=start_date, end_date=end_date)
        
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 导出到CSV
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['id', 'orderId', 'symbol', 'name', 'type', 'quantity', 'price', 'amount', 'fee', 
                         'timestamp', 'formattedDate', 'accountId', 'assetType', 'status']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # 写入表头
            writer.writeheader()
            
            # 写入数据
            for trade in trades_to_export:
                # 添加格式化的日期时间
                formatted_trade = trade.copy()
                formatted_trade['formattedDate'] = datetime.datetime.fromtimestamp(trade['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                writer.writerow(formatted_trade)
        
        return file_path
    
    def get_trade_statistics(self, account_id: str = None, 
                             start_date: Optional[float] = None, 
                             end_date: Optional[float] = None) -> Dict[str, Any]:
        """获取交易统计信息
        
        Args:
            account_id: 账户ID，可选
            start_date: 开始时间戳，可选
            end_date: 结束时间戳，可选
        
        Returns:
            交易统计信息
        """
        trades = self.get_trades(account_id=account_id, start_date=start_date, end_date=end_date)
        
        if not trades:
            return {
                'totalTrades': 0,
                'totalBuyTrades': 0,
                'totalSellTrades': 0,
                'totalAmount': 0,
                'totalFee': 0,
                'averageTradeAmount': 0
            }
        
        # 计算统计数据
        total_trades = len(trades)
        buy_trades = [t for t in trades if t['type'] == 'buy']
        sell_trades = [t for t in trades if t['type'] == 'sell']
        
        total_amount = sum(t['amount'] for t in trades)
        total_fee = sum(t['fee'] for t in trades)
        
        statistics = {
            'totalTrades': total_trades,
            'totalBuyTrades': len(buy_trades),
            'totalSellTrades': len(sell_trades),
            'totalAmount': total_amount,
            'totalFee': total_fee,
            'averageTradeAmount': total_amount / total_trades if total_trades > 0 else 0
        }
        
        return statistics

# 创建全局历史交易管理器实例
trade_history_manager = TradeHistoryManager()