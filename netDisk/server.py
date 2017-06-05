# coding=utf-8

import os
import socket
import time
import threading
import personalEncode
import shutil

md5File = "C:/Users/Rock/Desktop/netDisk/md5File.txt"


def getDir(path):
    """
    获取当前路径下的文件列表(ls)
    """
    file = os.listdir(path)
    fileList = []
    for target in file:
        if os.path.isdir(target):
            target = target + '/'
        fileList.append(target)

    return fileList


def Exit(conn, addr):
    """
    退出并关闭连接
    """
    conn.send('Cut Off the Connection!')
    conn.close()
    print 'Connection from %s:%s closed.' % addr


def Ls(conn, path):
    """
    给客户端返回当前文件夹的文件列表
    """
    file = getDir(path)
    file.append(path)
    fileList = '\n'.join(file)
    if fileList == '':
        conn.send(path + ':no file here')
        return
    conn.send(fileList)


def Cd(conn, path):
    """
    cd切换目录
    """
    data = conn.recv(1024)
    if data == '..':
        tem = path.split('/')
        if tem[-2] == 'netDisk':
            conn.send('No Authority!')
            return path
        if path[-1] == '/':
            tem = tem[:-2]
        else:
            tem = tem[:-1]
        newpath = '/'.join(tem)
        if path == '.':
            newpath = '.'
    elif data[0] == '.':
        if data[-1] == '/':
            newpath = data
        else:
            newpath = data + '/'
    else:
        if data[-1] == '/':
            newpath = path + '/' + data
        else:
            newpath = path + '/' + data

    if os.path.isdir(newpath):
        conn.send('Yes')
        print newpath
        return newpath
    else:
        conn.send('Wrong Dir!')
        return path


def Upload(conn, path):
    """
    上传文件，这里加了md5码验证,通过与md5File比较是否存在相同的文件，实现极速秒传
    """
    print 'Begin to upload file!'
    isUpload = False  # 判断文件是否存在
    filename = conn.recv(1024)
    tem = conn.recv(1024)
    # 验证文件与md5列表内容是否一致
    with open(md5File, 'rb') as f:
        while True:
            line = f.readline()
            # 读完了
            if not line:
                break
            codeList = line.split()
            if tem == codeList[0]:
                isUpload = True
                print 'quick transform!!'
                source = codeList[1]
                # 把已有文件copy一遍
                if source != path:
                    shutil.copy(source, path)
                conn.send('md5upload')
                print 'File upload successfully!'
                return

    if isUpload is False:
        conn.send('nofile')
    # 新文件，则向md5File写入此文件
        with open(md5File, 'a+') as f:
            line = tem + ' ' + path + '/' + filename + '\n'
            f.write(line)
        path = path + '/' + filename

        with open(path, 'wb') as f:
            while True:
                file = conn.recv(1024)
                if file == 'EOF':
                    print 'File upload successfully!'
                    break
                f.write(file)


def Download(conn, path):
    """
    下载文件
    """
    print 'Begin to download file!'
    filename = conn.recv(1024)
    path = path + '/' + filename
    with open(path, 'rb') as f:
        while True:
            data = f.read(1024)
            if not data:
                break
            conn.send(data)
    time.sleep(1)
    conn.send('EOF')
    print 'Successfully Downloaded!'


def isLogin(conn, path):
    """
    验证Client输入的用户名和密码，解密信息并验证是否是注册用户
    """
    logInTime = 5
    while logInTime > 0:
        username = conn.recv(1024)
        password = conn.recv(1024)
        password = personalEncode.decode(password)  # 解密用户信息
        # 将用户信息和已有的用户名单作对比，正确则登入
        with open('C:/Users/Rock/Desktop/netDisk/userList.txt', 'r') as userFile:
            for line in userFile:
                line = line.strip('\n')
                lineList = line.split(' ')
                if username == lineList[0] and password == lineList[1]:
                    conn.send('Welcome!')
                    path = path + '/' + username  # 改变路径 用户登录后只能在自己的网盘里上传和下载
                    return path
        conn.send('Fail Login!')
        logInTime = logInTime - 1

    return False


def Register(conn, path):
    """
    注册账户 之后登入账户才能进行操作
    """
    userList = open('C:/Users/Rock/Desktop/netDisk/userList.txt', 'a')
    username = conn.recv(1024)
    password = conn.recv(1024)
    password = personalEncode.decode(password)
    userList.write(username + ' ' + password + '\n')
    path = 'C:/Users/Rock/Desktop/netDisk/download'
    path = path + '/' + username
    if os.path.exists(path) is False:
        os.makedirs(path)
    conn.send('ok')
    userList.close()


def Synchronize(conn, path):
    """
    删除和同步文件夹不一致的内容
    """
    # 如果是在Public目录下同步 则请求被拒绝
    if path == 'C:/Users/Rock/Desktop/netDisk/public':
        conn.send('denied')
        return
    file = conn.recv(1024)
    netDiskFile = getDir(path)
    if netDiskFile == []:
        conn.send('removed')
        return
    fileList = file.split(' ')
    for item1 in fileList:
        flag = 0
        for item2 in netDiskFile:
            print 'item1, item2', item1, item2
            if item1 == item2:
                flag = 1
        if flag == 0:
            filename = path + '/' + item2
            if os.path.isfile(filename):
                os.remove(filename)
    conn.send('removed')


def main(conn, addr, path):
    """
    多线程的目标函数 同时是网盘分析命令的地方
    """
    print 'Connected by ', addr
    userpath = path

    while True:
        order = conn.recv(1024)
        if order == 'ls':
            print path
            Ls(conn, path)
        elif order == 'login':
            tem = isLogin(conn, path)
            if tem is False:
                return
            else:
                path = tem  # 改变路径 用户登录后只能在自己的网盘里上传和下载
                userpath = path  # 用userpath保存网盘用户的存储路径,退出share模式后可以重新定位到用户网盘
                if os.path.exists(path) is False:
                    os.makedirs(path)
        elif order == 'cd':
            path = Cd(conn, path)
        elif order == 'upload':
            Upload(conn, path)
        elif order == 'download':
            Download(conn, path)
        elif order == 'exit':
            Exit(conn, addr)
        elif order == 'share':
            path = 'C:/Users/Rock/Desktop/netDisk/public'   # 转到网盘共享区
        elif order == 'shareoff':
            path = userpath   # 返回用户网盘
        elif order == 'register':
            Register(conn, path)
        elif order == 'syn':
            Synchronize(conn, path)
        else:
            print 'wrong command!'

if __name__ == '__main__':
    HOST = 'localhost'
    PORT = 1180  # 大于1024均可
    socketServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 创建ipv4 TCP连接
    socketServer.bind((HOST, PORT))
    socketServer.listen(5)  # 允许最多5个连接

    print 'Server start at: %s:%s' % (HOST, PORT)
    print 'wait for connection...'

    while True:
        netDisk = 'C:/Users/Rock/Desktop/netDisk'
        conn, addr = socketServer.accept()
        # 创建新线程来处理TCP连接:
        t = threading.Thread(target=main, args=(conn, addr, netDisk))
        t.start()

    socketServer.close()
