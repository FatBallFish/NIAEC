from m_cos import py_cos_main as COS
from threading import Timer
from m_mysql.py_lock import Lock
from m_sms import py_sms_main as Sms
import pymysql, base64
import sys, os
import threading
import logging
from configparser import ConfigParser
import datetime
import time
import MD5, random
import re

Lock = Lock()
log_mysql = logging.getLogger("MySql")


def Initialize(cfg_path: str, main_path: str):
    """
    初始化 Pymsql 模块
    :param cfg_path: 配置文件路径
    :param main_path: 主程序运行目录
    :return:
    """
    Lock.timeout = 3
    Lock.timeout_def = Auto_KeepConnect
    cf = ConfigParser()
    cf.read(cfg_path)
    global host, port, user, password, db, conn
    try:
        host = str(cf.get("MYSQL", "host"))
        port = int(cf.get("MYSQL", "port"))
        user = str(cf.get("MYSQL", "user"))
        password = str(cf.get("MYSQL", "pass"))
        db = str(cf.get("MYSQL", "db"))
        print("[MYSQL]host:", host)
        print("[MYSQL]port:", port)
        print("[MYSQL]user:", user)
        print("[MYSQL]pass:", password)
        print("[MYSQL]db:", db)
    except Exception as e:
        log_mysql.error("UnkownError:", e)
        print("UnkownError:", e)
        log_mysql.info("Program Ended")
        sys.exit()
    try:
        conn = pymysql.connect(host=host, port=port, user=user,
                               passwd=password,
                               db=db, charset="utf8")
    except Exception as e:
        print("Failed to connect MYSQL database")
        log_mysql.error("Failed to connect MYSQL database")
        sys.exit()
    else:
        print("[MYSQL]Connect MYSQL database successfully!")
    global Main_filepath
    Main_filepath = main_path
    log_mysql.info("Module MySQL loaded")


def DisconnectDB():
    conn.close()


def Auto_del_token():
    """
    线程，自动删除过期token
    暂时不用，所有功能整合到Addtoken里了
    :return:
    """
    cur = conn.cursor()
    sql = "DELETE FROM tokens WHERE expiration < {}".format(int(time.time()))
    try:
        Lock.acquire(Auto_del_token, "Auto_del_token")
        num = cur.execute(sql)
        conn.commit()
        Lock.release()
        # print("【Thread-Token】Deleted {} tokens".format(num))
    except Exception as e:
        conn.rollback()
        print("Failed to execute sql:{}|{}".format(sql, e))
        log_mysql.error("Failed to execute sql:{}|{}".format(sql, e))
    cur.close()
    ## 下面的代码似乎是用来删除超出10条的记录，我放在addtoken里删除了
    # sql = "SELECT phone,createdtime FROM tokens GROUP BY phone"
    # try:
    #     num = cur.execute(sql)
    #     conn.commit()
    # except Exception as e:
    #     # conn.rollback()
    #     cur.close()
    #     print("Failed to execute sql:{}|{}".format(sql, e))
    #     log_mysql.error("Failed to execute sql:{}|{}".format(sql, e))
    #     time.sleep(3)
    #     continue
    # data = cur.fetchall()

    # # todo 喵喵喵？？？？
    #
    # for row in data :
    #     sql = 'DELETE FROM tokens WHERE ' \
    #           '((SELECT COUNT(phone) as num FROM tokens WHERE phone ="{0}") > 10 AND phone IN ' \
    #           '(SELECT phone FROM tokens WHERE phone = "{0}" ORDER BY createdtime ASC LIMIT num-10))'.format(row[0])
    #     try:
    #         num = cur.execute(sql)
    #         conn.commit()
    #         print("【Thread-Token】10:Deleted {} tokens".format(num))
    #     except Exception as e:
    #         conn.rollback()
    #         print("Thread-Token:Failed to execute sql:{}".format(sql))
    #         print(e)
    #         log_mysql.error("Failed to execute sql:{}".format(sql))


def Login(phone: str, password: str, enduring: int = 0) -> tuple:
    """
    Login API,return a tuple(status,result string)
    :param phone: username
    :param password: with base64
    :return: a tuple(status,result string)
    """
    cur = conn.cursor()
    sql = "SELECT password,salt FROM users WHERE phone = '{}'".format(phone)
    # print(sql)
    try:
        Lock.acquire(Login, "Login")
        num = cur.execute(sql)
        # conn.commit()
        Lock.release()
    except Exception as e:
        # conn.rollback()
        cur.close()
        print("Failed to execute sql:{}|{}".format(sql, e))
        log_mysql.error("Failed to execute sql:{}|{}".format(sql, e))
        Auto_KeepConnect()
        # status -200 sql执行失败
        return (-200, "Failure to operate database")

    if num == 1:
        row = cur.fetchone()
        pass_db = row[0]
        salt = row[1]
        cur.close()
        if pass_db == MD5.md5(password, salt):
            token = AddToken(phone, enduring=enduring)
            if token == "":
                # status 300 添加token失败
                return (300, "Add token failed")
            # status 0 执行成功，返回token
            return (0, token)
        else:
            # status 101 账号密码错误
            return (101, "Error password")
    elif num == 0:
        # status 100 无记录
        return (100, "Incorrect user")
    else:
        # status 200 记录数量有误
        return (200, "Invalid record number")


