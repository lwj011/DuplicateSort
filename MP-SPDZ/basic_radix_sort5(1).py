from Compiler import types, library, instructions
from Compiler.types import Array
import itertools
from Compiler.types import sint, cint
from Compiler.circuit import sha3_256
from Compiler.GC.types import sbitvec, sbits

nbits = 16  #maximum number of bits,Multiples of 8
pre_null = 2 ** (nbits-1) - 1  #Maximum number, representing null

"""
radix_sort参考 mp-spdz 中Compiler/sorting.py
"""

def array_remove(k0, i):
    """
    去除Array k0 的第i项,i起始为0
    :param k0:sint,cint格式,array
    :param i: int ,cint 
    :return:k0.value_type 的array
    leak: len(k0), i
    """
    k = k0.same_shape()
    k.assign(k0)
    res = k.value_type.Array(len(k) - 1)
    @library.for_range(len(k))
    def _(j):
        @library.if_(i < j)
        def _():
            res[j-1] = k[j]
        @library.if_(i > j)
        def _():
            res[j] = k[j]
    return res


def get_hash64(k0):
    """
    :param k0: 待排序数据的key,sint, key<=64bit
    :return: key+random(64bit)的sha3_256哈希值,仅返回最后64bit,sint格式
    leak: sha3_256(k0+rnd)
    """
    nbits_hash = nbits
    #@library.if_(nbits_hash > 32)
    #def _():
    #    nbits_hash = 40        
    k = k0.same_shape()
    k.assign(k0)
    rnd = sint.get_random_int(nbits_hash)  #64
    sb = sbits.get_type(nbits_hash)  #bit长度为64
    list_k = sint.Array(len(k))  # preserve sint hash64
    @library.for_range(len(k))  # 逐位循环
    def _(i):
        x = sbitvec(k[i] + rnd, nbits_hash, 1)  # k[i], n_bits rows, columns
        temp = sb(sha3_256(x).elements()[0]).reveal()
        temp2 = sint(temp)
        list_k.assign(temp2, i)  # 恢复hash值,取最后64bit
    return list_k
    
    
def get_cposition(k0):
    """
    根据多重排序规则,获得待排序数据与最终顺序所在位置的对应情况
    :param k0: sint,待排序数据的Key
    :return:cint array, cposition
    leak:泄露key的哈希值,key重复情况
    """
    k = k0.same_shape()
    k.assign(k0)
    list = get_hash64(k)  #得到哈希值的最后64bit, sint格式
    list2, list2order = radix_sort_both(list, list, n_bits=nbits)  #对哈希值进行安全排序
    clist = list.reveal()  # 恢复出哈希值
    clist2 = list2.reveal()  # 恢复出排序后的哈希值
    clist2order = list2order.reveal()  # 恢复出排序的位置向量
    cposition = cint.Array(len(clist))  # 数据-顺序所在位置对应Array
    y = cint.Array(1)  # mp-spdz循环数据传递只能用array

    @library.for_range(len(clist))
    def _(i):
        cx = clist2order[i]
        @library.if_e(clist2[0] == clist2[cx])
        def _():
            y[0] = 0
        @library.else_
        def _():
            @library.for_range(cx - 1, -1, -1)
            def _(j):
                @library.if_(clist2[j] != clist2[cx])
                def _():
                    y[0] = j + 1
                    library.break_loop()
        @library.for_range(len(clist))
        def _(z):
            @library.if_(clist2order[z] == y[0])
            def _():
                cposition[i] = z
                library.break_loop()
    return cposition

                
