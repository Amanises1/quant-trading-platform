# 交易执行模块

import pandas as pd
import numpy as np
from typing import Dict, List, Union, Optional, Callable, Tuple
import logging
from datetime import datetime
import uuid

class Order:
    """
    订单类，表示一个交易订单
    """
    
    def __init__(self, symbol: str, order_type: str, direction: int, quantity: float, 
                 price: Optional[float] = None, stop_price: Optional[float] = None,
                 limit_price: Optional[float] = None, time_in_force: str = 'GTC',
                 order_id: Optional[str] = None, timestamp: Optional[datetime] = None):
        """
        初始化订单
        
        参数:
            symbol: 交易标的代码
            order_type: 订单类型，如'MARKET', 'LIMIT', 'STOP', 'STOP_LIMIT'
            direction: 交易方向，1为买入，-1为卖出
            quantity: 交易数量
            price: 订单价格，对于市价单可为None
            stop_price: 止损价格，仅对止损单和止损限价单有效
            limit_price: 限价，仅对限价单和止损限价单有效
            time_in_force: 订单有效期，如'GTC'(Good Till Canceled), 'DAY'(当日有效), 'IOC'(Immediate or Cancel)
            order_id: 订单ID，如果为None则自动生成
            timestamp: 订单创建时间，如果为None则使用当前时间
        """
        self.symbol = symbol
        self.order_type = order_type.upper()
        self.direction = direction  # 1 for buy, -1 for sell
        self.quantity = quantity
        self.price = price
        self.stop_price = stop_price
        self.limit_price = limit_price
        self.time_in_force = time_in_force.upper()
        self.order_id = order_id if order_id else str(uuid.uuid4())
        self.timestamp = timestamp if timestamp else datetime.now()
        
        # 订单状态
        self.status = 'PENDING'  # PENDING, FILLED, PARTIALLY_FILLED, CANCELED, REJECTED, EXPIRED
        self.filled_quantity = 0.0
        self.filled_price = 0.0
        self.filled_time = None
        self.commission = 0.0
        self.slippage = 0.0
        
        # 验证订单参数
        self._validate()
    
    def _validate(self):
        """
        验证订单参数
        """
        # 验证订单类型
        valid_order_types = ['MARKET', 'LIMIT', 'STOP', 'STOP_LIMIT']
        if self.order_type not in valid_order_types:
            raise ValueError(f"无效的订单类型: {self.order_type}，有效类型为: {valid_order_types}")
        
        # 验证交易方向
        if self.direction not in [1, -1]:
            raise ValueError(f"无效的交易方向: {self.direction}，有效方向为: 1(买入) 或 -1(卖出)")
        
        # 验证数量
        if self.quantity <= 0:
            raise ValueError(f"无效的交易数量: {self.quantity}，必须大于0")
        
        # 验证价格参数
        if self.order_type == 'LIMIT' and self.price is None:
            raise ValueError("限价单必须指定价格")
        
        if self.order_type == 'STOP' and self.stop_price is None:
            raise ValueError("止损单必须指定止损价格")
        
        if self.order_type == 'STOP_LIMIT' and (self.stop_price is None or self.limit_price is None):
            raise ValueError("止损限价单必须同时指定止损价格和限价")
        
        # 验证订单有效期
        valid_time_in_force = ['GTC', 'DAY', 'IOC', 'FOK']
        if self.time_in_force not in valid_time_in_force:
            raise ValueError(f"无效的订单有效期: {self.time_in_force}，有效值为: {valid_time_in_force}")
    
    def __str__(self):
        return (f"Order(id={self.order_id}, symbol={self.symbol}, type={self.order_type}, "
                f"direction={'BUY' if self.direction == 1 else 'SELL'}, quantity={self.quantity}, "
                f"price={self.price}, status={self.status}, filled={self.filled_quantity})")
    
    def to_dict(self) -> Dict:
        """
        将订单转换为字典
        """
        return {
            'order_id': self.order_id,
            'symbol': self.symbol,
            'order_type': self.order_type,
            'direction': self.direction,
            'quantity': self.quantity,
            'price': self.price,
            'stop_price': self.stop_price,
            'limit_price': self.limit_price,
            'time_in_force': self.time_in_force,
            'timestamp': self.timestamp,
            'status': self.status,
            'filled_quantity': self.filled_quantity,
            'filled_price': self.filled_price,
            'filled_time': self.filled_time,
            'commission': self.commission,
            'slippage': self.slippage
        }