def Register(phone: str, password: str) -> tuple:
    """
    Register API,return a tuple(status,result string)
    :param phone: username
    :param password: with MD5
    :return: a tuple(status,result string)
    """
    cur = conn.cursor()
    sql = "SELECT phone FROM users WHERE phone='{}'".format(phone)
    try:
        Lock.acquire(Register, "Register")
        num = cur.execute(sql)
        Lock.release()
        # print("INSERT:",num)
        # conn.commit()
    except Exception as e:
        # conn.rollback()
        cur.close()
        print("Failed to execute sql:{}|{}".format(sql, e))
        log_mysql.error("Failed to execute sql:{}|{}".format(sql, e))
        Auto_KeepConnect()
        # status -200 sql执行失败
        return (-200, "Failure to operate database")
    if num > 0:
        # status 101 手机号已存在
        return (101, "Phone number existed")
    createdtime = time.strftime("%Y:%m:%d %H:%M:%S", time.localtime())

    # 生成10位salt
    salt = ""
    for i in range(10):
        # 每循环一次，随机生成一个字母或数字
        # 使用ASCII码，A-Z为65-90，a-z为97-122，0-9为48-57,使用chr把生成的ASCII码转换成字符
        char1 = random.choice([chr(random.randint(65, 90)), chr(random.randint(48, 57)), chr(random.randint(97, 122))])
        salt += char1
    pass_db = MD5.md5(password, salt)
    sql = "INSERT INTO users (phone,password,createdtime,`group`,salt) " \
          "VALUES ('{}','{}','{}','__NORMAL__','{}')".format(phone, pass_db, createdtime, salt)
    # print(sql)
    try:
        Lock.acquire(Register, "Register")
        num = cur.execute(sql)
        conn.commit()
        Lock.release()
    except Exception as e:
        conn.rollback()
        cur.close()
        print("Failed to execute sql:{}|{}".format(sql, e))
        log_mysql.error("Failed to execute sql:{}|{}".format(sql, e))
        Auto_KeepConnect()
        # status -200 sql执行失败
        return (-200, "Failure to operate database")
    if num == 1:
        ## 创建userinfo表
        sql = "INSERT INTO usersinfo (phone,`level`) VALUES ('{}',1)".format(phone)
        # print(sql)
        try:
            Lock.acquire(Register, "Register")
            num2 = cur.execute(sql)
            # print("INSERT:",num)
            conn.commit()
            Lock.release()
        except Exception as e:
            conn.rollback()
            cur.close()
            print("Failed to execute sql:{}|{}".format(sql, e))
            log_mysql.error("Failed to execute sql:{}|{}".format(sql, e))
            Auto_KeepConnect()
            # status -200 sql执行失败
            return (-200, "Failure to operate database")
        cur.close()
        if num2 == 1:
            # status 0 执行成功，返回token
            return (0, "Successful")
        elif num2 == 0:
            # status 102 创建用户信息失败
            return (102, "Incorrect user information")
        else:
            # status 200 记录数量有误
            return (200, "Invalid record number")
    elif num == 0:
        cur.close()
        # status 100 无记录
        return (101, "Incorrect user data")
    else:
        cur.close()
        # status 200 记录数量有误
        return (200, "Invalid record number ")


def ForgetPass(phone: str, password: str, id: int = -1) -> dict:
    """
忘记密码，重置密码
    :param phone: 用户账号
    :param password: 新密码
    :param id: 事件请求id
    :return: json_dict
    """
    cur = conn.cursor()
    # 生成10位salt
    salt = ""
    for i in range(10):
        # 每循环一次，随机生成一个字母或数字
        # 使用ASCII码，A-Z为65-90，a-z为97-122，0-9为48-57,使用chr把生成的ASCII码转换成字符
        char1 = random.choice([chr(random.randint(65, 90)), chr(random.randint(48, 57)), chr(random.randint(97, 122))])
        salt += char1
    pass_db = MD5.md5(password, salt)
    sql = "UPDATE users SET password = '{}',salt = '{}' WHERE phone = '{}'".format(pass_db, salt, phone)
    try:
        Lock.acquire(ForgetPass, "ForgetPass")
        num = cur.execute(sql)
        conn.commit()
        Lock.release()
    except Exception as e:
        conn.rollback()
        cur.close()
        print("Failed to execute sql:{}|{}".format(sql, e))
        log_mysql.error("Failed to execute sql:{}|{}".format(sql, e))
        Auto_KeepConnect()
        # status Failure to operate database sql语句错误
        return {"id": id, "status": -200, "message": "Failure to operate database", "data": {}}
    if num == 1:
        # status 0 执行成功s
        return {"id": id, "status": 0, "message": "successful", "data": {}}
    else:
        # status -200 sql执行失败
        return {"id": id, "status": -200, "message": "Failure to operate database", "data": {}}


def ChangePass(phone: str, old: str, new: str, id: int = -1) -> dict:
    """
更改用户密码
    :param phone: 用户账号
    :param old: 老密码
    :param new: 新密码
    :param id: 事件请求id
    :return: json_dict
    """
    status, message = Login(phone, old)
    if status != 0:
        # status xxxx
        return {"id": id, "status": status, "message": message, "data": {}}
    json_dict = ForgetPass(phone=phone, password=new, id=id)
    return json_dict


