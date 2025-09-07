# 持仓管理模块
import random
import datetime
from typing import List, Dict, Any

# 模拟持仓数据
simulated_positions = [
    {
        'id': 1,
        'symbol': '600519',
        'name': '贵州茅台',
        'quantity': 100,
        'avgPrice': 1680.00,
        'currentPrice': 1725.50,
        'marketValue': 172550.00,
        'profit': 4550.00,
        'profitRate': 2.71,
        'entryDate': '2023-11-15',
        'accountId': 'A001',
        'assetType': 'stock'
    },
    {
        'id': 2,
        'symbol': '600036',
        'name': '招商银行',
        'quantity': 500,
        'avgPrice': 35.20,
        'currentPrice': 36.80,
        'marketValue': 18400.00,
        'profit': 800.00,
        'profitRate': 4.55,
        'entryDate': '2023-11-10',
        'accountId': 'A001',
        'assetType': 'stock'
    },
    {
        'id': 3,
        'symbol': '000001',
        'name': '平安银行',
        'quantity': 1000,
        'avgPrice': 12.50,
        'currentPrice': 11.80,
        'marketValue': 11800.00,
        'profit': -700.00,
        'profitRate': -5.60,
        'entryDate': '2023-11-05',
        'accountId': 'A001',
        'assetType': 'stock'
    },
    {
        'id': 4,
        'symbol': 'IF2312',
        'name': '沪深300指数期货',
        'quantity': 2,
        'avgPrice': 3850.00,
        'currentPrice': 3890.50,
        'marketValue': 233430.00,
        'profit': 2430.00,
        'profitRate': 1.05,
        'entryDate': '2023-11-20',
        'accountId': 'A002',
        'assetType': 'futures'
    }
]

# 持仓ID计数器
next_position_id = 5

class PositionManager:
    """持仓管理类，负责管理持仓信息"""
    
    def __init__(self):
        self.positions = simulated_positions.copy()
        
    def get_positions(self, account_id: str = None, asset_type: str = None) -> List[Dict[str, Any]]:
        """获取持仓列表
        
        Args:
            account_id: 账户ID，可选
            asset_type: 资产类型，可选（stock、futures等）
        
        Returns:
            持仓列表
        """
        filtered_positions = self.positions.copy()
        
        # 按账户ID过滤
        if account_id:
            filtered_positions = [pos for pos in filtered_positions if pos['accountId'] == account_id]
        
        # 按资产类型过滤
        if asset_type:
            filtered_positions = [pos for pos in filtered_positions if pos['assetType'] == asset_type]
        
        return filtered_positions
    
    def get_position_by_id(self, position_id: int) -> Dict[str, Any]:
        """根据ID获取单个持仓信息
        
        Args:
            position_id: 持仓ID
        
        Returns:
            持仓信息
        """
        for position in self.positions:
            if position['id'] == position_id:
                return position
        return None
    
    def update_position(self, position_id: int, updates: Dict[str, Any]) -> bool:
        """更新持仓信息
        
        Args:
            position_id: 持仓ID
            updates: 需要更新的字段
        
        Returns:
            更新是否成功
        """
        for position in self.positions:
            if position['id'] == position_id:
                position.update(updates)
                # 重新计算市值和盈亏
                if 'currentPrice' in updates or 'quantity' in updates:
                    position['marketValue'] = position['quantity'] * position['currentPrice']
                    position['profit'] = position['quantity'] * (position['currentPrice'] - position['avgPrice'])
                    position['profitRate'] = (position['currentPrice'] - position['avgPrice']) / position['avgPrice'] * 100
                return True
        return False
    
    def add_position(self, position_data: Dict[str, Any]) -> Dict[str, Any]:
        """添加新持仓
        
        Args:
            position_data: 持仓数据
        
        Returns:
            添加后的持仓信息
        """
        global next_position_id
        
        # 计算市值和盈亏
        quantity = position_data.get('quantity', 0)
        avg_price = position_data.get('avgPrice', 0)
        current_price = position_data.get('currentPrice', avg_price)
        
        position = {
            'id': next_position_id,
            'symbol': position_data.get('symbol', ''),
            'name': position_data.get('name', ''),
            'quantity': quantity,
            'avgPrice': avg_price,
            'currentPrice': current_price,
            'marketValue': quantity * current_price,
            'profit': quantity * (current_price - avg_price),
            'profitRate': (current_price - avg_price) / avg_price * 100 if avg_price > 0 else 0,
            'entryDate': position_data.get('entryDate', datetime.datetime.now().strftime('%Y-%m-%d')),
            'accountId': position_data.get('accountId', ''),
            'assetType': position_data.get('assetType', 'stock')
        }
        
        self.positions.append(position)
        next_position_id += 1
        return position
    
    def remove_position(self, position_id: int) -> bool:
        """移除持仓
        
        Args:
            position_id: 持仓ID
        
        Returns:
            移除是否成功
        """
        for i, position in enumerate(self.positions):
            if position['id'] == position_id:
                self.positions.pop(i)
                return True
        return False
    
    def calculate_position_risk(self, position_id: int) -> Dict[str, Any]:
        """计算持仓风险评估
        
        Args:
            position_id: 持仓ID
        
        Returns:
            风险评估结果
        """
        position = self.get_position_by_id(position_id)
        if not position:
            return None
        
        # 模拟风险评估数据
        risk_assessment = {
            'positionId': position_id,
            'symbol': position['symbol'],
            'maxPotentialLoss': abs(position['profit']) * random.uniform(0.5, 2),
            'riskExposure': position['marketValue'] * random.uniform(0.8, 1.2),
            'volatility': random.uniform(5, 20),
            'riskLevel': self._determine_risk_level(position),
            'riskScore': random.randint(1, 10),
            'suggestions': self._generate_risk_suggestions(position)
        }
        
        return risk_assessment
    
    def _determine_risk_level(self, position: Dict[str, Any]) -> str:
        """确定风险等级"""
        profit_rate_abs = abs(position['profitRate'])
        
        if profit_rate_abs > 10 or position['marketValue'] > 100000:
            return '高风险'
        elif profit_rate_abs > 5 or position['marketValue'] > 50000:
            return '中风险'
        else:
            return '低风险'
    
    def _generate_risk_suggestions(self, position: Dict[str, Any]) -> List[str]:
        """生成风险建议"""
        suggestions = []
        
        if position['profitRate'] > 10:
            suggestions.append('考虑部分止盈，锁定利润')
        elif position['profitRate'] < -5:
            suggestions.append('评估是否需要止损')
        
        if position['marketValue'] > 100000:
            suggestions.append('持仓集中度较高，考虑分散投资')
        
        if not suggestions:
            suggestions.append('当前持仓风险可控，继续观察')
        
        return suggestions
    
    def update_positions_market_data(self):
        """更新所有持仓的市场数据（模拟实时更新）"""
        for position in self.positions:
            # 随机生成价格变化
            change_percent = random.uniform(-1, 1)
            new_price = position['currentPrice'] * (1 + change_percent / 100)
            
            # 更新持仓数据
            position['currentPrice'] = round(new_price, 2)
            position['marketValue'] = position['quantity'] * position['currentPrice']
            position['profit'] = position['quantity'] * (position['currentPrice'] - position['avgPrice'])
            position['profitRate'] = round((position['currentPrice'] - position['avgPrice']) / position['avgPrice'] * 100, 2)

# 创建全局持仓管理器实例
position_manager = PositionManager()