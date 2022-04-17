import os
from os.path import join, dirname

from flask import Flask, jsonify, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError, LineBotApiError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, FileMessage
)

from dotenv import load_dotenv

import pytz

from flask_pymongo import PyMongo

app = Flask(__name__)


from datetime import datetime, timedelta

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

app.config["MONGO_URI"] = os.environ.get("MONGODB_URI")
mongo = PyMongo(app)
db = mongo.db

line_bot_api = LineBotApi(os.environ.get("ACCESS_TOKEN"))
handler = WebhookHandler(os.environ.get("CHANNEL_SECRET"))

user_base_url = 'https://api.line.me/v2/bot'



def panggilAll():
    try:
        WIB = pytz.timezone('Asia/Jakarta')
        hariini = datetime.now(WIB).strftime("%A")
        allUser = db.siayank.find({})
        for user in allUser:
            user['jadwal'] = sorted(user['jadwal'], key=lambda d: d['Begin']) 
            output = ""
            matkul_today = []
            for matkul in user['jadwal']:
                if matkul['Day'] == hariini:
                    matkul_today.append(matkul)

            output = ""
            if not matkul_today:
                output = "Tidak ada jadwal hari ini!"
            for idx, matkul in enumerate(matkul_today):
                output = output + str(idx+1)+ ". " +matkul["Mata Kuliah"]+"\n" \
                +matkul["Day"]+" "+matkul["Begin"]+"-"+matkul["End"]+" "+matkul["Place"]+"\n"
                if("Link" in matkul):
                    output = output + "Meet : " +matkul["Link"] + "\n"

                if("Absen" in matkul):
                    output = output + "Absen : "+matkul["Absen"] + "\n"
                # for dosen in matkul["Pengajar"]:
                #     output = output + dosen + "\n"
                    

            line_bot_api.push_message(user['line_id'], TextSendMessage(text=output))
    except LineBotApiError as e:
        print(e)

panggilAll()