class Trade:
    """
    交易类，表示一个已执行的交易
    """
    
    def __init__(self, order: Order, filled_price: float, filled_quantity: float, 
                 timestamp: Optional[datetime] = None, commission: float = 0.0, 
                 slippage: float = 0.0, trade_id: Optional[str] = None):
        """
        初始化交易
        
        参数:
            order: 关联的订单对象
            filled_price: 成交价格
            filled_quantity: 成交数量
            timestamp: 成交时间，如果为None则使用当前时间
            commission: 佣金
            slippage: 滑点
            trade_id: 交易ID，如果为None则自动生成
        """
        self.order = order
        self.order_id = order.order_id
        self.symbol = order.symbol
        self.direction = order.direction
        self.filled_price = filled_price
        self.filled_quantity = filled_quantity
        self.timestamp = timestamp if timestamp else datetime.now()
        self.commission = commission
        self.slippage = slippage
        self.trade_id = trade_id if trade_id else str(uuid.uuid4())
    
    def __str__(self):
        return (f"Trade(id={self.trade_id}, order_id={self.order_id}, symbol={self.symbol}, "
                f"direction={'BUY' if self.direction == 1 else 'SELL'}, "
                f"price={self.filled_price}, quantity={self.filled_quantity}, "
                f"commission={self.commission}, slippage={self.slippage})")
    
    def to_dict(self) -> Dict:
        """
        将交易转换为字典
        """
        return {
            'trade_id': self.trade_id,
            'order_id': self.order_id,
            'symbol': self.symbol,
            'direction': self.direction,
            'filled_price': self.filled_price,
            'filled_quantity': self.filled_quantity,
            'timestamp': self.timestamp,
            'commission': self.commission,
            'slippage': self.slippage
        }


