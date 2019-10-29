# HelpAged-Python

[TOC]

## **Json请求通用格式**

```python
{
  "id":123456789,
  "type":"xxx",
  "subtype":"xxxx",
  "data":{
      "key":"value"
  }
}
```

## **Json返回通用格式**

```python
{
  "id":123456789,
  "status":0,
  "message":"successful",
  "data":{
      "key":"value"
  }
}
```



> **所需参数介绍：**

|  参数   |                             介绍                             |   调用方   |               样例               |
| :-----: | :----------------------------------------------------------: | :--------: | :------------------------------: |
|   id    |      事件处理id，整型，请求端发送，接收端返回时原样返回      | 请求、返回 |           "id":123456            |
| status  | 返回请求处理状态，请求时status填写0。默认返回0时为请求处理成功，若失败返回错误码 |    返回    |            "status":0            |
| message | 状态简略信息，若成功调用则返回"successful"，失败返回错误信息 |    返回    |      "message":"successful"      |
|  type   |                           请求类型                           |    请求    |          "type":"user"           |
| subtype |                          请求子类型                          |    请求    |        "subtype":"login"         |
|  data   |                   包含附加或返回的请求数据                   | 请求、返回 | "data":{"token":"xxxxxxxxxxxxx"} |

## **验证码类**

#### 登录图片验证码

> **API说明**

此API用于生成一个5位字母数字混合的图形验证码

成功则返回图片的base64数据和一个5位rand值。

> **API类型**

**请求类型：`POST`**

> **API地址：**

**http://www.helpaged.cn/api/captcha**

> **POST发送请求的json文本**

```python
{
    "id":事件ID, # 整数型
    "type":"img",
    "subtype":"generate",
    "data":{}
}
```

> **Python端返回成功处理情况**

```python
{
    "id":请求时的ID, # 整数型
    "status":0,
    "message":"successful",
    "data":{
        "imgdata":"iVBORw0yrfmx5m7975n32/23Y+cdf1Rv9oA6.....(以下省略)",
        "rand":"CST43"  #随机文本
    }
}
```

> ## 注意

- `id`字段需是整型数据。若是文本型数字数据，返回时自动转换成整数型数据；若是非数字型文本，则返回`-1`。`id`用于让前端在服务繁忙时能够对应服务;  
- Python成功返回时的`imgdata`为验证码base64图片数据，前端获得数据后进行转码再显示;  
- `rand`为随机字符串，前端获得验证码后需要将验证码和`rand`文本MD5加密后传给后端进行验证，`hash = MD5(code+rand)`。  
- 验证码**不区分大小写**，请自行将验证码转换成全部小写再进行hash操作。

> **Python端返回失败处理情况**

```python
{
  "id":"请求时的ID",
  "status":1000, # 错误码
  "message":"验证码文件创建失败",
  "data":{},
}
```

- `status`传递的错误码类型为整型。具体的错误码详见`全局status表`和`局部status表`。

> **所用到的全局status**

