# 用于获取交易信号的工具类
class Flag_tool():
    def __init__(self,data):
        # 获取数据
        self.data = data

        # 获取KDJ值
        self.K = data['KDJ.K'].values  # 获取K线
        self.D = data['KDJ.D'].values  # 获取D线
        self.J = data['KDJ.J'].values  # 获取J线

        # 获取DIF、DEA、MACD
        self.DIF = data['MACD.DIF'].values  # 获取DIF
        self.DEA = data['MACD.DEA'].values  # 获取DEA
        self.MACD = data['MACD.MACD'].values  # 获取MACD

    # 定义通过DIF,DEA的取值判断买卖信号函数，返回1表示买入，返回-1表示卖出，返回0表示不操作
    def get_MACD_flag(self, i):
        # 如果DIF上穿DEA，发出买入信号
        if (self.DIF[i - 1] > self.DEA[i - 1]) and (self.DIF[i - 2] < self.DEA[i - 2]) and self.DIF[i - 1] > 0 and self.DEA[i - 1] > 0:
            return 1
        # 如果DIF下穿DEA，发出卖出信号
        elif (self.DIF[i - 1] < self.DEA[i - 1]) and (self.DIF[i - 2] > self.DEA[i - 2]) and self.DIF[i - 1] < 0 and self.DEA[i - 1] < 0:
            return -1
        else:
            return 0

    # 定义通过K线，D线的取值判断买卖信号函数
    def get_KDJ_flag(self, i):
        # K线由下向上突破D线形成金叉时为买入信号
        if (self.K[i - 1] > self.D[i - 1]) and (self.K[i - 2] < self.D[i - 2]) and self.K[i - 1] < 0 and self.D[i - 1] < 0:
            return 1
        # K线由上向下跌破D线形成死叉为卖出信号
        elif (self.K[i - 1] < self.D[i - 1]) and (self.K[i - 2] > self.D[i - 2]) and self.K[i - 1] > 0 and self.D[i - 1] > 0:
            return -1
        else:
            return 0

