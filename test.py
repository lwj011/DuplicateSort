import time
from pathos.multiprocessing import ProcessingPool as propool
from pathos import multiprocessing
from client3p import client_3p

# 多重排序
def test_multi(data):
    # data = [[162, 438, 162], [263, 389, 162], [257, 162, 33, 170]]
    num = len(data[0]) + len(data[1]) + len(data[2])
    numb = [1, 2, 0]
    sord = []
    sord.append([0] * len(data[0]))
    sord.append([0] * len(data[1]))
    sord.append([0] * len(data[2]))
    l0 = []
    l0.append(len(data[2]))
    l0 = l0 * 3
    l1 = []
    l1.append(len(data[0]))
    l1 = l1 * 3
    l2 = []
    l2.append(len(data[1]))
    l2 = l2 * 3
    t1 = time.time()
    pool.map(client_3p, data, sord, numb, l0, l1, l2)
    t2 = time.time()
    print('num is %d, multi_time is %s' % (num, t2 - t1))

# 增序排序
def test_ascend(data):
    # data = [[162, 438, 162], [263, 389, 162], [257, 162, 33, 170]]
    num = len(data[0]) + len(data[1]) + len(data[2])
    numb = [1, 2, 0]
    sord = []
    sord0 = []
    sord1 = []
    sord2 = []
    cx = 0
    for i in range(len(data[2])):
        sord0.append(cx)
        cx = cx + 1
    for i in range(len(data[0])):
        sord1.append(cx)
        cx = cx + 1
    for i in range(len(data[1])):
        sord2.append(cx)
        cx = cx + 1
    sord.append(sord1)
    sord.append(sord2)
    sord.append(sord0)
    l0 = []
    l0.append(len(data[2]))
    l0 = l0 * 3
    l1 = []
    l1.append(len(data[0]))
    l1 = l1 * 3
    l2 = []
    l2.append(len(data[1]))
    l2 = l2 * 3
    t1 = time.time()
    pool.map(client_3p, data, sord, numb, l0, l1, l2)
    t2 = time.time()
    print('num is %d, ascend_time is %s' % (num, t2 - t1))


