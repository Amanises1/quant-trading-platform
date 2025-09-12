# 风控管理模块
import random
import datetime
from typing import List, Dict, Any, Optional
from .position_manager import position_manager
from .execution_engine import execution_engine

# 模拟账户数据
simulated_accounts = [
    {
        'id': 'A001',
        'name': '股票账户',
        'balance': 500000.00,
        'equity': 700000.00,
        'margin': 100000.00,
        'marginRatio': 170.00,
        'maxDrawdown': -8.50,
        'dailyProfit': 2500.00,
        'riskLevel': 'medium'
    },
    {
        'id': 'A002',
        'name': '期货账户',
        'balance': 300000.00,
        'equity': 350000.00,
        'margin': 150000.00,
        'marginRatio': 140.00,
        'maxDrawdown': -12.30,
        'dailyProfit': -1200.00,
        'riskLevel': 'high'
    }
]

# 风控阈值配置
default_risk_thresholds = {
    'marginWarning': 130.0,  # 保证金比例预警线
    'marginLiquidation': 100.0,  # 保证金比例强平线
    'positionLimit': 90.0,  # 持仓比例上限
    'maxDrawdownDaily': 5.0,  # 单日最大回撤
    'maxDrawdownOverall': 20.0,  # 总体最大回撤
    'singlePositionLimit': 30.0,  # 单一持仓占比上限
    'volatilityThreshold': 15.0  # 波动率预警阈值
}

