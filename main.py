from flask import Flask, request, abort
import requests, os
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageMessage, ImageSendMessage, FollowEvent, UnfollowEvent
from PIL import Image
from io import BytesIO
import psycopg2


LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_CHANNEL_SECRET = os.environ["LINE_CHANNEL_SECRET"]
#DATABASE_URL = os.environ["DATABASE_URL"]

app = Flask(__name__)

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

header = {
    "Content_Type": "application/json",
    "Authorization": "Bearer " + LINE_CHANNEL_ACCESS_TOKEN
}

@app.route("/")
def hello_world():
    return "hello world!"


# アプリにPOSTがあったときの処理
@app.route("/callback", methods=["POST"])
def callback():
    # get X-Line-Signature header value
    signature = request.headers["X-Line-Signature"]
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"


# botにメッセージを送ったときの処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))
    print("返信完了!!\ntext:", event.message.text)


# botに画像を送ったときの処理
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    print("画像を受信")
    message_id = event.message.id
    image_path = getImageLine(message_id)
    line_bot_api.reply_message(
        event.reply_token,
        ImageSendMessage(
            original_content_url = image_path["main"],
            preview_image_url = image_path["preview"]
        )
    )
    print("画像の送信完了!!")


# 受信メッセージに添付された画像ファイルを取得
def getImageLine(id):
    line_url = f"https://api-data.line.me/v2/bot/message/{id}/content"
    result = requests.get(line_url, headers=header)
    print(result)

    img = Image.open(BytesIO(result.content))
    w, h = img.size
    if w >= h:
        ratio_main, ratio_preview = w / 1024, w / 240
    else:
        ratio_main, ratio_preview = h / 1024, h / 240

    width_main, width_preview = int(w // ratio_main), int(w // ratio_preview)
    height_main, height_preview = int(h // ratio_main), int(h // ratio_preview)

    img_main = img.resize((width_main, height_main))
    img_preview = img.resize((width_preview, height_preview))
    image_path = {
        "main": f"static/images/image_{id}_main.jpg",
        "preview": f"static/images/image_{id}_preview.jpg"
    }
    img_main.save(image_path["main"])
    img_preview.save(image_path["preview"])
    return image_path

