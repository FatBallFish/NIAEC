from flask import Flask, request
from m_mysql import py_mysql as MySQL
from m_img import py_captcha_main as ImgCaptcha
from m_sms import py_sms_main as SmsCaptcha
from m_redis import py_redis as Redis
from m_cos import py_cos_main as COS
from configparser import ConfigParser
import logging, os, time, random
import sys, getopt
import json, ssl
import base64
import MD5
import threading

ssl._create_default_https_context = ssl._create_unverified_context
app = Flask(__name__)

LOG_FORMAT = "[%(asctime)-15s] - [%(name)10s]\t- [%(levelname)s]\t- [%(funcName)-20s:%(lineno)3s]\t- [%(message)s]"
DATA_FORMAT = "%Y.%m.%d %H:%M:%S %p "
log_outpath = "./my.log"
Main_filepath = os.path.dirname(os.path.abspath(__file__))
print("Main FilePath:", Main_filepath)


def Initialize(argv: list):
    """
模块初始化，此函数应在所有命令之前调用
    :param argv: 命令行参数表
    """
    # print("Enter the function")
    global config_addr
    try:
        opts, args = getopt.getopt(argv, "hc:", ["config", "help"])
    except getopt.GetoptError:
        print("test.py -c <ConfigFilePath> -h <help>")
        sys.exit(2)
    for opt, arg in opts:
        # print("opt,arg",opt,arg)
        if opt in ("-h", "--help"):
            print("-" * 80)
            print("-h or --help      Show this passage.")
            print("-c or --config    Configuration file path")
            print("-" * 80)
            sys.exit()
        elif opt in ("-c", "--config"):
            config_addr = str(arg)
            print("config_addr:", config_addr)
            break
        else:
            # log_main.warning("Useless argv:[%s|%s]",opt,arg)
            print("Useless argv:[%s|%s]" % (opt, arg))
    else:
        # log_main.error("missing config argv")
        print("missing config argv")
        # log_main.info("Program Ended")
        sys.exit()
    cf = ConfigParser()
    try:
        cf.read(config_addr)
    except Exception as e:
        ##log_main.error("Error config file path")
        print("Error config file path")
        ##log_main.info("Program Ended")
        sys.exit()
    sections = cf.sections()
    for section in sections:
        if section in ["Log", "Redis", "SmsCaptcha"]:
            break
    else:
        ##log_main.error("Config file missing some necessary sections")
        print("Config file missing some necessary sections")
        ##log_main.info("Program Ended")
        sys.exit()

    # 读main配置
    # TODO CONFIG
    global log_main
    try:
        global log_outpath, webhost, webport, webdebug
        log_outpath = cf.get("Main", "logoutpath")
        webhost = cf.get("Main", "webhost")
        webport = cf.get("Main", "webport")
        intdebug = cf.get("Main", "webdebug")
        if intdebug == 1:
            webdebug = True
        else:
            webdebug = False
        print("[Main]log_outpath:", log_outpath)
        print("[Main]webhost:", webhost)
        print("[Main]webport:", webport)
        print("[Main]webdebug:", webdebug)
    except Exception as e:
        print("Error")
    logging.basicConfig(filename=log_outpath, level=logging.INFO,
                        format=LOG_FORMAT.center(30),
                        datefmt=DATA_FORMAT)
    log_main = logging.getLogger(__name__)
    # ------模块初始化------
    ImgCaptcha.Initialize(config_addr, Main_filepath)
    SmsCaptcha.Initialize(config_addr, Main_filepath)
    COS.Initialize(config_addr, Main_filepath)
    MySQL.Initialize(config_addr, Main_filepath)
    Redis.Initialize(config_addr, Main_filepath)


class MyThread(threading.Thread):
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter

    def run(self):
        log_main.info("Start thread {} to auto del outtime code".format(self.name))
        print("开始线程：" + self.name)
        if self.name == "AutoRemoveExpireToken":
            # lock.acquire()
            # MySQL.Auto_del_token()
            # lock.release()
            pass
        elif self.name == "AutoKeepConnect":
            MySQL.Auto_KeepConnect()
        elif self.name == "AutoRemoveExpireHash":
            # lock.acquire()
            Redis.Auto_del_hash()
            # lock.release()
        # log_main.info("End thread {} to auto del outtime code".format(self.name))
        # print ("退出线程：" + self.name)


