# -*- coding:utf-8 -*-
import requests
import time
import json
import re
from tqdm import tqdm


headers = {
    "Host": "fund.eastmoney.com",
    "Referer": "http://fund.eastmoney.com/data/fundranking.html",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Cookie": "qgqp_b_id=65edcb132fd5abdedf8afe303f2c6b02; Eastmoney_Fund=008190_001632_260108_001986_003096_001551; AUTH_FUND.EASTMONEY.COM_GSJZ=AUTH*TTJJ*TOKEN; em_hq_fls=js; _qddaz=QD.v39p9f.64vdst.krzz6m8m; st_si=73059471768287; st_asi=delete; ASP.NET_SessionId=nu0vuvistpddbiywgigkyqlk; cowCookie=true; intellpositionL=1079.19px; intellpositionT=762px; HAList=a-sz-000792-%u76D0%u6E56%u80A1%u4EFD%2Ca-sz-002371-%u5317%u65B9%u534E%u521B%2Ca-sh-603501-%u97E6%u5C14%u80A1%u4EFD; FundWebTradeUserInfo=JTdCJTIyQ3VzdG9tZXJObyUyMjolMjIlMjIsJTIyQ3VzdG9tZXJOYW1lJTIyOiUyMiUyMiwlMjJWaXBMZXZlbCUyMjolMjIlMjIsJTIyTFRva2VuJTIyOiUyMiUyMiwlMjJJc1Zpc2l0b3IlMjI6JTIyJTIyLCUyMlJpc2slMjI6JTIyJTIyJTdE; searchbar_code=004890_162201_005076_162202_000496_006250_005939_400015_012079_001239; EMFUND0=08-10%2014%3A49%3A14@%23%24%u6613%u65B9%u8FBE%u4E0A%u8BC1%u4E2D%u76D8ETF%u8054%u63A5C@%23%24004743; EMFUND1=08-10%2014%3A49%3A47@%23%24%u56FD%u8054%u5B89%u4E2D%u8BC1%u534A%u5BFC%u4F53ETF%u8054%u63A5A@%23%24007300; EMFUND2=08-10%2014%3A30%3A38@%23%24%u5357%u65B9%u4E2D%u8BC1100%u6307%u6570A@%23%24202211; EMFUND3=08-10%2014%3A56%3A04@%23%24%u56FD%u6CF0%u4E2D%u8BC1%u94A2%u94C1ETF%u8054%u63A5A@%23%24008189; EMFUND4=08-10%2014%3A56%3A28@%23%24%u56FD%u6CF0%u521B%u4E1A%u677F%u6307%u6570%28LOF%29@%23%24160223; EMFUND5=08-10%2014%3A56%3A50@%23%24%u94F6%u534EMSCI%u4E2D%u56FDA%u80A1%u8054%u63A5A@%23%24006339; EMFUND6=08-10%2015%3A04%3A36@%23%24%u534E%u5B89CES%u534A%u5BFC%u4F53%u82AF%u7247%u884C%u4E1A%u6307%u6570%u53D1%u8D77C@%23%24012838; EMFUND8=08-10%2015%3A13%3A39@%23%24%u4FE1%u8FBE%u6FB3%u94F6%u65B0%u80FD%u6E90%u7CBE%u9009%u6DF7%u5408@%23%24012079; EMFUND9=08-10%2015%3A14%3A31@%23%24%u957F%u76DB%u56FD%u4F01%u6539%u9769%u6DF7%u5408@%23%24001239; EMFUND7=08-10 15:15:05@#$%u6C47%u6DFB%u5BCC%u4E2D%u8BC1%u65B0%u80FD%u6E90%u6C7D%u8F66A@%23%24501057; st_pvi=14154729707578; st_sp=2021-07-30%2009%3A28%3A21; st_inirUrl=https%3A%2F%2Fwww.google.com.hk%2F; st_sn=82; st_psi=2021081015150589-112200305282-7278550336",
}

list_code = []

#获取1年收益从大到小前8页的基金代码
def get_status(now,over_the_past_year,days):
    params = {
        "op": "ph",
        "dt": "kf",
        "ft": "all",
        "rs": None,
        "gs": 0,
        "sc": "1nzf",
        "st": "desc",
        "sd": over_the_past_year,
        "ed": now,
        "qdii": None,
        "tabSubtype": ",,,,,",
        "pi": days,
        "pn": 50,
        "dx": 1,

    }
    url = 'http://fund.eastmoney.com/data/rankhandler.aspx?'
    html = requests.get(url,headers=headers,params=params)
    if html.status_code == 200:
        get_html(html)
    else:
        print(html.status_code)

#根据它们的年收益来判断是否符合
def get_html(html):
    global list_code
    content = html.text
    #把一些不相干的东西清理干净
    content = content.replace('var rankData = ','')
    content = content.replace('};','}')
    content = content.replace('{datas:','')
    all = re.compile('"](.*?)}')
    alls = all.findall(content)
    content = content.replace(alls[0],'')
    content = content.replace('}','')
    content = eval(content)
    for c in content:
        #然后对其以逗号进行分割出来，形成一个个列表
        c = c.split(',')
        #再对一年的收益进行划分，大于等于百分之50的可以被保留并且传到列表里面
        if float(c[11]) > 50:
            list_code.append(c[0])

#把获取到的基金代码用一个txt文本保留下来
def write_code(list_code):
    with open('代码.txt','w',encoding='utf-8')as f:
        str1 = '\n'
        f.write(str1.join(list_code))


if __name__ == '__main__':
    #获取当前的时间
    now = time.strftime('%Y-%m-%d', time.localtime(time.time()))
    #获取一年前的今天
    over_the_past_year = str(int(now[0:4]) - 1) + now[4:]
    #获取10页基金列表
    for i in tqdm(range(1,10)):
        get_status(now,over_the_past_year,i)
    #保存获取到的基金代码并且写入TXT文本中
    write_code(list_code)