def AddToken(phone: str, enduring: int = 0) -> str:
    """
    Add token in database
    :param phone: username
    :return: result string,success return token,failed return void string.
    """
    createdtime = time.strftime("%Y:%m:%d %H:%M:%S", time.localtime())
    time_now = int(time.time())
    time_expiration = time_now + 10 * 60
    token = MD5.md5(phone + str(time_now), "helpaged")
    cur = conn.cursor()
    sql = 'INSERT INTO tokens (token,phone,createdtime,expiration,counting,enduring)' \
          'VALUES ("{}","{}","{}",{},{},{})'.format(token, phone, createdtime, time_expiration, 1, enduring)
    try:
        Lock.acquire(AddToken, "AddToken")
        cur.execute(sql)
        conn.commit()
        Lock.release()
    except Exception as e:
        conn.rollback()
        cur.close()
        print("Failed to execute sql:{}|{}".format(sql, e))
        log_mysql.error("Failed to execute sql:{}|{}".format(sql, e))
        Auto_KeepConnect()
        return ""

    # 检查并删除过期的token,不删除长效token
    sql = "DELETE FROM tokens WHERE  expiration < {} AND enduring = 0".format(int(time.time()))
    # sql = "DELETE FROM tokens WHERE phone = '{}' AND expiration < {}".format(phone,int(time.time()))
    try:
        Lock.acquire(AddToken, "AddToken")
        num = cur.execute(sql)
        conn.commit()
        Lock.release()
        # print("【Thread-Token】Deleted {} tokens".format(num))
    except Exception as e:
        conn.rollback()
        print("Failed to execute sql:{}|{}".format(sql, e))
        log_mysql.error("Failed to execute sql:{}|{}".format(sql, e))
        Auto_KeepConnect()
        # return ""
    # 检查并删除多余的token
    sql = "SELECT token FROM tokens WHERE (" \
          "SELECT SUM(counting) FROM tokens WHERE phone = '{0}' AND enduring = 0)>10 " \
          "AND phone = '{0}' AND enduring = 0 ORDER BY createdtime ASC".format(phone)
    try:
        Lock.acquire(AddToken, "AddToken")
        cur.execute(sql)
        Lock.release()
        # conn.commit()
    except Exception as e:
        # conn.rollback()
        cur.close()
        print("Failed to execute sql:{}|{}".format(sql, e))
        log_mysql.error("Failed to execute sql:{}|{}".format(sql, e))
        Auto_KeepConnect()
        return ""
    data = cur.fetchall()
    num = len(data)
    # print("over num:",num)
    data = data[0:(num - 10)]
    for row in data:
        sql = "DELETE FROM tokens WHERE token = '{}'".format(row[0])
        try:
            Lock.acquire(AddToken, "AddToken")
            cur.execute(sql)
            conn.commit()
            Lock.release()
        except Exception as e:
            conn.rollback()
            cur.close()
            print("Failed to execute sql:{}|{}".format(sql, e))
            log_mysql.error("Failed to execute sql:{}|{}".format(sql, e))
            Auto_KeepConnect()
            return ""
        print("Deleted over-flowing record:{}".format(row[0]))

    cur.close()
    # 全部成功返回新token
    return token


def RefreshToken(token: str) -> bool:
    """
    刷新token过期时间
    :param token:token值
    :return:返回处理结果，成功为True，否则False
    """
    cur = conn.cursor()
    sql = "UPDATE tokens SET expiration = {} WHERE token = '{}'".format(int(time.time() + 600), token)
    try:
        Lock.acquire(RefreshToken, "RefreshToken")
        num = cur.execute(sql)
        conn.commit()
        Lock.release()
        cur.close()
    except Exception as e:
        conn.rollback()
        cur.close()
        print("Failed to execute sql:{}|{}".format(sql, e))
        log_mysql.error("Failed to execute sql:{}|{}".format(sql, e))
        Auto_KeepConnect()  # 尝试一下当sql出错后自动重连
        return False
    return True


def Doki(token: str, id: int = -1) -> dict:
    """
    检测token是否有效，返回json字典，若有效自动刷新token过期时间
    :param token: token值
    :return: 直接返回json字典
    """
    cur = conn.cursor()
    sql = "SELECT token FROM tokens WHERE token = '{}'".format(token)
    try:
        Lock.acquire(Doki, "Doki")
        num = cur.execute(sql)
        Lock.release()
        # conn.commit()
        cur.close()
    except Exception as e:
        cur.close()
        print("Failed to execute sql:{}|{}".format(sql, e))
        log_mysql.error("Failed to execute sql:{}|{}".format(sql, e))
        Auto_KeepConnect()  # 尝试一下当sql出错后自动重连
        # status -200 Get Doki info failed sql语句错误
        return {"id": id, "status": -200, "message": "Failure to operate database", "data": {}}
    if num == 0:
        # status 1 Token not existed Token不存在
        return {"id": id, "status": 1, "message": "Token not existed", "data": {}}
    elif num == 1:
        RefreshToken(token)
        # status 0 Successful Token存在
        return {"id": id, "status": 0, "message": "Successful", "data": {}}
    else:
        # status 200 Unkonwn token Error 同一Token大于2条
        return {"id": id, "status": 200, "message": "Invalid token number", "data": {}}


def Doki2(token: str) -> tuple:
    """
    检测token是否有效，返回一个由bool值和用户名的组成的元组，若有效自动刷新token过期时间
    :param token: token值
    :return: 返回逻辑值，真为token存在，假为token不存在
    """
    cur = conn.cursor()
    sql = "SELECT phone FROM tokens WHERE token = '{}'".format(token)
    try:
        Lock.acquire(Doki2, "Doki2")
        num = cur.execute(sql)
        Lock.release()
        # conn.commit()
    except Exception as e:
        cur.close()
        print("Failed to execute sql:{}|{}".format(sql, e))
        log_mysql.error("Failed to execute sql:{}|{}".format(sql, e))
        Auto_KeepConnect()  # 尝试一下当sql出错后自动重连
        # status -200 Failure to operate database语句错误
        return (False, "")

    if num == 1:
        data = cur.fetchone()
        cur.close()
        phone = data[0]
        RefreshToken(token)
        # status 0 Successfully Token存在
        return (True, phone)
    else:
        cur.close()
        # status -404 Unkonwn token Error 同一Token大于2条
        return (False, "")


def Auto_KeepConnect():
    """
    每十分钟定时断开数据库并重连，保持连接活性
    :return:
    """
    global conn
    Lock.release()
    try:
        DisconnectDB()
    except:
        pass
    try:
        conn = pymysql.connect(host=host, port=port, user=user,
                               passwd=password,
                               db=db, charset="utf8")
    except Exception as e:
        print("[MYSQL]Failed to connect MYSQL database")
        log_mysql.error("Failed to keep connect MYSQL database")
        sys.exit()
    else:
        print("[MYSQL]Keep Connect MYSQL database successfully")
        log_mysql.info("Keep Connect MYSQL database successfully")
    timer = Timer(600, Auto_KeepConnect)
    timer.start()