@app.route("/ping")
def ping():
    return "<h1>Pong</h1>"


@app.route("/user/doki", methods=["GET"])
def doki():
    token = ""
    arg_dict = request.args
    try:
        token = arg_dict.get("token")
    except Exception as e:
        print(e)

    if token == None:
        # status -1000 Missing necessary args api地址中缺少token参数
        return json.dumps({"id": -1, "status": -1000, "message": "Missing necessary args", "data": {}})
    # print("token:",token)
    json_dict = MySQL.Doki(token)
    return json.dumps(json_dict)


@app.route("/user/login", methods=["POST"])
def login():
    data = request.json
    print(data)

    # 判断键值对是否存在
    try:
        keys = data.keys()
    except Exception as e:
        # status -1 json的key错误。此处id是因为没有进行读取，所以返回默认的-1。
        return json.dumps({"id": -1, "status": -1, "message": "Error JSON key", "data": {}})
    # 先获取json里id的值，若不存在，默认值为-1
    if "id" in data.keys():
        id = data["id"]
    else:
        id = -1

    # 判断指定所需字段是否存在，若不存在返回status -1 json。
    for key in ["type", "subtype", "data"]:
        if key not in data.keys():
            # status -1 json的key错误。
            return json.dumps({"id": id, "status": -1, "message": "Error JSON key", "data": {}})
    # 处理json
    if data["type"] == "login":
        if data["subtype"] == "pass":
            data = data["data"]
            for key in data.keys():
                if key not in ["phone", "pass", "enduring"]:
                    # status -3 json的value错误。
                    return json.dumps({"id": id, "status": -3, "message": "Error data key", "data": {}})
            phone = data["phone"]
            password = data["pass"]
            # todo check salt
            if "enduring" in data.keys():
                enduring = data["enduring"]
                if not isinstance(enduring, int):
                    enduring = 0
                if enduring != 0:
                    enduring = 1
            else:
                enduring = 0
            # print(password)
            status, result = MySQL.Login(phone, password, enduring=enduring)
            if status == 0:
                # status 0 登录成功，获取用户信息
                return json.dumps({"id": id, "status": 0, "message": "Successful", "data": {"token": result}})
            else:
                # status 其他错误
                return json.dumps({"id": id, "status": status, "message": result, "data": {}})
        else:
            # status -2 json的value错误。
            return json.dumps({"id": id, "status": -2, "message": "Error JSON value", "data": {}})
    else:
        # status -2 json的value错误。
        return json.dumps({"id": id, "status": -2, "message": "Error JSON value", "data": {}})


@app.route("/user/register", methods=["POST"])
def register():
    data = request.json
    print(data)
    # 判断键值对是否存在
    try:
        keys = data.keys()
    except Exception as e:
        # status -1 json的key错误。此处id是因为没有进行读取，所以返回默认的-1。
        return json.dumps({"id": -1, "status": -1, "message": "Error JSON key", "data": {}})
    # 先获取json里id的值，若不存在，默认值为-1
    if "id" in data.keys():
        id = data["id"]
    else:
        id = -1

    # 判断指定所需字段是否存在，若不存在返回status -1 json。
    for key in ["type", "subtype", "data"]:
        if not key in data.keys():
            # status -1 json的key错误。
            return json.dumps({"id": id, "status": -1, "message": "Error JSON key", "data": {}})
    # 处理json
    if data["type"] == "register":
        if data["subtype"] == "phone":
            data = data["data"]
            for key in data.keys():
                if key not in ["phone", "hash", "pass"]:
                    # status -3 json的value错误。
                    return json.dumps({"id": id, "status": -3, "message": "Error data key", "data": {}})
            phone = data["phone"]
            hash = data["hash"]
            password = data["pass"]
            # password = MD5.md5(password, "guochuang")
            result = Redis.SafeCheck(hash)
            if result == False:
                # status -4 hash不存在
                return json.dumps({"id": id, "status": -4, "message": "Error hash", "data": {}})

            status, result = MySQL.Register(phone, password)
            if status == 0:
                # status 0 注册成功
                return json.dumps({"id": id, "status": 0, "message": "Successful", "data": {}})
            else:
                # status -100,-200,100,101 Mysql处理结果
                return json.dumps({"id": id, "status": status, "message": result, "data": {}})
        else:
            # status -2 json的value错误。
            return json.dumps({"id": id, "status": -2, "message": "Error JSON value", "data": {}})
    else:
        # status -2 json的value错误。
        return json.dumps({"id": id, "status": -2, "message": "Error JSON value", "data": {}})