class RiskManager:
    """风控管理类，负责监控风险并执行风控措施"""
    
    def __init__(self):
        self.accounts = simulated_accounts.copy()
        self.thresholds = default_risk_thresholds.copy()
        self.monitoring_enabled = True
    
    def get_accounts(self) -> List[Dict[str, Any]]:
        """获取所有账户信息
        
        Returns:
            账户列表
        """
        return self.accounts
    
    def get_account_by_id(self, account_id: str) -> Dict[str, Any]:
        """根据ID获取账户信息
        
        Args:
            account_id: 账户ID
        
        Returns:
            账户信息
        """
        for account in self.accounts:
            if account['id'] == account_id:
                return account
        return None
    
    def update_account(self, account_id: str, updates: Dict[str, Any]) -> bool:
        """更新账户信息
        
        Args:
            account_id: 账户ID
            updates: 需要更新的字段
        
        Returns:
            更新是否成功
        """
        for account in self.accounts:
            if account['id'] == account_id:
                account.update(updates)
                return True
        return False
    
    def get_risk_thresholds(self) -> Dict[str, Any]:
        """获取风控阈值配置
        
        Returns:
            风控阈值配置
        """
        return self.thresholds
    
    def set_risk_thresholds(self, new_thresholds: Dict[str, Any]) -> Dict[str, Any]:
        """设置风控阈值配置
        
        Args:
            new_thresholds: 新的风控阈值配置
        
        Returns:
            更新后的风控阈值配置
        """
        self.thresholds.update(new_thresholds)
        return self.thresholds
    
    def monitor_account_risk(self, account_id: str) -> Dict[str, Any]:
        """监控账户风险
        
        Args:
            account_id: 账户ID
        
        Returns:
            风险监控结果
        """
        account = self.get_account_by_id(account_id)
        if not account:
            return None
        
        # 获取该账户的持仓
        positions = position_manager.get_positions(account_id=account_id)
        
        # 计算风险指标
        risk_metrics = self._calculate_risk_metrics(account, positions)
        
        # 检查风险预警
        alerts = self._check_risk_alerts(account, risk_metrics)
        
        # 生成风险报告
        risk_report = {
            'accountId': account_id,
            'riskMetrics': risk_metrics,
            'alerts': alerts,
            'timestamp': datetime.datetime.now().timestamp()
        }
        
        return risk_report
    
    def _calculate_risk_metrics(self, account: Dict[str, Any], positions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算风险指标
        
        Args:
            account: 账户信息
            positions: 持仓列表
        
        Returns:
            风险指标
        """
        # 计算总市值
        total_market_value = sum(pos['marketValue'] for pos in positions)
        
        # 计算持仓比例
        position_ratio = (total_market_value / account['equity']) * 100 if account['equity'] > 0 else 0
        
        # 计算最大单一持仓占比
        max_single_position_ratio = 0
        if positions and account['equity'] > 0:
            max_single_position = max(positions, key=lambda x: x['marketValue'])
            max_single_position_ratio = (max_single_position['marketValue'] / account['equity']) * 100
        
        # 计算总盈亏和盈亏率
        total_profit = sum(pos['profit'] for pos in positions)
        profit_rate = (total_profit / account['equity']) * 100 if account['equity'] > 0 else 0
        
        # 模拟波动率计算
        volatility = random.uniform(8, 20)
        
        risk_metrics = {
            'marginRatio': account['marginRatio'],
            'positionRatio': position_ratio,
            'maxSinglePositionRatio': max_single_position_ratio,
            'volatility': volatility,
            'totalProfit': total_profit,
            'profitRate': profit_rate,
            'maxDrawdown': account['maxDrawdown']
        }
        
        return risk_metrics
    
    def _check_risk_alerts(self, account: Dict[str, Any], risk_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检查风险预警
        
        Args:
            account: 账户信息
            risk_metrics: 风险指标
        
        Returns:
            风险预警列表
        """
        alerts = []
        
        # 检查保证金比例
        if risk_metrics['marginRatio'] < self.thresholds['marginWarning']:
            alert_level = 'warning' if risk_metrics['marginRatio'] >= self.thresholds['marginLiquidation'] else 'danger'
            alerts.append({
                'type': 'margin_ratio',
                'level': alert_level,
                'message': f'账户{account["name"]}保证金比例({risk_metrics["marginRatio"]:.2f}%)低于预警线({self.thresholds["marginWarning"]}%)',
                'suggestion': '请及时补充保证金'
            })
        
        # 检查持仓比例
        if risk_metrics['positionRatio'] > self.thresholds['positionLimit']:
            alerts.append({
                'type': 'position_ratio',
                'level': 'warning',
                'message': f'账户{account["name"]}持仓比例({risk_metrics["positionRatio"]:.2f}%)超过上限({self.thresholds["positionLimit"]}%)',
                'suggestion': '考虑降低仓位，控制风险'
            })
        
        # 检查单一持仓占比
        if risk_metrics['maxSinglePositionRatio'] > self.thresholds['singlePositionLimit']:
            alerts.append({
                'type': 'single_position_ratio',
                'level': 'warning',
                'message': f'账户{account["name"]}单一持仓占比({risk_metrics["maxSinglePositionRatio"]:.2f}%)超过上限({self.thresholds["singlePositionLimit"]}%)',
                'suggestion': '考虑分散投资，降低集中度风险'
            })
        
        # 检查波动率
        if risk_metrics['volatility'] > self.thresholds['volatilityThreshold']:
            alerts.append({
                'type': 'volatility',
                'level': 'warning',
                'message': f'账户{account["name"]}组合波动率({risk_metrics["volatility"]:.2f}%)较高',
                'suggestion': '注意市场波动风险'
            })
        
        # 检查当日盈亏
        if account['dailyProfit'] < 0 and abs(account['dailyProfit'] / account['equity'] * 100) > self.thresholds['maxDrawdownDaily']:
            alerts.append({
                'type': 'daily_loss',
                'level': 'danger',
                'message': f'账户{account["name"]}今日亏损({account["dailyProfit"]:.2f}元)超过单日最大回撤限制({self.thresholds["maxDrawdownDaily"]}%)',
                'suggestion': '评估持仓风险，考虑止损措施'
            })
        
        # 检查总体回撤
        if account['maxDrawdown'] < -self.thresholds['maxDrawdownOverall']:
            alerts.append({
                'type': 'overall_drawdown',
                'level': 'danger',
                'message': f'账户{account["name"]}总体回撤({account["maxDrawdown"]:.2f}%)超过限制({self.thresholds["maxDrawdownOverall"]}%)',
                'suggestion': '评估策略风险，考虑调整资产配置'
            })
        
        return alerts
    
    def execute_risk_measures(self, account_id: str) -> List[Dict[str, Any]]:
        """执行风控措施
        
        Args:
            account_id: 账户ID
        
        Returns:
            执行的风控措施列表
        """
        if not self.monitoring_enabled:
            return []
        
        account = self.get_account_by_id(account_id)
        if not account:
            return []
        
        measures = []
        
        # 检查是否需要强制平仓
        if account['marginRatio'] < self.thresholds['marginLiquidation']:
            # 执行强制平仓
            closed_positions = self._force_liquidation(account_id)
            measures.append({
                'type': 'force_liquidation',
                'message': f'账户{account["name"]}保证金不足，已执行强制平仓',
                'closedPositions': closed_positions,
                'timestamp': datetime.datetime.now().timestamp()
            })
        
        # 检查是否需要暂停交易
        if account['maxDrawdown'] < -self.thresholds['maxDrawdownOverall'] * 1.2:
            # 在实际应用中，这里应该有暂停交易的逻辑
            measures.append({
                'type': 'suspend_trading',
                'message': f'账户{account["name"]}回撤过大，已暂停交易权限',
                'timestamp': datetime.datetime.now().timestamp()
            })
        
        return measures
    
    def _force_liquidation(self, account_id: str) -> List[Dict[str, Any]]:
        """执行强制平仓
        
        Args:
            account_id: 账户ID
        
        Returns:
            平仓的持仓列表
        """
        positions = position_manager.get_positions(account_id=account_id)
        closed_positions = []
        
        # 按亏损程度排序，优先平仓亏损最多的持仓
        positions.sort(key=lambda x: x['profit'], reverse=True)
        
        # 模拟平仓操作
        for position in positions:
            # 创建卖出订单
            order_data = {
                'symbol': position['symbol'],
                'name': position['name'],
                'type': 'sell',
                'orderType': 'market',
                'quantity': position['quantity'],
                'price': position['currentPrice'],
                'accountId': account_id,
                'assetType': position['assetType']
            }
            
            # 提交订单
            order = execution_engine.submit_order(order_data)
            
            # 如果订单成功执行，记录平仓信息
            if order['status'] == 'filled':
                closed_positions.append({
                    'positionId': position['id'],
                    'symbol': position['symbol'],
                    'quantity': position['quantity'],
                    'price': position['currentPrice'],
                    'orderId': order['id']
                })
        
        # 创建强制平仓通知
        alert_system.add_alert({
            'type': 'risk',
            'level': 'danger',
            'title': '强制平仓通知',
            'message': f'账户{account_id}因保证金不足已执行强制平仓，共平仓{len(closed_positions)}个持仓',
            'accountId': account_id
        })
        
        return closed_positions
    
    def toggle_monitoring(self, enable: bool) -> bool:
        """开启或关闭风控监控
        
        Args:
            enable: 是否开启
        
        Returns:
            当前监控状态
        """
        self.monitoring_enabled = enable
        return self.monitoring_enabled

# 创建全局风控管理器实例
risk_manager = RiskManager()