全局参数详情请看[全局Status表](#全局Status表)

| status |
| ------ |
| -3     |
| -2     |
| -1     |

#### 验证码校验

> **API说明**

此API用于校验用户输入的验证码是否正确，**在目前版本中，此API暂时用不到**

> **API类型**

**请求类型：`POST`**

> **API地址：**

**http://www.helpaged.cn/api/captcha**

> **POST发送请求的json文本**

```python
{
    "id":事件ID, # 整数型
    "type":"img" or "sms",
    "subtype":"validate",
    "data":{"hash":"asddwfw……"}
}
```

> **data字段表**

| 参数 | 可否为空 | 可否缺省 | 数据类型 | 字段长度 |               例子               |           备注            |
| :--: | :------: | :------: | :------: | :------: | :------------------------------: | :-----------------------: |
| hash |          |          |  string  |    32    | cffb7f1eb316fd45bbfbd43082e36f9c | hash = MD5(imgcode + rand |



> ## 注意

- `hash`字段的数据要求是用户填写的验证码内容与rand文本进行MD5加密获得。即`hash = MD5(code + rand)`
- 验证码**不区分大小写**，请自行将验证码转换成全部小写再进行hash操作。

> **Python端返回成功处理情况**

```python
{
    "id":请求时的ID, # 整数型
    "status":0,
    "message":"successful",
    "data":{}
}
```

> **Python端返回失败处理情况**

```python
{
  "id":请求时的ID,
  "status":-1, # 验证码hash值不匹配
  "message":"Error captcha hash",
  "data":{},
}
```

- `status`传递的错误码类型为整型。具体的错误码详见`全局status表`和`局部status表`。

> **所用到的全局status**

全局参数详情请看[全局Status表](#全局Status表)

| status |
| ------ |
| -404   |
| -3     |
| -2     |
| -1     |

> **局部status表**

| status | message            | 内容                                           |
| ------ | ------------------ | ---------------------------------------------- |
| 100    | Error captcha hash | 校验失败，验证码hash值不匹配（包括验证码过期） |

#### 手机短信验证码

> **API说明**

***最新修改：增加了command_type字段，可缺省，默认为1，用于判断短信信息种类***

此API用于以手机号作为账号进行注册时发送短信验证码

成功则向指定手机发送短信，并返回一个5位`rand`值，用于用户注册时

> **API类型**

**请求类型：`POST`**

> **API地址：**

**http://www.helpaged.cn/api/captcha**

> **POST发送请求的json文本**

```python
{
    "id":事件ID,
    "type":"sms",
    "subtype":"generate",
    "data":{
        "phone":"137xxxxxxxx",
        "command_type":1
        }
}
```

> **data字段表**

|     参数     | 可否为空 | 可否缺省 | 数据类型 | 字段长度 |               例子               |                         备注                          |
| :----------: | :------: | :------: | :------: | :------: | :------------------------------: | :---------------------------------------------------: |
|    phone     |          |          |  string  |    11    |           13750687010            |                  中国大陆11位手机号                   |
| command_type |          |    √     |   int    |          |                1                 |               1为注册账号，2为找回密码                |
|     hash     |          |    √     |  string  |    32    | cffb7f1eb316fd45bbfbd43082e36f9c | **该字段目前不使用**<br />`hash = MD5(imgcode + rand` |

> ## 注意

- `phone`字段需用文本型传递，且只能为中国大陆手机号，不支持国外手机号
- `hash`字段的数据要求是用户填写的验证码内容与rand文本进行MD5加密获得。即`hash = MD5(code + rand)`

> **Python端返回成功处理情况**

```python
{
   "id":请求时的ID,
   "status":0,
   "message":"successful",
   "data":{
       "rand":"DSf4s"
   }
}
```

> ## 注意：

- 新版本里将返回数据`data`中的`code`字段删除了。   
- `rand`为随机字符串，前端获得验证码后需要将验证码和rand文本进行MD5加密后传给后端端进行验证，`hash = MD5(code+rand)`，此hash用于账号注册。
- **手机验证码的时效为3min，由后端处理。验证码超时后端会返回`status = -4`的错误。**

> **Python端返回失败处理情况**

```python
{
     "id":请求时的ID,
     "status":1016,  #错误码
     "message":"手机号格式错误",
     "data":{},
}
```

> **所用到的全局status**

全局参数详情请看[全局Status表](#全局Status表)

| status |
| ------ |
| -404   |
| -3     |
| -2     |
| -1     |

> **局部status表**

| status                                                       |
| ------------------------------------------------------------ |
| 具体错误码请看腾讯云[短信错误码](http://cloud.tencent.com/document/product/382/3771 "腾讯短信API文档") |

> ## 注意

- `status`传递的错误码类型为整型。具体的错误码参照**腾讯云短信服务API文档**。
  [短信错误码](http://cloud.tencent.com/document/product/382/3771 "腾讯短信API文档")

## 用户类

#### 账号登录·手机

> **API说明**

此API用于以手机号作为登录凭证时的登录请求

成功返回token值

> **API类型**

**请求类型：`POST`**

> **API地址：**

**http://www.helpaged.cn/api/user/login**

> **POST发送请求的json文本**

```python
{
    "id":1234,
    "type":"login",
    "subtype":"pass",
    "data":{
        "phone":"13750687010",
        "pass":"wlc570Q0",
        "enduring":False,
    }
}
```

> **data字段表**

|   参数   | 可否为空 | 可否缺省 | 数据类型 |  字段长度  |    例子     |                             备注                             |
| :------: | :------: | :------: | :------: | :--------: | :---------: | :----------------------------------------------------------: |
|  phone   |          |          |  string  |     11     | 13750687010 |                       登录账号(手机号)                       |
|   pass   |          |          |  string  | 由前端决定 |  wlc570Q0   |                           登录密码                           |
| enduring |          |    √     |   int    |     1      |    False    | 是否为长效登录，1为长效，0为非长效（无操作10min）<br />**默认为0** |

> ## 注意

- `phone`字段需用文本型传递
- `pass`字段的长度由前端限制，后端只取其MD5值进行判断

> **Python端返回成功处理情况**

```python
{
    "id": 1234,
    "status": 0, 
    "message": "Successful", 
    "data": {
        "token": "debc454ea24827b67178482fd73f37c3"
    }
}
```

> ## 注意：

- 获取的`token`用于后期所有需要用户验证的请求操作。  
- 账号每登录一次即可获得一个`token`
- 一个账号同时获得10个以上的`token`时，自动删除早期的`token`，维持token数在10以内
- 获得的`token`未被用于任何操作超过`10min`后将被自动删除（设置为长效token的除外）
- 若`enduring`传递了非`int`类型数据，则自动为`0`

> **Python端返回失败处理情况**

```python
{
     "id":1234,
     "status":101,  #错误码
     "message":"Error password",
     "data":{},
}
```

> **所用到的全局status**

全局参数详情请看[全局Status表](#全局Status表)

| status |
| ------ |
| -200   |
| -3     |
| -2     |
| -1     |

> **局部status表**

| status | message               | 内容                     |
| ------ | --------------------- | ------------------------ |
| 100    | Incorrect user        | 无该账号记录             |
| 101    | Error password        | 用户输入的密码错误       |
| 200    | Invalid record number | 有两条及以上该账号的数据 |
| 300    | Add token failed      | 获取token失败            |

#### 账号注册·手机

> **API说明**

此API用于以手机号作为登录凭证时的注册请求

成功返回token值

> **API类型**

**请求类型：`POST`**

> **API地址：**

**http://www.helpaged.cn/api/user/register**

> **POST发送请求的json文本**

```python
{
    "id":0,
    "status":0,
    "type":"register",
    "subtype":"phone",
    "data":{
        "phone":"13750687010",
        "hash":"cffb7f1eb316fd45bbfbd43082e36f9c",
        "pass":"wlc570Q0"
    }
}
```

> **data字段表**

| 参数  | 可否为空 | 可否缺省 | 数据类型 |  字段长度  |               例子               |                             备注                             |
| :---: | :------: | :------: | :------: | :--------: | :------------------------------: | :----------------------------------------------------------: |
| phone |          |          |  string  |     11     |           13750687010            |                       登录账号(手机号)                       |
| hash  |          |          |  string  |     32     | cffb7f1eb316fd45bbfbd43082e36f9c | 此hash由手机验证码的code与rand进行MD5加密获得<br />`hash=MD5(smscode+rand)` |
| pass  |          |          |  string  | 由前端决定 |             wlc570Q0             |                           登录密码                           |

> ## 注意

- `phone`字段需用文本型传递
- `pass`字段的长度由前端限制，后端只取其MD5值进行判断

> **Python端返回成功处理情况**

```python
{
    "id": 1234, 
    "status": 0, 
    "message": "Successful", 
    "data": {}
}
```

> **Python端返回失败处理情况**

```python
{
     "id":1234,
     "status":101,  #错误码
     "message":"Phone number existed",
     "data":{},
}
```

> **所用到的全局status**

全局参数详情请看[全局Status表](#全局Status表)

| status |
| ------ |
| -200   |
| -3     |
| -2     |
| -1     |

> **局部status表**

| status | message                    | 内容                     |
| ------ | -------------------------- | ------------------------ |
| 100    | Incorrect user data        | 创建账号失败             |
| 101    | Phone number existed       | 手机号已存在             |
| 102    | Incorrect user information | 创建用户资料失败         |
| 200    | Invalid record number      | 有两条及以上该账号的数据 |
| 400    | Error hash                 | Hash校验文本错误         |



#### 密码找回·手机

> **API说明**

此API用于找回以手机号作为登录凭证时的密码找回

> **API类型**

**请求类型：`POST`**

> **API地址：**

**http://www.helpaged.cn/api/user/password**

> **POST发送请求的json文本**

```python
{
    "id":0,
    "status":0,
    "type":"password",
    "subtype":"forget",
    "data":{
        "phone":"13750687010",
        "hash":"cffb7f1eb316fd45bbfbd43082e36f9c",
        "pass":"wlc570Q0"
    }
}
```

> **data字段表**

| 参数  | 可否为空 | 可否缺省 | 数据类型 |  字段长度  |               例子               |                             备注                             |
| :---: | :------: | :------: | :------: | :--------: | :------------------------------: | :----------------------------------------------------------: |
| phone |          |          |  string  |     11     |           13750687010            |                       登录账号(手机号)                       |
| hash  |          |          |  string  |     32     | cffb7f1eb316fd45bbfbd43082e36f9c | 此hash由手机验证码的code与rand进行MD5加密获得<br />`hash=MD5(smscode+rand)` |
| pass  |          |          |  string  | 由前端决定 |             wlc570Q0             |                           登录密码                           |

> ## 注意

- 使用api前，需要先调用一次短信验证码发送请求，且短信请求中command_type为2
- `phone`字段需用文本型传递
- `pass`字段的长度由前端限制，后端只取其MD5值进行判断

> **Python端返回成功处理情况**

```python
{
    "id": 1234, 
    "status": 0, 
    "message": "Successful", 
    "data": {}
}
```

> **Python端返回失败处理情况**

```python
{
     "id":1234,
     "status":101,  #错误码
     "message":"Phone number existed",
     "data":{},
}
```

> **所用到的全局status**

全局参数详情请看[全局Status表](#全局Status表)

| status |
| ------ |
| -200   |
| -3     |
| -2     |
| -1     |

> **局部status表**

| status | message    | 内容             |
| ------ | ---------- | ---------------- |
| 400    | Error hash | Hash校验文本错误 |

#### 密码修改·手机

> **API说明**

此API用于找回以手机号作为登录凭证时的密码修改

> **API类型**

**请求类型：`POST`**

> **API地址：**

**http://www.helpaged.cn/api/user/password**

> **POST发送请求的json文本**

```python
{
    "id":0,
    "status":0,
    "type":"password",
    "subtype":"change",
    "data":{
        "phone":"13750687010",
        "old":"wlc570Q0",
        "new":"abc123"
    }
}
```

> **data字段表**

| 参数  | 可否为空 | 可否缺省 | 数据类型 |  字段长度  |               例子               |       备注       |
| :---: | :------: | :------: | :------: | :--------: | :------------------------------: | :--------------: |
| phone |          |          |  string  |     11     |           13750687010            | 登录账号(手机号) |
|  old  |          |          |  string  | 由前端决定 | cffb7f1eb316fd45bbfbd43082e36f9c |      老密码      |
|  new  |          |          |  string  | 由前端决定 |              abc123              |      新密码      |

> ## 注意

- `phone`字段需用文本型传递
- `old`、`new`字段的长度由前端限制，后端只取其MD5值进行判断

> **Python端返回成功处理情况**

```python
{
    "id": 1234, 
    "status": 0, 
    "message": "Successful", 
    "data": {}
}
```

> **Python端返回失败处理情况**

```python
{
     "id":1234,
     "status":101,  #错误码
     "message":"Phone number existed",
     "data":{},
}
```

> **所用到的全局status**

全局参数详情请看[全局Status表](#全局Status表)

| status |
| ------ |
| -200   |
| -3     |
| -2     |
| -1     |

> **局部status表**

| status | message               | 内容                     |
| ------ | --------------------- | ------------------------ |
| 100    | Incorrect user        | 无该账号记录             |
| 101    | Error password        | 用户输入的密码错误       |
| 200    | Invalid record number | 有两条及以上该账号的数据 |
| 300    | Add token failed      | 获取token失败            |

#### 用户昵称·获取

> **API说明**

此API用于通过phone值获取对应用户信息

> **API类型**

**请求类型：`POST`**

> **API地址：**

**http://www.helpaged.cn/api/user/nickname?token=**

> **url 参数表**

| 参数  | 可否为空 | 可否缺省 | 数据类型 | 字段长度 |               例子               |       备注        |
| :---: | :------: | :------: | :------: | :------: | :------------------------------: | :---------------: |
| token |          |          |  string  |    32    | debc454ea24827b67178482fd73f37c3 | 由登录api返回获得 |

> **POST发送请求的json文本**

```python
{
    "id":0,
    "type":"info",
    "subtype":"nickname",
    "data":{
        "user_id":"13750687010"
    }
}
```

> **data字段表**

| 参数  | 可否为空 | 可否缺省 | 数据类型 | 字段长度 |    例子     |       备注       |
| :---: | :------: | :------: | :------: | :------: | :---------: | :--------------: |
| phone |          |          |  string  |    11    | 13750687010 | 登录账号(手机号) |

> **Python端返回成功处理情况**

```python
{
    "id": -1, 
    "status": 0, 
    "message": "Successful", 
    "data": { 
        "nickname": "FatBallFish"
    }
}
```

> **Python端返回失败处理情况**

```python
{
    "id": -1, 
    "status": 1, 
    "message": "Error Token", 
    "data": {}
}
```

> **所用到的全局status**

全局参数详情请看[全局Status表](#全局Status表)

| status |
| ------ |
| -200   |
| -100   |
| -3     |
| -2     |
| -1     |

> **局部status表**

| status | message                 | 内容             |
| :----- | ----------------------- | ---------------- |
| 100    | user not existed        | 账号不存在       |
| 200    | Unkonwn user info Error | 同一phone大于2条 |

#### 用户信息·获取

> **API说明**

此API用于通过token值获取对应用户信息

> **API类型**

**请求类型：`GET`**

> **API地址：**

**http://www.helpaged.cn/api/user/info?token=**

> **url 参数表**

| 参数  | 可否为空 | 可否缺省 | 数据类型 | 字段长度 |               例子               |       备注        |
| :---: | :------: | :------: | :------: | :------: | :------------------------------: | :---------------: |
| token |          |          |  string  |    32    | debc454ea24827b67178482fd73f37c3 | 由登录api返回获得 |

> **Python端返回成功处理情况**

```python
{
    "id": -1, 
    "status": 0, 
    "message": "Successful", 
    "data": {
        "phone": "13750687010", 
        "name": "\u738b\u51cc\u8d85", 
        "nickname": "FatBallFish", 
        "email": "893721708@qq.com", 
        "level": 1
    }
}
```

> **Python端返回失败处理情况**

```python
{
    "id": -1, 
    "status": 1, 
    "message": "Error Token", 
    "data": {}
}
```

> **所用到的全局status**

全局参数详情请看[全局Status表](#全局Status表)

| status |
| ------ |
| -200   |
| -100   |

> **局部status表**

| status | message     | 内容        |
| :----- | ----------- | ----------- |
| 1      | Error Token | token不正确 |

#### 用户信息·更新

> **API说明**

此API用于更新用户信息

> **API类型**

**请求类型：`POST`**

> **API地址：**

**http://www.helpaged.cn/api/user/info?token=**

> **url 参数表**

| 参数  | 可否为空 | 可否缺省 | 数据类型 | 字段长度 |               例子               |       备注        |
| :---: | :------: | :------: | :------: | :------: | :------------------------------: | :---------------: |
| token |          |          |  string  |    32    | debc454ea24827b67178482fd73f37c3 | 由登录api返回获得 |

> **POST发送请求的json文本**

```python
{
    "id":0,
    "type":"info",
    "subtype":"update",
    "data":{
        "phone":"13750687010",
        "name":"王凌超",
        "nickname":"FatBallFish",
        "email":"893721708@qq.com"}
}
```

> **data字段表**

|   参数   | 可否为空 | 可否缺省 | 数据类型 | 字段长度 |               例子               |       备注       |
| :------: | :------: | :------: | :------: | :------: | :------------------------------: | :--------------: |
|  phone   |          |          |  string  |    11    |           13750687010            | 登录账号(手机号) |
|   name   |    √     |    √     |  string  |    20    | cffb7f1eb316fd45bbfbd43082e36f9c |                  |
| nickname |    √     |    √     |  string  |    20    |             wlc570Q0             |     登录密码     |
|  email   |    √     |    √     |  string  |    50    |         893721708@qq.com         |     邮箱地址     |
|  level   |          |    √     |   int    |          |                1                 |     用户等级     |

> ## 注意

- `phone`用作检验机制，不可被修改
- `level`字段若被使用则必须传递数值，不能为空

> **Python端返回成功处理情况**

```python
{
    "id": 1234, 
    "status": 0, 
    "message": "Successful", 
    "data": {}
}
```

> **Python端返回失败处理情况**

```python
{
     "id":1234,
     "status":101,  #错误码
     "message":"Phone number existed",
     "data":{},
}
```

> **所用到的全局status**

全局参数详情请看[全局Status表](#全局Status表)

| status |
| ------ |
| -200   |
| -101   |
| -100   |
| -3     |
| -2     |
| -1     |

#### 用户头像·上传

> **API说明**

此API用于上传用户的头像图片

成功返回头像的url地址

> **API类型**

**请求类型：`POST`**

> **API地址：**

**http://www.helpaged.cn/api/portrait?token=**

> **url 参数表**

| 参数  | 可否为空 | 可否缺省 | 数据类型 | 字段长度 |               例子               |       备注        |
| :---: | :------: | :------: | :------: | :------: | :------------------------------: | :---------------: |
| token |          |          |  string  |    32    | debc454ea24827b67178482fd73f37c3 | 由登录api返回获得 |

> **POST发送请求的json文本**

```python
{
    "id":1234,
    "type":"portrait",
    "subtype":"upload",
    "data":{
        "base64":img_base64  # string型
    }
}
```

> **data字段表**

|  参数  | 可否为空 | 可否缺省 | 数据类型 | 字段长度 |                   例子                    |                             备注                             |
| :----: | :------: | :------: | :------: | :------: | :---------------------------------------: | :----------------------------------------------------------: |
| base64 |          |          |  string  |          | /9j/4AAQSkZJRgABAQEA.......(长度过长省略) | 图片的base64格式文本，前端尽量限制图片大小在1M以下，否则容易卡顿，3M以上请求容易失败 |

> ## 注意

- `base64`可选择是否带有base头标识，实际不影响。标识例子：`data:image/jpg;base64,`
- 若该用户原先已有头像，新头像将自动覆盖原有头像，原头像被删除。

> **Python端返回成功处理情况**

```python
{
    "id": 1234, 
    "status": 0,
    "message": "Successful", 
    "data": {
        "url": "./api/get/portrait/13750687010"
    }
}
```

> **Python端返回失败处理情况**

```python
{
     "id":1234,
     "status":-100,  #错误码
     "message":"Missing necessary args",
     "data":{},
}
```

> **所用到的全局status**

全局参数详情请看[全局Status表](#全局Status表)

| status |
| ------ |
| -101   |
| -100   |
| -3     |
| -2     |
| -1     |

#### 用户头像·获取

> **API说明**

此API用于通过token值获取对应用户信息

> **API类型**

**请求类型：`GET`**

> **API地址：**

**http://www.helpaged.cn/api/get/portrait/<user_id>**

> **url 参数表**

|  参数   | 可否为空 | 可否缺省 | 数据类型 | 字段长度 |    例子     |  备注  |
| :-----: | :------: | :------: | :------: | :------: | :---------: | :----: |
| user_id |          |          |  string  |    11    | 13750687010 | 用户id |

> **API例子**

**http://www.helpaged.cn/api/get/portrait/13750687010**

> **Python端返回成功处理情况**

```python
二进制型图片数据（bytes）
```

> ## 注意

+ 前端调用此api时，直接将api地址写在`src`中即可，例如：<br>`<img src="http://www.helpaged.cn/get/portrait/1180310086">`

> **Python端返回失败处理情况**

```python
视情况返回以下三种图片：
1.在服务器域名外访问此api，返回“ban.jpg”，提示“多媒体站内图片，禁止外部引用”
2.输入的user_id不存在但格式正确返回“default.jpg”，即默认头像
3.输入的user_id格式出错（出现非数字字符），返回“error.jpg”，提示“参数传递错误，无法获取图片”
```

> ## 注意

- 调用此api时，请注意当前api所在地址，若非`http://www.helpaged.cn`或`http://localhost`这两个根域名的话，将会返回`ban.jpg`

> **所用到的全局status**

无

## **Token类**

#### 心跳doki

> **API说明**

此API用于检验token是否有效，若有效并刷新token有效时间。

> **API类型**

**请求类型：`GET`**

> **API地址：**

**http://www.helpaged.cn/api/user/doki?token=**

> **url 参数表**

| 参数  | 可否为空 | 可否缺省 | 数据类型 | 字段长度 |               例子               |       备注        |
| :---: | :------: | :------: | :------: | :------: | :------------------------------: | :---------------: |
| token |          |          |  string  |    32    | debc454ea24827b67178482fd73f37c3 | 由登录api返回获得 |

> **Python端返回成功处理情况**

```python
{
    "id": id, 
    "status": 0, 
    "message": "Successful", 
    "data": {}
}
```

> **Python端返回失败处理情况**

```python
{
    "id": -1, 
    "status": 1,
    "message": "Token not existed", 
    "data": {}
}
```

> **所用到的全局status**

全局参数详情请看[全局Status表](#全局Status表)

| status |
| ------ |
| -200   |
| -100   |

> **局部status表**

| status | message              | 内容             |
| :----- | -------------------- | ---------------- |
| 1      | Token not existed    | Token不存在      |
| 200    | Invalid token number | 同一Token大于2条 |



## **设备类**

#### 设备类·添加设备

> **API说明**

此API用于添加一台设备。

> **API类型**

**请求类型：`POST`**

> **API地址：**

**http://www.helpaged.cn/api/device?token=**

> **url 参数表**

| 参数  | 可否为空 | 可否缺省 | 数据类型 | 字段长度 |               例子               |       备注        |
| :---: | :------: | :------: | :------: | :------: | :------------------------------: | :---------------: |
| token |          |          |  string  |    32    | debc454ea24827b67178482fd73f37c3 | 由登录api返回获得 |

> **POST发送请求的json文本**

```python
{
    "id":0,
    "type":"device",
    "subtype":"add",
    "data":
    {
        "device":"camera1"
    }
}
```

> **data字段表**

|  参数  | 可否为空 | 可否缺省 | 数据类型 | 字段长度 |  例子   |   备注   |
| :----: | :------: | :------: | :------: | :------: | :-----: | :------: |
| device |          |          |   str    |          | camera1 | 设备名称 |

> ## 注意



> **Python端返回成功处理情况**

```python
{
    "id": 0, 
    "status": 0, 
    "message": "successful", 
    "data": {}


```

> **Python端返回失败处理情况**

```python
{
    "id": -1, 
    "status": 1,
    "message": "Token not existed", 
    "data": {}
}
```

> **所用到的全局status**

全局参数详情请看[全局Status表](#全局Status表)

| status |
| ------ |
| -203   |
| -200   |
| -101   |
| -100   |
| -3     |
| -2     |
| -1     |

> **局部status表**

| status | message              | 内容           |
| ------ | -------------------- | -------------- |
| 100    | Failed to add device | 添加设备失败   |
| 101    | Duplicate device     | 重复的设备名称 |

#### 设备类·绑定设备

> **API说明**

此API用于添加一台设备。

**请求类型：`POST`**

> **API地址：**

**http://www.helpaged.cn/api/device?token=**

> **url 参数表**

| 参数  | 可否为空 | 可否缺省 | 数据类型 | 字段长度 |               例子               |       备注        |
| :---: | :------: | :------: | :------: | :------: | :------------------------------: | :---------------: |
| token |          |          |  string  |    32    | debc454ea24827b67178482fd73f37c3 | 由登录api返回获得 |

> **POST发送请求的json文本**

```python
{
    "id":0,
    "type":"device",
    "subtype":"bind",
    "data":
    {
        "device_id":"19ab376850337874ad19b2a958684bc4"
    }
}
```

> **data字段表**

|   参数    | 可否为空 | 可否缺省 | 数据类型 | 字段长度 |               例子               |     备注     |
| :-------: | :------: | :------: | :------: | :------: | :------------------------------: | :----------: |
| device_id |          |          |   str    |    32    | 19ab376850337874ad19b2a958684bc4 | 设备id token |

> ## 注意



> **Python端返回成功处理情况**

```python
{
    "id": 0, 
    "status": 0, 
    "message": "successful", 
    "data": {}


```

> **Python端返回失败处理情况**

```python
{
    "id": -1, 
    "status": 1,
    "message": "Token not existed", 
    "data": {}
}
```

> **所用到的全局status**

全局参数详情请看[全局Status表](#全局Status表)

| status |
| ------ |
| -203   |
| -200   |
| -101   |
| -100   |
| -3     |
| -2     |
| -1     |

> **局部status表**

| status | message             | 内容         |
| ------ | ------------------- | ------------ |
| 100    | device_id not exist | 设备id不存在 |

## **摔倒通知类**

#### 摔倒通知·添加

> **API说明**

此API用于新建一个摔倒通知，成功返回`pic_name`。

> **API类型**

**请求类型：`POST`**

> **API地址：**

**http://www.helpaged.cn/api/notice?token=**

> **url 参数表**

| 参数  | 可否为空 | 可否缺省 | 数据类型 | 字段长度 |               例子               |     备注     |
| :---: | :------: | :------: | :------: | :------: | :------------------------------: | :----------: |
| token |          |          |  string  |    32    | 19ab376850337874ad19b2a958684bc4 | 设备id token |

> ## 注意

**这里的token为设备id token**

> **POST发送请求的json文本**

```python
{
    "id":1234,
    "type":"notice",
    "subtype":"upload",
    "data":{
        "base64":img_base64,  # string型
        "content":"这个可以选填"
    }
}
```

> **data字段表**

|  参数   | 可否为空 | 可否缺省 | 数据类型 | 字段长度 |                       例子                        |                             备注                             |
| :-----: | :------: | :------: | :------: | :------: | :-----------------------------------------------: | :----------------------------------------------------------: |
| base64  |          |          |  string  |          |     /9j/4AAQSkZJRgABAQEA.......(长度过长省略)     | 图片的base64格式文本，前端尽量限制图片大小在1M以下，否则容易卡顿，3M以上请求容易失败 |
| content |    √     |    √     |  string  |   255    | 摔倒时间：2019年9月25日12:30:19<br>摔倒地点：卧室 |             照片描述信息，备用字段，方便后期拓展             |

> ## 注意

- `base64`可选择是否带有base头标识，实际不影响。标识例子：`data:image/jpg;base64,`
- 原`device`字段已删除，改为后端自动识别。

> **Python端返回成功处理情况**

```python
{
    "id": id, 
    "status": 0, 
    "message": "Successful", 
    "data": {
        "pic_name": "31af7195a1c22019516ab29b1d69e323"
    }
}
```

> **Python端返回失败处理情况**

```python
{
    "id": -1, 
    "status": 1,
    "message": "Token not existed", 
    "data": {}
}
```

> **所用到的全局status**

全局参数详情请看[全局Status表](#全局Status表)

| status |
| ------ |
| -500   |
| -200   |
| -104   |
| -101   |
| -100   |
| -3     |
| -2     |
| -1     |

#### 摔倒通知·获取列表

> **API说明**

此API用于获取摔倒通知，成功返回通知列表。

> **API类型**

**请求类型：`POST`**

> **API地址：**

**http://www.helpaged.cn/api/get/notice?token=**

> **url 参数表**

| 参数  | 可否为空 | 可否缺省 | 数据类型 | 字段长度 |               例子               |       备注        |
| :---: | :------: | :------: | :------: | :------: | :------------------------------: | :---------------: |
| token |          |          |  string  |    32    | debc454ea24827b67178482fd73f37c3 | 由登录api返回获得 |

> **POST发送请求的json文本**

```python
{
    "id":0,
    "type":"notice",
    "subtype":"get",
    "data":
    {
        "mode":0
    }
}
```

> **data字段表**

| 参数 | 可否为空 | 可否缺省 | 数据类型 | 字段长度 | 例子 |                       备注                        |
| :--: | :------: | :------: | :------: | :------: | :--: | :-----------------------------------------------: |
| mode |          |          |   int    |          |  0   | 0为返回未读通知，1为返回已读通知，2为返回全部通知 |

> ## 注意



> **Python端返回成功处理情况**

```python
{
    "id": 0, 
    "status": 0, 
    "message": "successful", 
    "data": {
        "num": 2, 
        "list": [
            {
                "event_id": "00d176d2fb76fbdb6b930ccdc3c46a3a", 
                "content": "", 
                "device": "camera1", 
                "pic_name": "31af7195a1c22019516ab29b1d69e323",  
                "createtime": "2019-10-01 20:30:36"
            }, 
            {
                "event_id": "17ccca31328d737fdac72066475529bb", 
                "content": "\u8fd9\u4e2a\u53ef\u4ee5\u9009\u586b", 
                "device": "camera1", 
                "pic_name": "3ea2457c6c698cc19e7ee426038566a0", 
                "createtime": "2019-09-26 19:55:30"
            }
        ]
    }
}


```

> **Python端返回失败处理情况**

```python
{
    "id": -1, 
    "status": 1,
    "message": "Token not existed", 
    "data": {}
}
```

> **所用到的全局status**

全局参数详情请看[全局Status表](#全局Status表)

| status |
| ------ |
| -200   |
| -101   |
| -100   |
| -3     |
| -2     |
| -1     |

> **局部status表**

| status | message           | 内容             |
| ------ | ----------------- | ---------------- |
| 100    | user_id not exist | 账号不存在       |
| 101    | not bind device   | 该账号未绑定账号 |
| 102    | mode value error  | mode值类型错误   |

#### 摔倒通知·获取信息

> **API说明**

此API用于获取摔倒通知，成功返回通知信息。

> **API类型**

**请求类型：`POST`**

> **API地址：**

**http://www.helpaged.cn/api/get/notice?token=**

> **url 参数表**

| 参数  | 可否为空 | 可否缺省 | 数据类型 | 字段长度 |               例子               |       备注        |
| :---: | :------: | :------: | :------: | :------: | :------------------------------: | :---------------: |
| token |          |          |  string  |    32    | debc454ea24827b67178482fd73f37c3 | 由登录api返回获得 |

> **POST发送请求的json文本**

```python
{
    "id":0,
    "type":"notice",
    "subtype":"info",
    "data":
    {
        "event_id":"0776a9f8da57d91ffae9616d65243af9"
    }
}
```

> **data字段表**

|   参数   | 可否为空 | 可否缺省 | 数据类型 | 字段长度 |               例子               |  备注  |
| :------: | :------: | :------: | :------: | :------: | :------------------------------: | :----: |
| event_id |          |          |   str    |    32    | 00d176d2fb76fbdb6b930ccdc3c46a3a | 活动id |

> ## 注意



> **Python端返回成功处理情况**

```python
{
    "id": 0, 
    "status": 0, 
    "message": "successful", 
    "data": {
        "event_id": "00d176d2fb76fbdb6b930ccdc3c46a3a", 
        "content": "", 
        "device": "camera1", 
        "pic_name": "31af7195a1c22019516ab29b1d69e323", 
        "base64": "/9j/4AAQSkZJRgABAQEAAQABAAD/2wBDAAYEBQYFBAYGBQYH....", 
        "createtime": "2019-10-01 20:30:36"
    }
}


```

> **Python端返回失败处理情况**

```python
{
    "id": -1, 
    "status": 1,
    "message": "Token not existed", 
    "data": {}
}
```

> **所用到的全局status**

全局参数详情请看[全局Status表](#全局Status表)

| status |
| ------ |
| -200   |
| -101   |
| -100   |
| -3     |
| -2     |
| -1     |

> **局部status表**

| status | message           | 内容             |
| ------ | ----------------- | ---------------- |
| 100    | user_id not exist | 账号不存在       |
| 101    | not bind device   | 该账号未绑定账号 |
| 102    | mode value error  | mode值类型错误   |

#### 摔倒通知·标记已读

> **API说明**

此API用于标记一条摔倒通知，使其变为已读状态。

> **API类型**

**请求类型：`POST`**

> **API地址：**

**http://www.helpaged.cn/api/get/notice?token=**

> **url 参数表**

| 参数  | 可否为空 | 可否缺省 | 数据类型 | 字段长度 |               例子               |       备注        |
| :---: | :------: | :------: | :------: | :------: | :------------------------------: | :---------------: |
| token |          |          |  string  |    32    | debc454ea24827b67178482fd73f37c3 | 由登录api返回获得 |

> **POST发送请求的json文本**

```python
{
    "id":0,
    "type":"notice",
    "subtype":"sign",
    "data":
    {
        "event_id":"00d176d2fb76fbdb6b930ccdc3c46a3a"
    }
}
```

> **data字段表**

|   参数   | 可否为空 | 可否缺省 | 数据类型 | 字段长度 |               例子               |    备注    |
| :------: | :------: | :------: | :------: | :------: | :------------------------------: | :--------: |
| event_id |          |          |   str    |    32    | 00d176d2fb76fbdb6b930ccdc3c46a3a | 通知事件id |

> ## 注意



> **Python端返回成功处理情况**

```python
{
    "id": 0, 
    "status": 0, 
    "message": "successful", 
    "data": {}


```

> **Python端返回失败处理情况**

```python
{
    "id": -1, 
    "status": 1,
    "message": "Token not existed", 
    "data": {}
}
```

> **所用到的全局status**

全局参数详情请看[全局Status表](#全局Status表)

| status |
| ------ |
| -203   |
| -200   |
| -101   |
| -100   |
| -3     |
| -2     |
| -1     |

> **局部status表**

| status | message                  | 内容                 |
| ------ | ------------------------ | -------------------- |
| 100    | Error event_id           | 错误的event_id       |
| 101    | event_id has been signed | 该通知已被标记为已读 |
| 102    | add notice sign error    | 添加已读标记失败     |

## **管理员类**

### admin-用户类

#### admin-用户列表·获取

> **API说明**

此API获取所有用户列表，仅管理员权限用户可用

> **API类型**

**请求类型：`POST`**

> **API地址：**

**http://www.helpaged.cn/api/admin/user?token=**

> **url 参数表**

| 参数  | 可否为空 | 可否缺省 | 数据类型 | 字段长度 |               例子               |              备注              |
| :---: | :------: | :------: | :------: | :------: | :------------------------------: | :----------------------------: |
| token |          |          |  string  |    32    | debc454ea24827b67178482fd73f37c3 | 由登录api返回获得，管理员token |

> **POST发送请求的json文本**

```python
{
    "id":1234,
    "type":"user",
    "subtype":"list",
    "data":{}
}
```

> **Python端返回成功处理情况**

```python
{
    "id": 0, 
    "status": 0, 
    "message": "successful", 
    "data": [
        {
            "phone": "13566284913", 
            "name": "\u8bb8\u6df3\u7693", 
            "nickname": "\u8bb8\u5927\u5e05\u54e5", 
            "email": "1010549831@qq.com", 
            "level": 1}, 
        {
            "phone": "13750687010", 
            "name": "\u738b\u51cc\u8d85", 
            "nickname": "FatBallFish", 
            "email": "893721708@qq.com", 
            "level": 1}, 
        {
            "phone": "15857174214", 
            "name": null, 
            "nickname": null, 
            "email": null, 
            "level": 1}, 
        {
            "phone": "15925868186", 
            "name": null, 
            "nickname": null, 
            "email": null, 
            "level": 1}, 
        {
            "phone": "17767174231", 
            "name": null, 
            "nickname": null, 
            "email": null, 
            "level": 1}, 
        {
            "phone": "17816064319", 
            "name": "\u94b1\u4e39", 
            "nickname": "\u86cb\u86cb", 
            "email": "3391791582@qq.com", 
            "level": 1}, 
        {
            "phone": "19857160634", 
            "name": null, 
            "nickname": null,
            "email": null, 
            "level": 1}
    ]
}

```

> **Python端返回失败处理情况**

```python
{
     "id":1234,
     "status":-103,  #错误码
     "message":"No permission to operate",
     "data":{},
}
```

> **所用到的全局status**

全局参数详情请看[全局Status表](#全局Status表)

| status |
| ------ |
| -200   |
| -103   |
| -101   |
| -100   |
| -3     |
| -2     |
| -1     |

#### admin-用户信息·获取

> **API说明**

此API用于通过user_id值获取对应用户信息，仅管理员权限用户可用

> **API类型**

**请求类型：`POST`**

> **API地址：**

**http://www.helpaged.cn/api/admin/user?token=**

> **url 参数表**

| 参数  | 可否为空 | 可否缺省 | 数据类型 | 字段长度 |               例子               |       备注        |
| :---: | :------: | :------: | :------: | :------: | :------------------------------: | :---------------: |
| token |          |          |  string  |    32    | debc454ea24827b67178482fd73f37c3 | 由登录api返回获得 |

> **POST发送请求的json文本**

```python
{
    "id":0,
    "type":"user",
    "subtype":"info",
    "data":{"phone":"13750687010"}
}
```

> **data字段表**

| 参数  | 可否为空 | 可否缺省 | 数据类型 | 字段长度 |    例子     |       备注       |
| :---: | :------: | :------: | :------: | :------: | :---------: | :--------------: |
| phone |          |          |  string  |    11    | 13750687010 | 登录账号(手机号) |

> **Python端返回成功处理情况**

```python
{
    "id": -1, 
    "status": 0, 
    "message": "Successful", 
    "data": {
        "phone": "13750687010", 
        "name": "\u738b\u51cc\u8d85", 
        "nickname": "FatBallFish", 
        "email": "893721708@qq.com", 
        "level": 1
    }
}
```

> **Python端返回失败处理情况**

```python
{
    "id": -1, 
    "status": 1, 
    "message": "Error Token", 
    "data": {}
}
```

> **所用到的全局status**

全局参数详情请看[全局Status表](#全局Status表)

| status |
| ------ |
| -200   |
| -103   |
| -101   |
| -100   |
| -3     |
| -2     |
| -1     |

#### admin-用户信息·更新

> **API说明**

此API用于更新用户信息，仅管理员权限用户可用

> **API类型**

**请求类型：`POST`**

> **API地址：**

**http://www.helpaged.cn/api/admin/user?token=**

> **url 参数表**

| 参数  | 可否为空 | 可否缺省 | 数据类型 | 字段长度 |               例子               |       备注        |
| :---: | :------: | :------: | :------: | :------: | :------------------------------: | :---------------: |
| token |          |          |  string  |    32    | debc454ea24827b67178482fd73f37c3 | 由登录api返回获得 |

> **POST发送请求的json文本**

```python
{
    "id":0,
    "type":"user",
    "subtype":"update",
    "data":{
        "phone":"13750687010",
        "name":"王凌超",
        "nickname":"FatBallFish",
        "email":"893721708@qq.com"}
}
```

> **data字段表**

|   参数   | 可否为空 | 可否缺省 | 数据类型 | 字段长度 |               例子               |       备注       |
| :------: | :------: | :------: | :------: | :------: | :------------------------------: | :--------------: |
|  phone   |          |          |  string  |    11    |           13750687010            | 登录账号(手机号) |
|   name   |    √     |    √     |  string  |    20    | cffb7f1eb316fd45bbfbd43082e36f9c |                  |
| nickname |    √     |    √     |  string  |    20    |             wlc570Q0             |     登录密码     |
|  email   |    √     |    √     |  string  |    50    |         893721708@qq.com         |     邮箱地址     |
|  level   |          |    √     |   int    |          |                1                 |     用户等级     |

> ## 注意

- `phone`用作检验机制，不可被修改
- `level`字段若被使用则必须传递数值，不能为空

> **Python端返回成功处理情况**

```python
{
    "id": 1234, 
    "status": 0, 
    "message": "Successful", 
    "data": {}
}
```

> **Python端返回失败处理情况**

```python
{
     "id":1234,
     "status":101,  #错误码
     "message":"Phone number existed",
     "data":{},
}
```

> **所用到的全局status**

全局参数详情请看[全局Status表](#全局Status表)

| status |
| ------ |
| -200   |
| -103   |
| -101   |
| -100   |
| -3     |
| -2     |
| -1     |

#### admin-用户·删除

> **API说明**

此API用于通过user_id值删除对应用户，仅管理员权限用户可用

> **API类型**

**请求类型：`POST`**

> **API地址：**

**http://www.helpaged.cn/api/admin/user?token=**

> **url 参数表**

| 参数  | 可否为空 | 可否缺省 | 数据类型 | 字段长度 |               例子               |       备注        |
| :---: | :------: | :------: | :------: | :------: | :------------------------------: | :---------------: |
| token |          |          |  string  |    32    | debc454ea24827b67178482fd73f37c3 | 由登录api返回获得 |

> **POST发送请求的json文本**

```python
{
    "id":0,
    "type":"user",
    "subtype":"delete",
    "data":{"phone":"13750687010"}
}
```

> **data字段表**

| 参数  | 可否为空 | 可否缺省 | 数据类型 | 字段长度 |    例子     |       备注       |
| :---: | :------: | :------: | :------: | :------: | :---------: | :--------------: |
| phone |          |          |  string  |    11    | 13750687010 | 登录账号(手机号) |

> **Python端返回成功处理情况**

```python
{
    "id": -1, 
    "status": 0, 
    "message": "Successful", 
    "data": {}
}
```

> **Python端返回失败处理情况**

```python
{
    "id": -1, 
    "status": 1, 
    "message": "Error Token", 
    "data": {}
}
```

> **所用到的全局status**

全局参数详情请看[全局Status表](#全局Status表)

| status |
| ------ |
| -500   |
| -200   |
| -103   |
| -101   |
| -100   |
| -3     |
| -2     |
| -1     |



## **全局Status表**

**所有的全局status值皆小于0**

**大于 0 的status值皆为请求局部status值**

| 参数 |              Message               |                内容                 | 请求类型  |
| :--: | :--------------------------------: | :---------------------------------: | --------- |
|  0   |             successful             |            函数处理正确             | POST、GET |
|  -1  |           Error JSON key           |         json文本必需key缺失         | POST      |
|  -2  |          Error JSON value          |          json文本value错误          | POST      |
|  -3  |           Error data key           |        data数据中必需key缺失        | POST      |
|  -4  |             Error Hash             |          Hash校验文本错误           | POST      |
| -100 |       Missing necessary args       |       api地址中缺少token参数        | POST、GET |
| -101 |            Error token             |             token不正确             | POST、GET |
| -102 |  Get userid failed for the token   |      使用该token获取userid失败      | POST、GET |
| -103 |      No permission to operate      |            用户无权操作             | POST      |
| -104 |       Error device_id token        |         错误的设备id token          | POST      |
| -200 |    Failure to operate database     | 数据库操作失败，检查SQL语句是否正确 | POST、GET |
| -201 | Necessary key-value can't be empty |        关键键值对值不可为空         | POST      |
| -202 |  Missing necessary data key-value  |          缺少关键的键值对           | POST      |
| -203 |       Arg's value type error       |         键值对数据类型错误          | POST      |
| -204 |         Arg's value error          |           键值对数据错误            | POST      |
| -404 |           Unknown Error            |           未知的Redis错误           | POST      |
| -500 |          COS upload Error          |           COS储存上传失败           | POST      |

------

- `status`传递的错误码类型为整型。

- 手机验证码相关的错误码详见[短信错误码](http://cloud.tencent.com/document/product/382/3771 "腾讯短信API文档")

