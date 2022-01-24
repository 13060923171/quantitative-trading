#导入类库
from sqlalchemy import create_engine
import pymysql
import talib as ta
import matplotlib.pyplot as plt
import pandas as pd

# 创建连接
sqlEngine       = create_engine('mysql+pymysql://mars:mars123@10.0.1.31/test', pool_recycle=3600)

dbConnection    = sqlEngine.connect()

# 查询所有数据

sqlstr="""
select * from stock20210317 order by trade_date 
"""
df = pd.read_sql(sqlstr,dbConnection)

sqlstr2="""
select distinct(ts_code) from stock20210317b
"""
df_list = pd.read_sql(sqlstr2,dbConnection)
full_list = list(df_list.ts_code)
len(full_list)

pd.options.mode.chained_assignment = None
df3 = pd.DataFrame()
for i in full_list[:]:

    df3 = df.loc[df['ts_code'] == str(i)]

    df3['trade_date'] = pd.to_datetime(df3['trade_date'], format='%Y%m%d', errors='ignore')
    df3.set_index("trade_date", inplace=True)
    upper, middle, lower = ta.BBANDS(df3['close'], timeperiod=20, nbdevup=1.7, nbdevdn=1.7)
    df3['upperband'] = upper

    df3['lowerband'] = lower
    df3['k'],df3['d'] = ta.STOCH(df3['high'].values,
                   df3['low'].values,
                   df3['close'].values,
                   fastk_period=9,
                   slowk_period=3,
                   slowk_matype=0,
                   slowd_period=3,slowd_matype=0)
    df3['j'] = 3* df3['k'] - 2 * df3['d']
    tempdf = df3.loc[(df3['close'] * 1.05 - df3['lowerband'] < 0)]
    if (tempdf.loc['2021-04-01':].empty):
        pass
    else:
        # print(i)
        print(tempdf.loc['2021-04-01':])
        tempdf.to_sql('result_in', dbConnection, if_exists='append');
    df3 = pd.DataFrame()

# for i in full_list[:]:
#
#     df3 = df.loc[df['ts_code'] == str(i)]
#
#     df3['trade_date'] = pd.to_datetime(df3['trade_date'], format='%Y%m%d', errors='ignore')
#     df3.set_index("trade_date", inplace=True)
#     upper, middle, lower = ta.BBANDS(df3['close'], timeperiod=20, nbdevup=1.7, nbdevdn=1.7)
#     df3['upperband'] = upper
#
#     df3['lowerband'] = lower
#     df3['k'],df3['d'] = ta.STOCH(df3['high'].values,
#                    df3['low'].values,
#                    df3['close'].values,
#                    fastk_period=9,
#                    slowk_period=3,
#                    slowk_matype=0,
#                    slowd_period=3,slowd_matype=0)
#     df3['j'] = 3* df3['k'] - 2 * df3['d']
#     tempdf = df3.loc[(df3['j'] > 80)]
#     if (tempdf.loc['2021-04-01':].empty):
#         pass
#     else:
#         # print(i)
#         print(tempdf.loc['2021-04-01':])
#         tempdf.to_sql('result_out', dbConnection, if_exists='append');
#     df3 = pd.DataFrame()