def UpdataUserInfo(phone: str, info: dict, id: int = -1) -> dict:
    """
Update user info ,return json dict,include id,status,message,data
    :param phone:
    :param info:
    :param id:
    :return: return json dict
    """
    cur = conn.cursor()
    sql = "UPDATE usersinfo SET "
    for key in info.keys():
        sql = sql + key + " = '{}' ,".format(info[key])
    sql = sql.rpartition(",")[0]
    sql = sql + "WHERE phone = '{}'".format(phone)
    try:
        Lock.acquire(UpdataUserInfo)
        num = cur.execute(sql)
        conn.commit()
        Lock.release()
    except Exception as e:
        conn.rollback()
        cur.close()
        print("Failed to execute sql:{}|{}".format(sql, e))
        log_mysql.error("Failed to execute sql:{}|{}".format(sql, e))
        Auto_KeepConnect()  # 尝试一下当sql出错后自动重连
        # status -200 Failure to operate database sql语句错误
        return {"id": id, "status": -200, "message": "Failure to operate database", "data": {}}
    cur.close()
    # status 0 Successful 成功！
    return {"id": id, "status": 0, "message": "Successful", "data": {}}


def DeleteUser(phone: str, id: int = -1) -> dict:
    """
删除用户，同时删除usersinfo,users,tokens里相关信息
    :param phone: 用户id
    :return:
    """
    cur = conn.cursor()
    sql = "DELETE usersinfo,users FROM usersinfo,users WHERE usersinfo.phone = '{0}' AND users.phone = '{0}'".format(
        phone)
    try:
        Lock.acquire(DeleteUser, "DeleteUser")
        num = cur.execute(sql)
        conn.commit()
        Lock.release()
    except Exception as e:
        conn.rollback()
        cur.close()
        print("Failed to execute sql:{}|{}".format(sql, e))
        log_mysql.error("Failed to execute sql:{}|{}".format(sql, e))
        Auto_KeepConnect()  # 尝试一下当sql出错后自动重连
        # status -200 Get user info failed sql语句错误
        return {"id": id, "status": -200, "message": "Failure to operate database", "data": {}}
    if num != 2:
        # status -200 Get user info failed sql语句错误
        return {"id": id, "status": -200, "message": "Failure to operate database", "data": {}}

    sql = "DELETE FROM tokens WHERE phone = '{}'".format(phone)
    try:
        Lock.acquire(DeleteUser, "DeleteUser")
        num = cur.execute(sql)
        conn.commit()
        Lock.release()
    except Exception as e:
        conn.rollback()
        cur.close()
        print("Failed to execute sql:{}|{}".format(sql, e))
        log_mysql.error("Failed to execute sql:{}|{}".format(sql, e))
        Auto_KeepConnect()  # 尝试一下当sql出错后自动重连
        # status -200 Get user info failed sql语句错误
        return {"id": id, "status": -200, "message": "Failure to operate database", "data": {}}
    if num > 0:
        # status 0 successful 成功处理事件
        return {"id": id, "status": 0, "message": "successful", "data": {}}
    else:
        # status -200 Get user info failed sql语句错误
        return {"id": id, "status": -200, "message": "Failure to operate database", "data": {}}


def GetUserInfo(token: str = "", user_id: str = "", id: int = -1) -> dict:
    """
    获取用户信息，返回json字典
    :param token: 用户token
    :param user_id: 用户id，此模块仅管理员用户有效
    :return: 直接返回json字典
    """
    if user_id == "":  # 判断查询方式，传user_id仅为管理员模式有效
        result, phone = Doki2(token)
        if result == False:
            # status 1 Error Token Token错误
            return {"id": id, "status": 1, "message": "Error Token", "data": {}}
    else:
        phone = user_id

    cur = conn.cursor()
    sql = "SELECT * FROM usersinfo WHERE phone = '{}'".format(phone)
    try:
        Lock.acquire(GetUserInfo, "GetUserInfo")
        num = cur.execute(sql)
        Lock.release()
        # conn.commit()
    except Exception as e:
        # conn.rollback()
        cur.close()
        print("Failed to execute sql:{}|{}".format(sql, e))
        log_mysql.error("Failed to execute sql:{}|{}".format(sql, e))
        Auto_KeepConnect()  # 尝试一下当sql出错后自动重连
        # status -200 Get user info failed sql语句错误
        return {"id": id, "status": -200, "message": "Failure to operate database", "data": {}}
    if num == 0:
        cur.close()
        # status 1 user not existed phone不存在
        return {"id": id, "status": 1, "message": "user not existed", "data": {}}
    elif num == 1:
        RefreshToken(token)
        row = cur.fetchone()
        data = {
            "phone": row[0],
            "name": row[1],
            "nickname": row[2],
            "email": row[3],
            "level": row[4],
        }
        cur.close()
        # status 0 Successful phone存在
        return {"id": id, "status": 0, "message": "Successful", "data": data}
    else:
        cur.close()
        # status 200 Unkonwn user info Error 同一phone大于2条
        return {"id": id, "status": 200, "message": "Unkonwn user info Error", "data": {}}
    # todo invavild


def GetUserNickname(user_id: str, id: int = -1) -> dict:
    cur = conn.cursor()
    sql = "SELECT nickname FROM usersinfo WHERE phone = '{}'".format(user_id)
    try:
        Lock.acquire(GetUserNickname, "GetUserNickname")
        num = cur.execute(sql)
        Lock.release()
        # conn.commit()
    except Exception as e:
        # conn.rollback()
        cur.close()
        print("Failed to execute sql:{}|{}".format(sql, e))
        log_mysql.error("Failed to execute sql:{}|{}".format(sql, e))
        Auto_KeepConnect()  # 尝试一下当sql出错后自动重连
        # status -200 Get user info failed sql语句错误
        return {"id": id, "status": -200, "message": "Failure to operate database", "data": {}}
    if num == 0:
        cur.close()
        # status 1 user not existed phone不存在
        return {"id": id, "status": 100, "message": "user not existed", "data": {}}
    elif num == 1:
        row = cur.fetchone()
        data = {
            "nickname": row[0],
        }
        cur.close()
        # status 0 Successful phone存在
        return {"id": id, "status": 0, "message": "Successful", "data": data}
    else:
        cur.close()
        # status 200 Unkonwn user info Error 同一phone大于2条
        return {"id": id, "status": 200, "message": "Unkonwn user info Error", "data": {}}


