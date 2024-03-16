import pandas as pd

from flag_tool import Flag_tool

# 进行交易操作的类 #
class Trade():
    # 初始化交易情况
    def __init__(self, instruments, commission_ratio, close_tax_ratio, total_asset):
        # 获取所有股票
        self.instruments = instruments

        # 获取信号工具类（需要的时候再实例化）
        self.Flag_tool = None

        # 获取佣金费率
        self.commission_ratio = commission_ratio

        # 获取印花税
        self.close_tax_ratio = close_tax_ratio

        # 用于记录股票持仓情况
        self.instrument_position = {}
        for instrument in instruments:
            self.instrument_position[instrument] = {}
            self.instrument_position[instrument]['amount'] = 0
            self.instrument_position[instrument]['cost_price'] = 0

        # 记录所有交易
        self.trade_records = pd.DataFrame(columns=['time','instrument', 'direction', 'order_price','order_amount','money_before_order','money_after_order','profit', 'profit_ratio', 'total_asset'])

        # 记录每个时间点的持仓情况
        self.time_records = pd.DataFrame(columns=['time', 'money', 'total_asset', 'market_value', 'profit'])

        # 记录初始资金
        self.init_asset = total_asset

        # 记录总资产
        self.total_asset = total_asset

        # 记录股票总市值
        self.market_value = 0

        # 记录资金余额
        self.money = total_asset

    # 在某段区间执行交易策略
    def trade_strategy_period(self, start_day, end_day, day_ma):
        # 对于所有股票进行遍历
        for instrument in self.instruments:
            # 获取股票数据
            instrument_data = pd.read_csv('data-set/instruments/' + instrument + '.csv',encoding= 'gb18030')
            print(instrument_data)

            # 获取分红信息
            instrument_bonus = pd.read_csv('data-set/bonus/' + instrument + '分红信息.csv', encoding='gb18030')
            print(instrument_bonus)

            # 实例化信号工具类
            self.Flag_tool = Flag_tool(instrument_data)

            # 获取前复权收盘价,便于后面进行比对
            close_adjust = instrument_data['close_adjust'].values

            # 模拟循环交易
            for index, row in instrument_data.iterrows():
                print(row['date'])
                # 如果时间在交易区间外则跳过
                if row['date'] < start_day or row['date'] > end_day:
                    continue

                # 初始化买卖信号为0
                flag_bs = 0

                # 第一天的信号比较特别
                if row['date'] == start_day:
                    # 给前1天收盘价赋值
                    close_last_1day = close_adjust[index - 1]
                    # 给前1天均线赋值
                    ma_1day = day_ma[index - 1, 0]

                    # 如果前1天收盘价大于均线
                    if close_last_1day > ma_1day:
                        flag_bs = 1  # 发出买卖信号
                    if close_last_1day < ma_1day:  # 如果前1天收盘价小于均线
                        flag_bs = -1  # 发出买卖信号
                else:
                    close_last_2day = close_adjust[index - 2]  # 给前2天收盘价赋值
                    ma_2day = day_ma[index - 2, 0]  # 给前2天均线赋值
                    close_last_1day = close_adjust[index - 1]  # 给前1天收盘价赋值
                    ma_1day = day_ma[index - 1, 0]  # 给前1天均线赋值
                    if (close_last_2day <= ma_2day) and (close_last_1day > ma_1day):  # 如果收盘价上穿均线
                        flag_bs = 1  # 发出买卖信号
                    elif (close_last_2day >= ma_2day) and (close_last_1day < ma_1day):  # 如果收盘价下穿均线
                        flag_bs = -1  # 发出买卖信号
                    # 如果长期均线没发出信号，则判断KDJ，MACD短线指标的值
                    else:
                        if self.Flag_tool.get_KDJ_flag(index) == 1:
                            for x in range(12):
                                if self.Flag_tool.get_MACD_flag(index - x) == 1:
                                    flag_bs = 1  # 发出买卖信号
                                    break
                        if self.Flag_tool.get_KDJ_flag(index) == -1:
                            for x in range(12):
                                if self.Flag_tool.get_MACD_flag(index - x) == -1:
                                    flag_bs = -1  # 发出买卖信号
                                    break

                if flag_bs != 0:  # 如果买卖信号已发
                    # 如果是买入信号
                    if flag_bs == 1:
                        # 买入价格为当天开盘价
                        price = row['open']

                        # 计算能买入的数量，之后全仓买入
                        amount = int( self.money / price / (1 + self.commission_ratio + self.close_tax_ratio))

                        if amount > 0:
                            print("买入，买入" + str(amount) + "股，" + "买入价格为" + str(price))

                            self.order(row['date'], instrument, 'buy' ,price, amount)

                    # 如果是卖出信号
                    if flag_bs == -1:
                        # 卖出价格为当天开盘价
                        price = row['open']

                        # 卖出数量为全部
                        amount = self.instrument_position[instrument]['amount']

                        print("卖出，卖出" + str(amount) + "股，" + "卖出价格为" + str(price))

                        # 全部平仓
                        self.order(row['date'], instrument, 'sell' ,price, amount)

                    # 买卖信号复位
                    flag_bs = 0

                # 如果是分红日
                if str(row['bonus_flag']) == '1':
                    # 调用分红函数
                    self.bonus(instrument,instrument_bonus,row['date'])

                # 更新每日所有持仓数据
                self.check(instrument, row['date'], row['close'])


    # 下单
    def order(self, time, instrument, direction, order_price, order_amount):
        # 记录下单前的资金余额情况
        money_before_order = self.money

        # 买单
        if direction == 'buy':
            # 判断佣金费是否不足五元，不足五元按照五元计算
            commission = order_price * order_amount * self.commission_ratio
            commission = 5 if commission < 5 and commission > 0 else round(commission,4)

            # 判断资金是否足够购买对应量和价格的股票
            if self.money < order_price * order_amount + commission:
                print('剩余资金不足，无法下单')
                return -1

            # 更新当前股票的持仓数
            self.instrument_position[instrument]['amount'] = self.instrument_position[instrument]['amount'] + order_amount
            # 更新当前股票的成本价
            self.instrument_position[instrument]['cost_price'] = ((self.instrument_position[instrument]['cost_price'] * self.instrument_position[instrument]['amount'] + order_price * order_amount  + commission)
                                                                  / (self.instrument_position[instrument]['amount'] + order_amount))

            # 更新剩余金额、平仓盈利与总资产
            self.money = self.money - order_price * order_amount - commission
            profit = 0
            profit_ratio = 0
            self.total_asset = self.total_asset - commission


        # 卖单
        else:
            # 判断手中的持仓是否足够卖出
            if order_amount > self.instrument_position[instrument]['amount'] or order_amount == 0:
                print('持仓手数不足，无法平仓')
                return -1

            # 判断佣金费是否不足五元，不足五元按照五元计算
            commission = order_price * order_amount * self.commission_ratio
            commission = 5 if commission < 5 and commission > 0 else round(commission,4)

            # 计算印花税
            close_tax = order_price * order_amount * self.close_tax_ratio

            print(self.money)

            # 判断资金是否足够支付平仓时的佣金与税费
            if self.money < commission + close_tax:
                print('平仓失败，剩余金额不足以支付平仓佣金与税费')
                return -1

            # 更新平仓盈利、总资产与剩余金额
            profit = (order_price - self.instrument_position[instrument]['cost_price']) * order_amount
            profit_ratio = profit / (self.instrument_position[instrument]['cost_price'] * order_amount)
            self.total_asset = profit + self.total_asset - commission - close_tax
            self.money = self.money + order_price * order_amount - commission - close_tax

            # 如果是全部平仓
            if order_amount == self.instrument_position[instrument]['amount']:
                # 更新当前股票持仓情况
                self.instrument_position[instrument]['cost_price'] = 0
                self.instrument_position[instrument]['amount'] = 0

            # 如果是部分平仓
            else:
                # 更新当前股票持仓情况
                self.instrument_position[instrument]['cost_price'] = ((self.instrument_position[instrument]['cost_price'] * self.instrument_position[instrument]['amount'] + commission + close_tax - order_price * order_amount)
                                                                      / (self.instrument_position[instrument]['amount'] - order_amount))
                self.instrument_position[instrument]['amount'] = self.instrument_position[instrument]['amount'] - order_amount

        # 记录本次下单
        trade_df = pd.DataFrame({'time':time, 'instrument':instrument, 'direction':direction, 'order_price':order_price, 'order_amount':order_amount,
                                   'money_before_order':money_before_order, 'money_after_order':self.money,
                                 'profit':profit, 'profit_ratio' : profit_ratio, 'total_asset':self.total_asset},index = [0])
        self.trade_records = pd.concat([self.trade_records,trade_df],axis=0)
        self.trade_records = self.trade_records.reset_index(drop=True)


    # 在每日结束时检查某只股票的持仓情况并记录
    def check(self, instrument, time, instrument_price):
        # 获取当前股票持仓情况
        instrument_position = self.instrument_position[instrument]
        # 获取当前股票的市值
        self.market_value = instrument_position['amount'] * instrument_price

        # 更新总资产
        self.total_asset = self.money + self.market_value

        record_df = pd.DataFrame({'time':time, 'money':self.money, 'total_asset':self.total_asset,
                                 'market_value':self.market_value, 'profit':self.total_asset - self.init_asset, 'profit_ratio': (self.total_asset - self.init_asset)/self.init_asset},
                                index=[0])
        self.time_records = pd.concat([self.time_records, record_df], axis=0)
        self.time_records = self.time_records.reset_index(drop=True)

    # 分红函数
    def bonus(self, instrument, instrument_bonus, date):
        # 获取当前股票的持仓额
        amount = self.instrument_position[instrument]['amount']

        # 如果没有持仓，则不分红
        if amount == 0:
            return

        # 将date列从字符串转化为datetime类型
        instrument_bonus['Ex-dividend-date'] = pd.to_datetime(instrument_bonus['Ex-dividend-date'])

        # 获取当前分红日的分红信息
        current_day = instrument_bonus[instrument_bonus['Ex-dividend-date'] == date]

        # 获取派息数、送股数和转增数
        interest = current_day['派息'].values[0]
        send_shares = current_day['送股'].values[0]
        convert_shares = current_day['转增'].values[0]

        # 计算派息额
        cash = round(amount / 10 * interest , 4)

        # 送股、转增
        shares = int(amount / 10 * (int(send_shares) + int(convert_shares)))

        # 现金分红
        self.money = self.money + cash

        # 送股和转增导致持仓增加
        self.instrument_position[instrument]['amount'] = self.instrument_position[instrument]['amount'] + shares