def get_cposition_normal(k0):
    """
    根据多重排序规则,获得待排序数据与最终顺序所在位置的对应情况
    :param k0: sint,待排序数据的Key
    :return:cint array, cposition
    leak:泄露key的哈希值,key重复情况
    """
    k = k0.same_shape()
    k.assign(k0)
    list = get_hash64(k)  # 得到哈希值的最后64bit, sint格式
    list2, list2order = radix_sort_both(list, list, n_bits=nbits)  # 对哈希值进行安全排序
    clist = list.reveal()  # 恢复出哈希值
    clist2 = list2.reveal()  # 恢复出排序后的哈希值
    clist2order = list2order.reveal()  # 恢复出排序的位置向量
    cposition = cint.Array(len(clist))  # 数据-顺序所在位置对应Array
    cposition_del = cint.Array(len(clist))
    y = cint.Array(1)  # mp-spdz循环数据传递只能用array

    @library.for_range(len(clist))
    def _(i):
        cx = clist2order[i]
        @library.if_e(clist2[0] == clist2[cx])
        def _():
            y[0] = 0
        @library.else_
        def _():
            @library.for_range(cx - 1, -1, -1)
            def _(j):
                @library.if_(clist2[j] != clist2[cx])
                def _():
                    y[0] = j + 1
                    library.break_loop()            
        @library.for_range(len(clist))
        def _(z):
            @library.if_(clist2order[z] == y[0])
            def _():
                cposition[i] = z
                @library.if_e(i == z)
                def _():
                    cposition_del[i] = 1
                @library.else_
                def _():
                    cposition_del[i] = 0
                library.break_loop()        
    return cposition, cposition_del


def cpo_to_cpodel(cpo0, cpo_del0):
    """
    根据多重排序的cposition得到归一排序的cposition(对应先删除重复数据,再排序后的结果)
    :param cpo0: 多重排序的cpo, cint array
    :param cpo_del0: 01序列,0表示删除对应项 ,cint array
    :return:针对归一排序结果的cposition,cint array
    leak: same as cpo0,cpo_del0
    """
    cpo = cpo0.same_shape()
    cpo.assign(cpo0)
    cpo_del = cpo_del0.same_shape()
    cpo_del.assign(cpo_del0)
    y = cint.Array(1)
    y[0] = 0
    @library.for_range(len(cpo))
    def _(i):
        @library.if_e(cpo_del[i] == 0)
        def _():
            y[0] = y[0] + 1
        @library.else_
        def _():
            cx = cpo[i]
            cpo[i] = cpo[i] - y[0]
            @library.for_range(i, len(cpo), 1)
            def _(j):
                @library.if_(cpo[j] == cx)
                def _():
                    cpo[j] = cpo[i]
    return cpo


def gen_bit_perm(b):
    """
    生成单比特序列的排序置换
    例如输入b=[0,1,0,1], 返回[0,2,1,3]
    leak: null
    """
    B = types.sint.Matrix(len(b), 2)  # len(b)行,2列矩阵
    B.set_column(0, 1 - b.get_vector())
    B.set_column(1, b.get_vector())  # 用[0,1]表示1,用[1,0]表示0,B=[[1,0],[0,1],[1,0],[0,1]]
    Bt = B.transpose()  #转置 Bt=[[1,0,1,0],[0,1,0,1]]
    Bt_flat = Bt.get_vector()
    St_flat = Bt.value_type.Array(len(Bt_flat))
    St_flat.assign(Bt_flat)  #St_flat连接Bt, St_flat=[1,0,1,0,0,1,0,1]
    @library.for_range(len(St_flat) - 1)
    def _(i):
        St_flat[i + 1] = St_flat[i + 1] + St_flat[i]  #递加,数1的数量
    Tt_flat = Bt.get_vector() * St_flat.get_vector()  # Tt_flat[[1],[0],[2],[0],[0],[3],[0],[4]]
    Tt = types.Matrix(*Bt.sizes, B.value_type)  #产生一个与Bt同大小的矩阵
    Tt.assign_vector(Tt_flat)  #将Tt_flat分段  Tt=[[1,0,2,0], [0,3,0,4]]
      
    return sum(Tt) - 1  # 返回排序置换[0,2,1,3]

