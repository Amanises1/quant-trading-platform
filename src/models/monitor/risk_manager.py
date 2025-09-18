import datetime
from typing import List, Dict, Any, Optional
import datetime
import logging
from .database_connection import db_conn
from .position_manager import position_manager
from .execution_engine import execution_engine

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
        self.thresholds = default_risk_thresholds.copy()
        self.monitoring_enabled = True
        self.logger = logging.getLogger(__name__)
    
    def get_accounts(self) -> List[Dict[str, Any]]:
        """从数据库获取所有账户信息
        
        Returns:
            账户列表
        """
        query = "SELECT * FROM accounts"
        return db_conn.execute_query(query)
    
    def get_account_by_id(self, account_id: str) -> Dict[str, Any]:
        """根据ID从数据库获取账户信息
        
        Args:
            account_id: 账户ID
        
        Returns:
            账户信息
        """
        query = "SELECT * FROM accounts WHERE id = %s"
        result = db_conn.execute_query(query, (account_id,))
        return result[0] if result else None
    
    def update_account(self, account_id: str, updates: Dict[str, Any]) -> bool:
        """更新数据库中的账户信息
        
        Args:
            account_id: 账户ID
            updates: 需要更新的字段
        
        Returns:
            更新是否成功
        """
        try:
            # 构建UPDATE语句
            set_clauses = []
            params = []
            
            for key, value in updates.items():
                set_clauses.append(f"{key} = %s")
                params.append(value)
            
            params.append(account_id)  # 最后添加WHERE条件的参数
            
            query = f"UPDATE accounts SET {', '.join(set_clauses)}, updated_at = NOW() WHERE id = %s"
            db_conn.execute_query(query, tuple(params))
            return True
        except Exception as e:
            self.logger.error(f"更新账户信息失败: {e}")
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
        
        # 将风险报告保存到数据库
        self._save_risk_report_to_db(risk_report)
        
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
        total_market_value = sum(pos['market_value'] for pos in positions)
        
        # 计算持仓比例
        position_ratio = (total_market_value / account['equity']) * 100 if account['equity'] > 0 else 0
        
        # 计算最大单一持仓占比
        max_single_position_ratio = 0
        if positions and account['equity'] > 0:
            max_single_position = max(positions, key=lambda x: x['market_value'])
            max_single_position_ratio = (max_single_position['market_value'] / account['equity']) * 100
        
        # 计算总盈亏和盈亏率
        total_profit = sum(pos['unrealized_pnl'] for pos in positions)
        profit_rate = (total_profit / account['equity']) * 100 if account['equity'] > 0 else 0
        
        # 从数据库获取波动率数据
        # 这里简化处理，实际应用中应该从市场数据服务获取
        volatility = 15.0  # 默认波动率
        try:
            query = """
            SELECT AVG(volatility) as avg_volatility 
            FROM market_data 
            WHERE symbol IN %s 
            ORDER BY timestamp DESC 
            LIMIT 30
            """
            
            symbols = tuple(pos['symbol'] for pos in positions) if positions else ('',)
            result = db_conn.execute_query(query, (symbols,))
            
            if result and result[0]['avg_volatility'] is not None:
                volatility = result[0]['avg_volatility']
        except Exception as e:
            self.logger.error(f"获取波动率数据失败: {e}")
        
        # 获取账户最大回撤
        max_drawdown = account.get('max_drawdown', 0.0)
        
        risk_metrics = {
            'marginRatio': account['margin_used'] / account['equity'] * 100 if account['equity'] > 0 else 0,
            'positionRatio': position_ratio,
            'maxSinglePositionRatio': max_single_position_ratio,
            'volatility': volatility,
            'totalProfit': total_profit,
            'profitRate': profit_rate,
            'maxDrawdown': max_drawdown
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
        
        # 检查当日盈亏（从数据库获取）
        try:
            query = """
            SELECT SUM(realized_pnl) as daily_profit 
            FROM trade_history 
            WHERE account_id = %s AND date_trunc('day', created_at) = date_trunc('day', NOW())
            """
            result = db_conn.execute_query(query, (account['id'],))
            daily_profit = result[0]['daily_profit'] if result and result[0]['daily_profit'] is not None else 0
            
            if daily_profit < 0 and abs(daily_profit / account['equity'] * 100) > self.thresholds['maxDrawdownDaily']:
                alerts.append({
                    'type': 'daily_loss',
                    'level': 'danger',
                    'message': f'账户{account["name"]}今日亏损({daily_profit:.2f}元)超过单日最大回撤限制({self.thresholds["maxDrawdownDaily"]}%)',
                    'suggestion': '评估持仓风险，考虑止损措施'
                })
        except Exception as e:
            self.logger.error(f"获取当日盈亏数据失败: {e}")
        
        # 检查总体回撤
        if 'max_drawdown' in account and account['max_drawdown'] < -self.thresholds['maxDrawdownOverall']:
            alerts.append({
                'type': 'overall_drawdown',
                'level': 'danger',
                'message': f'账户{account["name"]}总体回撤({account["max_drawdown"]:.2f}%)超过限制({self.thresholds["maxDrawdownOverall"]}%)',
                'suggestion': '评估策略风险，考虑调整资产配置'
            })
        
        # 将风险预警保存到数据库
        for alert in alerts:
            self._save_alert_to_db(account['id'], alert)
        
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
        margin_ratio = account['margin_used'] / account['equity'] * 100 if account['equity'] > 0 else 0
        if margin_ratio < self.thresholds['marginLiquidation']:
            # 执行强制平仓
            closed_positions = self._force_liquidation(account_id)
            measures.append({
                'type': 'force_liquidation',
                'message': f'账户{account["name"]}保证金不足，已执行强制平仓',
                'closedPositions': closed_positions,
                'timestamp': datetime.datetime.now().timestamp()
            })
        
        # 检查是否需要暂停交易
        if 'max_drawdown' in account and account['max_drawdown'] < -self.thresholds['maxDrawdownOverall'] * 1.2:
            # 在实际应用中，这里应该有暂停交易的逻辑
            measures.append({
                'type': 'suspend_trading',
                'message': f'账户{account["name"]}回撤过大，已暂停交易权限',
                'timestamp': datetime.datetime.now().timestamp()
            })
        
        # 将风控措施记录到数据库
        for measure in measures:
            self._save_risk_measure_to_db(account_id, measure)
        
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
        positions.sort(key=lambda x: x['unrealized_pnl'], reverse=True)
        
        # 模拟平仓操作
        for position in positions:
            # 创建卖出订单
            order_data = {
                'symbol': position['symbol'],
                'name': position.get('name', position['symbol']),
                'side': 'sell',
                'order_type': 'market',
                'quantity': position['quantity'],
                'price': position['market_price'],
                'account_id': account_id,
                'asset_type': position.get('asset_type', 'stock')
            }
            
            # 提交订单
            try:
                order = execution_engine.submit_order(order_data)
                
                # 如果订单成功执行，记录平仓信息
                if order and order.get('status') == 'filled':
                    closed_positions.append({
                        'position_id': position.get('position_id', ''),
                        'symbol': position['symbol'],
                        'quantity': position['quantity'],
                        'price': position['market_price'],
                        'order_id': order.get('order_id', '')
                    })
            except Exception as e:
                self.logger.error(f"提交平仓订单失败: {e}")
        
        # 创建强制平仓通知
        try:
            from .alert_system import alert_system
            alert_system.add_alert({
                'type': 'risk',
                'level': 'danger',
                'title': '强制平仓通知',
                'message': f'账户{account_id}因保证金不足已执行强制平仓，共平仓{len(closed_positions)}个持仓',
                'account_id': account_id
            })
        except Exception as e:
            self.logger.error(f"创建强制平仓通知失败: {e}")
        
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
    
    def _save_risk_report_to_db(self, risk_report: Dict[str, Any]) -> None:
        """将风险报告保存到数据库"""
        try:
            query = """
            INSERT INTO risk_reports (account_id, risk_metrics, alerts, timestamp)
            VALUES (%s, %s, %s, %s)
            """
            
            params = (
                risk_report['accountId'],
                str(risk_report['riskMetrics']),
                str(risk_report['alerts']),
                risk_report['timestamp']
            )
            
            db_conn.execute_query(query, params)
        except Exception as e:
            self.logger.error(f"保存风险报告失败: {e}")
    
    def _save_alert_to_db(self, account_id: str, alert: Dict[str, Any]) -> None:
        """将风险预警保存到数据库"""
        try:
            query = """
            INSERT INTO risk_alerts (account_id, type, level, message, suggestion, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            params = (
                account_id,
                alert['type'],
                alert['level'],
                alert['message'],
                alert.get('suggestion', ''),
                datetime.datetime.now().timestamp()
            )
            
            db_conn.execute_query(query, params)
        except Exception as e:
            self.logger.error(f"保存风险预警失败: {e}")
    
    def _save_risk_measure_to_db(self, account_id: str, measure: Dict[str, Any]) -> None:
        """将风控措施记录到数据库"""
        try:
            query = """
            INSERT INTO risk_measures (account_id, type, message, closed_positions, timestamp)
            VALUES (%s, %s, %s, %s, %s)
            """
            
            params = (
                account_id,
                measure['type'],
                measure['message'],
                str(measure.get('closedPositions', [])),
                measure['timestamp']
            )
            
            db_conn.execute_query(query, params)
        except Exception as e:
            self.logger.error(f"保存风控措施记录失败: {e}")

# 创建全局风控管理器实例
risk_manager = RiskManager()