import json
import math
import socket
import pickle
from elgamal import fastExpMod, encrypt, e_gcd
bufsize = 40960000  #Ci和Mlf的缓冲区大小
bufsize_s = 1024  #接受pk,g,p,ui的缓冲区大小
ip = socket.gethostbyname(socket.gethostname())
#ip = '127.0.0.1'
base_port = 60000  #基础端口号,client Pi 的端口号为base_port+numb(+0开始)
comm = [0,0,0]  #储存发送数据量

#发送大规模数据
def send_dumps(cli, M):
    #等效于cli.send(bytes(json.dumps(M).encode('utf-8')))
    scom = 0 #cli发送的数据量
    lm = len(M)
    scom += cli.send(bytes(json.dumps(lm).encode('utf-8')))
    #print('send lm')
    #tag = json.loads(cli.recv(bufsize_s))
    #print('get ok1')
    for i in range(lm):
        temp_m = []
        temp_m.append(i)
        temp_m.append(M[i])
        tag = json.loads(cli.recv(bufsize_s))
        #print('send get tag ok')
        scom += cli.send(bytes(json.dumps(temp_m).encode('utf-8')))
        #print('send has send temp_m')
    tag = json.loads(cli.recv(bufsize_s))
    return scom

#接受大规模数据
def rec_loads(cli):
    #等效于json.loads(cli.recv(bufsize))
    lm = json.loads(cli.recv(bufsize_s))
    scom = 0  #cli发送的数据量
    #print('lm is %d '%lm)
    Mlf = [0]*lm
    #cli.send(bytes(json.dumps('ok').encode('utf-8')))
    for i in range(lm):
        scom += cli.send(bytes(json.dumps('ok').encode('utf-8')))
        #print('send ok')
        temp_m = json.loads(cli.recv(bufsize))
        #print('get temp_m')
        Mlf[temp_m[0]] = temp_m[1]
    scom += cli.send(bytes(json.dumps('end').encode('utf-8')))
    return Mlf,scom

def send_M(port,M):  #P0执行向Pi发送M
    cl0 = socket.socket()
    cl0.connect((ip, port))
    scom1 = send_dumps(cl0, M[0])
    scom2 = send_dumps(cl0, M[1])
    if port==base_port+1:  #实际中广播即可
        comm[0] += scom1
        comm[0] += scom2
    cl0.close()
    return 0

def get_u_sk(port,u):  #向port公布u,然后接收u^sk,适用于P0和Pi
    cl0 = socket.socket()
    cl0.connect((ip, port))
    com1 = cl0.send(pickle.dumps(u))
    usk = pickle.loads(cl0.recv(bufsize_s))
    cl0.close()
    return usk, com1

def get_Ci(port):  #P0执行,从Pi处得到Ci
    cl0 = socket.socket()
    cl0.connect((ip, port))
    #print('get ci has connected')
    Cleft,scom1 = rec_loads(cl0)
    Cright,scom2 = rec_loads(cl0)
    comm[0] += scom1
    comm[0] += scom2
    cl0.close()
    return Cleft,Cright

def get_vector(data, lim):
    #[0,0,0,1,1,1,...,1]表示data=4,[]长度为lim
    list = [0]*lim
    for i in range(data-1, lim):
        list[i] = list[i] + 1
    return list

def get_hi(Mleft, Mright, p, g, pk, data, n_data): #计算Hi,针对协议1,数据范围有限且并列计位
    u,v = encrypt(p,g,pk,1)
    for i in range(n_data):
        u = (u * Mleft[i][data-2]) % p
        v = (v * Mright[i][data-2]) % p
    return u,v

def get_ord(Mleft,Mright,p,g,pk,data,sknumb,numb, n_data):  #得到Pnumb的协议1位置,适用于P0和Pi
    if data == 1:
        u0,v0 = encrypt(p,g,pk,1)
        for po in range(base_port, base_port + numb):  #防止其他参与方一直等待
            usknumb, com1 = get_u_sk(po, u0)
            comm[numb] += com1
        for po in range(base_port + numb + 1, base_port + 3):
            usknumb, com1 = get_u_sk(po, u0)
            comm[numb] += com1
        h0 = 1
    else:
        sk0 = sknumb
        u0, v0 = get_hi(Mleft, Mright, p, g, pk, data, n_data)
        usk = fastExpMod(u0, sk0, p)
        for po in range(base_port, base_port + numb):
            usknumb, com1 = get_u_sk(po, u0)
            comm[numb] += com1
            usk = usk * usknumb % p
        for po in range(base_port + numb + 1, base_port + 3):
            usknumb, com1 = get_u_sk(po, u0)
            comm[numb] += com1
            usk = usk * usknumb % p
        temp1, usk_1, temp2 = e_gcd(usk, p)
        h0 = v0 * usk_1 % p
        h0 = int(math.log2(h0))
    return h0