def inverse_permutation(k):
    """
    对置换取反
    例如输入k=[],返回
    只会泄露len(k)
    """
    shuffle = types.sint.get_secure_shuffle(len(k))  # 初始化shuffle
    k_prime = k.get_vector().secure_permute(shuffle).reveal()  #shuffle k,k_prime为明文但不会泄露信息
    idx = Array.create_from(k_prime)  #格式转换
    res = Array.create_from(types.sint(types.regint.inc(len(k))))  #生成sint Array [0,1,2,...,len(k)-1]
    res.secure_permute(shuffle, reverse=False)  # shuffle res
    res.assign_slice_vector(idx, res.get_vector())
    library.break_point()
    instructions.delshuffle(shuffle)  #删除shuffle
    return res


def apply_perm(k, D, reverse=False):
    """
    将置换k应用到D
    reverse为false,合成排序置换,返回k(D);reverse为ture按排序置换k对D进行排序
    leak: null
    """
    assert len(k) == len(D)
    library.break_point()
    shuffle = types.sint.get_secure_shuffle(len(k))
    k_prime = k.get_vector().secure_permute(shuffle).reveal()
    idx = types.Array.create_from(k_prime)
    if reverse:
        D.assign_vector(D.get_slice_vector(idx))
        library.break_point()
        D.secure_permute(shuffle, reverse=True)
    else:
        D.secure_permute(shuffle)
        library.break_point()
        v = D.get_vector()
        D.assign_slice_vector(idx, v)
    library.break_point()
    instructions.delshuffle(shuffle)


def radix_sort(k0, D0, n_bits=None, get_D=True, signed=True):
    """
    按照k0的值对D0进行排序
    n_bits是基数排序最大位数
    get_D=true,返回排序后后的D0,否则返回排序后的位置向量
    D为排序后的D0,D_order为D中数据排序后的位置向量
    安全性:只会泄露len(k)
    this is same as the MP-SPDZ
    """
    n_bits = nbits
    k = k0.same_shape()
    k.assign(k0)
    D = D0.same_shape()
    D.assign(D0)
    assert len(k) == len(D)  # k=[2,5,0,1]
    bs = types.Matrix.create_from(k.get_vector().bit_decompose(n_bits))  #bit_decompose（）位分解 bs=[[0,1,0,1],[1,0,0,0],[0,1,0,0],[0,0,0,0,],...[0,0,0,0]]
    if signed and len(bs) > 1:
        bs[-1][:] = bs[-1][:].bit_not()  # bs最后一行取否
    h = types.Array.create_from(types.sint(types.regint.inc(len(k))))  #初始化排序置换,生成sint Array [0,1,2,...,len(k)-1]
    @library.for_range(len(bs))  #逐位循环
    def _(i):
        b = bs[i]
        c = gen_bit_perm(b)  #得到单比特排序结果
        apply_perm(c, h, reverse=False)  # 返回 h1=c0(h0),循环后h=cn...c3c2c1c0(h0),h0=[0,1,2,3,...]
        @library.if_e(i < len(bs) - 1)
        def _():
            apply_perm(h, bs[i + 1], reverse=True)
        @library.else_
        def _():
            apply_perm(h, D, reverse=True)  #对D进行排序, D为密文形式
    D_order = inverse_permutation(h)  #生成D中数据排序后位置向量,密文形式
    if get_D:
        return D
    else:
        return D_order


def radix_sort_both(k0, D0, n_bits=None, signed=True):
    """
    按照k0的值对D0进行排序
    n_bits是基数排序最大位数
    返回排序后后的D0,返回排序后的位置向量
    D为排序后的D0,D_order为D中数据排序后的位置向量
    安全性:只会泄露len(k)
    """
    n_bits =nbits
    k = k0.same_shape()
    k.assign(k0)
    D = D0.same_shape()
    D.assign(D0)
    assert len(k) == len(D)  # k=[2,5,0,1]
    bs = types.Matrix.create_from(k.get_vector().bit_decompose(n_bits))  #bit_decompose（）位分解 bs=[[0,1,0,1],[1,0,0,0],[0,1,0,0],[0,0,0,0,],...[0,0,0,0]]
    if signed and len(bs) > 1:
        bs[-1][:] = bs[-1][:].bit_not()  # bs最后一行取否
    h = types.Array.create_from(types.sint(types.regint.inc(len(k))))  #初始化排序置换,生成sint Array [0,1,2,...,len(k)-1]

    @library.for_range(len(bs))  #逐位循环
    def _(i):
        b = bs[i]
        c = gen_bit_perm(b)  #得到单比特排序结果
        apply_perm(c, h, reverse=False)  # 返回 h1=c0(h0),循环后h=cn...c3c2c1c0(h0),h0=[0,1,2,3,...]
        @library.if_e(i < len(bs) - 1)
        def _():
            apply_perm(h, bs[i + 1], reverse=True)
        @library.else_
        def _():
            apply_perm(h, D, reverse=True)  #对D进行排序, D为密文形式
    D_order = inverse_permutation(h)  #生成D中数据排序后位置向量,密文形式
    return D, D_order
    