@app.route("/user/password", methods=["POST"])
def password():
    data = request.json
    print(data)
    # 判断键值对是否存在
    try:
        keys = data.keys()
    except Exception as e:
        # status -1 json的key错误。此处id是因为没有进行读取，所以返回默认的-1。
        return json.dumps({"id": -1, "status": -1, "message": "Error JSON key", "data": {}})
    # 先获取json里id的值，若不存在，默认值为-1
    if "id" in data.keys():
        id = data["id"]
    else:
        id = -1

    # 判断指定所需字段是否存在，若不存在返回status -1 json。
    for key in ["type", "subtype", "data"]:
        if key not in data.keys():
            # status -1 json的key错误。
            return json.dumps({"id": id, "status": -1, "message": "Error JSON key", "data": {}})
    # 处理json
    if data["type"] == "password":
        if data["subtype"] == "forget":
            data = data["data"]
            for key in data.keys():
                if key not in ["phone", "hash", "pass"]:
                    # status -3 json的value错误。
                    return json.dumps({"id": id, "status": -3, "message": "Error data key", "data": {}})
            phone = data["phone"]
            hash = data["hash"]
            password = data["pass"]
            # todo check salt
            result = Redis.SafeCheck(hash)
            if result == False:
                # status 400 hash不存在
                return json.dumps({"id": id, "status": 400, "message": "Error hash", "data": {}})
            json_dict = MySQL.ForgetPass(phone=phone, password=password, id=id)
            return json.dumps(json_dict)
        elif data["subtype"] == 'change':
            data = data["data"]
            for key in data.keys():
                if key not in ["phone", "old", "new"]:
                    # status -3 json的value错误。
                    return json.dumps({"id": id, "status": -3, "message": "Error data key", "data": {}})
            phone = data["phone"]
            old = data["old"]
            new = data["new"]
            json_dict = MySQL.ChangePass(phone=phone, old=old, new=new, id=id)
            return json.dumps(json_dict)
        else:
            # status -2 json的value错误。
            return json.dumps({"id": id, "status": -2, "message": "Error JSON value", "data": {}})
    else:
        # status -2 json的value错误。
        return json.dumps({"id": id, "status": -2, "message": "Error JSON value", "data": {}})


@app.route("/user/info", methods=["GET", "POST"])
def userinfo():
    if request.method == "GET":
        token = ""
        arg_dict = request.args
        try:
            token = arg_dict.get("token")
        except Exception as e:
            print(e)

        if token == None:
            # status -100 Missing necessary args api地址中缺少token参数
            return json.dumps({"id": -1, "status": -100, "message": "Missing necessary args", "data": {}})
        # print("token:",token)
        json_dict = dict(MySQL.GetUserInfo(token=token))
        return json.dumps(json_dict)
    elif request.method == "POST":
        try:
            token = request.args["token"]
            print("token:", token)
        except Exception as e:
            print("Missing necessary args")
            log_main.error("Missing necessary agrs")
            # status -100 缺少必要的参数
            return json.dumps({"id": -1, "status": -100, "message": "Missing necessary args", "data": {}})
        token_check_result, username = MySQL.Doki2(token)
        if token_check_result == False:
            # status -101 token不正确
            return json.dumps({"id": -1, "status": -101, "message": "Error token", "data": {}})
        # 验证身份完成，处理数据
        data = request.json
        print(data)

        # 先获取json里id的值，若不存在，默认值为-1
        try:
            keys = data.keys()
        except Exception as e:
            # status -1 json的key错误。此处id是因为没有进行读取，所以返回默认的-1。
            return json.dumps({"id": -1, "status": -1, "message": "Error JSON key", "data": {}})

        if "id" in data.keys():
            id = data["id"]
        else:
            id = -1

        ## 判断指定所需字段是否存在，若不存在返回status -1 json。
        for key in ["type", "subtype", "data"]:
            if key not in data.keys():
                # status -1 json的key错误。
                return json.dumps({"id": id, "status": -1, "message": "Error JSON key", "data": {}})
        type = data["type"]
        subtype = data["subtype"]
        ## -------正式处理事务-------
        data = data["data"]
        if type == "info":  ## 用户信息api
            if subtype == "update":  ## 用户信息更新api
                # 判断指定所需字段是否存在，若不存在返回status -1 json。
                for key in data.keys():
                    if key not in ["phone", "name", "nickname", "email", "level"]:
                        # status -3 Error data key data数据中必需key缺失
                        return json.dumps(
                            {"id": id, "status": -3, "message": "Error data key", "data": {}})
                phone = data["phone"]
                temp_info = {}
                for key in data.keys():
                    if key == "phone":
                        continue
                    temp_info[key] = data[key]
                json_dict = MySQL.UpdataUserInfo(phone, temp_info, id=id)

                return json.dumps(json_dict)
            else:
                # status -2 json的value错误。
                return json.dumps({"id": id, "status": -2, "message": "Error JSON value", "data": {}})
        else:
            # status -2 json的value错误。
            return json.dumps({"id": id, "status": -2, "message": "Error JSON value", "data": {}})