def GetUserNickname2(user_id: str) -> str:
    """
只返回用户昵称，不返回json_dict
    :param user_id: 用户id
    :return: 返回用户昵称
    """
    cur = conn.cursor()
    sql = "SELECT nickname FROM usersinfo WHERE phone = '{}'".format(user_id)
    try:
        Lock.acquire(GetUserNickname2, "GetUserNickname2")
        num = cur.execute(sql)
        Lock.release()
        # conn.commit()
    except Exception as e:
        # conn.rollback()
        cur.close()
        print("Failed to execute sql:{}|{}".format(sql, e))
        log_mysql.error("Failed to execute sql:{}|{}".format(sql, e))
        Auto_KeepConnect()  # 尝试一下当sql出错后自动重连
        # status -200 Get user info failed sql语句错误
        return ""
    if num == 0:
        cur.close()
        # status 1 user not existed phone不存在
        return ""
    elif num == 1:
        row = cur.fetchone()
        return row[0]
    else:
        cur.close()
        # status 200 Unkonwn user info Error 同一phone大于2条
        return ""


def AdminCheck(phone: str) -> bool:
    cur = conn.cursor()
    sql = "SELECT `group` FROM users WHERE phone = '{}'".format(phone)
    try:
        Lock.acquire(AdminCheck, "AdminCheck")
        row_num = cur.execute(sql)
        Lock.release()
        # conn.commit()
    except Exception as e:
        # conn.rollback()
        cur.close()
        print("Failed to execute sql:{}|{}".format(sql, e))
        log_mysql.error("Failed to execute sql:{}|{}".format(sql, e))
        Auto_KeepConnect()
        return False
    if row_num == 1:
        group = cur.fetchone()[0]
        if group == "__ADMIN__":
            return True
        else:
            return False
    else:
        return False


def AdminUserList(id: int = -1) -> dict:
    cur = conn.cursor()
    sql = "SELECT phone,`name`,nickname,email,`level` FROM usersinfo"
    try:
        Lock.acquire(AdminUserList, "AdminUserList")
        row_num = cur.execute(sql)
        Lock.release()
        # conn.commit()
    except Exception as e:
        # conn.rollback()
        cur.close()
        print("Failed to execute sql:{}|{}".format(sql, e))
        log_mysql.error("Failed to execute sql:{}|{}".format(sql, e))
        Auto_KeepConnect()
        # status -200 Execute sql failed sql语句错误
        return {"id": id, "status": -200, "message": "Failure to operate database", "data": {}}
    rows = cur.fetchall()
    user_list = []
    for row in rows:
        user_dict = {}
        user_dict["phone"] = row[0]
        user_dict["name"] = row[1]
        user_dict["nickname"] = row[2]
        user_dict["email"] = row[3]
        user_dict["level"] = row[4]
        user_list.append(user_dict)
    return {"id": id, "status": 0, "message": "successful", "data": user_list}


def AddFallPic(pic_name: str, device_name: str, content: str = "", id: int = -1):
    cur = conn.cursor()
    createdtime = time.strftime("%Y:%m:%d %H:%M:%S", time.localtime())
    event_id = MD5.md5(pic_name, str(time.time()))

    sql = "INSERT INTO notice (event_id,content,device,pic_name,createtime) VALUES ('{}','{}','{}','{}','{}')".format(
        event_id, content, device_name, pic_name, createdtime)
    try:
        Lock.acquire(AddFallPic, "AddFallPic")
        num = cur.execute(sql)
        conn.commit()
        Lock.release()
    except Exception as e:
        conn.rollback()
        cur.close()
        print("Failed to execute sql:{}|{}".format(sql, e))
        log_mysql.error("Failed to execute sql:{}|{}".format(sql, e))
        Auto_KeepConnect()
        # status -200 Execute sql failed sql语句错误
        return {"id": id, "status": -200, "message": "Failure to operate database", "data": {}}
    if num == 1:
        info_list = GetDevice2PhoneList(device=device_name)
        for info in info_list:
            result = Sms.SendFallMessage(info["phone"], info["name"])
            sms_status = result["result"]
            sms_message = result["errmsg"]
            if sms_message == "OK":
                sms_message = "Successful"
            if sms_status != 0:
                return {"id": id, "status": sms_status, "message": sms_message, "data": {}}
        # status 0 事件成功处理
        return {"id": id, "status": 0, "message": "Successful", "data": {"pic_name": pic_name}}
    else:
        # status -200 Execute sql failed sql语句错误
        return {"id": id, "status": -200, "message": "Failure to operate database", "data": {}}


def GetDevice2PhoneList(device: str) -> list:
    cur = conn.cursor()
    sql = "SELECT phone,`name` FROM usersinfo WHERE device = '{}'".format(device)
    info_list = []
    try:
        Lock.acquire(GetDevice2PhoneList, "GetDevice2PhoneList")
        num = cur.execute(sql)
        Lock.release()
    except Exception as e:
        conn.rollback()
        cur.close()
        print("Failed to execute sql:{}|{}".format(sql, e))
        log_mysql.error("Failed to execute sql:{}|{}".format(sql, e))
        Auto_KeepConnect()
        # status -200 Execute sql failed sql语句错误
        return info_list
    if num > 0:
        rows = cur.fetchall()
        cur.close()
        for row in rows:
            info_list.append({"phone": row[0], "name": row[1]})
        return info_list
    else:
        cur.close()
        return info_list


def GetBindDevice(user_id: str) -> tuple:
    cur = conn.cursor()
    ## 获取设备名
    sql = "SELECT device FROM usersinfo WHERE phone = '{}'".format(user_id)
    try:
        Lock.acquire(GetBindDevice, "GetBindDevice")
        num = cur.execute(sql)
        Lock.release()
    except Exception as e:
        cur.close()
        print("Failed to execute sql:{}|{}".format(sql, e))
        log_mysql.error("Failed to execute sql:{}|{}".format(sql, e))
        Auto_KeepConnect()
        # status -200 Execute sql failed sql语句错误
        return -200, "Failure to operate database", []
        # return {"id": id, "status": -200, "message": "Failure to operate database", "data": {}}
    if num == 0:
        cur.close()
        # status 100 账号不存在
        return 100, "user_id not exist", []
        # return {"id": id, "status": 100, "message": "user_id not exist", "data": {}}
    elif num == 1:
        row = cur.fetchone()
        device_name = str(row[0])
        if device_name == "":
            # status 101 账号未绑定设备
            return 101, "not bind device", []
            # return {"id": id, "status": 101, "message": "not bind device", "data": {}}
        device_list = device_name.split("|")
        device_last = device_list.pop(-1)
        if device_last != "":
            device_list.append(device_last)
        return 0, "successful", device_list
    else:
        # status -200 Execute sql failed sql语句错误
        return -200, "Failure to operate database", []
        # return {"id": id, "status": -200, "message": "Failure to operate database", "data": {}}


