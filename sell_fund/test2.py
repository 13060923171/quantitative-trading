import requests
import sys,os,re
import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.header import Header
from smtplib import SMTP_SSL
import itertools
from tqdm import tqdm

def parse_url(codes):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Host": "api.fund.eastmoney.com",
        "Origin": "https://favor.fund.eastmoney.com",
        "Referer": "https://favor.fund.eastmoney.com/",
    }
    # 在这里填写你的基金代码
    data = {
        "fcodes": codes,
    }
    url = "https://api.fund.eastmoney.com/favor/GetFundsInfo?"
    requests.packages.urllib3.disable_warnings()
    html = requests.post(url,headers=headers,data=data,verify=False)
    if html.status_code == 200:
        content = html.json()
        data = content['Data']['KFS']
        for d in data[:-2]:
            #基金名字
            name = d['SHORTNAME']
            # 净值估算
            gsz = d['gsz']
            #估算涨幅
            gszzl = d['gszzl']
            return name,gsz,gszzl

    else:
        print(html.status_code)


def read_file():
    total = []
    filename = './data/{}/{}/{}'.format(year, month, day)
    file_pathname = os.listdir(filename)
    for f in tqdm(file_pathname):
        code = f[:-4]
        df = pd.read_csv('./data/{}/{}/{}/{}'.format(year, month, day, f)).loc[:, ['净值日期', '单位净值']]

        name, gsz, gszzl = parse_url(code)
        try:
            # 将最新获取的和之前的合并成一个新的dataframe
            df2 = pd.DataFrame([[str(today), float(gsz)]], columns=['净值日期', '单位净值'])
            df = df.append(df2, ignore_index=True)
        except ValueError:
            df = df

        close = df['单位净值']
        days = df['净值日期']
        close1 = close.values
        ma5 = pd.Series(0.0,index=close.index)
        for i in range(4,len(close1)):
            ma5[i] = float(sum(close1[(i-4):(i+1)]) / 5)

        ma20 = pd.Series(0.0,index=close.index)
        for i in range(19,len(close1)):
            ma20[i] = float(sum(close1[(i-19):(i+1)]) / 20)

        days = days.values

        list_T1 = []
        for j in range(len(ma5.index)):
            if ma5[j] != 0.0 and ma20[j] != 0.0:
                T1 = ma5[j] - ma20[j]
                list_T1.append(T1)

        list_out = []
        sum_datetime = []
        list_datetime = []
        list_out2 = []

        total_list = []
        for j,k in zip(list_T1,days[19:]):
            total_list.append((j,k))

        # #对list_T1进行处理正的和负的完全分开，因为用while最新的正的或者负的无法分开
        for key,group in itertools.groupby(total_list, lambda x: float(x[0]) > 0 or float(x[0]) == 0):
            for g in list(group):
                list_out.append(g[0])
                list_datetime.append(g[1])
            list_out2.append(list_out)
            sum_datetime.append(list_datetime)
            list_out = []
            list_datetime = []
        list_sum = []

        for j in range(len(list_out2)):
            if sum(list_out2[j]) < 0:
                a = [[list_out2[j][0],'卖出',sum_datetime[j][0]]]
                list_sum.append(a[0])
        filename1 = './img/{}/{}/{}'.format(year, month, day)
        if not os.path.exists(filename1):
            os.makedirs(filename1)
        for l in list_sum:
            #print([l[1], l[2], code, name])
            if l[2] == today and l[1] == '卖出':
                total.append([l[1], l[2], code, name])
        plt.rcParams['font.sans-serif'] = ['simhei']
        plt.figure(figsize=(9, 6))
        plt.plot(close[4:], label='Close', color='g')
        plt.plot(ma5[4:],   label='ma5',   color='r')
        plt.plot(ma20[19:], label='ma20',  color='b')
        plt.title('{}-{}'.format(code,name))
        plt.grid(True)
        plt.legend()
        plt.savefig('./img/{}/{}/{}/{}.jpg'.format(year, month, day, code))
        # plt.show()

    return total


#删除整个文件夹
def remove_img():
    import shutil
    try:
        shutil.rmtree('./img')
        print("File removed successfully")
    except:
        return '该文件不存在'

#计算总基金持有收益
def get_data():
    list_name = []
    list_gsz = []
    list_gszzl = []
    #获取基金代码
    with open('所持基金.txt','r',encoding='utf-8')as f:
        content = f.readlines()
    list_code = [str(c).replace('\n', '') for c in content]
    #筛选属于自己的代码
    for c in list_code[:-1]:
        name, gsz,gszzl = parse_url(c)
        list_name.append(name)
        list_gsz.append(gsz)
        list_gszzl.append(float(gszzl))
    #计算收益率
    def jisuan(g,c):
        syl = "%0.2lf" % (float(float(float(g) - float(c)) / float(c)) * 100)
        return syl
    list_sum = []
    # with open('累加.txt','r')as f:
    #     content = f.readlines()
    # sylj = [float(c.strip('\n')) for c in content]

    # ar_sylj = np.array(sylj)
    # ar_gz = np.array(list_gszzl)
    # arry = ar_sylj + ar_gz
                #中欧   医药     汇丰    国投     创金  华夏    宝盈    医疗   蓝筹
    list_cbj = [3.5660, 1.1051, 5.0805, 4.7088, 3.5504, 4.5901 ,3.8365 ,3.4733, 2.9064]
    for i in range(len(list_cbj)):
        n = list_name[i]
        g = list_gsz[i]
        c = list_cbj[i]
        gz = list_gszzl[i]
        syl = jisuan(g,c)
        # syl = "%0.2lf" %(float(float(float(g) - float(c)) / float(c)) * 100)
        if float(syl) >= 8:
            neirong = '收益率大于8,请速抛！！！'
            list_sum.append([n, syl, gz, neirong])
        elif float(gz) <= -1.5:
            neirong = '跌幅大于-1.5,可以加仓'
            list_sum.append([n, syl, gz, neirong])
        else:
            neirong = ''
            list_sum.append([n, syl, gz, neirong])

    # arry[arry <= -4] = 0
    # np.savetxt('累加.txt', arry, fmt='%0.1f', delimiter=',')
    if len(list_sum) > 0:
        #把列表写成HTML语句用于后面发送邮件
        trigger_html_str = ''
        for l in list_sum:
            tail_html_str = '''<tr>
                            <td>{}</td>
                            <td>{}</td>
                            <td>{}</td>
                            <td>{}</td>             
                            </tr>'''.format(l[0], l[1], l[2], l[3])
            trigger_html_str = trigger_html_str + tail_html_str
        return trigger_html_str
    else:
        trigger_html_str = ''
        return trigger_html_str