class Position:
    """
    持仓类，表示一个交易标的的持仓情况
    """
    
    def __init__(self, symbol: str, quantity: float = 0.0, avg_price: float = 0.0):
        """
        初始化持仓
        
        参数:
            symbol: 交易标的代码
            quantity: 持仓数量，正数表示多头，负数表示空头
            avg_price: 平均持仓价格
        """
        self.symbol = symbol
        self.quantity = quantity
        self.avg_price = avg_price
        self.realized_pnl = 0.0  # 已实现盈亏
        self.unrealized_pnl = 0.0  # 未实现盈亏
        self.last_price = avg_price  # 最新价格
        self.trades = []  # 持仓相关的交易记录
    
    def update(self, trade: Trade):
        """
        更新持仓
        
        参数:
            trade: 新的交易
        """
        # 记录交易
        self.trades.append(trade)
        
        # 更新持仓
        old_quantity = self.quantity
        old_avg_price = self.avg_price
        
        # 计算新的持仓数量和平均价格
        if trade.direction == 1:  # 买入
            if old_quantity >= 0:  # 增加多头或建立多头
                # 更新平均价格
                self.avg_price = (old_quantity * old_avg_price + trade.filled_quantity * trade.filled_price) / \
                                (old_quantity + trade.filled_quantity)
                # 更新持仓数量
                self.quantity += trade.filled_quantity
            else:  # 减少空头
                if abs(old_quantity) >= trade.filled_quantity:  # 部分平仓
                    # 计算平仓盈亏
                    self.realized_pnl += (old_avg_price - trade.filled_price) * trade.filled_quantity
                    # 更新持仓数量
                    self.quantity += trade.filled_quantity
                else:  # 全部平仓并建立多头
                    # 计算平仓盈亏
                    self.realized_pnl += (old_avg_price - trade.filled_price) * abs(old_quantity)
                    # 剩余的部分建立多头
                    remaining_quantity = trade.filled_quantity - abs(old_quantity)
                    self.quantity = remaining_quantity
                    self.avg_price = trade.filled_price
        
        elif trade.direction == -1:  # 卖出
            if old_quantity <= 0:  # 增加空头或建立空头
                # 更新平均价格
                if old_quantity == 0:
                    self.avg_price = trade.filled_price
                else:
                    self.avg_price = (abs(old_quantity) * old_avg_price + trade.filled_quantity * trade.filled_price) / \
                                    (abs(old_quantity) + trade.filled_quantity)
                # 更新持仓数量
                self.quantity -= trade.filled_quantity
            else:  # 减少多头
                if old_quantity >= trade.filled_quantity:  # 部分平仓
                    # 计算平仓盈亏
                    self.realized_pnl += (trade.filled_price - old_avg_price) * trade.filled_quantity
                    # 更新持仓数量
                    self.quantity -= trade.filled_quantity
                else:  # 全部平仓并建立空头
                    # 计算平仓盈亏
                    self.realized_pnl += (trade.filled_price - old_avg_price) * old_quantity
                    # 剩余的部分建立空头
                    remaining_quantity = trade.filled_quantity - old_quantity
                    self.quantity = -remaining_quantity
                    self.avg_price = trade.filled_price
        
        # 更新最新价格
        self.last_price = trade.filled_price
        
        # 更新未实现盈亏
        self.update_unrealized_pnl(self.last_price)
    
    def update_unrealized_pnl(self, price: float):
        """
        更新未实现盈亏
        
        参数:
            price: 最新价格
        """
        self.last_price = price
        
        if self.quantity == 0:
            self.unrealized_pnl = 0.0
        elif self.quantity > 0:  # 多头
            self.unrealized_pnl = (price - self.avg_price) * self.quantity
        else:  # 空头
            self.unrealized_pnl = (self.avg_price - price) * abs(self.quantity)
    
    def __str__(self):
        position_type = "多头" if self.quantity > 0 else "空头" if self.quantity < 0 else "空仓"
        return (f"Position(symbol={self.symbol}, type={position_type}, quantity={abs(self.quantity)}, "
                f"avg_price={self.avg_price}, realized_pnl={self.realized_pnl}, "
                f"unrealized_pnl={self.unrealized_pnl})")
    
    def to_dict(self) -> Dict:
        """
        将持仓转换为字典
        """
        return {
            'symbol': self.symbol,
            'quantity': self.quantity,
            'avg_price': self.avg_price,
            'realized_pnl': self.realized_pnl,
            'unrealized_pnl': self.unrealized_pnl,
            'last_price': self.last_price,
            'market_value': self.quantity * self.last_price if self.last_price else 0.0
        }


