# coding=utf-8


def encode(passwd):
    enCode = []
    for bit in passwd:
        bit = ord(bit) + 1
        enCode.append(chr(bit))
    enPasswd = ''.join(enCode)
    return enPasswd


def decode(passwd):
    deCode = []
    for bit in passwd:
        bit = ord(bit) - 1
        deCode.append(chr(bit))
    dePasswd = ''.join(deCode)
    return dePasswd