@app.route("/user/nickname", methods=["POST"])
def usernickename():
    try:
        token = request.args["token"]
        print("token:", token)
    except Exception as e:
        print("Missing necessary args")
        log_main.error("Missing necessary agrs")
        # status -100 缺少必要的参数
        return json.dumps({"id": -1, "status": -100, "message": "Missing necessary args", "data": {}})
    token_check_result, username = MySQL.Doki2(token)
    if token_check_result == False:
        # status -101 token不正确
        return json.dumps({"id": -1, "status": -101, "message": "Error token", "data": {}})
    # 验证身份完成，处理数据
    data = request.json
    # print(data)
    try:
        keys = data.keys()
    except Exception as e:
        # status -1 json的key错误。此处id是因为没有进行读取，所以返回默认的-1。
        return json.dumps({"id": -1, "status": -1, "message": "Error JSON key", "data": {}})

    if "id" in data.keys():
        id = data["id"]
    else:
        id = -1

    # 判断指定所需字段是否存在，若不存在返回status -1 json。
    for key in ["type", "subtype", "data"]:
        if not key in data.keys():
            # status -1 json的key错误。
            return json.dumps({"id": id, "status": -1, "message": "Error JSON key", "data": {}})
    type = data["type"]
    subtype = data["subtype"]
    data = data["data"]
    # 处理json
    if type == "info":
        if subtype == "nickname":
            if "user_id" not in data.keys():
                # status -3 json的value错误。
                return json.dumps({"id": id, "status": -3, "message": "Error data key", "data": {}})
            user_id = data['user_id']
            json_dict = MySQL.GetUserNickname(user_id=user_id, id=id)
            return json.dumps(json_dict)
        else:
            # status -2 json的value错误。
            return json.dumps({"id": id, "status": -2, "message": "Error JSON value", "data": {}})
    else:
        # status -2 json的value错误。
        return json.dumps({"id": id, "status": -2, "message": "Error JSON value", "data": {}})


