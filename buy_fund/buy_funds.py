import requests
import sys,os,re
import pandas as pd
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
    html = requests.post(url,headers=headers,data=data,verify=False)
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

        close = df['单位净值']
        days = df['净值日期']
        close1 = close.values
        #计算ma5的值
        ma5 = pd.Series(0.0,index=close.index)
        for i in range(4,len(close1)):
            ma5[i] = float(sum(close1[(i-4):(i+1)]) / 5)
        #计算ma20的值
        ma20 = pd.Series(0.0,index=close.index)
        for i in range(19,len(close1)):
            ma20[i] = float(sum(close1[(i-19):(i+1)]) / 20)

        days = days.values
        #用ma5-ma20为后面区分段落做准备
        list_T1 = []
        for j in range(len(ma5.index)):
            if ma5[j] != 0.0 and ma20[j] != 0.0:
                T1 = ma5[j] - ma20[j]
                list_T1.append(T1)

        list_out = []
        sum_datetime = []
        temp = []
        list_datetime = []
        count = 0
        list_out2 = []
        for j,k in itertools.groupby(list_T1,lambda x: x < 0):
            list_out2.append(list(k))

        #对数据开始判断是否是连续值
        while count+1 < len(list_T1):
            temp.append(list_T1[count])
            list_datetime.append(days[count+19])
            #当两个相乘为正的时候，那么就是连续的，一直这样乘下去，直到出现小于0那就是不连续正数或者负数，这样开始打断
            while list_T1[count] * list_T1[count+1] >= 0:
                temp.append(list_T1[count + 1])
                list_datetime.append(days[count+20])
                count += 1
                if count+1 == len(list_T1):
                    break
            list_out.append(temp)
            sum_datetime.append(list_datetime)
            #把该列表清空
            temp = []
            list_datetime = []
            count += 1

        if len(list_out) != len(list_out2):
            changdu = len(list_out2) - len(list_out)
            a = list_out2[-changdu]
            b = days[-1]
            list_out.append(a)
            sum_datetime.append([b])

        list_sum = []

        for j in range(len(list_out)):

            #如果该段落的和小于0，说明蓝线在上，红线在下，符合我们的判断继续下一步
            if sum(list_out[j]) < 0:
                #如果该段落的最后一段总和大于零，说明这时候蓝线在下，红线在上，是最后一段
                if sum(list_out[-1]) > 0:
                    #蓝线的头为卖出，蓝线的尾为买入
                    a = [[list_out[j][0], '卖出', sum_datetime[j][0]], [list_out[j][-1], '买入', sum_datetime[j][-1]]]
                    list_sum.append(a[0])
                    list_sum.append(a[1])
                #否则，该蓝线在上，但没有交叉点，所以无法判断最后买入的时间，只能给出最后卖出的时间
                else:
                    a = [[list_out[j][0], '卖出', sum_datetime[j][0]]]
                    list_sum.append(a[0])

        filename1 = './img/{}/{}/{}'.format(year, month, day)
        if not os.path.exists(filename1):
            os.makedirs(filename1)

        for l in list_sum:
            #然后时间是今天，并且状态是买入，那么符合我们的判断条件
            if l[2] == today and l[1] == '买入':
                # print([l[1], l[2], code, name])
                #把该时间，状态值，代码和名称传入列表用于后面发送邮箱
                total.append([l[1], l[2], code, name])
                #并且开始做图，画出最新的图形状态，根据图来做出判断
                plt.rcParams['font.sans-serif'] = ['SimHei']
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
    #这一块是发件人要填写的内容
    host_server = 'smtp.qq.com'  # QQ邮箱的SMTP服务器
    sender_qq = '960751327'  # 发件人的QQ号码
    pwd = 'fdrrjmiqqnaubdcj'  # QQ邮箱的授权码
    sender_qq_mail = '960751327@qq.com'  # 发件人邮箱地址

    mail_title = '量化交易之基金买入'  # 设置邮件标题

    msg = MIMEMultipart('related')
    msg["Subject"] = Header(mail_title, 'utf-8')  # 填写邮件标题
    msg["From"] = sender_qq_mail  # 发送者邮箱地址
    msg["To"] = receiver  # 接收者邮件地址

    table_html_code = '''
    <table width="90%" border="1" cellspacing="0" cellpadding="4" bgcolor="#cccccc" class="tabtop13">
        <tr>
        <th colspan="4" class="btbg titfont">量化交易之基金买入
        </tr>
        <tr class="btbg titfont">
            <th>基金代码</th>
            <th>基金名称</th>
            <th>最新日期</th>
            <th>买入节点</th>
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
    threeday = datetime.timedelta(days=3)
    day3 = today - threeday
    day3 = str(day3)
    today = str(today)
    year = today.split('-')[0]
    month = today.split('-')[1]
    day = today.split('-')[2]

    # read_file()

    try:
        receiver = sys.argv[1]
    except:
        receiver = 'Felix_Zeng@macroview.com'  # 收件人邮箱地址
    send_mail(receiver)  # 调用函数，发送邮件
