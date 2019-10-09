import hashlib
def md5(string,salt='helpaged')->str:
    #satl是盐值，默认是123456
    string = str(string)
    string = string+salt
    md = hashlib.md5()  # 构造一个md5对象
    md.update(string.encode())
    res = md.hexdigest()
    return res
def md5_bytes(byte:bytes,salt:bytes=b'helpaged')->str:
    # satl是盐值，默认是b'multimedia'
    byte = bytes(byte)
    byte = byte + salt
    md = hashlib.md5()  # 构造一个md5对象
    md.update(byte)
    res = md.hexdigest()
    return res
if __name__ == "__main__":
    print(md5("nDtg4"))