@app.route("/captcha", methods=["POST"])
def captcha():
    data = request.json
    print(data)

    # 判断键值对是否存在
    try:
        keys = data.keys()
    except Exception as e:
        # status -1 json的key错误。此处id是因为没有进行读取，所以返回默认的-1。
        return json.dumps({"id": -1, "status": -1, "message": "Error JSON key", "data": {}})
    # 先获取json里id的值，若不存在，默认值为-1
    if "id" in data.keys():
        id = data["id"]
    else:
        id = -1

    # 判断指定所需字段是否存在，若不存在返回status -1 json。
    for key in ["type", "subtype", "data"]:
        if not key in data.keys():
            # status -1 json的key错误。
            return json.dumps({"id": id, "status": -1, "message": "Error JSON key", "data": {}})

    # 处理json
    if data["type"] == "img":
        if data["subtype"] == "generate":
            data = data["data"]
            # code,addr = ImgCaptcha.CreatCode()
            code, b64_data = ImgCaptcha.CreatCode()
            code = code.lower()  # 将所有的验证码转成小写
            rand_str = ""
            for i in range(5):
                char1 = random.choice(
                    [chr(random.randint(65, 90)), chr(random.randint(48, 57)), chr(random.randint(97, 122))])
                rand_str += char1
            hash = MD5.md5(code, salt=rand_str)
            result = Redis.AddImgHash(hash)
            # todo 优化验证机制
            if result == False:
                # status -404 Unkown Error
                return json.dumps({
                    "id": id,
                    "status": -404,
                    "message": "Unknown Error",
                    "data": {}
                })
            # status 0 ImgCaptcha生成成功
            # return json.dumps({
            #     "id":id,
            #     "status":0,
            #     "message":"Successful",
            #     "data":{"code":code,"addr":addr,"rand":rand_str}
            return json.dumps({
                "id": id,
                "status": 0,
                "message": "Successful",
                "data": {"imgdata": b64_data, "rand": rand_str}
                # 改动：将code字段删除
            })
        elif data["subtype"] == "validate":
            data = data["data"]
            for key in data.keys():
                if key not in ["hash"]:
                    # status -3 json的value错误。
                    return json.dumps({"id": id, "status": -3, "message": "Error data key", "data": {}})
            hash = data["hash"]
            result = Redis.SafeCheck(hash)
            if result == True:
                # status 0 校验成功。
                return json.dumps({
                    "id": id,
                    "status": 0,
                    "message": "successful",
                    "data": {}
                })
            elif result == False:
                # status 100 验证码hash值不匹配(包括验证码过期)。
                return json.dumps({
                    "id": id,
                    "status": 100,
                    "message": "Error captcha hash",
                    "data": {}
                })
            else:
                # status -404 Unkown Error
                return json.dumps({
                    "id": id,
                    "status": -404,
                    "message": "Unknown Error",
                    "data": {}
                })
        else:
            # status -2 json的value错误。
            return json.dumps({"id": id, "status": -2, "message": "Error JSON value", "data": {}})
    elif data["type"] == "sms":
        if data["subtype"] == "generate":
            data = data["data"]
            for key in ["phone"]:
                # if key not in ["phone","hash"]:
                if key not in data.keys():
                    # status -3 Error data key | data_json key错误
                    return json.dumps({"id": id, "status": -3, "message": "Error data key", "data": {}})
            # hash = data["hash"]
            # result = Redis.SafeCheck(hash)
            # if result != 0:
            #     # status -4 json的value错误。
            #     return json.dumps({"id": id, "status": -4, "message": "Error Hash", "data": {}})
            phone = str(data["phone"])
            command_type = 1
            if "command_type" in data.keys():
                command_type = data["command_type"]
            code = random.randint(10000, 99999)
            if command_type == 1:
                result = SmsCaptcha.SendCaptchaCode(phone_number=phone, captcha=code, command_str="注册账号", ext=str(id))
            elif command_type == 2:
                result = SmsCaptcha.SendCaptchaCode(phone_number=phone, captcha=code, command_str="找回密码", ext=str(id))
            else:
                # status -204 Arg's value error 键值对数据错误。
                return json.dumps({"id": id, "status": -204, "message": "Arg's value error", "data": {}})
            status = result["result"]
            message = result["errmsg"]
            if message == "OK":
                message = "Successful"
            rand_str = ""
            if status == 0:
                for i in range(5):
                    char1 = random.choice(
                        [chr(random.randint(65, 90)), chr(random.randint(48, 57)), chr(random.randint(97, 122))])
                    rand_str += char1
                hash = MD5.md5(code, salt=rand_str)
                result = Redis.AddSmsHash(hash)
                if result == False:
                    # status -404 Unkown Error
                    return json.dumps({
                        "id": id,
                        "status": -404,
                        "message": "Unknown Error",
                        "data": {}
                    })
                # status 0 SmsCaptcha生成成功
                return json.dumps({
                    "id": id,
                    "status": status,
                    "message": message,
                    "data": {"rand": rand_str}
                })
                # 改动：将code字段删除
            else:
                # status=result["result"] 遇到错误原样返回腾讯云信息
                return json.dumps({
                    "id": id,
                    "status": status,
                    "message": message,
                    "data": {}
                })
        elif data["subtype"] == "validate":
            data = data["data"]
            for key in data.keys():
                if key not in ["hash"]:
                    # status -3 json的value错误。
                    return json.dumps({"id": id, "status": -3, "message": "Error data key", "data": {}})
            hash = data["hash"]
            result = Redis.SafeCheck(hash)
            if result == True:
                # status 0 校验成功。
                return json.dumps({
                    "id": id,
                    "status": 0,
                    "message": "successful",
                    "data": {}
                })
            elif result == False:
                # status 100 验证码hash值不匹配(包括验证码过期)。
                return json.dumps({
                    "id": id,
                    "status": 100,
                    "message": "Error captcha hash",
                    "data": {}
                })
            else:
                # status -404 Unkown Error
                return json.dumps({
                    "id": id,
                    "status": -404,
                    "message": "Unknown Error",
                    "data": {}
                })
        elif data["subtype"] == "delete":
            pass
        else:
            # status -2 json的value错误。
            return json.dumps({"id": id, "status": -2, "message": "Error JSON value", "data": {}})
    else:
        # status -2 json的value错误。
        return json.dumps({"id": id, "status": -2, "message": "Error JSON value", "data": {}})


