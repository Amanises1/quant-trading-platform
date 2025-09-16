import random
import datetime
from typing import List, Dict, Any, Optional
from .database_connection import db_conn
from .market_monitor import market_monitor
import logging
import random

class PositionManager:
    """持仓管理类，负责管理持仓信息"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # 初始化时向数据库插入一些模拟数据（如果表为空）
        self._init_sample_data()
        
    def _init_sample_data(self) -> None:
        """初始化样本数据（如果数据库中没有数据）"""
        # 检查是否已有数据
        existing_positions = self.get_positions()
        if not existing_positions:
            # 模拟持仓数据
            sample_positions = [
                {
                    'symbol': '600519',
                    'name': '贵州茅台',
                    'quantity': 100,
                    'avgPrice': 1680.00,
                    'currentPrice': 1725.50,
                    'accountId': 'A001',
                    'assetType': 'stock'
                },
                {
                    'symbol': '600036',
                    'name': '招商银行',
                    'quantity': 500,
                    'avgPrice': 35.20,
                    'currentPrice': 36.80,
                    'accountId': 'A001',
                    'assetType': 'stock'
                },
                {
                    'symbol': '000001',
                    'name': '平安银行',
                    'quantity': 1000,
                    'avgPrice': 12.50,
                    'currentPrice': 11.80,
                    'accountId': 'A001',
                    'assetType': 'stock'
                },
                {
                    'symbol': 'IF2312',
                    'name': '沪深300指数期货',
                    'quantity': 2,
                    'avgPrice': 3850.00,
                    'currentPrice': 3890.50,
                    'accountId': 'A002',
                    'assetType': 'futures'
                }
            ]
            
            # 插入样本数据
            for position in sample_positions:
                self.add_position(position)
            
            self.logger.info("已向数据库添加样本持仓数据")
    
    def get_positions(self, account_id: str = None, asset_type: str = None) -> List[Dict[str, Any]]:
        """从数据库获取持仓列表
        
        Args:
            account_id: 账户ID，可选
            asset_type: 资产类型，可选（stock、futures等）
        
        Returns:
            持仓列表
        """
        query = "SELECT * FROM positions WHERE 1=1"
        params = []
        
        if account_id:
            query += " AND account_id = %s"
            params.append(account_id)
        
        if asset_type:
            query += " AND asset_type = %s"
            params.append(asset_type)
        
        query += " ORDER BY symbol"
        
        results = db_conn.execute_query(query, tuple(params))
        
        # 转换字段名以保持与原有接口兼容
        if results:
            for result in results:
                # 将数据库字段名转换为驼峰命名
                result['avgPrice'] = result.pop('avg_price')
                result['currentPrice'] = result.pop('current_price')
                result['marketValue'] = result.pop('market_value')
                result['profit'] = result.pop('profit')
                result['profitRate'] = result.pop('profit_rate')
                result['entryDate'] = result.pop('entry_date').strftime('%Y-%m-%d')
                result['accountId'] = result.pop('account_id')
                result['assetType'] = result.pop('asset_type')
                
                # 删除不需要返回的字段
                for field in ['created_at', 'updated_at']:
                    if field in result:
                        del result[field]
        
        return results or []
    
    def get_position_by_id(self, position_id: int) -> Optional[Dict[str, Any]]:
        """根据ID从数据库获取单个持仓信息
        
        Args:
            position_id: 持仓ID
        
        Returns:
            持仓信息，如果未找到则返回None
        """
        query = "SELECT * FROM positions WHERE id = %s"
        result = db_conn.execute_query(query, (position_id,))
        
        if result and len(result) > 0:
            position = result[0]
            # 转换字段名以保持与原有接口兼容
            position['avgPrice'] = position.pop('avg_price')
            position['currentPrice'] = position.pop('current_price')
            position['marketValue'] = position.pop('market_value')
            position['profit'] = position.pop('profit')
            position['profitRate'] = position.pop('profit_rate')
            position['entryDate'] = position.pop('entry_date').strftime('%Y-%m-%d')
            position['accountId'] = position.pop('account_id')
            position['assetType'] = position.pop('asset_type')
            
            # 删除不需要返回的字段
            for field in ['created_at', 'updated_at']:
                if field in position:
                    del position[field]
            
            return position
        
        return None
    
    def update_position(self, position_id: int, updates: Dict[str, Any]) -> bool:
        """更新数据库中的持仓信息
        
        Args:
            position_id: 持仓ID
            updates: 需要更新的字段
        
        Returns:
            更新是否成功
        """
        # 先获取当前持仓
        current_position = self.get_position_by_id(position_id)
        if not current_position:
            return False
        
        # 转换驼峰命名为下划线命名
        db_data = {}
        for key, value in updates.items():
            if key == 'avgPrice':
                db_data['avg_price'] = value
            elif key == 'currentPrice':
                db_data['current_price'] = value
            elif key == 'marketValue':
                db_data['market_value'] = value
            elif key == 'profitRate':
                db_data['profit_rate'] = value
            elif key == 'entryDate':
                db_data['entry_date'] = value
            elif key == 'accountId':
                db_data['account_id'] = value
            elif key == 'assetType':
                db_data['asset_type'] = value
            else:
                db_data[key] = value
        
        # 准备更新字段和参数
        update_fields = []
        params = []
        
        for field, value in db_data.items():
            update_fields.append(f"{field} = %s")
            params.append(value)
        
        # 添加updated_at字段
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        
        # 添加position_id到参数列表末尾
        params.append(position_id)
        
        # 构建并执行更新语句
        query = f"UPDATE positions SET {', '.join(update_fields)} WHERE id = %s"
        
        result = db_conn.execute_query(query, tuple(params))
        
        return result is not None
    
    def add_position(self, position_data: Dict[str, Any]) -> Dict[str, Any]:
        """向数据库添加新持仓
        
        Args:
            position_data: 持仓数据
        
        Returns:
            添加后的持仓信息
        """
        # 计算市值和盈亏
        quantity = position_data.get('quantity', 0)
        avg_price = position_data.get('avgPrice', 0)
        current_price = position_data.get('currentPrice', avg_price)
        
        market_value = quantity * current_price
        profit = quantity * (current_price - avg_price)
        profit_rate = (current_price - avg_price) / avg_price * 100 if avg_price > 0 else 0
        
        # 准备插入数据库的数据
        query = """
        INSERT INTO positions (symbol, name, quantity, avg_price, current_price, market_value, profit, profit_rate, entry_date, account_id, asset_type)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        
        params = (
            position_data.get('symbol', ''),
            position_data.get('name', ''),
            quantity,
            avg_price,
            current_price,
            market_value,
            profit,
            profit_rate,
            position_data.get('entryDate', datetime.datetime.now().strftime('%Y-%m-%d')),
            position_data.get('accountId', ''),
            position_data.get('assetType', 'stock')
        )
        
        result = db_conn.execute_query(query, params)
        
        if result and len(result) > 0:
            position_id = result[0]['id']
            return self.get_position_by_id(position_id)
        
        raise Exception("添加持仓失败")
    
    def remove_position(self, position_id: int) -> bool:
        """从数据库中移除持仓
        
        Args:
            position_id: 持仓ID
        
        Returns:
            移除是否成功
        """
        query = "DELETE FROM positions WHERE id = %s"
        result = db_conn.execute_query(query, (position_id,))
        
        return result is not None
    
    def calculate_position_risk(self, position_id: int) -> Optional[Dict[str, Any]]:
        """计算持仓风险评估
        
        Args:
            position_id: 持仓ID
        
        Returns:
            风险评估结果
        """
        position = self.get_position_by_id(position_id)
        if not position:
            return None
        
        # 风险评估数据
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
        
        # 保存风险评估结果到数据库
        self._save_risk_assessment(risk_assessment)
        
        return risk_assessment
    
    def _save_risk_assessment(self, risk_assessment: Dict[str, Any]) -> None:
        """保存风险评估结果到数据库"""
        query = """
        INSERT INTO risk_assessments (position_id, symbol, max_potential_loss, risk_exposure, volatility, risk_level, risk_score)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (position_id) DO UPDATE
        SET max_potential_loss = EXCLUDED.max_potential_loss,
            risk_exposure = EXCLUDED.risk_exposure,
            volatility = EXCLUDED.volatility,
            risk_level = EXCLUDED.risk_level,
            risk_score = EXCLUDED.risk_score,
            updated_at = CURRENT_TIMESTAMP
        """
        
        params = (
            risk_assessment['positionId'],
            risk_assessment['symbol'],
            risk_assessment['maxPotentialLoss'],
            risk_assessment['riskExposure'],
            risk_assessment['volatility'],
            risk_assessment['riskLevel'],
            risk_assessment['riskScore']
        )
        
        db_conn.execute_query(query, params)
    
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
        positions = self.get_positions()
        
        for position in positions:
            # 随机生成价格变化
            change_percent = random.uniform(-1, 1)
            new_price = position['currentPrice'] * (1 + change_percent / 100)
            
            # 计算新的市值、盈亏和盈亏率
            new_quantity = position['quantity']
            new_market_value = new_quantity * new_price
            new_profit = new_quantity * (new_price - position['avgPrice'])
            new_profit_rate = round((new_price - position['avgPrice']) / position['avgPrice'] * 100, 2)
            
            # 更新数据库中的持仓数据
            self.update_position(position['id'], {
                'currentPrice': round(new_price, 2),
                'marketValue': new_market_value,
                'profit': new_profit,
                'profitRate': new_profit_rate
            })
            
            # 更新持仓对象
            position['currentPrice'] = round(new_price, 2)
            position['marketValue'] = new_market_value
            position['profit'] = new_profit
            position['profitRate'] = new_profit_rate

# 创建全局持仓管理器实例
position_manager = PositionManager()