# coding=utf-8
import requests,json
import base64
import MD5

headers = {'content-type': "application/json"}
# # 发送手机短信
# data={"id":0,"status":0,"type":"sms","subtype":"generate","data":{"phone":"13750687010"}}
# # response = requests.post(url="http://www.helpaged.cn/api/captcha",data=json.dumps(data),headers=headers)
# response = requests.post(url="http://localhost:8888/captcha",data=json.dumps(data),headers=headers)
# print(response.text)
# code = input("验证码：")
# rand = input("随机值：")
# md5 = MD5.md5(code,rand)
# print("md5:",md5)
# # 注册
# # md5 = "dbf1b8bee48178556a28c4fcb2921340"
# data={"id":0,"status":0,"type":"register","subtype":"phone","data":{"phone":"13750687010","hash":md5,"pass":"wlc570Q0"}}
# # response = requests.post(url="http://www.helpaged.cn/api/user/register",data=json.dumps(data),headers=headers)
# response = requests.post(url="http://localhost:8888/user/register",data=json.dumps(data),headers=headers)
# print(response.text)

# # 登录
# data={
#       "id":0,
#       "status":0,
#       "type":"login",
#       "subtype":"pass",
#       "data":{
#             "phone":"13750687010",
#             "pass":"wlc570Q0",
#             "enduring":False
#       }
# }
# response = requests.post(url="http://www.helpaged.cn/api/user/login",data=json.dumps(data),headers=headers)
# # response = requests.post(url="http://localhost:8888/user/login",data=json.dumps(data),headers=headers)
# # print(response.text)
token = "3f5bba4da0e98041cc6eea3845072712"

# # 添加设备
# data={"id":0,
#       "type":"device",
#       "subtype":"add",
#       "data":{"device":"camera1"}}
# # response = requests.post(url="http://www.helpaged.cn/api/device?token={}".format(token),data=json.dumps(data),headers=headers)
# response = requests.post(url="http://127.0.0.1:8888/device?token={}".format(token),data=json.dumps(data),headers=headers)

## 绑定设备
# data={"id":0,
#       "type":"device",
#       "subtype":"bind",
#       "data":{"device_id":"19ab376850337874ad19b2a958684bc4"}}
# # response = requests.post(url="http://www.helpaged.cn/api/device?token={}".format(token),data=json.dumps(data),headers=headers)
# response = requests.post(url="http://127.0.0.1:8888/device?token={}".format(token),data=json.dumps(data),headers=headers)

device_token = "19ab376850337874ad19b2a958684bc4"
## 上传摔倒图片
with open("./temp/temp.png","rb") as f:
      file_data = f.read()
# print(file_data)
img_base64 = str(base64.b64encode(file_data),"utf-8")
print("base64:\n{}".format(img_base64))
data={"id":0,
      "type":"notice",
      "subtype":"upload",
      "data":{"base64":"{}".format(img_base64),"device":"camera1","content":"测试自动获取"}}
response = requests.post(url="http://www.helpaged.cn/api/notice?token={}".format(device_token),data=json.dumps(data),headers=headers)
# response = requests.post(url="http://127.0.0.1:8888/notice?token={}".format(device_token),data=json.dumps(data),headers=headers)

# # 获取通知
# data={"id":0,
#       "type":"notice",
#       "subtype":"get",
#       "data":{"mode":0}}
# response = requests.post(url="http://www.helpaged.cn/api/get/notice?token={}".format(token),data=json.dumps(data),headers=headers)
# # response = requests.post(url="http://127.0.0.1:8888/get/notice?token={}".format(token),data=json.dumps(data),headers=headers)

# # 标记通知
# data={"id":0,
#       "type":"notice",
#       "subtype":"sign",
#       "data":{"event_id":"a994dc5453d127c9ea26f1a6b15b03c6"}}
# # response = requests.post(url="http://www.helpaged.cn/api/get/notice?token={}".format(token),data=json.dumps(data),headers=headers)
# response = requests.post(url="http://127.0.0.1:8888/get/notice?token={}".format(token),data=json.dumps(data),headers=headers)


print(response.text)


# print(response.text)
# data_json = response.json()
# data = data_json["data"]
# img_b64 = data["imgdata"]
# img_data = base64.b64decode(img_b64)
# with open("./captcha/[%s].png" % data["code"],"wb") as f:
#     f.write(img_data)