def multi_sort(k0, D0):
    """
    根据k0的值对D0进行多重排序,k0,D0均为sint Array
    :param k0:value
    :param D0:data
    :return:排序后的D0,排序后D0的顺序向量,sint Array
    leak: k0的哈希值, k0的重复情况,len(k0)
    """
    k = k0.same_shape()
    k.assign(k0)
    D = D0.same_shape()
    D.assign(D0)
    assert len(k) == len(D)
    cpo = get_cposition(k)  # 数据重复情况 cint array
    d_sort, d_order = radix_sort_both(k,D, nbits)  # 排序后的D, D排序后的顺序向量, 增序排序 sint array
    d_order_multi = sint.Array(len(d_order))
    @library.for_range(len(d_order))
    def _(i):
        d_order_multi[i] = d_order[cpo[i]]
    return d_sort, d_order_multi


def normal_sort(k0, D0):
    """
    根据k0的值对D0进行归一排序,k0,D0均为sint Array
    :param k0:value
    :param D0:data
    :return:排序后的D0(已删除重复数据,若k0同而D0不同,也算重复数据),排序后D0的顺序向量,sint Array
    leak: k0的哈希值, k0的重复情况,len(k0), pre_null will leak part range of the max number
    ???question: I use 1152921504606847000=2e60 to present null
    """
    k = k0.same_shape()
    k.assign(k0)
    D = D0.same_shape()
    D.assign(D0)
    assert len(k) == len(D)
    #pre_null = pre_null

    cpo, cpo_del = get_cposition_normal(k)  # cpo储存数据重复情况, cpo_del判断数据是否删除, cint array
    cpo_normal = cpo_to_cpodel(cpo, cpo_del)  #最终数据-位置对应 cint array

    kn = k0.same_shape()
    kn.assign_all(pre_null)
    dn = D0.same_shape()
    dn.assign_all(pre_null)
    
    y = cint.Array(1)
    y[0] = 0
    @library.for_range(len(k))  # 去重
    def _(i):
        @library.if_(cpo_del[i] == 1)
        def _():
            kn[y[0]] = k[i]
            dn[y[0]] = D[i]
            y[0] = y[0] + 1

    d_sort, d_order = radix_sort_both(kn, dn, nbits)  # 排序后的D, D排序后的顺序向量, 增序排序 sint array
    d_order_normal = sint.Array(len(d_order))
    @library.for_range(len(d_order))
    def _(i):
        d_order_normal[i] = d_order[cpo_normal[i]]

    return d_sort, d_order_normal
    
    
def gen_bit_perm_multi(b0):
    """
    生成单比特序列的多重排序置换
    例如输入b0=[0,1,0,1], 返回[0,2,0,2]
    leak: len(b0)
    """
    b = b0.value_type.Array(len(b0))
    b.assign(b0.get_vector())
    sum = b.value_type.Array(1)
    sum[0] = len(b)  # 1 的数量
    @library.for_range(len(b))
    def _(i):
        sum[0] = sum[0] - b[i]
    res_flat = sum[0] * b.get_vector()
    res = b.value_type.Array(len(b))
    res.assign(res_flat)

    return res  # 返回排序置换[0,2,0,2]

    
def sort_belong(k0, D0):
    D, D_order = radix_sort_both(k0, D0,nbits)
    Dm = D.reveal()
    return Dm
    























