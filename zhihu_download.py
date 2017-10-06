#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
download pictures from zhihu's topic
'''
import requests
try:
    import cookielib
except:
    import http.cookiejar as cookielib
import re
import time
import os.path
try:
    from PIL import Image
except:
    pass
from urllib import request


main_url = 'https://www.zhihu.com/'

# 构造 Request headers
agent = 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Mobile Safari/537.36'
headers = {
    "Host": "www.zhihu.com",
    "Referer": main_url,
    'User-Agent': agent
}


r = requests.get(main_url,headers=headers)
print(r.cookies)

# 使用登录cookie信息
session = requests.session()
session.cookies = cookielib.LWPCookieJar(filename='cookies')
try:
    session.cookies.load(ignore_discard=True)
except:
    print("Cookie 未能加载")


def get_xsrf():
    '''_xsrf 是一个动态变化的参数'''
    index_url = 'https://www.zhihu.com'
    # 获取登录时需要用到的_xsrf
    index_page = session.get(index_url, headers=headers)
    html = index_page.headers
    print("encoding: ", index_page.encoding)
    print("content-type: ", index_page.headers)

    # 这里的_xsrf 返回的是一个list
    #_xsrf = re.findall(pattern, html)
    _xsrf = index_page.headers['Set-Cookie']
    print('_xsrf=', _xsrf)
    return _xsrf


# 获取验证码
def get_captcha():
    t = str(int(time.time() * 1000))
    captcha_url = main_url + 'captcha.gif?r=' + t + "&type=login"
    r = session.get(captcha_url, headers=headers)
    with open('captcha.jpg', 'wb') as f:
        f.write(r.content)
        f.close()
    # 用pillow 的 Image 显示验证码
    # 如果没有安装 pillow 到源代码所在的目录去找到验证码然后手动输入
    try:
        im = Image.open('captcha.jpg')
        im.show()
        im.close()
    except:
        print(u'请到 %s 目录找到captcha.jpg 手动输入' % os.path.abspath('captcha.jpg'))
    captcha = input("please input the captcha\n>")
    return captcha


def isLogin():
    # 通过查看用户个人信息来判断是否已经登录
    url = "https://www.zhihu.com/settings/profile"
    login_code = session.get(url, headers=headers, allow_redirects=False).status_code
    if login_code == 200:
        return True
    else:
        return False


def login(password, account):
    _xsrf = get_xsrf()
    headers["X-Xsrftoken"] = _xsrf
    headers["X-Requested-With"] = "XMLHttpRequest"
    # 通过输入的用户名判断是否是手机号
    if re.match(r"^1\d{10}$", account):
        print("手机号登录 \n")
        post_url = main_url + 'login/phone_num'
        postdata = {
            '_xsrf': _xsrf,
            'password': password,
            'phone_num': account
        }
    else:
        if "@" in account:
            print("邮箱登录 \n")
        else:
            print("你的账号输入有问题，请重新登录")
            return 0
        post_url = main_url + 'login/email'
        postdata = {
            '_xsrf': _xsrf,
            'password': password,
            'email': account
        }
    # 不需要验证码直接登录成功
    login_page = session.post(post_url, data=postdata, headers=headers)
    login_code = login_page.json()
    if login_code['r'] == 1:
        # 不输入验证码登录失败
        # 使用需要输入验证码的方式登录
        postdata["captcha"] = get_captcha()
        login_page = session.post(post_url, data=postdata, headers=headers)
        login_code = login_page.json()
        print(login_code['msg'])
    # 保存 cookies 到文件，
    # 下次可以使用 cookie 直接登录，不需要输入账号和密码
    session.cookies.save()

try:
    input = raw_input
except:
    pass


def download_images_from_html(page, dirname):
    print('开始下载(', dirname, ')图片')
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    with open(dirname + '/' + dirname + 'topic.html','wb') as f:
        f.write(page.content)
        f.close()
    # get img label and img url
    img_urls = []
    for url in re.findall(r'<img src=".*?"', page.text):
        img_urls.append(url[10:-1])

    for url in re.findall(r'img src=&quot;.*?&quot;', page.text):
        img_urls.append(url[14:-6])

    count = 0
    for url in img_urls:
        count += 1
        filename = url[-10:]
        dir=os.path.abspath('./' + dirname + '/')
        img_path = os.path.join(dir, filename)
        request.urlretrieve(url, img_path)
        print(img_path)
    print('下载', count, '张图片，请查看 ' + dir +' 目录')


#todo: modify requests.get to https://www.zhihu.com/topic/19552207/hot format
# transform 'topic' to topicID, such as 美女 to 19552207
def download_img_from_topic(topic_search_keyword):
    # params = {
    #     'type': 'topic',
    #     'q': topic_search_keyword
    # }
    # page = requests.get(main_url + 'search', params)

    #print(page.url)
    page = requests.get(main_url + 'search?type=topic&q='+topic_search_keyword,headers=headers)
   

    with open(topic_search_keyword + '/' + topic_search_keyword + 'topic.html','wb') as f:
        f.write(page.content)
        f.close()

    # get first topic of topic_search_keyword search list
    topic_sub_url = re.findall('"/topic/.*?"', page.text)
    if len(topic_sub_url) == 0:
        print("Sorry, no content for such topic!")
        return

    # real topic is the first one of search list
    topic = re.findall('data-highlight>.*?</a>', page.text)[0][15:-4]
    # 精华回答
    topic_url = main_url + topic_sub_url[0][2:-1] + '/top-answers'
    print(topic_url)
    topic_hot_page = requests.get(topic_url, headers=headers)
    download_images_from_html(topic_hot_page, topic)


def download_img_from_search_content(content):
    if not os.path.exists(content):
        os.makedirs(content)
    page = requests.get(main_url + 'search?type=content&q='+content,headers=headers)
    with open(content + '/' + content + 'content.html','wb') as f:
        f.write(page.content)
        f.close()
    download_images_from_html(page, content)


if __name__ == '__main__':
    if isLogin():
        print('您已经登录')
    else:
        account = input('请输入你的用户名\n>  ')
        password = input("请输入你的密码\n>  ")
        login(password, account)
    #download all img from content in zhihu
    content = input('请输入你感兴趣的知乎话题,按回车结束后自动下载该话题下的图片\n> ')
    download_img_from_search_content(content)
    download_img_from_topic(content)

