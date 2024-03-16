import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["SimHei"]

from datetime import datetime

from enum import Enum
from tool import get_ma, get_year, get_sharpe_ratio, get_max_drawdown, best_ma_period
from trade import Trade

# 设置回测的一些基础参数
class CFG(Enum):
    # 设置交易佣金费率，开仓平仓时都收取佣金
    COMMISSION_RATIO = 0.0003

    # 设置印花税税率，只有平仓时收取
    CLOSE_TAX_RATIO = 0.001

    # 设置初始资金为一百万
    TOTAL_ASSET = 1000000

    # 设置交易起始时间
    BEGIN_DATE = '2012-01-04'

    # 设置交易终止时间
    END_DATE = '2022-12-30'

# 所有股票名称（本研究中只有平安银行一只股票）
instruments = ['平安银行']

# 初始化交易类
Trade = Trade(instruments, CFG.COMMISSION_RATIO.value, CFG.CLOSE_TAX_RATIO.value, CFG.TOTAL_ASSET.value)

# 获取平安银行数据，以便计算每一年的最佳均线
# 获取股票数据
data = pd.read_csv('data-set/instruments/平安银行.csv',encoding= 'gb18030')
print(data)

# 获取真实收盘价与前复权收盘价,便于后面进行比对
close_adjust = data['close_adjust'].values

#
# 计算均线，先定下均线范围，之后获取每一天的均线
ma_range=range(120,241)
day_ma = get_ma(close_adjust, ma_range)

# 获取原数据中每一年的第一天与最后一天
year_all = get_year(data['date'])
print(year_all)

# 1.计算每一年的最佳长期均线，采取滑动窗口方式，使用过去20年的数据来预测当年的最佳均线
# 存储每年的最佳均线
best_ma_all = {}

# 循环所有年获取每一年的最佳均线
for year in year_all.keys():
    # 因为用过去20年的数据来获取当年最佳均线，而数据是从1992年开始，所以从2012年开始获取每年的最佳均线
    if int(year) < 2012:
        continue

    # 获取过去20年的开始日与结束日
    start_day = year_all[str(int(year)-20)]['first_day']
    end_day = year_all[str(int(year)-1)]['last_day']

    # 获取每一年的最佳均线,day_ma中是要获取的均线范围
    sum_result = best_ma_period(data, day_ma, ma_range, start_day, end_day, CFG.TOTAL_ASSET.value, CFG.TOTAL_ASSET.value, CFG.COMMISSION_RATIO.value, CFG.CLOSE_TAX_RATIO.value)
    imax = sum_result['netAsset'].idxmax()
    best_ma = sum_result.iloc[imax, 0]
    print(year + "年最好均线是：", best_ma)
    best_ma_all[year] = best_ma

# 输出每年的最好均线
df_best_ma_all = pd.DataFrame(list(dict.items(best_ma_all)))
df_best_ma_all.to_csv('out/best_ma_annual.csv',index = False)

# 读取每年最好的均线
df_best_ma_all = pd.read_csv('out/best_ma_annual.csv')
df_best_ma_all.rename(columns={'0': 'year', '1' : 'best_ma'}, inplace=True)

# 2.遍历测试集的每年根据前面计算的每年最好均线进行回测
for year in df_best_ma_all['year']:
    # 获取储存的每年最佳均线
    best_ma = df_best_ma_all[df_best_ma_all['year'] == year]['best_ma'].values

    # 根据最佳均线获取每日的均线值
    day_ma = get_ma(close_adjust, best_ma)

    # 对于当前年进行回测
    Trade.trade_strategy_period(year_all[str(year)]['first_day'], year_all[str(year)]['last_day'],day_ma)

# 输出所有交易记录
Trade.trade_records.to_csv('out/trade_records.csv', encoding="utf_8_sig", index=False)

# 输出每日交易情况
Trade.time_records.to_csv('out/time_records.csv', encoding="utf_8_sig", index=False)

# 3.统计交易情况
# 读取每日交易情况
time_records = pd.read_csv('out/time_records.csv')

# 转化起始日与最终日日期
date_format = "%Y-%m-%d"
begin_day = datetime.strptime(CFG.BEGIN_DATE.value, date_format)
end_day = datetime.strptime(CFG.END_DATE.value, date_format)

# 获取沪深300做为基准
benchmark_data = pd.read_csv('data-set/instruments/沪深300.csv')

# 截取数据与回测区间对应
benchmark_data['date'] = pd.to_datetime(benchmark_data['date'])
benchmark_data = benchmark_data[(benchmark_data['date'] >= begin_day) & (benchmark_data['date'] <= end_day)]

# 用来存储每年的收益情况
years_return = {}
years_return_list = []

#计算每年的收益率
for year in df_best_ma_all['year']:
    # 获取每年的第一天与最后一天
    first_day = year_all[str(year)]['first_day']
    last_day = year_all[str(year)]['last_day']

    # 每年第一天的总资产
    first_day_asset = time_records.loc[time_records['time'] == first_day,'total_asset'].values[0]
    # 每年最后一天的总资产
    last_day_asset = time_records.loc[time_records['time'] == last_day,'total_asset'].values[0]

    # 计算每年的收益率
    year_return = (last_day_asset - first_day_asset) / first_day_asset

    #每年第一天的沪深300收盘价
    first_day_benchmark = benchmark_data.loc[benchmark_data['date'] == first_day,'close'].values[0]
    # 每年最后一天的沪深300收盘价
    last_day_benchmark = benchmark_data.loc[benchmark_data['date'] == last_day, 'close'].values[0]

    # 计算沪深300每年涨跌幅度
    benchmark_return = (last_day_benchmark - first_day_benchmark) / first_day_benchmark

    # 记录
    years_return[year] = {}
    years_return[year]['year_return'] = year_return
    years_return_list.append(year_return)
    years_return[year]['benchmark_return'] = benchmark_return

print(years_return)

# 获取最终收益率
time_records['time'] = pd.to_datetime(time_records['time'])
total_return = time_records.loc[time_records['time'] == end_day, 'profit_ratio'].values[0]
print("Total return: ", total_return)

# 获取沪深300每日涨跌幅
benchmark_data['change'] = (benchmark_data['close'] - benchmark_data['close'].iloc[0]) / benchmark_data['close'].iloc[0]

# 获取沪深300整个交易区间的涨跌幅
benchmark_total_return = benchmark_data.loc[benchmark_data['date'] == end_day, 'change'].values[0]
print("Benchmark total return: ", benchmark_total_return)

# 计算超额收益率
excess_return = total_return - benchmark_total_return
print("Excess return: ", excess_return)

# 计算交易区间天数
days = (end_day - begin_day).days + 1

# 计算年均收益率复利
annual_return = (total_return + 1) ** (365.0 / days) - 1
print("Annual return: ", annual_return)

# 计算回测区间的夏普比率
sharpe_ratio = get_sharpe_ratio(years_return_list)
print("Sharpe ratio: ", sharpe_ratio)

# 计算回测区间的最大回撤
max_drawdown = get_max_drawdown(time_records['total_asset'])
print("Max drawdown: ", max_drawdown)

# 绘制投资组合每日涨跌幅与沪深300每日涨跌幅
plt.plot(benchmark_data['date'], benchmark_data['change'], label='沪深300')
plt.plot(time_records['time'], time_records['profit_ratio'], label='长期均线结合技术指标策略')
plt.legend()
plt.show()







