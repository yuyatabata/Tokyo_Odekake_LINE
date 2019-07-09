import os
import sys

from flask import Flask, request, abort
# WebhookはLINE、Herokuサーバー間通信で使う(webソケットの友達)
# 受信時に関数を呼び出すためにWebhookHandlerを使う(Webhookには構文解析データ変換用のParserもある)
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage
)

# Set up Database
from pymongo import MongoClient
from urllib.parse import urlparse

MONGO_URL = "MongoDB URI "

# Get a connection
client = MongoClient(MONGO_URL)
# Get the database
db = client[urlparse(MONGO_URL).path[1:]]

MAX_RETRY_NUM = 3

app = Flask(__name__)

# get channel_secret and channel_access_token from your environment variable
#channel_secretはtabinakaチャンネル固有の値
#getenvはherokuのconfigで設定した値を取ってくる作業
channel_secret = os.getenv('channel_secret', default=None)
#channel_access_tokenはAPIを利用する際に使うトークン（認証用？）
channel_access_token = os.getenv('channel_access_token', default=None)
print(channel_access_token)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)

# LINE、Herokuサーバー間通信で使う(webソケットの友達)
handler = WebhookHandler(channel_secret)

# Create
post={"user_id":"temp",
    "cost":"temp",
    "mood":"temp",
    "state":0}

#create correction by "db.collection_name"
posts = db.posts
posts.insert_one(post)

@app.route("/health", methods=["GET"])
def healthcheck():
    return "healty!"

@app.route("/callback", methods=["POST"])
def callback():
    # get X-Line-Signature header value
    # リクエストがLINE Platformから送信されたものであることを確認
    signature = request.headers["X-Line-Signature"]

    # get request body as text：クライアント(LINE)からのリクエストをテキストとして受け取る
    body = request.get_data(as_text=True)
    # DEBUG用のログを出力できます。
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        #署名signatureを検証。通ればhandleに定義されている関数を呼び出す。(handleされたメソッドを呼び出す)＝@handlerのついた関数を呼び出す
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# スポット情報の返信
def answer_spot(posts,user_id):
    if posts.find_one({"user_id":user_id})["cost"]== "high" and posts.find_one({"user_id":user_id})["mood"] == "romantic":
        answer_text = "Tokyo Disney Resort"
    elif posts.find_one({"user_id":user_id})["cost"] == "low" and posts.find_one({"user_id":user_id})["mood"] == "romantic":
        answer_text = "AQUA PARQ SHINAGAWA"
    elif posts.find_one({"user_id":user_id})["cost"]== "high" and posts.find_one({"user_id":user_id})["mood"] == "exciting":
        answer_text = "Fujikyu Highland"
    elif posts.find_one({"user_id":user_id})["cost"] == "low" and posts.find_one({"user_id":user_id})["mood"] == "exciting":
        answer_text = "Yomiuri Land"
    else:
        answer_text = "Error"
    return answer_text

def categorize_text(event,message_text,text_dic,attribute_list):
    retry_num = 0
    while True:
        if retry_num >= MAX_RETRY_NUM:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="The upper limit number of times"))
            exit(1)
        try:
            input_num = int(event.message.text)
            if input_num <= len(text_dic) and input_num >= 1:
                tmp_list = list(text_dic.keys())
                tmp = tmp_list[input_num-1]
                result = text_dic[tmp]
                break
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="input number"))
                retry_num += 1
        except ValueError:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="input integer"))
            retry_num += 1
    return result

def get_attribute(num,attribute_list,threshold):
    if num > threshold:
        result = str(attribute_list[0])
    else:
        result = str(attribute_list[1])
    return result

def receive_nature(event,message_text,min_num,max_num):
    retry_num = 0
    while True:
        if retry_num >= MAX_RETRY_NUM:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="The upper limit number of times")
            )
            exit(1)
        try:
            answer_num = int(event.message.text)
            if min_num <= answer_num and answer_num <= max_num:
                result = answer_num
                break
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=(str(min_num) + "~" + str(max_num))))
                retry_num += 1
        except ValueError:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="input integer"))
            retry_num += 1
    return result

#シチュエーション(state)の振り分け
def huriwake(user_id,posts):
    # 回答状況の振り分け
    if not posts.find_one({"user_id":user_id}):
        posts.update_one({"user_id":"temp"}, {"$set":{"user_id":user_id}})
        posts.update_one({"state":0}, {"$set":{"state":1}})
    elif posts.find_one()["user_id"] != "temp" and posts.find_one()["cost"]== "temp":
        posts.update_one({"state":1}, {"$set":{"state":2}})
    elif posts.find_one()["cost"]!= "temp":
        posts.update_one({"state":2}, {"$set":{"state":3}})

#addメソッドは条件付け：event.messageがTextMessageのときだけhandlerメソッドが呼ばれる。default()だとなんでもOKになる
@handler.add(MessageEvent, message=TextMessage)
def message_text(event):
    # sourceはLINE_BotのオブジェクトuserId属性(sourceuserのID)を持つ。送信者のIDを意味するプロパティがSourceクラスにはある。
    user_id = event.source.user_id
    huriwake(user_id,posts)
    # 質問文
    if posts.find_one()["state"] == 1:
        #idを指定を各ユーザーeventから持ってくる
        line_bot_api.push_message(event.source.user_id, TextSendMessage(text="Hello!"))
        next_message = ("How much is the budget?\n\n"  + "Answer {0}~{1}".format(1000,100000))
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=next_message)
        )
    elif posts.find_one()["state"] == 2:
        attribute_list = ["high","low"]
        num = receive_nature(event,message_text,min_num=1000,max_num=1000000)
        attribute = get_attribute(num,attribute_list,threshold=10000)
        #テーブルを更新
        posts.update_one({"user_id":user_id}, {"$set":{"cost":attribute}})
        next_message = ("What is your purpose?\n\n" + "1.go to play\n" +"2.have a date")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=next_message)
        )
        line_bot_api.push_message(event.source.user_id, TextSendMessage(text="Please input number!"))
    elif posts.find_one()["state"] == 3:
        attribute_list = ["exciting","romantic"]
        text_dic = {"1.go to play":"exciting","2.have a date":"romantic"}
        mood_text = categorize_text(event,message_text,text_dic,attribute_list)
        #テーブルを更新
        posts.update_one({"user_id":user_id}, {"$set":{"mood":mood_text}})
        message = answer_spot(posts,user_id)

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=message)
        )
        # 初期化
        posts.delete_many({})

    else:
        message = "reset!!"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=message)
        )
        # 初期化
        posts.delete_many({})

if __name__ == '__main__':
    #main()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)