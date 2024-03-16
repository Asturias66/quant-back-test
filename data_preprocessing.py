import pandas as pd

# 获取原始数据
raw_data = pd.read_csv('data-set/raw-data/平安银行原始数据.csv', encoding= 'gb18030')
print(raw_data)
# 对原数据进行去空格处理
raw_data = raw_data.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
# 将date列从字符串转化为datetime类型
raw_data['date'] = pd.to_datetime(raw_data['date'])

# 获取分红数据
bonus_data = pd.read_csv('data-set/bonus/平安银行分红信息.csv', encoding= 'gb18030')
# 对分红数据进行去空格处理
bonus_data = bonus_data.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
# 将date列从字符串转化为datetime类型
bonus_data['Ex-dividend-date'] = pd.to_datetime(bonus_data['Ex-dividend-date'])

# 给原始数据新建一列bonus_flag，用于识别分红日期，0为无分红，1为有分红
raw_data['bonus_flag'] = 0

# 获取分红日期并标记为1
raw_data.loc[raw_data['date'].isin(bonus_data['Ex-dividend-date']),'bonus_flag'] = 1

# 去除所有列名里的空格
raw_data.columns = raw_data.columns.str.replace(' ', '')

# 去除用不到的列
raw_data.drop(columns=['MA.MA1', 'MA.MA2', 'MA.MA3', 'MA.MA4', 'MA.MA5', 'MA.MA6', 'MA.MA7', 'MA.MA8'], inplace=True)

# 筛选数据的范围
data = raw_data[(raw_data['date'] >= '1992-01-02') & (raw_data['date'] <= '2022-12-30')]

print(data)
print(data.info())
print(data.describe())

# 输出有分红列的数据
data.to_csv('data-set/instruments/平安银行.csv',index = False)

