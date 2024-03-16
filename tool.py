import numpy as np
import pandas as pd

# 定义计算均线函数，data是原始数据，ma_range是待计算的均线范围
def get_ma(data, ma_range):
    n_data = len(data)
    n_ma = len(ma_range)
    ma = np.zeros((n_data, n_ma))  # ma用于保存计算结果，保存均线的矩阵
    # 计算均线
    for j in range(n_ma):
        for i in range(ma_range[j] - 1, n_data):
            ma[i, j] = data[(i - ma_range[j] + 1):(i + 1)].mean()
    return ma

# 从原数据中找到每一年的起始日与结束日
def get_year(date):
    # 记录每一年的第一天与最后一天
    year_all = {}

    # 遍历所有日期，找到年份前后不一致的进行记录
    for i in range(1, len(date)):
        date_last_year = str(date[i - 1]).split('-')
        date_next_year = str(date[i]).split('-')

        # 如果原字典中没有当前年份，则添加当前年份
        if date_last_year[0] not in year_all.keys():
            year_all[date_last_year[0]] = {}
        if date_next_year[0] not in year_all.keys():
            year_all[date_next_year[0]] = {}

        # 给第一天和最后一天赋值
        if i == 1:
            year_all[date_last_year[0]]['first_day'] = date[i - 1]
        if i == len(date) - 1:
            year_all[date_last_year[0]]['last_day'] = date[i]

        if date_last_year[0] != date_next_year[0]:
            # 记录上一年的最后一天和这一年的第一天
            year_all[date_last_year[0]]['last_day'] = date[i - 1]
            year_all[date_next_year[0]]['first_day'] = date[i]

    return year_all

# 计算最大回撤
def get_max_drawdown(asset):
    netA = asset.values  # 净资产数据
    num = len(netA)
    maxNetA = netA[0]
    max_dd = 0.0

    for i in range(1, num):
        maxNetA = max(netA[i], maxNetA)
        drawdown = netA[i] / maxNetA - 1
        max_dd = min(drawdown, max_dd)
    return max_dd

# 计算夏普比率
def get_sharpe_ratio(rate):
    eRp = np.mean(rate)  # 计算平均年收益率E(Rp)
    stdRp = np.std(rate)  # 计算Rp的标准差σp
    rf = 0.03  # 设置年化无风险利率Rf为3%
    sharpeRatio = (eRp - rf) / stdRp  # 计算夏普率
    return sharpeRatio


# 寻找某一段时间内的最佳均线
def best_ma_period(data, day_ma, ma_range, start_day, end_day, money0, netAsset0, commission_rate, close_tax_ratio):
    # 获取所有收盘价,便于后面进行比对
    close_adjust = data['close_adjust'].values
    close_real = data['close'].values

    # 记录买卖次数
    num_bs = 0

    # 获取均线数
    nma = len(day_ma[0])

    # 用于返回结果
    sum_result = pd.DataFrame({'MA': ma_range, 'netAsset': [0.0] * nma})

    # 对每一条均线进行回测
    for j in range(nma):
        # 记录仓位是否为空
        position = 0

        # 记录买卖信号
        flag_bs = 0

        # 记录初始资金
        money = money0

        # 记录交易
        record_bs = [['序号', '日期', '买卖', '价格', '证券数量', '资金余额', '净资产', '平仓盈利'],
                     [1, start_day, 0, 0.0, 0, money, money, 0.0]]

        # 获取交易区间的数据
        trade_data = data[(data['date'] >= start_day) & (data['date'] <= end_day)]

        # 模拟循环交易
        for index, row in trade_data.iterrows():
            # 第一天的信号比较特别
            if row['date'] == start_day:
                # 给前1天收盘价赋值
                close_last_1day = close_adjust[index - 1]
                # 给前1天均线赋值
                ma_1day = day_ma[index - 1, j]

                # 如果前1天收盘价大于均线
                if close_last_1day > ma_1day:
                    flag_bs = 1  # 发出买卖信号
                if close_last_1day < ma_1day:  # 如果前1天收盘价小于均线
                    flag_bs = -1  # 发出买卖信号
            else:
                # 获取两天前的收盘价
                cl_2day = close_adjust[index - 2]
                # 获取两天前的均线值
                ma_2day = day_ma[index - 2, j]
                # 获取一天前的收盘价
                cl_1day = close_adjust[index - 1]
                # 获取一天前的均线值
                ma_1day = day_ma[index - 1, j]
                # 如果收盘价上穿了均线则买入，跌穿了均线则卖出
                if (cl_2day <= ma_2day) and (cl_1day > ma_1day):
                    flag_bs = 1
                if (cl_2day >= ma_2day) and (cl_1day < ma_1day):
                    flag_bs = -1

            # 如果尚未发出买卖信号
            if (flag_bs != 0):
                # 如果是买入信号并且当前没有仓位则以当日开盘价买入
                if (flag_bs == 1) and (position == 0):
                    price = row['open']
                    amount = int(money / price / (1 + commission_rate))
                    money = money - price * amount * (1 + commission_rate)
                    position = 1
                    netAsset = money + price * amount
                    num_bs += 1  # 买卖记录序号加一
                    date_bs = row['date']
                    record_bs.append([num_bs, date_bs, 1, price, amount, money, netAsset, 0.0])
                # 如果是卖出信号并且当前拥有仓位则以当日开盘价卖出
                if (flag_bs == -1) and (position == 1):
                    price = row['open']
                    money = money + price * amount * (1 - commission_rate - close_tax_ratio)
                    position = 0
                    amount = 0
                    netAsset = money
                    profit = netAsset - netAsset0
                    netAsset0 = netAsset
                    num_bs += 1  # 买卖记录序号加一
                    date_bs = row['date']
                    record_bs.append([num_bs, date_bs, -1, price, amount, money, netAsset, profit])
                flag_bs = 0

        # 如果持仓不为0，用最后一天的收盘价计算净资产
        if (position != 0):
            price = close_real[index]
            netAsset9 = money + price * amount
        else:
            netAsset9 = money
        sum_result.iat[j, 1] = netAsset9
    return sum_result