def GetNoticeList(username: str, mode: int, id: int = -1) -> dict:
    ## 获取设备名
    device_status, device_message, device_list = GetBindDevice(user_id=username)
    if device_status != 0:
        return {"id": id, "status": device_status, "message": device_message, "data": {}}
    cur = conn.cursor()
    device_sql = "("
    for device in device_list:
        device_sql = device_sql + "device = '{}' or ".format(device)
    device_sql = device_sql.rpartition("or ")[0]
    device_sql = device_sql + ")"

    ## 查询该设备发送的消息
    if mode == 0:  # 未读消息
        sql = "SELECT event_id,content,device,pic_name,createtime " \
              "FROM notice WHERE event_id NOT IN " \
              "(SELECT notice_user.event_id FROM notice_user " \
              "WHERE notice_user.user_id = '{}' AND notice_user.count = 1) AND {} ORDER BY createtime ASC".format(
            username,
            device_sql)
    elif mode == 1:  # 已读消息
        sql = "SELECT event_id,content,device,pic_name,createtime " \
              "FROM notice WHERE event_id IN " \
              "(SELECT notice_user.event_id FROM notice_user " \
              "WHERE notice_user.user_id = '{}' AND notice_user.count = 1) AND {} ORDER BY createtime ASC".format(
            username,
            device_sql)
    elif mode == 2:  # 全部消息
        sql = "SELECT event_id,content,device,pic_name,createtime FROM notice WHERE {} ORDER BY createtime ASC".format(
            device_sql)
    else:
        # status 102 mode value error
        return {"id": id, "status": 102, "message": "mode value error", "data": {}}
    try:
        Lock.acquire(GetNoticeList, "GetNoticeList")
        num = cur.execute(sql)
        Lock.release()
    except Exception as e:
        cur.close()
        print("Failed to execute sql:{}|{}".format(sql, e))
        log_mysql.error("Failed to execute sql:{}|{}".format(sql, e))
        Auto_KeepConnect()
        # status -200 Execute sql failed sql语句错误
        return {"id": id, "status": -200, "message": "Failure to operate database", "data": {}}
    rows = cur.fetchall()
    cur.close()
    notice_list = []
    for row in rows:
        notice_dict = {}
        notice_dict["event_id"] = row[0]
        notice_dict["content"] = row[1]
        notice_dict["device"] = row[2]
        notice_dict["pic_name"] = row[3]
        # img_bytes = COS.bytes_download("fallpic/{}".format(notice_dict["pic_name"]))
        # img_base64 = str(base64.b64encode(img_bytes), "utf-8")
        # notice_dict["base64"] = img_base64
        notice_dict["createtime"] = str(row[4])
        notice_list.append(notice_dict)
    # status 0 成功处理事件
    return {"id": id, "status": 0, "message": "successful", "data": {"num": num, "list": notice_list}}


def GetNoticeInfo(username: str, event_id: str, id: int = -1) -> dict:
    ## 获取设备名
    device_status, device_message, device_list = GetBindDevice(user_id=username)
    if device_status != 0:
        return {"id": id, "status": device_status, "message": device_message, "data": {}}
    cur = conn.cursor()
    device_sql = "("
    for device in device_list:
        device_sql = device_sql + "device = '{}' or ".format(device)
    device_sql = device_sql.rpartition("or ")[0]
    device_sql = device_sql + ")"
    sql = "SELECT event_id,content,device,pic_name,createtime FROM notice WHERE event_id = '{}' AND {}".format(event_id,
                                                                                                               device_sql)
    try:
        Lock.acquire(GetNoticeInfo, "GetNoticeInfo")
        num = cur.execute(sql)
        Lock.release()
    except Exception as e:
        cur.close()
        print("Failed to execute sql:{}|{}".format(sql, e))
        log_mysql.error("Failed to execute sql:{}|{}".format(sql, e))
        Auto_KeepConnect()
        # status -200 Execute sql failed sql语句错误
        return {"id": id, "status": -200, "message": "Failure to operate database", "data": {}}
    if num != 1:
        # status 200 GetNotice error
        return {"id": id, "status": 200, "message": "GetNotice error", "data": {}}
    row = cur.fetchone()
    # rows = cur.fetchall()
    cur.close()
    # notice_list = []
    # for row in rows:
    notice_dict = {}
    notice_dict["event_id"] = row[0]
    notice_dict["content"] = row[1]
    notice_dict["device"] = row[2]
    notice_dict["pic_name"] = row[3]
    img_bytes = COS.bytes_download("fallpic/{}".format(notice_dict["pic_name"]))
    img_base64 = str(base64.b64encode(img_bytes), "utf-8")
    notice_dict["base64"] = img_base64
    notice_dict["createtime"] = str(row[4])
    # notice_list.append(notice_dict)
    # status 0 成功处理事件
    return {"id": id, "status": 0, "message": "successful", "data": notice_dict}


def CheckDeviceIfExist(device: str) -> bool:
    cur = conn.cursor()
    sql = "SELECT COUNT(device_name) AS num FROM devices WHERE device_name = '{}'".format(device)
    try:
        Lock.acquire(CheckDeviceIfExist, "GetFallPicList")
        cur.execute(sql)
        Lock.release()
    except Exception as e:
        cur.close()
        print("Failed to execute sql:{}|{}".format(sql, e))
        log_mysql.error("Failed to execute sql:{}|{}".format(sql, e))
        Auto_KeepConnect()
        # status -200 Execute sql failed sql语句错误
        return False
    cur.close()
    num = cur.fetchone()[0]
    if num != 0:
        return True
    else:
        return False


