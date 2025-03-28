import numpy as np
import pandas as pd
from collections import Counter
from pyevmasm import disassemble_hex  # 以太坊反汇编工具 pyevmasm
from web3 import Web3  # 以太坊交互库 web3
from web3.eth import AsyncEth
import math
import time
import matplotlib.pyplot as plt
from datetime import datetime
import math

#url = 'https://cloudflare-eth.com'  # 定义了一个以太坊节点的 URL,不太稳定
#url = 'https://rpc.ankr.com/eth'    #稍微稳定点，不能得到混币的字节码
url = 'https://ethereum.publicnode.com'     #可以得到混币的字节码，暂时挺稳定


def address_to_operation_dic(address):               #地址->操作码（字典）
    w3 = Web3(Web3.HTTPProvider(url))
    # 如果地址有效，将输入的地址转换为校验和地址格式
    address2 = w3.to_checksum_address(address)  # 以太坊地址 -> checksum address
    code = w3.eth.get_code(address2)
        # 处理字节码，获取操作码.将字节码转换为十六进制字符串，如果字节码为空（只有 '0x'），则返回表示不是合约地址的信息字符串和数值 0
    code = code.hex()
    if code == '0x':  # 如果操作码为'0x'，即16进制为空
        info = 'not contract address'
        return info, 0
        #如果字节码不为空，使用disassemble_hex函数将十六进制字节码转换为汇编指令，并将其按行分割。创建一个空字典opcode_map用于存储操作码的计数
    else:
        opcode = disassemble_hex(code)  # 16进制 -> 汇编
        opcode = opcode.split('\n')
    # 获取指定地址的字节码
    opcode_map = {}
            #遍历每个汇编指令，将操作码作为键存储到字典中，并统计每个操作码出现的次数
    for struction in opcode:
            struction = struction.split(' ')
            if struction[0] in opcode_map.keys():
                opcode_map[struction[0]] = opcode_map[struction[0]] + 1
            else:
                opcode_map[struction[0]] = 1
    return opcode_map

def cosine_similarity(counter1, counter2):   #参数为字典

    words = set(counter1.keys()).union(set(counter2.keys()))

    vector1 = [counter1.get(word, 0) for word in words]
    vector2 = [counter2.get(word, 0) for word in words]

    dot_product = sum(a * b for a, b in zip(vector1, vector2))
    magnitude1 = math.sqrt(sum(a * a for a in vector1))
    magnitude2 = math.sqrt(sum(b * b for b in vector2))

    if magnitude1 == 0 or magnitude2 == 0:
        return 0
    else:
        return dot_product / (magnitude1 * magnitude2)

def bytecode_to_opcode_dic(bcode):  #字节码->操作码次数字典
    if len(bcode) % 2!= 0:
        bcode += '0'
    opcode = disassemble_hex(bcode)  # 16进制 -> 汇编
    opcode = opcode.split('\n')
    opcode_map = {}
    # 遍历每个汇编指令，将操作码作为键存储到字典中，并统计每个操作码出现的次数
    for struction in opcode:
        struction = struction.split(' ')
        if struction[0] in opcode_map.keys():
            opcode_map[struction[0]] = opcode_map[struction[0]] + 1
        else:
            opcode_map[struction[0]] = 1
    return  opcode_map

def bytecode_to_opcode_list(bcode):  #返回操作码，列表
    if len(bcode) % 2!= 0:
        bcode += '0'
    opcode = disassemble_hex(bcode)  # 16进制 -> 汇编
    opcode = opcode.split('\n')
    return  opcode

def levenshtein_distance(list1, list2):
    # 获取两个字符串的长度
    len_str1 = len(list1)
    len_str2 = len(list2)

    # 创建一个二维数组来存储距离
    dp = [[0] * (len_str2 + 1) for _ in range(len_str1 + 1)]

    # 初始化第一行和第一列
    for i in range(len_str1 + 1):
        dp[i][0] = i  # 从 str1 到空字符串的距离
    for j in range(len_str2 + 1):
        dp[0][j] = j  # 从空字符串到 str2 的距离

    # 填充 DP 表
    for i in range(1, len_str1 + 1):
        for j in range(1, len_str2 + 1):
            cost = 0 if list1[i - 1] == list2[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1,  # 删除
                           dp[i][j - 1] + 1,  # 插入
                           dp[i - 1][j - 1] + cost)  # 替换
    return dp[len_str1][len_str2]

def calculate_risk(x):
    x0 = 0.975  # 拐点中心
    k = 85.0  # 曲率参数（经数值优化）
    alpha = 0.18  # 倾斜因子

    # 核心计算逻辑
    if x < 0.95:
        return max(round(0.0005 * x / 0.95, 4), 0.0)  # 低值区线性处理

    exponent = -k * (x - x0)
    base = 1 / (1 + math.exp(exponent))
    tilt = alpha * (x - x0)

    # 合成风险值并限制范围
    risk = base + tilt
    return max(0.0, min(round(risk, 4), 1.0))

def detect(data):#data为合约地址，返回值为风险评分，阈值0.975
    base = pd.read_excel('baseaddress_mix.xlsx').iloc[:10,1].tolist()
    base_list = []
    for i in range(len(base)):
        base_list.append(address_to_operation_dic(base[i]))
    sum_cos = 0
    data_operation = address_to_operation_dic(data)
    for i in range(len(base)):
        sum_cos += cosine_similarity(data_operation,base_list[i])
    average = sum_cos/len(base)
    return calculate_risk(average)


if __name__ == '__main__':
    print(detect("0x610B717796ad172B316836AC95a2ffad065CeaB4"))