if __name__ == '__main__':
    # 根据CPU的核数开对应的进程,运行速度快,我的Ubuntu主机是12核
    cores = multiprocessing.cpu_count()
    pool = propool(processes=cores)
    print('core is %d' % cores)

    #通信开销基本由公开M决定,目前方案是P1P2发送M/3,P1发送M

    #----------------data number----------------------
    
    data = [[162, 438, 162], [263, 389, 162], [257, 162, 33, 170]]  #10
    test_ascend(data)
    #test_multi(data)

    data = [[383, 15, 397, 288, 460, 79, 207, 340, 327, 239, 218, 301, 315, 457, 93, 388],
            [442, 495, 413, 196, 400, 341, 108, 489, 273, 75, 374, 40, 421, 82, 378, 229, 411],
            [301, 28, 21, 276, 371, 454, 183, 209, 161, 326, 345, 114, 399, 496, 173, 193, 301]]  # 50
    #test_ascend(data)
    #test_multi(data)

    data = [
        [472, 206, 351, 190, 281, 272, 382, 137, 473, 289, 220, 11, 235, 470, 234, 86, 243, 316, 94, 151, 239, 253, 135,
         182, 141, 64, 34, 304, 182, 329, 213, 115, 194],
        [432, 154, 329, 244, 300, 490, 387, 463, 64, 288, 230, 231, 239, 152, 230, 213, 252, 53, 306, 89, 226, 53, 434,
         105, 114, 129, 207, 139, 426, 422, 416, 473, 5],
        [24, 186, 491, 107, 388, 1, 129, 260, 44, 324, 266, 325, 278, 269, 382, 228, 436, 199, 348, 330, 459, 268, 471,
         291, 422, 205, 5, 52, 448, 432, 386, 159, 277, 343]]  # 100个数,
    #test_ascend(data)
    #test_multi(data)

    data = [[178, 276, 361, 411, 135, 220, 388, 286], [421, 307, 313, 402, 448, 2, 170, 174], [148, 146, 499, 262, 475, 200, 447, 202, 390]]  #25
    #test_ascend(data)
    #test_multi(data)

    data = [[407, 427, 169, 345, 405, 156, 22, 320, 258, 455, 270, 135, 273, 127, 222, 320, 123, 273, 211, 57, 304, 400, 313, 170, 426], [459, 413, 394, 343, 497, 182, 435, 32, 354, 463, 116, 239, 351, 412, 446, 325, 0, 212, 291, 307, 61, 137, 4, 317, 402], [406, 354, 485, 463, 391, 240, 354, 278, 108, 235, 218, 437, 291, 303, 443, 378, 481, 115, 397, 204, 153, 407, 154, 498, 218]]  #75
    #test_ascend(data)
    #test_multi(data)

    #--------------------number size------------------
    data = [[14, 14, 14],[4, 8, 0] , [2, 5, 4, 1]]  #var
    #test_ascend(data)
    #test_multi(data)
    
    data = [[232, 85, 137],[196, 141, 187] , [141, 197, 224, 183]]  #var
    #test_ascend(data)
    #test_multi(data)
    
    data = [[2899, 7028, 40126],[61877, 53406, 62743] , [53406, 8189, 39925, 60819]]  #var
    #test_ascend(data)
    #test_multi(data)
    
    data = [[3691996800, 675069419, 3237228706],[4048578902, 4286001725, 1029334041] , [4286001725, 581668864, 1532798973, 845575485]]  #var
    #test_ascend(data)
    #test_multi(data)
    
    
    data = [[147645938924790, 280156373092306, 14764086257085],[221183509361799, 50196198376915, 40847424316041] , [92194041473421, 54432120386798, 46947956165893, 102935991099113]]  #var
    #test_ascend(data)
    #test_multi(data)
    
    
    data = [[13277003731435107564, 10978386021181458075, 15907606449544495697], [5827833303657455581, 14087185782894318682, 9260112917058777351], [14087185782894318682, 6230613138126508517, 3571131322921886982, 18308335084349078510]]  #var
    #test_ascend(data)
    #test_multi(data)
    
    
    #--------------------dump data------------------
    data = [[288, 53, 497, 392, 408, 103, 60, 157, 327, 416, 135, 365, 363, 434, 36, 105, 92, 500, 446, 39, 85, 170, 181, 214, 410, 117, 351, 252, 119, 399, 11, 412, 97],[49, 73, 151, 333, 230, 387, 378, 496, 293, 417, 350, 406, 201, 210, 397, 69, 139, 330, 256, 2, 191, 263, 409, 386, 202, 453, 444, 415, 329, 27, 87, 298, 168] , [452, 72, 190, 136, 273, 340, 167, 154, 104, 472, 20, 404, 209, 303, 64, 499, 262, 441, 469, 141, 26, 353, 134, 182, 334, 281, 137, 197, 121, 200, 331, 425, 59, 219]]  #var
    #test_ascend(data)
    #test_multi(data)
    
    data = [[114, 463, 381, 404, 241, 435, 73, 432, 376, 383, 145, 290, 175, 363, 256, 196, 457, 288, 492, 64, 160, 142, 56, 241, 180, 16, 410, 470, 8, 392, 257, 396, 264],[83, 498, 7, 78, 44, 495, 362, 419, 437, 300, 184, 317, 24, 62, 197, 377, 263, 190, 25, 479, 156, 326, 391, 195, 454, 190, 261, 456, 389, 470, 343, 93, 65] , [190, 458, 262, 368, 226, 350, 261, 279, 69, 2, 184, 238, 381, 367, 211, 314, 252, 432, 89, 170, 130, 380, 390, 47, 164, 96, 333, 344, 420, 472, 125, 383, 47, 228]]  #var
    #test_ascend(data)
    #test_multi(data)
    
    data = [[120, 98, 162, 333, 214, 389, 404, 229, 360, 283, 38, 333, 65, 21, 140, 30, 404, 163, 295, 248, 75, 183, 194, 34, 405, 61, 404, 98, 137, 355, 463, 396, 108],[294, 300, 306, 404, 307, 456, 354, 102, 468, 94, 284, 446, 281, 404, 128, 194, 352, 307, 37, 149, 303, 414, 104, 404, 138, 5, 79, 135, 55, 445, 124, 354, 107] , [404, 98, 446, 123, 120, 243, 421, 78, 188, 338, 404, 36, 316, 471, 284, 472, 117, 414, 467, 469, 404, 284, 145, 43, 125, 119, 462, 330, 190, 440, 404, 345, 308, 205]]  #var
    #test_ascend(data)
    #test_multi(data)
    
    data = [[191, 180, 323, 430, 177, 198, 205, 411, 458, 246, 279, 82, 323, 297, 177, 198, 205, 281, 167, 246, 126, 458, 323, 327, 177, 198, 205, 406, 34, 246, 63, 155, 323],[151, 177, 198, 205, 149, 109, 246, 190, 21, 323, 356, 177, 198, 205, 224, 273, 246, 226, 123, 323, 368, 177, 198, 205, 152, 124, 246, 24, 296, 323, 484, 177, 198] , [205, 473, 420, 246, 130, 430, 323, 324, 177, 198, 205, 42, 472, 246, 256, 244, 323, 76, 177, 198, 205, 364, 113, 246, 273, 46, 323, 76, 177, 198, 205, 456, 120, 246]]  #var
    #test_ascend(data)
    #test_multi(data)
    
    
    data = [[123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123],[123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123] , [123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123]]  #var
    #test_ascend(data)
    #test_multi(data)
    
    
    
    

    print('success')