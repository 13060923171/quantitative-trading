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
from tqdm import tqdm
import itertools
#填写基金的代码
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
    html = requests.post(url,headers=headers,data=data,verify=False,timeout=15)
    if html.status_code == 200:
        #对获取到的内容进行定位
        content = html.json()
        #获取基金的内容
        data = content['Data']['KFS']
        for d in data[:-2]:
            #基金名字
            name = d['SHORTNAME']
            # 净值估算
            gsz = d['gsz']
            return name,gsz

    else:
        print(html.status_code)


def read_file():
    total = []
    #创建对应日期的文件
    filename = './data/{}/{}/{}'.format(year, month, day)
    #去获取该文件夹下的所有文件名称
    file_pathname = os.listdir(filename)
    for f in tqdm(file_pathname):

        code = f[:-4]
        #读取文件
        df = pd.read_csv('./data/{}/{}/{}/{}'.format(year, month, day,f)).loc[:,['净值日期','单位净值']]
        name, gsz = parse_url(code)
        #获取基金的名字和净值估算
        try:
            #将最新获取的和之前的合并成一个新的dataframe
            df2 = pd.DataFrame([[str(today),float(gsz)]], columns=['净值日期','单位净值'])
            df = df.append(df2, ignore_index=True)
        except ValueError:
            df = df
        df1 = df.copy()
        df1.index = df1['净值日期']
        close = df['单位净值']
        days = df['净值日期']
        close1 = close.values

        #用的是wma平均加权值算法
        def wmaCal(tsPrice, number):
            b = np.arange(1, int(number+1))
            w = b / sum(b)
            k = len(w)
            arrWeight = np.array(w)
            Wma = pd.Series(0.0, index=tsPrice.index)
            for i in range(k - 1, len(tsPrice.index)):
                Wma[i] = sum(arrWeight * tsPrice[(i - k + 1):(i + 1)])
            return (Wma)

        day_5 = 5
        day_20 = 20
        wma5 = wmaCal(close,day_5)
        wma20 = wmaCal(close, day_20)

        days = days.values
        #用ma5-ma20为后面区分段落做准备
        list_T1 = []
        for j in range(len(wma5.index)):
            if wma5[j] != 0.0 and wma20[j] != 0.0:
                T1 = wma5[j] - wma20[j]
                list_T1.append(T1)

        list_out = []
        sum_datetime = []
        list_datetime = []
        list_out2 = []

        total_list = []
        for j, k in zip(list_T1, days[int(day_20 - 1):]):
            total_list.append((j, k))

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
            #     if sum(list_out2[-1]) > 0:
            # 如果该段落的最后一段总和大于零，说明这时候蓝线在下，红线在上，是最后一段
            if sum(list_out2[j]) >= 0:
                #         #蓝线的头为卖出，蓝线的尾为买入
                a = [list_out2[j][0], '买入', sum_datetime[j][0]]
                list_sum.append(a)
            #否则，该蓝线在上，但没有交叉点，所以无法判断最后买入的时间，只能给出最后卖出的时间
            elif sum(list_out2[j]) < 0:
                a = [list_out2[j][0], '卖出', sum_datetime[j][0]]
                list_sum.append(a)
        #创建保存图片的文件夹
        filename1 = './img/{}/{}/{}'.format(year, month, day)
        if not os.path.exists(filename1):
            os.makedirs(filename1)
        #对买入和卖出的列表进行切割，删除不符合规范的列表的头部和尾部，使得最后呈现买入，卖出，这样的数据结构
        def clsj(list_sum):
            #头部是卖出则删除头部卖出的部分
            if list_sum[0][1] == '卖出':
                #尾部是买入则删除尾部买入的部分
                list_sum = list_sum[1:]
                if list_sum[-1][1] == '买入':
                    list_sum = list_sum[:-1]
                    return list_sum
                else:
                    return list_sum
            # 尾部是买入则删除尾部买入的部分
            elif list_sum[-1][1] == '买入':
                list_sum = list_sum[:-1]
                # 头部是卖出则删除头部卖出的部分
                if list_sum[0][1] == '卖出':
                    list_sum = list_sum[1:]
                    return list_sum
                else:
                    return list_sum
            else:
                return list_sum
        #获取清洗好的数据列表
        list_sum1 = clsj(list_sum)

        time_date = []
        #把它们买入卖出的时间收集起来
        for i in list_sum1:
            time_date.append(i[2])

        #获取它们对应的收益率情况
        sum_close = []
        for t in time_date:
            close2 = df1.loc[(t),'单位净值']
            close3 = "%0.4lf" %close2
            sum_close.append(float(close3))

        #计算它们买入和卖出之间这个周期的收益情况

        def jisuan(g, c):
            syl = "%0.2lf" % (float(float(float(g) - float(c)) / float(c)) * 100)
            return syl

        sum_syl = []
        #然后去汇总，它们一年下来的平均收益情况如何来判断该基金是否适合买入
        for s in range(0,len(sum_close),2):
            # 卖出时的价格
            g = sum_close[s+1]
            #买入时的价格
            c = sum_close[s]
            #收益率
            syl = jisuan(g,c)
            sum_syl.append(float(syl))
        #计算它的下半年的平均收益情况
        mean_syl = "%0.2lf" % np.mean(sum_syl[int(len(sum_syl)/2):len(sum_syl)])


        for l in list_sum:
            # print([l[1], l[2], code, name])
            #然后时间是今天，并且状态是买入，那么符合我们的判断条件
            if l[2] == today and l[1] == '买入' and float(mean_syl) > 0:
                #把该时间，状态值，代码和名称传入列表用于后面发送邮箱
                total.append([l[1], l[2], code, name,sum_syl[-2],sum_syl[-1], mean_syl])
                #并且开始做图，画出最新的图形状态，根据图来做出判断
                plt.rcParams['font.sans-serif'] = ['simhei']
                plt.figure(figsize=(9, 6))
                plt.plot(close[int(day_5 - 1):], label='Close', color='g')
                plt.plot(wma5[int(day_5 - 1):], label='wma5', color='r')
                plt.plot(wma20[int(day_20 - 1):], label='wma20', color='b')
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
        #删除图片的文件夹
        shutil.rmtree('./img')
        print("File removed successfully")
    except:
        return '该文件不存在'


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
                            <td>{}</td>
                            <td>{}</td>
                            <td>{}</td>            
                            </tr>'''.format(l[2], l[3], l[1], l[0], l[4], l[5], l[6])
            trigger_html_str = trigger_html_str + tail_html_str
        return trigger_html_str
    else:
        trigger_html_str = ''
        return trigger_html_str


def send_mail(receiver):
    #这一块是发件人要填写的内容
    host_server = 'xxx'  # QQ邮箱的SMTP服务器
    sender_qq = 'xxx'  # 发件人的QQ号码
    pwd = 'xxx'  # QQ邮箱的授权码
    sender_qq_mail = 'xxx'  # 发件人邮箱地址

    mail_title = '量化交易之基金买入'  # 设置邮件标题

    msg = MIMEMultipart('related')
    msg["Subject"] = Header(mail_title, 'utf-8')  # 填写邮件标题
    msg["From"] = sender_qq_mail  # 发送者邮箱地址
    msg["To"] = receiver  # 接收者邮件地址

    table_html_code = '''
    <table width="90%" border="1" cellspacing="0" cellpadding="4" bgcolor="#cccccc" class="tabtop13">
        <tr>
        <th colspan="7" class="btbg titfont">量化交易之基金买入
        </tr>
        <tr class="btbg titfont">
            <th>基金代码</th>
            <th>基金名称</th>
            <th>最新日期</th>
            <th>买入节点</th>
            <th>收益率二</th>
            <th>收益率一</th>
            <th>平均收益</th>
        </tr>
    <!-- trigger -->
	</table>
	<br>'''

    mail_html = open("table.html", "r", encoding="utf-8").read()
    #添加HTML文本内容
    mail_html = mail_html.replace('<!-- imgstart -->', table_html_code)
    #在里面添加表格形式，以表格的形式发送出来
    mail_html = mail_html.replace('<!-- trigger -->', text_to_html())

    filename1 = './img/{}/{}/{}'.format(year, month, day)
    file_pathname = os.listdir(filename1)
    #批量读取图片并且发送
    if len(file_pathname) > 0:
        for f in file_pathname:
            insert_img_str = """
                        <br><img src="cid:image%s" alt="image%s"><br><!-- imgend -->
                        """ % (f, f)
            mail_html = re.sub("<!-- imgend -->", insert_img_str, mail_html)

    content = MIMEText(mail_html, 'html', 'utf-8')
    msg.attach(content)

    #这一块也是
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
        receiver = 'xxxx'  # 收件人邮箱地址
    try:
        send_mail(receiver)  # 调用函数，发送邮件
        remove_img()
    except:
        send_mail(receiver)  # 调用函数，发送邮件
        remove_img()