@app.route("/admin/user", methods=["POST"])
def admin_user():
    try:
        token = request.args["token"]
        print("token:", token)
    except Exception as e:
        print("Missing necessary args")
        log_main.error("Missing necessary agrs")
        # status -100 缺少必要的参数
        return json.dumps({"id": -1, "status": -100, "message": "Missing necessary args", "data": {}})
    token_check_result, username = MySQL.Doki2(token)
    if token_check_result == False:
        # status -101 token不正确
        return json.dumps({"id": -1, "status": -101, "message": "Error token", "data": {}})
    admin_check_result = MySQL.AdminCheck(phone=username)
    if admin_check_result == False:
        # status -103 用户无权操作
        return json.dumps({"id": -1, "status": -103, "message": "No permission to operate", "data": {}})
    # 验证身份完成，处理数据
    data = request.json
    print(data)

    # 判断键值对是否存在
    try:
        keys = data.keys()
    except Exception as e:
        # status -1 json的key错误。此处id是因为没有进行读取，所以返回默认的-1。
        return json.dumps({"id": -1, "status": -1, "message": "Error JSON key", "data": {}})
    # 先获取json里id的值，若不存在，默认值为-1
    if "id" in data.keys():
        id = data["id"]
    else:
        id = -1

    # 判断指定所需字段是否存在，若不存在返回status -1 json。
    for key in ["type", "subtype", "data"]:
        if key not in data.keys():
            # status -1 json的key错误。
            return json.dumps({"id": id, "status": -1, "message": "Error JSON key", "data": {}})
    # 处理json
    type = data["type"]
    subtype = data["subtype"]
    data = data["data"]
    if type == "user":
        if subtype == "list":
            json_dict = MySQL.AdminUserList(id=id)
            return json.dumps(json_dict)
        elif subtype == "info":
            for key in ["phone"]:
                if key not in data.keys():
                    # status -3 json的value错误。
                    return json.dumps({"id": id, "status": -3, "message": "Error data key", "data": {}})
                phone = data["phone"]
                json_dict = MySQL.GetUserInfo(user_id=phone, id=id)
                return json.dumps(json_dict)
        elif subtype == "update":
            for key in data.keys():
                if key not in ["phone", "name", "nickname", "email", "level"]:
                    # status -3 Error data key data数据中必需key缺失
                    return json.dumps(
                        {"id": id, "status": -3, "message": "Error data key", "data": {}})
            phone = data["phone"]
            temp_info = {}
            for key in data.keys():
                if key == "phone":
                    continue
                temp_info[key] = data[key]
            json_dict = MySQL.UpdataUserInfo(phone, temp_info, id=id)
            return json.dumps(json_dict)
        elif subtype == "delete":
            for key in ["phone"]:
                if key not in data.keys():
                    # status -3 Error data key data数据中必需key缺失
                    return json.dumps({"id": id, "status": -3, "message": "Error data key", "data": {}})
            phone = data["phone"]
            json_dict = MySQL.DeleteUser(phone=phone, id=id)
            return json.dumps(json_dict)
        else:
            # status -2 json的value错误。
            return json.dumps({"id": id, "status": -2, "message": "Error JSON value", "data": {}})
    else:
        # status -2 json的value错误。
        return json.dumps({"id": id, "status": -2, "message": "Error JSON value", "data": {}})


