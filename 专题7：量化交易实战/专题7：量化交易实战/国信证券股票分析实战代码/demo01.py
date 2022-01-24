import tushare as ts
f1 = open('../tk','r')
akey = ''
for i in f1:
    akey = i
ts.set_token(akey)
ts2= ts.pro_api()
st = ts2.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
# print(st)
print(type(st))
print(st.ts_code)

print(type(list(st.ts_code)))

import pandas as pd
from sqlalchemy import create_engine
import time
sqlEngine       = create_engine('mysql+pymysql://mars:mars123@10.0.1.31/test', pool_recycle=3600)
dbConnection    = sqlEngine.connect()

list1=list(st['ts_code'])
str_stock_list=''
count= 0
count2 = 0
for i in list1:
    if count == 99:
        count2 += 1
        df = ts2.daily(ts_code=str_stock_list, start_date='20210327', end_date='20221218')
        print(df.head(10))
        print(df.columns)
        newdf2 = pd.DataFrame()
        newdf2 = df[['ts_code', 'trade_date', 'open', 'high', 'low', 'close', 'vol']]

        str_stock_list = ''

        frame = newdf2.to_sql('stock20210409c', dbConnection, if_exists='append');
        count = 0
        time.sleep(2)
    str_stock_list += i + ','
    count += 1
dbConnection.close()