def AddDevice(device: str, id: int = -1) -> dict:
    check_device = CheckDeviceIfExist(device)
    if check_device == True:
        # status 101 Duplicate device 重复的设备名称
        return {"id": id, "status": 101, "message": "Duplicate device", "data": {}}
    device_id = MD5.md5(device, "helpaged")
    cur = conn.cursor()
    sql = "INSERT INTO devices (device_id,device_name) VALUES ('{}','{}')".format(device_id, device)
    try:
        Lock.acquire(AddDevice, "AddDevice")
        num = cur.execute(sql)
        conn.commit()
        Lock.release()
    except Exception as e:
        cur.close()
        print("Failed to execute sql:{}|{}".format(sql, e))
        log_mysql.error("Failed to execute sql:{}|{}".format(sql, e))
        Auto_KeepConnect()
        # status -200 Execute sql failed sql语句错误
        return {"id": id, "status": -200, "message": "Failure to operate database", "data": {}}
    cur.close()
    if num == 1:
        # status 0 successful 成功处理事件
        return {"id": id, "status": 0, "message": "successful", "data": {}}
    else:
        # status 100 Failed to add device 添加设备失败
        return {"id": id, "status": 100, "message": "Failed to add device", "data": {}}


def BindDevice(username: str, device_id: str, id: int = -1) -> dict:
    cur = conn.cursor()
    # check device,因为用的是device_id进行筛选，故无法使用BindDevice函数
    sql = "SELECT device_name FROM devices WHERE device_id = '{}'".format(device_id)
    try:
        Lock.acquire(BindDevice, "BindDevice")
        num = cur.execute(sql)
        Lock.release()
    except Exception as e:
        cur.close()
        print("Failed to execute sql:{}|{}".format(sql, e))
        log_mysql.error("Failed to execute sql:{}|{}".format(sql, e))
        Auto_KeepConnect()
        # status -200 Execute sql failed sql语句错误
        return {"id": id, "status": -200, "message": "Failure to operate database", "data": {}}
    if num == 0:
        # status 100 device_id not exist 设备id不存在
        return {"id": id, "status": 100, "message": "device_id not exist", "data": {}}
    elif num > 1:
        # status 101 error
        pass
    row = cur.fetchone()
    device_name = row[0]

    device_status, device_message, device_list = GetBindDevice(user_id=username)
    if device_status != 0:
        return {"id": id, "status": device_status, "message": device_message, "data": {}}
    if device_list.count(device_name) != 0:
        # status 101 The device has already be bind 该账号已绑定该设备
        return {"id": id, "status": 101, "message": "The device has already be bind", "data": {}}
    device_list.append(device_name)
    device_str = ""
    for device in device_list:
        device_str = device_str + device + "|"
    sql = "UPDATE usersinfo SET device = '{}' WHERE phone = '{}'".format(device_str, username)
    try:
        Lock.acquire(BindDevice, "BindDevice")
        num = cur.execute(sql)
        conn.commit()
        Lock.release()
    except Exception as e:
        conn.rollback()
        cur.close()
        print("Failed to execute sql:{}|{}".format(sql, e))
        log_mysql.error("Failed to execute sql:{}|{}".format(sql, e))
        Auto_KeepConnect()
        # status -200 Execute sql failed sql语句错误
        return {"id": id, "status": -200, "message": "Failure to operate database", "data": {}}
    cur.close()
    if num == 1 or num == 0:
        # status 0 successful 成功处理事件
        return {"id": id, "status": 0, "message": "successful", "data": {}}
    else:
        # status -200 Execute sql failed sql语句错误
        return {"id": id, "status": -200, "message": "Failure to operate database", "data": {}}


def GetDeviceList(username: str, id: int = -1) -> dict:
    device_status, device_message, device_list = GetBindDevice(user_id=username)
    if device_status != 0:
        return {"id": id, "status": device_status, "message": device_message, "data": {}}
    device_info_list = []
    for device in device_list:
        device_info_dict = {}
        device_status, device_message, device_id, device_name = GetDeviceInfo2(device_name=device)
        if device_status != 0:
            return {"id": id, "status": device_status, "message": device_message, "data": {}}
        device_info_dict["device_id"] = device_id
        device_info_dict["device_name"] = device_name
        device_info_list.append(device_info_dict)
    # status 0 Successful 成功
    return {"id": id, "status": 0, "message": "Successful",
            "data": {"num": len(device_info_list), "list": device_info_list}}


def GetDeviceInfo(device_name: str = "", device_id: str = "", id: int = -1) -> dict:
    cur = conn.cursor()
    if device_name == "" and device_id == "":
        # status 100 Error device_name or device_id 设备名或设备id未传递
        return {"id": id, "status": 100, "message": "Error device_name or device_id", "data": {}}
    sql = ""
    if device_name == "":
        sql = "SELECT device_id,device_name FROM devices WHERE device_id = '{}'".format(device_id)
    elif device_id == "":
        sql = "SELECT device_id,device_name FROM devices WHERE device_name = '{}'".format(device_name)
    try:
        Lock.acquire(GetDeviceInfo, "GetDeviceInfo")
        num = cur.execute(sql)
        Lock.release()
    except Exception as e:
        cur.close()
        print("Failed to execute sql:{}|{}".format(sql, e))
        log_mysql.error("Failed to execute sql:{}|{}".format(sql, e))
        Auto_KeepConnect()
        # status -200 Execute sql failed sql语句错误
        return {"id": id, "status": -200, "message": "Failure to operate database", "data": {}}
    if num == 0:
        cur.close()
        # status -200 No Such Device 设备不存在
        return {"id": id, "status": 101, "message": "No Such Device", "data": {}}
    elif num == 1:
        row = cur.fetchone()
        cur.close()
        device_dict = {}
        device_dict["device_id"] = row[0]
        device_dict["device_name"] = row[1]
        # status 0 successful 成功
        return {"id": id, "status": 0, "message": "Successful", "data": device_dict}
    else:
        cur.close()
        # status -200 Execute sql failed sql语句错误
        return {"id": id, "status": -200, "message": "Failure to operate database", "data": {}}


