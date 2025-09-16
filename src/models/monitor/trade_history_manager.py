import datetime
import csv
import os
import datetime
from typing import List, Dict, Any, Optional
from .database_connection import db_conn
from .execution_engine import execution_engine
import logging

class TradeHistoryManager:
    """历史交易记录管理类，负责记录和查询交易历史"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # 初始化时向数据库插入一些模拟数据（如果表为空）
        self._init_sample_data()
    
    def _init_sample_data(self) -> None:
        """初始化样本数据（如果数据库中没有数据）"""
        # 检查是否已有数据
        existing_trades = self.get_trades()
        if not existing_trades:
            # 模拟历史交易数据
            sample_trades = [
                {
                    'order_id': 1,
                    'symbol': '600519',
                    'name': '贵州茅台',
                    'type': 'buy',
                    'quantity': 50,
                    'price': 1720.00,
                    'amount': 86000.00,
                    'fee': 25.80,
                    'timestamp': datetime.datetime.now().timestamp() - 3600,
                    'account_id': 'A001',
                    'asset_type': 'stock',
                    'status': 'completed'
                },
                {
                    'order_id': 2,
                    'symbol': '000001',
                    'name': '平安银行',
                    'type': 'sell',
                    'quantity': 300,
                    'price': 11.85,
                    'amount': 3555.00,
                    'fee': 1.07,
                    'timestamp': datetime.datetime.now().timestamp() - 7200,
                    'account_id': 'A001',
                    'asset_type': 'stock',
                    'status': 'completed'
                },
                {
                    'order_id': 0,
                    'symbol': '600036',
                    'name': '招商银行',
                    'type': 'buy',
                    'quantity': 500,
                    'price': 35.20,
                    'amount': 17600.00,
                    'fee': 5.28,
                    'timestamp': datetime.datetime.now().timestamp() - 86400 * 5,
                    'account_id': 'A001',
                    'asset_type': 'stock',
                    'status': 'completed'
                },
                {
                    'order_id': 0,
                    'symbol': '000001',
                    'name': '平安银行',
                    'type': 'buy',
                    'quantity': 1000,
                    'price': 12.50,
                    'amount': 12500.00,
                    'fee': 3.75,
                    'timestamp': datetime.datetime.now().timestamp() - 86400 * 10,
                    'account_id': 'A001',
                    'asset_type': 'stock',
                    'status': 'completed'
                }
            ]
            
            # 插入样本数据
            for trade in sample_trades:
                query = """
                INSERT INTO trade_history (order_id, symbol, name, type, quantity, price, amount, fee, timestamp, account_id, asset_type, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                params = (
                    trade['order_id'],
                    trade['symbol'],
                    trade['name'],
                    trade['type'],
                    trade['quantity'],
                    trade['price'],
                    trade['amount'],
                    trade['fee'],
                    trade['timestamp'],
                    trade['account_id'],
                    trade['asset_type'],
                    trade['status']
                )
                
                db_conn.execute_query(query, params)
            
            self.logger.info("已向数据库添加样本交易历史数据")
    
    def record_trade(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """记录一笔交易到数据库
        
        Args:
            order: 订单信息
        
        Returns:
            交易记录
        """
        # 计算交易金额和费用
        amount = order['filledQuantity'] * order['price']
        fee = execution_engine.calculate_transaction_fee(order)
        
        # 准备插入数据库的数据
        query = """
        INSERT INTO trade_history (order_id, symbol, name, type, quantity, price, amount, fee, timestamp, account_id, asset_type, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        
        params = (
            order['id'],
            order['symbol'],
            order['name'],
            order['type'],
            order['filledQuantity'],
            order['price'],
            amount,
            fee,
            order['timestamp'],
            order['accountId'],
            order['assetType'],
            'completed' if order['status'] == 'filled' else 'failed'
        )
        
        result = db_conn.execute_query(query, params)
        
        if result and len(result) > 0:
            trade_id = result[0]['id']
            return self.get_trade_by_id(trade_id)
        
        raise Exception("记录交易失败")
    
    def get_trades(self, 
                   account_id: str = None, 
                   symbol: str = None, 
                   trade_type: str = None, 
                   asset_type: str = None, 
                   start_date: Optional[float] = None, 
                   end_date: Optional[float] = None) -> List[Dict[str, Any]]:
        """从数据库查询历史交易记录
        
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
        query = "SELECT * FROM trade_history WHERE 1=1"
        params = []
        
        # 按账户ID过滤
        if account_id:
            query += " AND account_id = %s"
            params.append(account_id)
        
        # 按交易标的过滤
        if symbol:
            query += " AND symbol = %s"
            params.append(symbol)
        
        # 按交易类型过滤
        if trade_type:
            query += " AND type = %s"
            params.append(trade_type)
        
        # 按资产类型过滤
        if asset_type:
            query += " AND asset_type = %s"
            params.append(asset_type)
        
        # 按时间范围过滤
        if start_date:
            query += " AND timestamp >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= %s"
            params.append(end_date)
        
        # 按时间戳排序（最新的在前）
        query += " ORDER BY timestamp DESC"
        
        results = db_conn.execute_query(query, tuple(params))
        
        # 转换字段名以保持与原有接口兼容
        if results:
            for result in results:
                # 将数据库字段名转换为驼峰命名
                result['orderId'] = result.pop('order_id')
                result['accountId'] = result.pop('account_id')
                result['assetType'] = result.pop('asset_type')
                
                # 删除不需要返回的字段
                for field in ['created_at', 'updated_at']:
                    if field in result:
                        del result[field]
        
        return results or []
    
    def get_trade_by_id(self, trade_id: int) -> Optional[Dict[str, Any]]:
        """根据ID从数据库获取单个交易记录
        
        Args:
            trade_id: 交易记录ID
        
        Returns:
            交易记录
        """
        query = "SELECT * FROM trade_history WHERE id = %s"
        result = db_conn.execute_query(query, (trade_id,))
        
        if result and len(result) > 0:
            trade = result[0]
            # 转换字段名以保持与原有接口兼容
            trade['orderId'] = trade.pop('order_id')
            trade['accountId'] = trade.pop('account_id')
            trade['assetType'] = trade.pop('asset_type')
            
            # 删除不需要返回的字段
            for field in ['created_at', 'updated_at']:
                if field in trade:
                    del trade[field]
            
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
        # 使用数据库查询获取统计信息
        query = """
        SELECT 
            COUNT(*) as total_trades,
            SUM(CASE WHEN type = 'buy' THEN 1 ELSE 0 END) as total_buy_trades,
            SUM(CASE WHEN type = 'sell' THEN 1 ELSE 0 END) as total_sell_trades,
            SUM(amount) as total_amount,
            SUM(fee) as total_fee,
            AVG(amount) as average_trade_amount
        FROM trade_history
        WHERE 1=1
        """
        
        params = []
        
        if account_id:
            query += " AND account_id = %s"
            params.append(account_id)
        
        if start_date:
            query += " AND timestamp >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= %s"
            params.append(end_date)
        
        result = db_conn.execute_query(query, tuple(params))
        
        if result and len(result) > 0:
            stats = result[0]
            
            return {
                'totalTrades': stats['total_trades'] or 0,
                'totalBuyTrades': stats['total_buy_trades'] or 0,
                'totalSellTrades': stats['total_sell_trades'] or 0,
                'totalAmount': float(stats['total_amount']) if stats['total_amount'] is not None else 0,
                'totalFee': float(stats['total_fee']) if stats['total_fee'] is not None else 0,
                'averageTradeAmount': float(stats['average_trade_amount']) if stats['average_trade_amount'] is not None else 0
            }
        
        return {
            'totalTrades': 0,
            'totalBuyTrades': 0,
            'totalSellTrades': 0,
            'totalAmount': 0,
            'totalFee': 0,
            'averageTradeAmount': 0
        }

# 创建全局历史交易管理器实例
trade_history_manager = TradeHistoryManager()