def client_function(clnumb, data0, numb, lim, p, g, pk, sknumb, l0, l1, l2, comm_one):  #在client_function2基础上修改,大数组pickle换成json
    lim = lim+2  #
    data = []
    n_data = l0 + l1 + l2
    for i in range(len(data0)):
        data.append(data0[i]+2)
    if numb == 0:  # 由P0生成p,g,并接受信息生成pk
        # 1.根据data生成lim维向量,加密,公布
        comm[numb] = comm_one
        U0 = []
        for i in range(len(data)):
            U0.append(get_vector(data[i], lim))
        Cleft0 = []  # c1
        Cright0 = []  # c2
        for j in range(len(U0)):
            Cleft01= []
            Cright01= []
            for i in range(len(U0[j])):
                c1, c2 = encrypt(p, g, pk, U0[j][i])
                Cleft01.append(c1)
                Cright01.append(c2)
            Cleft0.append(Cleft01)
            Cright0.append(Cright01)
        # 2.公布Cleft,Cright,从Pi接收信息,合成矩阵M,发送给Pi
        Mleft = []
        Mright = []
        for i in range(len(Cleft0)):
            Mleft.append(Cleft0[i])
        for i in range(len(Cright0)):
            Mright.append(Cright0[i])
        for po in range(base_port + 2, base_port, -1):
            #print('---------------get ci has started------------------------')
            Cleftnumb, Crightnumb = get_Ci(po)
            #print('------------get ci has finished--------------------------')
            for i in range(len(Cleftnumb)):
                Mleft.append(Cleftnumb[i])
            for i in range(len(Crightnumb)):
                Mright.append(Crightnumb[i])
        Mlf = []
        Mlf.append(Mleft)
        Mlf.append(Mright)
        for po in range(base_port + 1, base_port + 3):
            send_M(po, Mlf)
        # 3.P0计算H0=(u0,v0)并公布u0,接收u0^skj,解密得到位置h0
        h0 = []
        for i in range(len(data)):
            h0.append(get_ord(Mleft, Mright, p, g, pk, data[i], sknumb, numb, n_data))
        # 4. P0帮助其他参与者Pi获得其位置
        for i in range(l1 + l2):
            cl0, addr = clnumb.accept()
            u0 = pickle.loads(cl0.recv(bufsize_s))
            usk = fastExpMod(u0, sknumb, p)
            comm[numb] +=cl0.send(pickle.dumps(usk))
        return h0, comm[numb]

    else:  # 其他Pi接收p,g,生成ski,并给P0发送pki,接收pk
        # 1.根据data生成lim维向量,加密,公布
        comm[numb] = comm_one
        Unumb = []
        for i in range(len(data)):
            Unumb.append(get_vector(data[i], lim))
        Cleftnumb = []  # c1
        Crightnumb = []  # c2
        for j in range(len(Unumb)):
            Cleft01 = []
            Cright01 = []
            for i in range(len(Unumb[j])):
                c1, c2 = encrypt(p, g, pk, Unumb[j][i])
                Cleft01.append(c1)
                Cright01.append(c2)
            Cleftnumb.append(Cleft01)
            Crightnumb.append(Cright01)
        Cnumb = []
        Cnumb.append(Cleftnumb)
        Cnumb.append(Crightnumb)
        # 2.公布Cleft,Cright给P0信息,从P0接收合成矩阵M
        cl0, addr = clnumb.accept()

        comm[numb] += send_dumps(cl0, Cnumb[0])
        comm[numb] += send_dumps(cl0, Cnumb[1])
        cl0, addr = clnumb.accept()
        Mleft, scom1 = rec_loads(cl0)
        Mright, scom2 = rec_loads(cl0)
        comm[numb] += scom1
        comm[numb] +=scom2
        # 3. 从P0接收u0,返回u0^sk,帮助P0获得位置  4.Pi获得自己的位置
        if numb==1:
            for i in range(l0):
                cl0, addr = clnumb.accept()
                u0 = pickle.loads(cl0.recv(bufsize_s))
                usk = fastExpMod(u0, sknumb, p)
                comm[numb] += cl0.send(pickle.dumps(usk))
            h0 = []
            for i in range(l1):
                h0.append(get_ord(Mleft, Mright, p, g, pk, data[i], sknumb, numb, n_data))
            for i in range(l2):
                cl0, addr = clnumb.accept()
                u0 = pickle.loads(cl0.recv(bufsize_s))
                usk = fastExpMod(u0, sknumb, p)
                comm[numb] += cl0.send(pickle.dumps(usk))
        else:
            for i in range(l0+l1):
                cl0, addr = clnumb.accept()
                u0 = pickle.loads(cl0.recv(bufsize_s))
                usk = fastExpMod(u0, sknumb, p)
                comm[numb] += cl0.send(pickle.dumps(usk))
            h0 = []
            for i in range(l2):
                h0.append(get_ord(Mleft, Mright, p, g, pk, data[i], sknumb, numb, n_data))
        return h0, comm[numb]



