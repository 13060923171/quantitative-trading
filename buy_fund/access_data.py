# 导入需要的模块


import requests
from bs4 import BeautifulSoup
import re
import numpy as np
import pandas as pd
import time
from tqdm import tqdm
import os

#获取基金往期数据的一个开源api
def get_html(code, start_date, end_date, page=1, per=20):
    '''
    :param code:是基金代码
    :param start_date: 开始时间
    :param end_date: 最后的时间
    :param page: 页数
    :param per: 数量
    :return:
    '''
    url = 'http://fund.eastmoney.com/f10/F10DataApi.aspx?type=lsjz&code={0}&page={1}&sdate={2}&edate={3}&per={4}'.format(
        code, page, start_date, end_date, per)
    rsp = requests.get(url)
    html = rsp.text
    return html


def get_fund(code, start_date, end_date, page=1, per=20):
    # 获取html
    html = get_html(code, start_date, end_date, page, per)
    soup = BeautifulSoup(html, 'html.parser')
    # 获取总页数
    pattern = re.compile('pages:(.*),')
    result = re.search(pattern, html).group(1)
    total_page = int(result)
    # 获取表头信息
    heads = []
    for head in soup.findAll("th"):
        heads.append(head.contents[0])

    # 数据存取列表
    records = []
    # 获取每一页的数据
    current_page = 1
    while current_page <= total_page:
        html = get_html(code, start_date, end_date, current_page, per)
        soup = BeautifulSoup(html, 'html.parser')
        # 获取数据
        for row in soup.findAll("tbody")[0].findAll("tr"):
            row_records = []
            for record in row.findAll('td'):
                val = record.contents
                # 处理空值
                if val == []:
                    row_records.append(np.nan)
                else:
                    row_records.append(val[0])
            # 记录数据
            records.append(row_records)
        # 下一页
        current_page = current_page + 1

    # 将数据转换为Dataframe对象
    np_records = np.array(records)
    fund_df = pd.DataFrame()
    for col, col_name in enumerate(heads):
        fund_df[col_name] = np_records[:, col]

    # 按照日期排序
    fund_df['净值日期'] = pd.to_datetime(fund_df['净值日期'], format='%Y/%m/%d')
    fund_df = fund_df.sort_values(by='净值日期', axis=0, ascending=True).reset_index(drop=True)
    fund_df = fund_df.set_index('净值日期')

    # 数据类型处理
    fund_df['单位净值'] = fund_df['单位净值'].astype(float)
    fund_df['累计净值'] = fund_df['累计净值'].astype(float)
    fund_df['日增长率'] = fund_df['日增长率'].str.strip('%').astype(float)
    return fund_df


def data():
    #获取上一个代码保存的基金代码
    with open('代码.txt','r',encoding='utf-8')as f:
        content = f.readlines()
    #读取完成后用列表的形式保留
    list_code = [str(c).replace('\n', '') for c in content]
    #获取当前的时间
    now = time.strftime('%Y-%m-%d', time.localtime(time.time()))
    #获取上一年当前的时间
    over_the_past_year = str(int(now[0:4]) - 1) + now[4:]

    #今天的日期
    today = str(now)
    #年
    year = today.split('-')[0]
    #月
    month = today.split('-')[1]
    #日
    day = today.split('-')[2]
    #创建对应的文件夹用来保存CSV文件
    filename = './data/{}/{}/{}'.format(year,month,day)
    #如果没有就自动生成
    if not os.path.exists(filename):
        os.makedirs(filename)
    #传入对应的参数去获取基金
    for l in tqdm(list_code):
        fund = get_fund('{}'.format(l),over_the_past_year,now)
        #然后再把获取到的数据用CSV保存下来，格式默认为utf-8
        fund.to_csv('./data/{}/{}/{}/{}.csv'.format(year,month,day,l))
    time.sleep(0.5)


if __name__ == '__main__':
    data()