def text_to_html():
    list_sum = read_file()
    if len(list_sum) > 0:
        #把列表写成HTML语句用于后面发送邮件
        trigger_html_str = ''
        for l in list_sum:
            tail_html_str = '''<tr>
                            <td>{}</td>
                            <td>{}</td>
                            <td>{}</td>
                            <td>{}</td>                
                            </tr>'''.format(l[2], l[3], l[1], l[0])
            trigger_html_str = trigger_html_str + tail_html_str
        return trigger_html_str
    else:
        trigger_html_str = ''
        return trigger_html_str


def send_mail(receiver):
    host_server = 'smtp.qq.com'  # QQ邮箱的SMTP服务器
    sender_qq = '960751327'  # 发件人的QQ号码
    pwd = 'fdrrjmiqqnaubdcj'  # QQ邮箱的授权码
    sender_qq_mail = '960751327@qq.com'  # 发件人邮箱地址

    mail_title = '量化交易之基金卖出'  # 设置邮件标题

    msg = MIMEMultipart('related')
    msg["Subject"] = Header(mail_title, 'utf-8')  # 填写邮件标题
    msg["From"] = sender_qq_mail  # 发送者邮箱地址
    msg["To"] = receiver  # 接收者邮件地址

    table_html_code = '''
    <table width="90%" border="1" cellspacing="0" cellpadding="4" bgcolor="#cccccc" class="tabtop13">
        <tr>
        <th colspan="4" class="btbg titfont">量化交易之基金卖出
        </tr>
        <tr class="btbg titfont">
            <th>基金代码</th>
            <th>基金名称</th>
            <th>最新日期</th>
            <th>买入节点</th>
        </tr>
    <!-- trigger -->
    </table>
    <br>
    <table width="90%" border="1" cellspacing="0" cellpadding="4"  class="tabtop13">
                <tr>
                <th bgcolor="#6633FF" colspan="4" class="btbg titfont" style="color:#fff; font-weight: bold; ">量化交易之基金收益率
                </tr>
                <tr class="btbg titfont">
                    <th style='background:#E74C3C'>基金名称</th>
                    <th style='background:#E74C3C'>持有收益</th>
                    <th style='background:#E74C3C'>每日涨幅</th>
                    <th style='background:#E74C3C'>重要告警</th>
                </tr>
            <!-- host -->
        </table>
        <br>'''

    mail_html = open("table.html", "r", encoding="utf-8").read()
    #添加HTML文本内容
    mail_html = mail_html.replace('<!-- imgstart -->', table_html_code)
    #在里面添加表格形式，以表格的形式发送出来
    mail_html = mail_html.replace('<!-- trigger -->', text_to_html())
    mail_html = mail_html.replace('<!-- host -->', get_data())
    filename1 = './img/{}/{}/{}'.format(year, month, day)
    file_pathname = os.listdir(filename1)
    if len(file_pathname) > 0:
        for f in file_pathname:
            insert_img_str = """
                        <br><img src="cid:image%s" alt="image%s"><br><!-- imgend -->
                        """ % (f, f)
            mail_html = re.sub("<!-- imgend -->", insert_img_str, mail_html)

    content = MIMEText(mail_html, 'html', 'utf-8')
    msg.attach(content)


    if len(file_pathname) > 0:
        for f in file_pathname:
            fp = open('./img/{}/{}/{}/{}'.format(year, month, day, f), 'rb')
            msgImage = MIMEImage(fp.read())
            fp.close()
            msgImage.add_header('Content-ID', 'image' + str(f))  # 该id和html中的img src对应
            msg.attach(msgImage)


    smtp = SMTP_SSL(host_server)  # SSL 登录
    smtp.set_debuglevel(0)  # set_debuglevel()是用来调试的。参数值为1表示开启调试模式，参数值为0关闭调试模式
    smtp.ehlo(host_server)  # 连接服务器
    smtp.login(sender_qq, pwd)  # 邮箱登录



    try:
        smtp.sendmail(sender_qq_mail, receiver, msg.as_string())  # 发送邮件函数
        smtp.quit()  # 发送邮件结束
        print("Successfully Send！")  # 输出成功标志
    except Exception as e:
        print("The sever is busy,please continue later.",e)


if __name__ == '__main__':
    today = datetime.date.today()
    yesterday = datetime.timedelta(days=1)
    yesterday = today - yesterday
    yesterday = str(yesterday)
    today = str(today)
    year = today.split('-')[0]
    month = today.split('-')[1]
    day = today.split('-')[2]

    # read_file()

    try:
        receiver = sys.argv[1]
    except:
        receiver = 'Felix_Zeng@macroview.com'  # 收件人邮箱地址
    try:
        send_mail(receiver)  # 调用函数，发送邮件
    except:
        send_mail(receiver)  # 调用函数，发送邮件
