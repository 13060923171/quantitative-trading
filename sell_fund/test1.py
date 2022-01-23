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
    sum_mean = []
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

        df1 = df.copy()
        df1.index = df1['净值日期']
        close = df['单位净值']
        days = df['净值日期']
        close1 = close.values

        #5日线
        ma5 = pd.Series(0.0,index=close.index)
        for i in range(4,len(close1)):
            ma5[i] = float(sum(close1[(i-4):(i+1)]) / 5)

        #20日线
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
            # 如果该段落的最后一段总和大于零，说明这时候蓝线在下，红线在上，是最后一段
            if sum(list_out2[j]) >= 0:
                #蓝线的头为卖出，蓝线的尾为买入
                a = [list_out2[j][0], '买入', sum_datetime[j][0]]
                list_sum.append(a)
            # 否则，该蓝线在上，但没有交叉点，所以无法判断最后买入的时间，只能给出最后卖出的时间
            elif sum(list_out2[j]) < 0:
                a = [list_out2[j][0], '卖出', sum_datetime[j][0]]
                list_sum.append(a)
        filename1 = './img/{}/{}/{}'.format(year, month, day)
        if not os.path.exists(filename1):
            os.makedirs(filename1)
        #对买入和卖出的列表进行切割，删除不符合规范的列表的头部和尾部，使得最后呈现买入，卖出，这样的数据结构
        def clsj(list_sum):
            # 头部是卖出则删除头部卖出的部分
            if list_sum[0][1] == '卖出':
                # 尾部是买入则删除尾部买入的部分
                list_sum = list_sum[1:]
                if list_sum[-1][1] == '买入':
                    list_sum = list_sum[:-1]
                    return list_sum
                else:
                    return list_sum
            # 尾部是买入则删除尾部买入的部分
            elif list_sum[-1][1] == '买入':
                # 头部是卖出则删除头部卖出的部分
                list_sum = list_sum[:-1]
                if list_sum[0][1] == '卖出':
                    list_sum = list_sum[1:]
                    return list_sum
                else:
                    return list_sum
            else:
                return list_sum

        # 获取清洗好的数据列表
        list_sum1 = clsj(list_sum)
        time_date = []
        # 把它们买入卖出的时间收集起来
        for i in list_sum1:
            time_date.append(i[2])

        # 获取它们对应的收益率情况
        sum_close = []
        for t in time_date:
            close2 = df1.loc[(t), '单位净值']
            close3 = "%0.4lf" % close2
            sum_close.append(float(close3))

        # 计算它们买入和卖出之间这个周期的收益情况
        def jisuan(g, c):
            syl = "%0.2lf" % (float(float(float(g) - float(c)) / float(c)) * 100)
            return syl

        # print(len(sum_close))
        sum_syl = []
        # 然后去汇总，它们一年下来的平均收益情况如何来判断该基金是否适合买入
        for s in range(0, len(sum_close), 2):
            # 卖出时的价格
            g = sum_close[s + 1]
            # 买入时的价格
            c = sum_close[s]
            # 收益率
            syl = jisuan(g, c)
            sum_syl.append(float(syl))
        # 计算它的下半年的平均收益情况
        mean_syl = "%0.2lf" % np.mean(sum_syl[int(len(sum_syl)/2):len(sum_syl)])

        #去获取最后一次买入的基金净值时间
        if list_sum[-1][1] == '买入':
            finally_sell_time = list_sum[-1][2]
        else:
            finally_sell_time = list_sum[-2][2]
        # 去获取最后一次买入的基金净值
        finally_sell_close = df1.loc[(finally_sell_time), '单位净值']
        finally_sell_close1 = "%0.4lf" % finally_sell_close

        dic = {
            'code':code,
            'mean_syl':mean_syl,
            'finally_sell_close':finally_sell_close1
        }
        sum_mean.append(dic)

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

    return total,sum_mean


#删除整个文件夹
def remove_img():
    import shutil
    try:
        # 删除图片的文件夹
        shutil.rmtree('./img')
        print("File removed successfully")
    except:
        return '该文件不存在'


#计算总基金持有收益
def get_data():
    #将上面获取到的基金列表，按照TXT文档的顺序进行重新排序
    def new_list(code):
        for s in sum_mean:
            if s['code'] == code:
                return s


    list_name = []
    list_gsz = []
    list_gszzl = []
    #获取基金代码
    with open('所持基金.txt','r',encoding='utf-8')as f:
        content = f.readlines()
    list_code = [str(c).replace('\n', '') for c in content]
    new_code = []
    #整理好一个新的列表，顺序就是按照TXT文件的顺序来进行
    for code in list_code:
        dic = new_list(code)
        new_code.append(dic)

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

                #中欧   医药    汇丰    国投    创金    华夏    医疗    蓝筹
    list_cbj = [3.5660, 1.1051, 5.0805, 4.7088, 3.5077, 4.5915, 3.4733, 2.9064]
    for i in range(len(list_cbj)):
        #获取基金的名字
        n = list_name[i]
        #获取最新的净值单位
        g = list_gsz[i]
        #获取持仓的基金净值单位
        c = list_cbj[i]
        #获取每日最新的涨幅
        gz = list_gszzl[i]
        #获取半年平均涨幅
        mean_syl = new_code[i]['mean_syl']
        #获取最后买入的时间的单位净值
        finally_sell_close = new_code[i]['finally_sell_close']
        #获取总体的收益情况
        syl = jisuan(g,c)
        #获取最后买入时间单位净值与最新单位净值的收益情况
        finally_syl = jisuan(g,finally_sell_close)
        if float(syl) >= 8:
            neirong = '收益率大于8,请速抛！！！'
            list_sum.append([n, syl, gz, finally_syl, mean_syl, neirong])
        elif float(gz) <= -1.5:
            neirong = '跌幅大于-1.5,可以加仓'
            list_sum.append([n, syl, gz, finally_syl, mean_syl, neirong])
        elif float(finally_syl) >= float(mean_syl):
            neirong = '增幅已大于平均增幅，可以抛售'
            list_sum.append([n, syl, gz, finally_syl, mean_syl, neirong])
        else:
            neirong = ''
            list_sum.append([n, syl, gz, finally_syl, mean_syl, neirong])


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
                            </tr>'''.format(l[0], l[1], l[2], l[3], l[4], l[5])
            trigger_html_str = trigger_html_str + tail_html_str
        return trigger_html_str
    else:
        trigger_html_str = ''
        return trigger_html_str


def text_to_html():
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
                <th bgcolor="#6633FF" colspan="6" class="btbg titfont" style="color:#fff; font-weight: bold; ">量化交易之基金收益率
                </tr>
                <tr class="btbg titfont">
                    <th style='background:#E74C3C'>基金名称</th>
                    <th style='background:#E74C3C'>持有收益</th>
                    <th style='background:#E74C3C'>每日涨幅</th>
                    <th style='background:#E74C3C'>买入涨幅</th>
                    <th style='background:#E74C3C'>平均收益</th>
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

    list_sum,sum_mean = read_file()

    try:
        receiver = sys.argv[1]
    except:
        receiver = 'Felix_Zeng@macroview.com'  # 收件人邮箱地址
    try:
        send_mail(receiver)  # 调用函数，发送邮件
        remove_img()
    except:
        send_mail(receiver)  # 调用函数，发送邮件
        remove_img()
