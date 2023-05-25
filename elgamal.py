import math
import time

#from Cryptodome.Util import number
from random import randint
import sympy
import sys


#快速取模幂a^e mod m
def fastExpMod(a, e, m):
    a = a % m
    res = 1
    while e != 0:
        if e&1:
            res = (res * a) % m
        e >>= 1
        a = (a * a) % m
    return res

#生成原根
def primitive_element(p, q):
    while True:
        g = randint(2, p - 2)
        if fastExpMod(g, 2, p) != 1 and fastExpMod(g, q, p) != 1:
            return g

def e_gcd(a, b):
    if b == 0:
        return a, 1, 0
    g, x, y = e_gcd(b, a%b)
    return g, y, x-a//b*y  #gcd     a^-1 mod b     b^-1 mod a

#加密, lifted elgamal是对2^m进行加密
def encrypt(p, g, pk, m):
    m2 = int(math.pow(2, m))
    if m2 >= p:
        print('the m is too big')
        m2 = m2 % p
    while True:
        r = randint(2, p-2)
        if e_gcd(r, p-1)[0]:
            break
    c1 = fastExpMod(g, r, p)
    c2 = (m2 * fastExpMod(pk, r, p))%p
    return c1, c2

#解密,返回m
def decrypt(c1, c2, p, sk):
    v = fastExpMod(c1, sk, p)
    v_1 = e_gcd(v, p)[1]
    m_d = c2 * v_1 % p
    m = int(math.log2(m_d))
    return m

#生成模数p,生成元g,p为n bit
def get_p_g2(n):
    while True:
        q = sympy.randprime(2 ** (n-2), 2 ** (n-1)-1)  # randprime(a,b)  return a random prime between a and b
        if sympy.isprime(q):
            p = 2 * q + 1
            if sympy.isprime(p):
                break
    g = primitive_element(p, q)
    return p, g

def yg(n):  # 默认求最小原根
    k=(n-1)//2
    for i in range(2,n-1):
        if fastExpMod(i,k,n)!=1:
            return i

def get_p_g(n):  #得到p,g,但是p不一定强,g为最小的原根,该函数效率高
    p = sympy.randprime(2 ** (n-1), 2 ** n -1)
    g = yg(p)
    return p,g


#生成公私钥pk,sk,密钥长度为n bit
def key_gen(p, g, n):
    sk = randint(2 ** (n-1), 2 ** n)
    pk = fastExpMod(g, sk, p)
    return pk, sk



if __name__ == '__main__':
    t1 = time.time()
    p,g = get_p_g2(512)
    t2 = time.time()
    print(t2-t1)
    print(p)
    print(g)