class TradeExecutor:
    """
    交易执行器，用于执行交易订单
    支持多种订单类型和执行模式
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化交易执行器
        
        参数:
            config: 配置信息，包含交易执行参数
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 设置默认参数
        self.config.setdefault('commission_rate', 0.0003)  # 佣金率，默认万三
        self.config.setdefault('slippage_model', 'fixed')  # 滑点模型，fixed或random
        self.config.setdefault('fixed_slippage', 0.0)  # 固定滑点
        self.config.setdefault('random_slippage_range', (0.0, 0.0))  # 随机滑点范围
        self.config.setdefault('market_impact_model', None)  # 市场冲击模型
        
        # 订单和交易记录
        self.orders = {}  # 订单字典，键为订单ID
        self.trades = []  # 交易列表
        self.positions = {}  # 持仓字典，键为交易标的代码
        
        # 待执行的订单
        self.pending_orders = []  # 待执行的订单列表
        self.stop_orders = []  # 止损订单列表
    
    def place_order(self, order: Order) -> str:
        """
        下单
        
        参数:
            order: 订单对象
            
        返回:
            订单ID
        """
        # 记录订单
        self.orders[order.order_id] = order
        
        # 根据订单类型处理
        if order.order_type == 'MARKET':
            self.pending_orders.append(order)
        elif order.order_type == 'LIMIT':
            self.pending_orders.append(order)
        elif order.order_type == 'STOP' or order.order_type == 'STOP_LIMIT':
            self.stop_orders.append(order)
        
        self.logger.info(f"下单成功: {order}")
        return order.order_id
    
    def cancel_order(self, order_id: str) -> bool:
        """
        取消订单
        
        参数:
            order_id: 订单ID
            
        返回:
            是否成功取消
        """
        if order_id not in self.orders:
            self.logger.warning(f"取消订单失败: 订单ID {order_id} 不存在")
            return False
        
        order = self.orders[order_id]
        if order.status in ['FILLED', 'CANCELED', 'REJECTED', 'EXPIRED']:
            self.logger.warning(f"取消订单失败: 订单 {order} 已经是 {order.status} 状态")
            return False
        
        # 从待执行订单列表中移除
        if order in self.pending_orders:
            self.pending_orders.remove(order)
        if order in self.stop_orders:
            self.stop_orders.remove(order)
        
        # 更新订单状态
        order.status = 'CANCELED'
        self.logger.info(f"取消订单成功: {order}")
        return True
    
    def _calculate_slippage(self, price: float, direction: int) -> float:
        """
        计算滑点
        
        参数:
            price: 价格
            direction: 交易方向，1为买入，-1为卖出
            
        返回:
            滑点金额
        """
        slippage_model = self.config['slippage_model']
        
        if slippage_model == 'fixed':
            # 固定滑点
            fixed_slippage = self.config['fixed_slippage']
            return fixed_slippage * direction  # 买入时价格上升，卖出时价格下降
        
        elif slippage_model == 'random':
            # 随机滑点
            min_slippage, max_slippage = self.config['random_slippage_range']
            random_slippage = np.random.uniform(min_slippage, max_slippage)
            return random_slippage * direction
        
        else:
            # 默认无滑点
            return 0.0
    
    def _calculate_commission(self, price: float, quantity: float) -> float:
        """
        计算佣金
        
        参数:
            price: 价格
            quantity: 数量
            
        返回:
            佣金金额
        """
        commission_rate = self.config['commission_rate']
        return price * quantity * commission_rate
    
    def _calculate_market_impact(self, price: float, quantity: float, direction: int) -> float:
        """
        计算市场冲击
        
        参数:
            price: 价格
            quantity: 数量
            direction: 交易方向，1为买入，-1为卖出
            
        返回:
            市场冲击金额
        """
        market_impact_model = self.config['market_impact_model']
        
        if market_impact_model is None:
            # 无市场冲击
            return 0.0
        
        elif market_impact_model == 'linear':
            # 线性市场冲击模型
            impact_factor = self.config.get('market_impact_factor', 0.1)  # 市场冲击因子
            return price * impact_factor * quantity * direction / 10000  # 假设每10000股产生impact_factor的价格变动
        
        elif market_impact_model == 'square_root':
            # 平方根市场冲击模型
            impact_factor = self.config.get('market_impact_factor', 0.1)
            return price * impact_factor * np.sqrt(quantity) * direction / 100  # 假设每100股产生impact_factor的价格变动
        
        else:
            # 默认无市场冲击
            return 0.0
    
    def _execute_market_order(self, order: Order, price: float) -> Optional[Trade]:
        """
        执行市价单
        
        参数:
            order: 订单对象
            price: 当前价格
            
        返回:
            交易对象，如果未成交则返回None
        """
        if order.status != 'PENDING':
            return None
        
        # 计算滑点
        slippage = self._calculate_slippage(price, order.direction)
        
        # 计算市场冲击
        market_impact = self._calculate_market_impact(price, order.quantity, order.direction)
        
        # 计算成交价格
        filled_price = price + slippage + market_impact
        
        # 计算佣金
        commission = self._calculate_commission(filled_price, order.quantity)
        
        # 更新订单状态
        order.status = 'FILLED'
        order.filled_quantity = order.quantity
        order.filled_price = filled_price
        order.filled_time = datetime.now()
        order.commission = commission
        order.slippage = slippage
        
        # 创建交易记录
        trade = Trade(
            order=order,
            filled_price=filled_price,
            filled_quantity=order.quantity,
            timestamp=order.filled_time,
            commission=commission,
            slippage=slippage
        )
        
        # 记录交易
        self.trades.append(trade)
        
        # 更新持仓
        self._update_position(trade)
        
        self.logger.info(f"市价单成交: {trade}")
        return trade
    
    def _execute_limit_order(self, order: Order, price: float) -> Optional[Trade]:
        """
        执行限价单
        
        参数:
            order: 订单对象
            price: 当前价格
            
        返回:
            交易对象，如果未成交则返回None
        """
        if order.status != 'PENDING':
            return None
        
        # 检查是否满足限价条件
        if order.direction == 1:  # 买入
            if price > order.price:  # 当前价格高于限价，不成交
                return None
        else:  # 卖出
            if price < order.price:  # 当前价格低于限价，不成交
                return None
        
        # 计算滑点（限价单通常不考虑滑点，但这里为了模型完整性仍然计算）
        slippage = 0.0
        
        # 计算市场冲击
        market_impact = self._calculate_market_impact(price, order.quantity, order.direction)
        
        # 计算成交价格（限价单以限价成交）
        filled_price = order.price
        
        # 计算佣金
        commission = self._calculate_commission(filled_price, order.quantity)
        
        # 更新订单状态
        order.status = 'FILLED'
        order.filled_quantity = order.quantity
        order.filled_price = filled_price
        order.filled_time = datetime.now()
        order.commission = commission
        order.slippage = slippage
        
        # 创建交易记录
        trade = Trade(
            order=order,
            filled_price=filled_price,
            filled_quantity=order.quantity,
            timestamp=order.filled_time,
            commission=commission,
            slippage=slippage
        )
        
        # 记录交易
        self.trades.append(trade)
        
        # 更新持仓
        self._update_position(trade)
        
        self.logger.info(f"限价单成交: {trade}")
        return trade
    
    def _execute_stop_order(self, order: Order, price: float) -> Optional[Trade]:
        """
        执行止损单
        
        参数:
            order: 订单对象
            price: 当前价格
            
        返回:
            交易对象，如果未成交则返回None
        """
        if order.status != 'PENDING':
            return None
        
        # 检查是否触发止损条件
        if order.direction == 1:  # 买入
            if price < order.stop_price:  # 当前价格低于止损价，不触发
                return None
        else:  # 卖出
            if price > order.stop_price:  # 当前价格高于止损价，不触发
                return None
        
        # 止损单触发后转为市价单执行
        order.order_type = 'MARKET'
        return self._execute_market_order(order, price)
    
    def _execute_stop_limit_order(self, order: Order, price: float) -> Optional[Trade]:
        """
        执行止损限价单
        
        参数:
            order: 订单对象
            price: 当前价格
            
        返回:
            交易对象，如果未成交则返回None
        """
        if order.status != 'PENDING':
            return None
        
        # 检查是否触发止损条件
        if order.direction == 1:  # 买入
            if price < order.stop_price:  # 当前价格低于止损价，不触发
                return None
        else:  # 卖出
            if price > order.stop_price:  # 当前价格高于止损价，不触发
                return None
        
        # 止损限价单触发后转为限价单执行
        order.order_type = 'LIMIT'
        order.price = order.limit_price
        return self._execute_limit_order(order, price)
    
    def _update_position(self, trade: Trade):
        """
        更新持仓
        
        参数:
            trade: 交易对象
        """
        symbol = trade.symbol
        
        # 如果持仓不存在，创建新持仓
        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol)
        
        # 更新持仓
        self.positions[symbol].update(trade)
    
    def execute_orders(self, data: pd.DataFrame) -> List[Trade]:
        """
        执行所有待执行的订单
        
        参数:
            data: 行情数据，包含OHLCV数据
            
        返回:
            本次执行的交易列表
        """
        executed_trades = []
        
        # 获取当前价格（使用收盘价作为成交价格）
        price = data['close'].iloc[-1]
        
        # 执行止损单和止损限价单
        triggered_stop_orders = []
        for order in self.stop_orders:
            if order.order_type == 'STOP':
                trade = self._execute_stop_order(order, price)
                if trade:
                    executed_trades.append(trade)
                    triggered_stop_orders.append(order)
            elif order.order_type == 'STOP_LIMIT':
                trade = self._execute_stop_limit_order(order, price)
                if trade:
                    executed_trades.append(trade)
                    triggered_stop_orders.append(order)
        
        # 从止损单列表中移除已触发的订单
        for order in triggered_stop_orders:
            self.stop_orders.remove(order)
        
        # 执行市价单和限价单
        executed_orders = []
        for order in self.pending_orders:
            if order.order_type == 'MARKET':
                trade = self._execute_market_order(order, price)
                if trade:
                    executed_trades.append(trade)
                    executed_orders.append(order)
            elif order.order_type == 'LIMIT':
                trade = self._execute_limit_order(order, price)
                if trade:
                    executed_trades.append(trade)
                    executed_orders.append(order)
        
        # 从待执行订单列表中移除已执行的订单
        for order in executed_orders:
            self.pending_orders.remove(order)
        
        # 更新所有持仓的未实现盈亏
        for symbol, position in self.positions.items():
            if symbol in data['close'].index:
                position.update_unrealized_pnl(data.loc[symbol, 'close'])
        
        return executed_trades
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """
        获取指定交易标的的持仓
        
        参数:
            symbol: 交易标的代码
            
        返回:
            持仓对象，如果不存在则返回None
        """
        return self.positions.get(symbol)
    
    def get_positions(self) -> Dict[str, Position]:
        """
        获取所有持仓
        
        返回:
            持仓字典，键为交易标的代码
        """
        return self.positions
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """
        获取指定订单
        
        参数:
            order_id: 订单ID
            
        返回:
            订单对象，如果不存在则返回None
        """
        return self.orders.get(order_id)
    
    def get_orders(self) -> Dict[str, Order]:
        """
        获取所有订单
        
        返回:
            订单字典，键为订单ID
        """
        return self.orders
    
    def get_trades(self) -> List[Trade]:
        """
        获取所有交易
        
        返回:
            交易列表
        """
        return self.trades
    
    def get_pending_orders(self) -> List[Order]:
        """
        获取所有待执行的订单
        
        返回:
            待执行的订单列表
        """
        return self.pending_orders
    
    def get_stop_orders(self) -> List[Order]:
        """
        获取所有止损订单
        
        返回:
            止损订单列表
        """
        return self.stop_orders
    
    def get_portfolio_value(self) -> float:
        """
        获取投资组合价值
        
        返回:
            投资组合总价值
        """
        return sum(position.quantity * position.last_price for position in self.positions.values())
    
    def get_portfolio_pnl(self) -> Tuple[float, float]:
        """
        获取投资组合盈亏
        
        返回:
            (已实现盈亏, 未实现盈亏)的元组
        """
        realized_pnl = sum(position.realized_pnl for position in self.positions.values())
        unrealized_pnl = sum(position.unrealized_pnl for position in self.positions.values())
        return realized_pnl, unrealized_pnl