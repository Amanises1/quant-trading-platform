import sys
import os
import logging
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入必要的库
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd

# 导入数据库连接类
from src.models.visualization.db_connection import DatabaseConnection

# 尝试导入图表生成类（如果存在）
try:
    from src.models.visualization.chart_generator import ChartGenerator
    has_chart_generator = True
except ImportError:
    logger.warning("无法导入ChartGenerator类，将使用matplotlib直接生成图表")
    has_chart_generator = False

class ChartTest:
    """
    测试图表生成功能
    """
    
    def __init__(self):
        """初始化测试类"""
        self.db = DatabaseConnection()
        self.output_dir = "chart_outputs"
        
        # 创建输出目录
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def run_test(self):
        """运行完整的测试流程"""
        logger.info("开始测试图表生成功能")
        
        # 1. 测试数据库连接
        if not self.db.connect():
            logger.error("数据库连接失败，无法继续测试")
            return False
        
        try:
            # 2. 获取支持的图表类型
            supported_charts = self.db.get_supported_chart_types()
            logger.info(f"支持的图表类型: {supported_charts}")
            
            # 3. 获取可用的股票列表
            stocks = self.db.get_available_stocks(limit=10)
            if not stocks:
                logger.error("没有找到可用的股票数据")
                return False
            
            logger.info(f"找到 {len(stocks)} 只可用股票: {stocks}")
            
            # 4. 选择一只股票获取数据（尝试前3只股票）
            selected_stock = None
            stock_data = None
            
            for i, stock in enumerate(stocks[:3]):  # 尝试前3只股票
                logger.info(f"尝试获取股票: {stock} 的数据")
                
                # 设置日期范围（过去30天）
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                
                # 5. 获取股票数据
                data = self.db.get_stock_data(stock, start_date, end_date)
                
                if data is not None and not data.empty:
                    selected_stock = stock
                    stock_data = data
                    logger.info(f"成功获取股票 {selected_stock} 的数据，共 {len(stock_data)} 条记录")
                    logger.info(f"数据示例:\n{stock_data.head(5)}")
                    break
                else:
                    logger.warning(f"没有获取到股票 {stock} 的数据，尝试下一只")
            
            if stock_data is None:
                logger.error("尝试的所有股票都没有获取到数据")
                return False
            
            # 6. 生成图表
            self._generate_charts(selected_stock, stock_data)
            
            logger.info("图表生成测试完成")
            return True
        except Exception as e:
            logger.error(f"测试过程中发生错误: {e}")
            return False
        finally:
            # 关闭数据库连接
            self.db.disconnect()
    
    def _generate_charts(self, stock_name: str, data):
        """
        生成支持的各种图表
        
        参数:
            stock_name: 股票名称
            data: 股票数据DataFrame
        """
        # 确保data是DataFrame格式
        if not isinstance(data, pd.DataFrame):
            logger.error("数据格式错误，需要DataFrame类型")
            return
        
        # 检查数据是否为空
        if data.empty:
            logger.error("数据为空，无法生成图表")
            return
        
        logger.info(f"开始为股票 {stock_name} 生成图表")
        
        # 确保date列是索引或转换为索引
        if 'date' in data.columns and not isinstance(data.index, pd.DatetimeIndex):
            data = data.copy()
            data['date'] = pd.to_datetime(data['date'])
            data.set_index('date', inplace=True)
        
        # 确保数值列的数据类型正确
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')
        
        # 生成价格走势图
        try:
            plt.figure(figsize=(12, 6))
            plt.plot(data.index, data['close'], label='收盘价')
            plt.title(f'{stock_name} 价格走势')
            plt.xlabel('日期')
            plt.ylabel('价格')
            plt.grid(True)
            plt.legend()
            price_chart_path = os.path.join(self.output_dir, f"{stock_name}_price_chart.png")
            plt.savefig(price_chart_path)
            plt.close()
            logger.info(f"价格走势图已保存到: {price_chart_path}")
        except Exception as e:
            logger.error(f"生成价格走势图失败: {e}")
        
        # 生成K线图（如果有mplfinance）
        try:
            if all(col in data.columns for col in ['open', 'high', 'low', 'close']):
                mpf.plot(data, type='candle', style='yahoo', title=f'{stock_name} K线图', 
                         savefig=os.path.join(self.output_dir, f"{stock_name}_candlestick_chart.png"))
                logger.info(f"K线图已保存到: {stock_name}_candlestick_chart.png")
        except Exception as e:
            logger.error(f"生成K线图失败: {e}")
        
        # 生成成交量图
        try:
            if 'volume' in data.columns:
                plt.figure(figsize=(12, 4))
                plt.bar(data.index, data['volume'], label='成交量')
                plt.title(f'{stock_name} 成交量')
                plt.xlabel('日期')
                plt.ylabel('成交量')
                plt.grid(True)
                volume_chart_path = os.path.join(self.output_dir, f"{stock_name}_volume_chart.png")
                plt.savefig(volume_chart_path)
                plt.close()
                logger.info(f"成交量图已保存到: {volume_chart_path}")
        except Exception as e:
            logger.error(f"生成成交量图失败: {e}")

if __name__ == "__main__":
    # 如果缺少pandas，尝试导入或安装
    try:
        import pandas as pd
    except ImportError:
        logger.error("请安装pandas: pip install pandas")
        sys.exit(1)
    
    # 运行测试
    test = ChartTest()
    test.run_test()