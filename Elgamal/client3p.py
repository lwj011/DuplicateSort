import socket
import time
from elgamal import get_p_g, fastExpMod
from random import randint
from client import client_function
bufsize = 40960000  #缓冲区大小
bufsize_s = 1024
n_p = 256  #mod p中p的bit数,can change
n_sk = 128  #sk的bit数, can change
max2 = 12 #2进制下最大位数, can change
ip = socket.gethostbyname(socket.gethostname())
#ip = '127.0.0.1'
base_port = 60000  #基础端口号,client Pi 的端口号为base_port+numb(+0开始)
#通信完成后立刻用close()断开,密钥分发、矩阵获取分发等均由P0发起通信,最后计算Pi的order时由Pi发起通信
#自定义协议三个参与者,当初始sord均为0则是多重排序,为1234...时为增序排序
comm = [0,0,0]  #通信开销,分别为P1发送,P2发送,P3发送


def get_pki(port,p,g):  #P0执行向Pi发送p,g,得到Pi的pki,port是Pi的端口号
    cl0 = socket.socket()
    cl0.connect((ip, port))
    comm[0] += cl0.send((str(p)+','+str(g)).encode())
    pki = int(cl0.recv(bufsize_s).decode())
    cl0.close()
    return pki

def send_pk(port, pk):  #P0执行向Pi发送pk
    cl0 = socket.socket()
    cl0.connect((ip, port))
    comm[0] += cl0.send((str(pk)).encode())
    cl0.close()
    return 0

def client_3p(data0,sord, numb, l0, l1, l2):  #客户端,输入数据,初始序列,客户端编号,三个客户端的数据长度
    n_data = l0 + l1 + l2  # 参与排序是数据数量
    lim = 2 * n_data + 1  #数据编码时的范围限制
    data = []
    comm = [0, 0, 0]  #初始化
    for i in range(len(data0)):
        data.append(data0[i])
    if lim>=n_p-1:  #必须满足lim<n_p-1
        print('the lim is %d'%lim)
        print('the p is too small')
    if numb<0 or numb>=3:
        print('the client number is error')
    if numb==0:  #由P0生成p,g,并接受信息生成pk
        time.sleep(3)  #question?确保Pi先运行监听,P0随后运行发起连接
        clnumb = socket.socket()
        clnumb.bind((ip, base_port + numb))
        clnumb.listen(100)
        print('-----------------P%d started-----------------' % numb)
        t0 = time.time()  #P0开始运行的时间
        p, g = get_p_g(n_p)
        pk_i = []
        sk0 = randint(2 ** (n_sk - 1), 2 ** n_sk)
        pk0 = fastExpMod(g, sk0, p)
        pk_i.append(pk0)
        #P0将p,g发送给所有Pi,得到pki
        for po in range(base_port+1,base_port+3):  #这部分自己实现的不好question?
            pk_i.append(get_pki(po, p, g))
        pk = 1
        for i in range(len(pk_i)):
            pk = pk * pk_i[i] % p
        for po in range(base_port + 1, base_port + 3):  # 这部分自己实现的不好question?
            send_pk(po, pk)
        t1 = time.time()
        print('-----------------ken generation finished, using %f s-----------------'%(t1-t0))
        h0 = sord
        for i in range(max2):
            data_temp=[]
            for j in range(len(data)):
                data_temp.append((data[j]%2)*n_data + h0[j])
            #print('----------')
            #print(comm)
            h0, scom0 = client_function(clnumb,data_temp,numb,lim,p,g,pk,sk0, l0, l1, l2, comm[numb])
            comm[numb] = scom0
            #print(comm)
            #print('-------------%d bit has finished----------------------------------'%i)
            for j in range(len(data)):
                data[j] = int(data[j]/2)
        print('P%d data and ord is:'%numb)
        print('-----------------P%d sent %f MB-----------------' % (numb, comm[numb]/1024/1024))
        print(data0)
        print(h0)
        clnumb.close()
        t2 = time.time()
        print('-----------------end, total time is %f s-----------------'%(t2-t0))

    else:  #其他Pi接收p,g,生成ski,并给P0发送pki,接收pk
        clnumb = socket.socket()
        clnumb.bind((ip, base_port+numb))
        clnumb.listen(100)
        print('-----------------P%d started-----------------'%numb)
        cl0, addr = clnumb.accept()
        pandg = cl0.recv(bufsize_s).decode().split(',')
        p = int(pandg[0])
        g = int(pandg[1])
        sknumb = randint(2 ** (n_sk - 1), 2 ** n_sk)
        pknumb = fastExpMod(g, sknumb, p)
        comm[numb] += cl0.send(str(pknumb).encode())
        cl0, addr = clnumb.accept()
        pk = int(cl0.recv(bufsize_s).decode())
        h0 = sord
        for i in range(max2):
            data_temp = []
            for j in range(len(data)):
                data_temp.append((data[j] % 2) * n_data + h0[j])
            h0, scomi = client_function(clnumb,data_temp,numb,lim,p,g,pk,sknumb, l0, l1, l2, comm[numb])
            comm[numb] = scomi
            for j in range(len(data)):
                data[j] = int(data[j] / 2)
        print('P%d data and ord is:' % numb)
        print('-----------------P%d sent %f MB-----------------' % (numb, comm[numb]/1024/1024))
        print(data0)
        print(h0)
        clnumb.close()