@app.route("/device", methods=["POST"])
def device():
    try:
        token = request.args["token"]
        print("token:", token)
    except Exception as e:
        print("Missing necessary args")
        log_main.error("Missing necessary agrs")
        # status -100 缺少必要的参数
        return json.dumps({"id": -1, "status": -100, "message": "Missing necessary args", "data": {}})
    token_check_result, username = MySQL.Doki2(token)
    if token_check_result == False:
        # status -101 token不正确
        return json.dumps({"id": -1, "status": -101, "message": "Error token", "data": {}})
    # 验证身份完成，处理数据
    data = request.json
    # print(data)
    try:
        keys = data.keys()
    except Exception as e:
        # status -1 json的key错误。此处id是因为没有进行读取，所以返回默认的-1。
        return json.dumps({"id": -1, "status": -1, "message": "Error JSON key", "data": {}})

    if "id" in data.keys():
        id = data["id"]
    else:
        id = -1

    # 判断指定所需字段是否存在，若不存在返回status -1 json。
    for key in ["type", "subtype", "data"]:
        if not key in data.keys():
            # status -1 json的key错误。
            return json.dumps({"id": id, "status": -1, "message": "Error JSON key", "data": {}})
    type = data["type"]
    subtype = data["subtype"]
    data = data["data"]
    # 处理json
    if type == "device":
        if subtype == "bind":
            for key in ["device_id"]:
                if key not in data.keys():
                    # status -3 data数据中必需key缺失
                    return json.dumps({"id": id, "status": -3, "message": "Error data key", "data": {}})
            device_id = data["device_id"]
            json_dict = MySQL.BindDevice(username=username, device_id=device_id, id=id)
            return json.dumps(json_dict)
        elif subtype == "add":
            for key in ["device"]:
                if key not in data.keys():
                    # status -3 json的value错误。
                    return json.dumps({"id": id, "status": -3, "message": "Error data key", "data": {}})
            device_name = data["device"]
            json_dict = MySQL.AddDevice(device=device_name,id=id)
            return json.dumps(json_dict)
        else:
            # status -2 json的value错误。
            return json.dumps({"id": id, "status": -2, "message": "Error JSON value", "data": {}})
    else:
        # status -2 json的value错误。
        return json.dumps({"id": id, "status": -2, "message": "Error JSON value", "data": {}})


# todo 增加获取设备列表api
# TODO 给增加通知api增加发送短信功能
@app.route("/notice", methods=["POST"])
def notice():
    try:
        token = request.args["token"]
        print("token:", token)
    except Exception as e:
        print("Missing necessary args")
        log_main.error("Missing necessary agrs")
        # status -100 缺少必要的参数
        return json.dumps({"id": -1, "status": -100, "message": "Missing necessary args", "data": {}})
    token_check_result, device_name = MySQL.DeviceDoki(token)
    if token_check_result == False:
        # status -101 token不正确
        return json.dumps({"id": -1, "status": -104, "message": "Error device_id token", "data": {}})
    # 验证身份完成，处理数据
    data = request.json
    # print(data)
    try:
        keys = data.keys()
    except Exception as e:
        # status -1 json的key错误。此处id是因为没有进行读取，所以返回默认的-1。
        return json.dumps({"id": -1, "status": -1, "message": "Error JSON key", "data": {}})

    if "id" in data.keys():
        id = data["id"]
    else:
        id = -1

    # 判断指定所需字段是否存在，若不存在返回status -1 json。
    for key in ["type", "subtype", "data"]:
        if not key in data.keys():
            # status -1 json的key错误。
            return json.dumps({"id": id, "status": -1, "message": "Error JSON key", "data": {}})
    type = data["type"]
    subtype = data["subtype"]
    data = data["data"]
    # 处理json
    if type == "notice":
        if subtype == "upload":
            for key in ["base64"]:
                if key not in data.keys():
                    # status -3 data数据中必需key缺失
                    return json.dumps({"id": id, "status": -3, "message": "Error data key", "data": {}})
            img_base64 = data["base64"]
            base64_head_index = img_base64.find(";base64,")
            if base64_head_index != -1:
                print("进行了替换")
                img_base64 = img_base64.partition(";base64,")[2]
            # print("-------接收到数据-------\n", img_base64, "\n-------数据结构尾-------")
            if "type" in data.keys():
                img_type = data["type"]
            img_file = base64.b64decode(img_base64)
            content = ""
            if "content" in data.keys():
                content = data["content"]
            pic_name = MD5.md5_bytes(img_file)
            try:
                COS.bytes_upload(img_file, "fallpic/{}".format(pic_name))
                print("Upload fallpic:{} for device:{}".format(pic_name, device_name))
                log_main.info("Upload fallpic:{} for device:{}".format(pic_name, device_name))
            except Exception as e:
                print("Failed to Upload fallpic:{} for device:{}".format(pic_name, device_name))
                print(e)
                log_main.error("Failed to Upload fallpic:{} for device:{}".format(pic_name, device_name))
                log_main.error(e)
                # status -500 COS upload Error
                return {"id": id, "status": -500, "message": "COS upload Error", "data": {}}
            json_dict = MySQL.AddFallPic(pic_name=pic_name, device_name=device_name, content=content, id=id)
            return json.dumps(json_dict)
        else:
            # status -2 json的value错误。
            return json.dumps({"id": id, "status": -2, "message": "Error JSON value", "data": {}})
    else:
        # status -2 json的value错误。
        return json.dumps({"id": id, "status": -2, "message": "Error JSON value", "data": {}})


