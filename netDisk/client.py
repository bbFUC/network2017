# coding=utf-8

import socket
import time
import getpass
import personalEncode
import md5
import os
import tkFileDialog

userDiskPath = 'C:/Users/Rock/Desktop/netDisk'


def Ls(conn, order):
    """
    查看当前目录下文件
    """
    conn.send(order[0])
    print conn.recv(1024)


def Cd(conn, order):
    """
    chage directory命令,改变当前目录
    """
    conn.send(order[0])
    conn.send(order[1])
    rec = conn.recv(1024)
    if rec == 'Wrong Dir!':
        print rec
    elif rec == 'No Authority!':
        print rec


def Exit(conn, order):
    """
    断开连接并退出
    """
    conn.send(order[0])
    print conn.recv(1024)


def Upload(conn, file):
    """
    向服务器发起upload请求,可视化上传页面可以可视化选择文件
    """
    conn.send(file[0])
    username = userDiskPath.split('/')[-1]
    username = 'C:/Users/Rock/Desktop/download/' + username
    fn = tkFileDialog.askopenfilename(initialdir=username)
    if fn == '':
        return
    filename = fn.split('/')[-1]
    conn.send(filename)
    md5Code = md5.new()
    md5Code.update(filename)
    with open(fn, 'rb') as f:
        while True:
            data = f.read(1024)
            # 若无数据
            if not data:
                break
            md5Code.update(data)
    conn.send(md5Code.hexdigest())

    info = conn.recv(1024)
    if info == 'md5upload':
        print 'Successfully Upload!'
        return

    if info == 'nofile':
        with open(fn, 'rb') as f:
            while True:
                data = f.read(1024)
                if not data:
                    break
                conn.sendall(data)
            time.sleep(1)
            conn.sendall('EOF')
            print 'Successfully Upload!'


def Download(conn, file):
    """
    向服务器发起下载请求，收到服务器发来的文件并下载到下载目录
    """
    conn.send(file[0])
    filename = file[1]
    username = userDiskPath.split('/')[-1]
    path = 'C:/Users/Rock/Desktop/download'
    path = path + '/' + username
    if os.path.exists(path) is False:
        os.makedirs(path)
    path = path + '/' + filename
    conn.send(filename)
    print 'Downloading...'
    writeFile = open(path, 'wb')
    while True:
        data = conn.recv(1024)
        if data == 'EOF':
            writeFile.close()
            print 'Download Successfully!'
            break
        writeFile.write(data)


def Login(conn):
    """
    输入账户名和密码来登陆网盘
    """
    print 'Sign in your account!'
    logInTime = 5
    isLogin = False
    while logInTime > 0:
        username = raw_input("Your Username: ")
        conn.send(username)
        password = getpass.getpass('Your Password: ')
        password = personalEncode.encode(password)
        conn.send(password)
        isLogin = conn.recv(1024)
        if isLogin == 'Welcome!':
            print 'Successfully Logged In! You can use the netDisk'
            global userDiskPath
            temPath = userDiskPath
            userDiskPath = temPath + '/' + username  # 改变路径 用户登录后只能在自己的网盘里上传和下载
            return True
        logInTime = logInTime - 1
        print 'Error Account! %d times login chance left' % logInTime

    return False


def Register(conn):
    """
    注册账户 之后登入账户才能进行操作
    """
    username = raw_input("Your Username: ")
    conn.send(username)
    time.sleep(1)
    password = raw_input('Your Password: ')
    password = personalEncode.encode(password)
    conn.send(password)
    message = conn.recv(1024)
    if message == 'ok':
        print 'sign up successfully!'


def Synchronize(conn):
    """
    网盘同步功能,使得网盘里面的内容和用户本地文件一致
    """
    print 'Begin to synchronize the netDisk...'
    conn.send('syn')
    username = userDiskPath.split('/')[-1]
    filePath = 'C:/Users/Rock/Desktop/download/' + username
    file = os.listdir(filePath)
    sendFile = ' '.join(file)
    conn.send(sendFile)

    command = conn.recv(1024)
    if command == 'denied':
        print 'You cannot synchronize under this public area!!'
        return
    elif command == 'removed':
        print 'First stage finished, begin next stage...'
        time.sleep(1)
    for target in file:
        conn.send('upload')
        time.sleep(1)
        conn.send(target)
        targetFile = filePath + '/' + target
        md5Code = md5.new()
        md5Code.update(targetFile)
        with open(targetFile, 'rb') as f:
            while True:
                data = f.read(1024)
                # 若无数据
                if not data:
                    break
                md5Code.update(data)
        conn.send(md5Code.hexdigest())

        info = conn.recv(1024)
        if info == 'md5upload':
            print 'Successfully Upload!'
            time.sleep(1)
            continue

        if info == 'nofile':
            with open(targetFile, 'rb') as f:
                while True:
                    data = f.read(1024)
                    if not data:
                        break
                    conn.sendall(data)
                time.sleep(1)
                conn.sendall('EOF')
                print 'Successfully Upload!'
            time.sleep(1)


if __name__ == '__main__':
    HOST = 'localhost'
    PORT = 1180
    socketServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socketServer.connect((HOST, PORT))


    print """Orders are listed below:
    1.ls                    -- Listed all files and directories
    2.cd <dir>              -- Change directory
    3.download <filename>   -- Download the files
    4.upload                -- Upload the files
    5.reg                   -- Register user
    6.login                 -- sign in your own account so that the file uploaded will be stored in your personal warehouse
    7.share                 -- Go to the public area and the file you uploaded will be shared to the public and everyone can download it
    8.shareoff              -- exit the public area and go back to user netDisk
    9.exit                  -- Exit the netdisk
    10.syn                  -- synchronize                  
    """

    loggedIn = False
    userpath = ''
    while True:
        data = raw_input('>>')
        order = data.split()
        if order[0] == 'ls' and loggedIn is True:
            Ls(socketServer, order)
        elif order[0] == 'cd' and loggedIn is True:
            Cd(socketServer, order)
        elif order[0] == 'exit':
            Exit(socketServer, order)
            break
        elif order[0] == 'reg':
            socketServer.send('register')
            Register(socketServer)
        elif order[0] == 'upload' and loggedIn is True:
            Upload(socketServer, order)
        elif order[0] == 'download' and loggedIn is True:
            Download(socketServer, order)
        elif order[0] == 'login':
            socketServer.send('login')
            loggedIn = Login(socketServer)
        elif order[0] == 'share' and loggedIn is True:
            socketServer.send('share')
            time.sleep(1)
        elif order[0] == 'shareoff' and loggedIn is True:
            socketServer.send('shareoff')
        elif order[0] == 'syn' and loggedIn is True:
            Synchronize(socketServer)
        else:
            print 'Wrong Command!'

    socketServer.close()
