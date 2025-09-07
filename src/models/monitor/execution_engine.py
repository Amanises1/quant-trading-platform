# 交易执行引擎模块
import random
import datetime
import time
from typing import List, Dict, Any
from .position_manager import position_manager

# 模拟订单数据
simulated_orders = [
    {
        'id': 1,
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
        'id': 2,
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
        'id': 3,
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

# 订单ID计数器
next_order_id = 4

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
        self.orders = simulated_orders.copy()
        self.order_status_callbacks = {}
        self.running = False
        
    def start_monitoring(self):
        """启动订单监控"""
        if not self.running:
            self.running = True
            # 在实际应用中，这里应该是一个单独的线程来监控订单状态
            print("订单监控已启动")
    
    def stop_monitoring(self):
        """停止订单监控"""
        self.running = False
        print("订单监控已停止")
    
    def submit_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """提交交易订单
        
        Args:
            order_data: 订单数据
        
        Returns:
            订单信息
        """
        global next_order_id
        
        # 创建订单
        order = {
            'id': next_order_id,
            'symbol': order_data.get('symbol', ''),
            'name': order_data.get('name', ''),
            'type': order_data.get('type', 'buy'),
            'orderType': order_data.get('orderType', 'market'),
            'quantity': order_data.get('quantity', 0),
            'price': order_data.get('price', 0),
            'filledQuantity': 0,
            'status': 'pending',
            'timestamp': datetime.datetime.now().timestamp(),
            'accountId': order_data.get('accountId', ''),
            'assetType': order_data.get('assetType', 'stock'),
            'message': '订单已提交'
        }
        
        self.orders.append(order)
        next_order_id += 1
        
        # 模拟订单处理
        self._process_order(order)
        
        return order
    
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
            
            # 更新持仓
            self._update_position(order)
            
        else:
            # 订单执行失败
            order['status'] = 'rejected'
            order['message'] = f'交易失败：市场流动性不足'
        
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
    
    def cancel_order(self, order_id: int) -> bool:
        """取消订单
        
        Args:
            order_id: 订单ID
        
        Returns:
            取消是否成功
        """
        for order in self.orders:
            if order['id'] == order_id and order['status'] == 'pending':
                order['status'] = 'cancelled'
                order['message'] = '订单已取消'
                return True
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
        filtered_orders = self.orders.copy()
        
        # 按账户ID过滤
        if account_id:
            filtered_orders = [order for order in filtered_orders if order['accountId'] == account_id]
        
        # 按订单状态过滤
        if status:
            filtered_orders = [order for order in filtered_orders if order['status'] == status]
        
        # 按资产类型过滤
        if asset_type:
            filtered_orders = [order for order in filtered_orders if order['assetType'] == asset_type]
        
        # 按时间戳排序（最新的在前）
        filtered_orders.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return filtered_orders
    
    def get_order_by_id(self, order_id: int) -> Dict[str, Any]:
        """根据ID获取单个订单信息
        
        Args:
            order_id: 订单ID
        
        Returns:
            订单信息
        """
        for order in self.orders:
            if order['id'] == order_id:
                return order
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