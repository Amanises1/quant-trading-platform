import random
import datetime
import time
from typing import List, Dict, Any
from .position_manager import position_manager
from .database_connection import db_conn
import logging

# 模拟交易费用
TRANSACTION_FEE_RATES = {
    'stock': {
        'buy': 0.0003,  # 0.03%
        'sell': 0.0003  # 0.03% + 印花税
    },
    'futures': {
        'buy': 0.0001,
        'sell': 0.0001
    }
}

class ExecutionEngine:
    """交易执行引擎，负责处理交易订单"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.order_status_callbacks = {}
        self.running = False
        
        # 初始化数据库表
        self._init_database()
        
        # 初始化样本数据（如果表为空）
        self._init_sample_data()
    
    def _init_database(self) -> None:
        """初始化数据库表结构"""
        try:
            # 创建orders表用于存储订单信息
            create_orders_table = """
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(50) NOT NULL,
                name VARCHAR(100) NOT NULL,
                type VARCHAR(10) NOT NULL,
                order_type VARCHAR(10) NOT NULL,
                quantity INTEGER NOT NULL,
                price DOUBLE PRECISION NOT NULL,
                filled_quantity INTEGER NOT NULL DEFAULT 0,
                status VARCHAR(20) NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                account_id VARCHAR(20) NOT NULL,
                asset_type VARCHAR(20) NOT NULL,
                message TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
            """
            db_conn.execute_query(create_orders_table)
            
            # 创建交易费用表
            create_transaction_fees_table = """
            CREATE TABLE IF NOT EXISTS transaction_fees (
                id SERIAL PRIMARY KEY,
                order_id INTEGER NOT NULL,
                fee_amount DOUBLE PRECISION NOT NULL,
                fee_rate DOUBLE PRECISION NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (order_id) REFERENCES orders(id)
            )
            """
            db_conn.execute_query(create_transaction_fees_table)
            
            # 创建索引以提高查询性能
            create_indexes = [
                "CREATE INDEX IF NOT EXISTS idx_orders_account_id ON orders (account_id)",
                "CREATE INDEX IF NOT EXISTS idx_orders_symbol ON orders (symbol)",
                "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders (status)",
                "CREATE INDEX IF NOT EXISTS idx_orders_timestamp ON orders (timestamp DESC)"
            ]
            
            for idx in create_indexes:
                db_conn.execute_query(idx)
            
            self.logger.info("交易执行引擎数据库表初始化完成")
        except Exception as e:
            self.logger.error(f"初始化交易执行引擎数据库表失败: {e}")
    
    def _init_sample_data(self) -> None:
        """初始化样本数据（如果数据库中没有数据）"""
        # 检查是否已有数据
        existing_orders = self.get_orders()
        if not existing_orders:
            # 模拟订单数据
            sample_orders = [
                {
                    'symbol': '600519',
                    'name': '贵州茅台',
                    'type': 'buy',  # buy 或 sell
                    'orderType': 'limit',  # market 或 limit
                    'quantity': 50,
                    'price': 1720.00,
                    'filledQuantity': 50,
                    'status': 'filled',  # pending, filled, cancelled, rejected
                    'timestamp': datetime.datetime.now().timestamp() - 3600,
                    'accountId': 'A001',
                    'assetType': 'stock',
                    'message': '交易成功'
                },
                {
                    'symbol': '000001',
                    'name': '平安银行',
                    'type': 'sell',
                    'orderType': 'market',
                    'quantity': 300,
                    'price': 11.85,
                    'filledQuantity': 300,
                    'status': 'filled',
                    'timestamp': datetime.datetime.now().timestamp() - 7200,
                    'accountId': 'A001',
                    'assetType': 'stock',
                    'message': '交易成功'
                },
                {
                    'symbol': 'IF2312',
                    'name': '沪深300指数期货',
                    'type': 'buy',
                    'orderType': 'limit',
                    'quantity': 1,
                    'price': 3880.00,
                    'filledQuantity': 0,
                    'status': 'pending',
                    'timestamp': datetime.datetime.now().timestamp() - 1800,
                    'accountId': 'A002',
                    'assetType': 'futures',
                    'message': '订单待成交'
                }
            ]
            
            # 插入样本数据
            for order_data in sample_orders:
                # 直接插入数据库，不触发订单处理逻辑
                timestamp = datetime.datetime.fromtimestamp(order_data['timestamp'])
                
                query = """
                INSERT INTO orders (symbol, name, type, order_type, quantity, price, 
                                   filled_quantity, status, timestamp, account_id, 
                                   asset_type, message)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                params = (
                    order_data['symbol'],
                    order_data['name'],
                    order_data['type'],
                    order_data['orderType'],
                    order_data['quantity'],
                    order_data['price'],
                    order_data['filledQuantity'],
                    order_data['status'],
                    timestamp,
                    order_data['accountId'],
                    order_data['assetType'],
                    order_data['message']
                )
                
                db_conn.execute_query(query, params)
            
            self.logger.info("已向数据库添加样本订单数据")
    
    def start_monitoring(self):
        """启动订单监控"""
        if not self.running:
            self.running = True
            # 在实际应用中，这里应该是一个单独的线程来监控订单状态
            self.logger.info("订单监控已启动")
    
    def stop_monitoring(self):
        """停止订单监控"""
        self.running = False
        self.logger.info("订单监控已停止")
    
    def submit_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """提交交易订单
        
        Args:
            order_data: 订单数据
        
        Returns:
            订单信息
        """
        # 创建订单
        current_time = datetime.datetime.now()
        
        # 插入数据库获取订单ID
        query = """
        INSERT INTO orders (symbol, name, type, order_type, quantity, price, 
                           filled_quantity, status, timestamp, account_id, 
                           asset_type, message)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        params = (
            order_data.get('symbol', ''),
            order_data.get('name', ''),
            order_data.get('type', 'buy'),
            order_data.get('orderType', 'market'),
            order_data.get('quantity', 0),
            order_data.get('price', 0),
            0,  # filled_quantity
            'pending',  # status
            current_time,
            order_data.get('accountId', ''),
            order_data.get('assetType', 'stock'),
            '订单已提交'
        )
        
        result = db_conn.execute_query(query, params)
        
        if result and len(result) > 0:
            order_id = result[0]['id']
            
            # 获取刚创建的订单
            order = self.get_order_by_id(order_id)
            
            # 模拟订单处理
            self._process_order(order)
            
            return order
        
        raise Exception("提交订单失败")
    
    def _process_order(self, order: Dict[str, Any]):
        """处理订单（模拟交易执行）"""
        # 模拟交易延迟
        # 注意：在实际应用中，这里应该是异步的，不会阻塞主线程
        time.sleep(0.5)  # 仅用于模拟，实际代码中应该避免
        
        # 模拟市场价格
        asset_type = order['assetType']
        symbol = order['symbol']
        
        # 模拟订单执行结果
        success_probability = 0.9  # 90%的成功率
        if random.random() < success_probability:
            # 订单成功执行
            order['status'] = 'filled'
            order['filledQuantity'] = order['quantity']
            order['message'] = '交易成功'
            
            # 更新数据库中的订单状态
            query = """
            UPDATE orders
            SET status = %s,
                filled_quantity = %s,
                message = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """
            params = (order['status'], order['filledQuantity'], order['message'], order['id'])
            db_conn.execute_query(query, params)
            
            # 更新持仓
            self._update_position(order)
            
            # 计算并保存交易费用
            fee = self.calculate_transaction_fee(order)
            self._save_transaction_fee(order['id'], fee)
            
        else:
            # 订单执行失败
            order['status'] = 'rejected'
            order['message'] = f'交易失败：市场流动性不足'
            
            # 更新数据库中的订单状态
            query = """
            UPDATE orders
            SET status = %s,
                message = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """
            params = (order['status'], order['message'], order['id'])
            db_conn.execute_query(query, params)
        
        # 调用回调函数
        if order['id'] in self.order_status_callbacks:
            callback = self.order_status_callbacks[order['id']]
            callback(order)
            del self.order_status_callbacks[order['id']]
    
    def _update_position(self, order: Dict[str, Any]):
        """根据订单结果更新持仓"""
        account_id = order['accountId']
        symbol = order['symbol']
        name = order['name']
        quantity = order['quantity']
        price = order['price']
        order_type = order['type']
        asset_type = order['assetType']
        
        # 检查是否已有该证券的持仓
        existing_positions = position_manager.get_positions(account_id=account_id, asset_type=asset_type)
        target_position = None
        
        for pos in existing_positions:
            if pos['symbol'] == symbol:
                target_position = pos
                break
        
        if order_type == 'buy':
            if target_position:
                # 更新现有持仓
                total_quantity = target_position['quantity'] + quantity
                avg_price = ((target_position['quantity'] * target_position['avgPrice']) + 
                            (quantity * price)) / total_quantity
                
                position_manager.update_position(target_position['id'], {
                    'quantity': total_quantity,
                    'avgPrice': avg_price,
                    'currentPrice': price  # 假设当前价格为成交价格
                })
            else:
                # 添加新持仓
                position_manager.add_position({
                    'symbol': symbol,
                    'name': name,
                    'quantity': quantity,
                    'avgPrice': price,
                    'currentPrice': price,
                    'accountId': account_id,
                    'assetType': asset_type
                })
        elif order_type == 'sell':
            if target_position and target_position['quantity'] >= quantity:
                if target_position['quantity'] == quantity:
                    # 全部卖出，移除持仓
                    position_manager.remove_position(target_position['id'])
                else:
                    # 部分卖出，更新持仓数量
                    position_manager.update_position(target_position['id'], {
                        'quantity': target_position['quantity'] - quantity,
                        'currentPrice': price  # 假设当前价格为成交价格
                    })
    
    def _save_transaction_fee(self, order_id: int, fee_amount: float) -> None:
        """保存交易费用信息"""
        try:
            # 获取订单信息以确定费率
            order = self.get_order_by_id(order_id)
            if order:
                asset_type = order['assetType']
                order_type = order['type']
                
                # 获取费率
                rate = TRANSACTION_FEE_RATES.get(asset_type, {}).get(order_type, 0.0003)
                
                # 保存交易费用
                query = """
                INSERT INTO transaction_fees (order_id, fee_amount, fee_rate)
                VALUES (%s, %s, %s)
                """
                params = (order_id, fee_amount, rate)
                db_conn.execute_query(query, params)
                
                self.logger.info(f"已保存订单{order_id}的交易费用: {fee_amount}")
        except Exception as e:
            self.logger.error(f"保存交易费用失败: {e}")
    
    def cancel_order(self, order_id: int) -> bool:
        """取消订单
        
        Args:
            order_id: 订单ID
        
        Returns:
            取消是否成功
        """
        try:
            # 检查订单是否存在且处于pending状态
            query = """
            SELECT status FROM orders WHERE id = %s
            """
            result = db_conn.execute_query(query, (order_id,))
            
            if result and len(result) > 0:
                status = result[0]['status']
                
                if status == 'pending':
                    # 取消订单
                    update_query = """
                    UPDATE orders
                    SET status = 'cancelled',
                        message = '订单已取消',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """
                    db_conn.execute_query(update_query, (order_id,))
                    return True
            
            return False
        except Exception as e:
            self.logger.error(f"取消订单{order_id}失败: {e}")
            return False
    
    def get_orders(self, account_id: str = None, status: str = None, 
                   asset_type: str = None) -> List[Dict[str, Any]]:
        """获取订单列表
        
        Args:
            account_id: 账户ID，可选
            status: 订单状态，可选
            asset_type: 资产类型，可选
        
        Returns:
            订单列表
        """
        try:
            query = """
            SELECT id, symbol, name, type, order_type, quantity, price, 
                   filled_quantity, status, timestamp, account_id, asset_type, message
            FROM orders
            WHERE 1=1
            """
            params = []
            
            # 按账户ID过滤
            if account_id:
                query += " AND account_id = %s"
                params.append(account_id)
            
            # 按订单状态过滤
            if status:
                query += " AND status = %s"
                params.append(status)
            
            # 按资产类型过滤
            if asset_type:
                query += " AND asset_type = %s"
                params.append(asset_type)
            
            # 按时间戳排序（最新的在前）
            query += " ORDER BY timestamp DESC"
            
            results = db_conn.execute_query(query, tuple(params))
            
            # 转换字段名以保持与原有接口兼容
            if results:
                for result in results:
                    # 将数据库字段名转换为驼峰命名
                    result['orderType'] = result.pop('order_type')
                    result['filledQuantity'] = result.pop('filled_quantity')
                    result['accountId'] = result.pop('account_id')
                    result['assetType'] = result.pop('asset_type')
                    result['timestamp'] = result['timestamp'].timestamp()
            
            return results or []
        except Exception as e:
            self.logger.error(f"获取订单列表失败: {e}")
            return []
    
    def get_order_by_id(self, order_id: int) -> Dict[str, Any]:
        """根据ID获取单个订单信息
        
        Args:
            order_id: 订单ID
        
        Returns:
            订单信息
        """
        try:
            query = """
            SELECT id, symbol, name, type, order_type, quantity, price, 
                   filled_quantity, status, timestamp, account_id, asset_type, message
            FROM orders
            WHERE id = %s
            """
            result = db_conn.execute_query(query, (order_id,))
            
            if result and len(result) > 0:
                order = result[0]
                # 将数据库字段名转换为驼峰命名
                order['orderType'] = order.pop('order_type')
                order['filledQuantity'] = order.pop('filled_quantity')
                order['accountId'] = order.pop('account_id')
                order['assetType'] = order.pop('asset_type')
                order['timestamp'] = order['timestamp'].timestamp()
                return order
            
            return None
        except Exception as e:
            self.logger.error(f"获取订单{order_id}失败: {e}")
            return None
    
    def calculate_transaction_fee(self, order: Dict[str, Any]) -> float:
        """计算交易费用
        
        Args:
            order: 订单信息
        
        Returns:
            交易费用
        """
        asset_type = order['assetType']
        order_type = order['type']
        quantity = order['filledQuantity']
        price = order['price']
        
        # 获取费率
        rate = TRANSACTION_FEE_RATES.get(asset_type, {}).get(order_type, 0.0003)
        
        # 计算交易金额
        amount = quantity * price
        
        # 计算费用
        fee = amount * rate
        
        # 最低费用
        min_fee = 5.0  # 股票交易最低5元
        if asset_type == 'futures':
            min_fee = 1.0  # 期货交易最低1元
        
        return max(fee, min_fee)

# 创建全局执行引擎实例
execution_engine = ExecutionEngine()