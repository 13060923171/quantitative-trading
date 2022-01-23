import shutil
try:
    shutil.rmtree('./data')
    print("File removed successfully")
except:
    print('该文件不存在')