def GetDeviceInfo2(device_name: str = "", device_id: str = "") -> tuple:
    cur = conn.cursor()
    if device_name == "" and device_id == "":
        # status 102 Error device_name or device_id 设备名或设备id未传递
        return 102, "Error device_name or device_id", "", ""
        # return {"id": id, "status": 102, "message": "Error device_name or device_id", "data": {}}
    sql = ""
    if device_name == "":
        sql = "SELECT device_id,device_name FROM devices WHERE device_id = '{}'".format(device_id)
    elif device_id == "":
        sql = "SELECT device_id,device_name FROM devices WHERE device_name = '{}'".format(device_name)
    try:
        Lock.acquire(GetDeviceInfo, "GetDeviceInfo")
        num = cur.execute(sql)
        Lock.release()
    except Exception as e:
        cur.close()
        print("Failed to execute sql:{}|{}".format(sql, e))
        log_mysql.error("Failed to execute sql:{}|{}".format(sql, e))
        Auto_KeepConnect()
        # status -200 Execute sql failed sql语句错误
        return 200, "Failure to operate database", "", ""
        # return {"id": id, "status": -200, "message": "Failure to operate database", "data": {}}
    if num == 0:
        cur.close()
        # status -200 No Such Device 设备不存在
        return 103, "No Such Device", "", ""
        # return {"id": id, "status": 103, "message": "No Such Device", "data": {}}
    elif num == 1:
        row = cur.fetchone()
        cur.close()
        # status 0 successful 成功
        return 0, "Successful", row[0], row[1]
        # return {"id": id, "status": 0, "message": "Successful", "data": device_dict}
    else:
        cur.close()
        # status -200 Execute sql failed sql语句错误
        return 200, "Failure to operate database", "", ""
        # return {"id": id, "status": -200, "message": "Failure to operate database", "data": {}}


def CheckEventIfExist(event_id: str) -> bool:
    cur = conn.cursor()
    sql = "SELECT COUNT(event_id) AS num FROM notice WHERE event_id = '{}'".format(event_id)
    try:
        Lock.acquire(CheckEventIfExist, "CheckEventIfExist")
        cur.execute(sql)
        Lock.release()
    except Exception as e:
        conn.rollback()
        cur.close()
        print("Failed to execute sql:{}|{}".format(sql, e))
        log_mysql.error("Failed to execute sql:{}|{}".format(sql, e))
        Auto_KeepConnect()
        # status -200 Execute sql failed sql语句错误
        return False
    num = cur.fetchone()[0]
    if num == 1:
        return True
    else:
        return False


def CheckEventIfSigned(username: str, event_id: str) -> bool:
    cur = conn.cursor()
    # 查找是否已标记
    sql = "SELECT COUNT(`count`) AS num FROM notice_user WHERE event_id = '{}' AND user_id = '{}'".format(event_id,
                                                                                                          username)
    try:
        Lock.acquire(CheckEventIfSigned, "CheckEventIfSigned")
        cur.execute(sql)
        Lock.release()
    except Exception as e:
        conn.rollback()
        cur.close()
        print("Failed to execute sql:{}|{}".format(sql, e))
        log_mysql.error("Failed to execute sql:{}|{}".format(sql, e))
        Auto_KeepConnect()
        # status -200 Execute sql failed sql语句错误
        return False
    num = cur.fetchone()[0]
    if num >= 1:
        return True
    else:
        return False


def SignNotice(username: str, event_id: str, id: int = -1) -> dict:
    check_event = CheckEventIfExist(event_id)
    if check_event == False:
        # status 100 error event_id
        return {"id": id, "status": 100, "message": "Error event_id", "data": {}}
    check_signed = CheckEventIfSigned(username=username, event_id=event_id)
    if check_signed == True:
        # status 101 this event_id has been signed
        return {"id": id, "status": 101, "message": "event_id has been signed", "data": {}}
    cur = conn.cursor()
    sql = "INSERT INTO notice_user (event_id,user_id,`count`) VALUES ('{}','{}',{})".format(event_id, username, 1)
    try:
        Lock.acquire(SignNotice, "SignNotice")
        num = cur.execute(sql)
        conn.commit()
        Lock.release()
    except Exception as e:
        conn.rollback()
        cur.close()
        print("Failed to execute sql:{}|{}".format(sql, e))
        log_mysql.error("Failed to execute sql:{}|{}".format(sql, e))
        Auto_KeepConnect()
        # status -200 Execute sql failed sql语句错误
        return {"id": id, "status": -200, "message": "Failure to operate database", "data": {}}
    if num == 1:
        # status 0 successful 成功处理事件
        return {"id": id, "status": 0, "message": "successful", "data": {}}
    else:
        # status 102 add notice sign error
        return {"id": id, "status": 102, "message": "add notice sign error", "data": {}}


def DeviceDoki(token: str) -> tuple:
    """
    检测token是否有效，返回一个由bool值和用户名的组成的元组，若有效自动刷新token过期时间
    :param token: token值
    :return: 返回逻辑值，真为token存在，假为token不存在
    """
    cur = conn.cursor()
    sql = "SELECT device_name FROM devices WHERE device_id = '{}'".format(token)
    try:
        Lock.acquire(DeviceDoki, "DeviceDoki")
        num = cur.execute(sql)
        Lock.release()
        # conn.commit()
    except Exception as e:
        cur.close()
        print("Failed to execute sql:{}|{}".format(sql, e))
        log_mysql.error("Failed to execute sql:{}|{}".format(sql, e))
        Auto_KeepConnect()  # 尝试一下当sql出错后自动重连
        # status -200 Failure to operate database语句错误
        return (False, "")

    if num == 1:
        data = cur.fetchone()
        cur.close()
        device_name = data[0]
        RefreshToken(token)
        # status 0 Successful Token存在
        return (True, device_name)
    else:
        cur.close()
        # status -404 Unkonwn token Error 同一Token大于2条
        return (False, "")


if __name__ == '__main__':
    Initialize()