@app.route("/get/notice", methods=["POST"])
def get_notice():
    try:
        token = request.args["token"]
        print("token:", token)
    except Exception as e:
        print("Missing necessary args")
        log_main.error("Missing necessary agrs")
        # status -100 缺少必要的参数
        return json.dumps({"id": -1, "status": -100, "message": "Missing necessary args", "data": {}})
    token_check_result, username = MySQL.Doki2(token)
    if token_check_result == False:
        # status -101 token不正确
        return json.dumps({"id": -1, "status": -101, "message": "Error token", "data": {}})
    # 验证身份完成，处理数据
    data = request.json
    # print(data)
    try:
        keys = data.keys()
    except Exception as e:
        # status -1 json的key错误。此处id是因为没有进行读取，所以返回默认的-1。
        return json.dumps({"id": -1, "status": -1, "message": "Error JSON key", "data": {}})

    if "id" in data.keys():
        id = data["id"]
    else:
        id = -1

    # 判断指定所需字段是否存在，若不存在返回status -1 json。
    for key in ["type", "subtype", "data"]:
        if not key in data.keys():
            # status -1 json的key错误。
            return json.dumps({"id": id, "status": -1, "message": "Error JSON key", "data": {}})
    type = data["type"]
    subtype = data["subtype"]
    data = data["data"]
    # 处理json
    if type == "notice":
        if subtype == "get":
            for key in ["mode"]:
                if key not in data.keys():
                    # status -3 data数据中必需key缺失
                    return json.dumps({"id": id, "status": -3, "message": "Error data key", "data": {}})
            mode = 0  # 0为未读，1为已读，2为全部
            if isinstance(data["mode"], int):
                mode = data["mode"]
            elif isinstance(data["mode"], str):
                if str(data["mode"]).isdecimal():
                    mode = int(data["mode"])
            json_dict = MySQL.GetNoticeList(username=username, mode=mode, id=id)
            return json.dumps(json_dict)
        elif subtype == "sign":
            for key in ["event_id"]:
                if key not in data.keys():
                    # status -3 data数据中必需key缺失
                    return json.dumps({"id": id, "status": -3, "message": "Error data key", "data": {}})
            event_id = data["event_id"]
            if not isinstance(event_id, str):
                # status -203 Arg's value type error
                return {"id": id, "status": -203, "message": "Arg's value type error", "data": {}}
            json_dict = MySQL.SignNotice(username=username, event_id=event_id, id=id)
            return json.dumps(json_dict)
        elif subtype == "info":
            for key in ["event_id"]:
                if key not in data.keys():
                    # status -3 data数据中必需key缺失
                    return json.dumps({"id": id, "status": -3, "message": "Error data key", "data": {}})
            event_id = data["event_id"]
            if not isinstance(event_id, str):
                # status -203 Arg's value type error
                return {"id": id, "status": -203, "message": "Arg's value type error", "data": {}}
            json_dict = MySQL.GetNoticeInfo(username=username,event_id=event_id,id=id)
            MySQL.SignNotice(username=username, event_id=event_id, id=id)
            return json.dumps(json_dict)
        else:
            # status -2 json的value错误。
            return json.dumps({"id": id, "status": -2, "message": "Error JSON value", "data": {}})
    else:
        # status -2 json的value错误。
        return json.dumps({"id": id, "status": -2, "message": "Error JSON value", "data": {}})


if __name__ == '__main__':
    Initialize(sys.argv[1:])
    # thread_token = MyThread(1, "AutoRemoveExpireToken", 1)
    # thread_token.start()
    thread_keep = MyThread(1, "AutoKeepConnect", 1)
    thread_keep.start()
    thread_hash = MyThread(1, "AutoRemoveExpireHash", 1)
    thread_hash.start()
    app.run(host=webhost, port=webport, debug=webdebug)
