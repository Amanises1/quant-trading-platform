# 量化交易策略回测模块

本目录包含量化交易平台的策略回测模块，提供了完整的交易策略开发、回测和评估功能。

## 模块结构

```
backtest/
├── __init__.py             # 模块初始化文件
├── backtest_engine.py      # 回测引擎实现
├── performance_metrics.py  # 绩效指标计算
├── risk_manager.py         # 风险管理器
├── strategy_evaluator.py   # 策略评估器
├── trade_executor.py       # 交易执行器
├── strategy_base.py        # 策略基类
├── strategy_demo.py        # 策略演示示例
├── strategies/             # 策略实现目录
│   ├── sma_strategy.py     # 移动平均线交叉策略
│   ├── rsi_strategy.py     # RSI策略
│   ├── mean_reversion_strategy.py  # 均值回归策略
│   └── macd_strategy.py    # MACD策略
└── README.md               # 本说明文件
```

## 核心组件

### 1. 策略基类 (`strategy_base.py`)

提供了所有策略的基础接口和常用技术指标计算方法。策略开发者可以通过继承`BaseStrategy`类来创建自定义策略。

主要功能：
- 定义策略接口（`generate_signals`, `on_bar`等方法）
- 提供常用技术指标计算（SMA, EMA, RSI, 布林带, MACD, ATR, OBV等）

### 2. 回测引擎 (`backtest_engine.py`)

负责整个回测流程的执行，包括数据输入、策略信号生成、交易执行和结果记录。

主要功能：
- 支持多种参数配置（初始资金、佣金率、滑点、仓位大小等）
- 执行策略回测并生成详细的交易记录
- 计算资产净值曲线

### 3. 绩效指标 (`performance_metrics.py`)

计算各种绩效评估指标，用于衡量策略的表现。

主要指标：
- 总收益率
- 年化收益率
- 夏普比率
- 最大回撤
- 胜率
- 盈亏比
- 索提诺比率
- 卡玛比率

### 4. 预定义策略 (`strategies/`)

提供了几种常用的交易策略实现：

- **移动平均线交叉策略 (`sma_strategy.py`)**: 当短期均线上穿长期均线时买入，下穿时卖出。
- **RSI策略 (`rsi_strategy.py`)**: 当RSI低于超卖阈值时买入，高于超买阈值时卖出。
- **均值回归策略 (`mean_reversion_strategy.py`)**: 基于统计均值回归理论，价格偏离均值一定程度时进行反向交易。
- **MACD策略 (`macd_strategy.py`)**: 当MACD线上穿信号线时买入，下穿时卖出。

## 使用方法

### 1. 创建策略实例

```python
from models.backtest.strategies.sma_strategy import SimpleMovingAverageStrategy

# 创建移动平均线交叉策略实例，可以指定参数
sma_strategy = SimpleMovingAverageStrategy({
    'short_window': 5,  # 短期均线窗口
    'long_window': 20   # 长期均线窗口
})
```

### 2. 准备数据

回测模块支持标准的OHLCV格式数据（开盘价、最高价、最低价、收盘价、成交量）。

```python
import pandas as pd

# 从CSV文件加载数据
data = pd.read_csv('path/to/data.csv', index_col='date', parse_dates=True)

# 或者使用演示模块生成的示例数据
from models.backtest.strategy_demo import StrategyDemo
data = StrategyDemo.generate_sample_data()
```

### 3. 运行回测

```python
from models.backtest.backtest_engine import BacktestEngine

# 创建回测引擎实例
backtest_engine = BacktestEngine()

# 运行回测
results = backtest_engine.run(
    data=data,                  # 价格数据
    strategy=sma_strategy,      # 交易策略
    initial_capital=100000,     # 初始资金
    commission_rate=0.001,      # 佣金率
    slippage=0.0005,            # 滑点
    position_size=100           # 每笔交易的仓位大小
)
```

### 4. 评估策略表现

```python
from models.backtest.performance_metrics import PerformanceMetrics

# 计算绩效指标
performance_metrics = PerformanceMetrics(results)
metrics = performance_metrics.get_metrics()

# 打印绩效指标
for key, value in metrics.items():
    print(f"{key}: {value}")
```

### 5. 可视化回测结果

```python
from models.backtest.strategy_demo import StrategyDemo

# 可视化回测结果
StrategyDemo.plot_results(results)
```

## 策略比较

回测模块支持多种策略的比较分析：

```python
from models.backtest.strategy_demo import StrategyDemo

# 运行策略比较
all_results, all_metrics = StrategyDemo.run_strategy_comparison()

# 可视化比较结果
StrategyDemo.plot_strategy_comparison(all_results, all_metrics)
```

## 运行演示

可以直接运行演示文件来查看各种策略的回测结果：

```bash
python -m models.backtest.strategy_demo
```

## 创建自定义策略

要创建自定义策略，可以继承`BaseStrategy`类并实现必要的方法：

```python
from models.backtest.strategy_base import BaseStrategy

class MyCustomStrategy(BaseStrategy):
    def __init__(self, params=None):
        # 设置默认参数
        default_params = {'param1': value1, 'param2': value2}
        if params:
            default_params.update(params)
        super().__init__(default_params)
    
    def generate_signals(self, data):
        # 实现信号生成逻辑
        # ...
        return data
    
    def on_bar(self, data):
        # 实现单根K线的信号生成逻辑
        # ...
        return signal  # 1=买入, -1=卖出, 0=持有
```

## 注意事项

1. 回测结果仅供参考，不代表未来实际交易表现
2. 不同市场环境下策略表现可能有显著差异
3. 建议在实盘前进行充分的参数优化和压力测试
4. 可以结合风险管理器来控制单笔交易风险和整体仓位风险

## 相关资源

- 查看`strategy_demo.py`文件了解完整的使用示例
- 阅读各策略文件了解具体的策略实现细节