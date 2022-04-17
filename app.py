from email import message
import os
from os.path import join, dirname

from pprint import pprint

import httpx

import pytz

# import camelot
import camelot.io as camelot

import pandas as pd

from posixpath import dirname
from flask import Flask, jsonify, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, FileMessage
)

from dotenv import load_dotenv


from flask_pymongo import PyMongo

import pymongo

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
# req_headers = {'Authorization': 'Bearer '+os.environ.get("ACCESS_TOKEN")}

@app.route("/cekTime")
def cekTime():
    ts = datetime.now().strftime("%H:%M:%S")
    print(ts)
    return str(ts)

@app.route("/cekTanggal")
def cekTanggal():
    WIB = pytz.timezone('Asia/Jakarta')
    hariini = datetime.today(WIB)
    tomorrowDay = (hariini + timedelta(days = 1)).strftime('%A')
    return tomorrowDay

# @app.route("/findToday")
def findToday(line_id):
    user = db.siayank.find_one({"line_id": line_id})
    if user == None:
        return "Jadwal belum diunggah!\nSilakan unggah melalui keep, atau menggunakan fitur share pada PDF reader!"
    

    WIB = pytz.timezone('Asia/Jakarta')
    hariini = datetime.now(WIB).strftime("%A")
    matkul_today = []
    user['jadwal'] = sorted(user['jadwal'], key=lambda d: d['Begin']) 
    for matkul in user['jadwal']:
        if matkul['Day'] == hariini:
            matkul_today.append(matkul)

    print(matkul_today)
    
    output = ""
    if not matkul_today:
        output = "Tidak ada jadwal hari ini!"
    for idx, matkul in enumerate(matkul_today):
        output = output + str(idx+1)+ ". " +matkul["Mata Kuliah"]+"\n" \
        +matkul["Day"]+" "+matkul["Begin"]+"-"+matkul["End"]+"\n" \
        +matkul["Place"]+"\n"
        if("Link" in matkul):
            output = output + "Meet : " +matkul["Link"] + "\n"

        if("Absen" in matkul):
            output = output + "Absen : "+matkul["Absen"] + "\n"
        # for dosen in matkul["Pengajar"]:
        #     output = output + dosen + "\n"
    
    return output

def findJadwalAll(line_id):
    user = db.siayank.find_one({"line_id": line_id})
    if user == None:
        return "Jadwal belum diunggah!\nSilakan unggah melalui keep, atau menggunakan fitur share pada PDF reader!"

    output = ""
    for idx, matkul in enumerate(user['jadwal']):
        
        output = output + str(idx+1)+ ". " +matkul["Mata Kuliah"]+"("+matkul["Kode"]+")"+"\n" \
        +matkul["Day"]+" "+matkul["Begin"]+"-"+matkul["End"]+"\n"+matkul["Place"]+"\n"

        if("Link" in matkul):
            output = output + "Meet : " +matkul["Link"] + "\n"

        if("Absen" in matkul):
            output = output + "Absen : "+matkul["Absen"] + "\n"
        
        for dosen in matkul["Pengajar"]:
            output = output + dosen + "\n"

    return output


@app.route("/parse")
def parse(fileName):
    file = fileName+".pdf"
    try:
        tables = camelot.read_pdf(file, pages="all")
        tableHead = ["No","Kode", "Mata Kuliah"]
        for no in range(3):
            print(tables[0].df[no][0])
            if(tables[0].df[no][0] != tableHead[no]):
                return "NO"


        for page in range(0, len(tables)):

            # remove backslashes in class code
            for i in range(1, len(tables[page].df[1])):
                # hapus backslashes
                tables[page].df[1][i] = tables[page].df[1][i].replace("\n","")

            # remove backslashes in pengajar
            for i in range(1, len(tables[page].df[5])):
                # hapus, return list
                tables[page].df[5][i] = tables[page].df[5][i].split("\n")

            # remove backslashes in mata kuliah
            for i in range(1, len(tables[page].df[2])):
                # split backslashes terakhir
                tables[page].df[2][i] = tables[page].df[2][i].rsplit("\n", 1)
                # hapus backslashes sebelumnya
                for j in range(0, len(tables[0].df[2][i])):
                    tables[page].df[2][i][j] = tables[page].df[2][i][j].replace("\n"," ")


        minggu = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
        week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        arr=[]
        for page in range(0, len(tables)):
            for i in range(1, len(tables[page].df[0])):
                obj = {}
                # obj['No']= tables[0].df[0][i]
                obj['Kode']= tables[page].df[1][i]
                obj['Mata Kuliah'] = tables[page].df[2][i][0]
                obj['Kelas'] = tables[page].df[2][i][1].replace('Kelas: ', '')
                obj['Paket Semester'] = int(tables[page].df[3][i])
                obj['SKS'] = int(tables[page].df[4][i])
                obj['Pengajar'] = tables[page].df[5][i]
                jadwal = tables[page].df[6][i].split(" ")
                jam = jadwal[1].split("-")
                obj['Begin'] = jam[0]
                obj['End'] = jam[1]
                obj['Place'] = ''
                for z in range(2, len(jadwal)):
                    obj['Place'] = obj['Place'] + jadwal[z] + ' '
                obj['Jadwal'] = tables[page].df[6][i]
                for idx, hari in enumerate(minggu):
                    if minggu[idx] in obj['Jadwal']:
                        obj['Day'] = week[idx]
                arr.append(obj)

        print(arr)
        return arr
    except:
        return "NO"
    

    

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=FileMessage)
def handle_file(event):

    if (event.message.type=="file"):
        print(event.message.id)
        print(event.source.user_id)
        isUserExist = db.siayank.find_one({"line_id": event.source.user_id})
        if isUserExist != None:
            return line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="Jadwal sudah pernah diunggah! \nKetik /remove untuk menghapus jadwal."))

        try:    
            message_content = line_bot_api.get_message_content(event.message.id)

            with open(os.path.abspath(os.getcwd())+'/'+event.source.user_id+'.pdf', 'wb') as fd:
                fd.write(message_content.content)

            
            result = parse(event.source.user_id)
        except: 
            result = "NO"
        print(result)
        if result == "NO":
            return line_bot_api.push_message(event.source.user_id, TextSendMessage(text="Upload file error!\nGunakan jadwal PDF dari Simaster!"))
        data = {
            "line_id": event.source.user_id,
            "jadwal": result
        }
        
        db.siayank.insert_one(data)
        
        print("PDF berhasil diupload!")
        return line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="PDF berhasil diupload!"))


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
        
    etext = event.message.text

    print(etext)
    print(event.reply_token)

    if (etext == '/id'):
        
        print(event.source.user_id)
        line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(event.source.user_id))
        

    elif (etext == '/sebut nama'):
        displayName = getNama(event.source.user_id)
        # displayName = userData.display_name
        line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="Halo "+displayName))

    elif (etext == '/remove'):

        db.siayank.delete_one({"line_id": event.source.user_id})
        line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="Jadwal berhasil dihapus!"))

    elif (etext == '/jadwal'):

        jadwal = findToday(event.source.user_id)
        return line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=jadwal))

    elif (etext == '/jadwalAll'):
        jadwal = findJadwalAll(event.source.user_id)
        return line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=jadwal))

    # /move KODE_MK HARI START-END
    # /move MII2003 Senin 09:30-11:20
    elif (etext[0:5] == '/move'):
        if(etext.count(" ") != 3):
            return line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="Format error!\nGunakan format /move MII2000 Friday 07:30-09:10"))
        
        inputString = etext.split(" ")
        print(inputString)
        minggu = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day = None
        for hari in minggu:
            if inputString[2] == hari:
                day = hari

        print(day)
        
        if day == None:
            return line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="Format error!\nGunakan format /move MII2000 Friday 07:30-09:10"))

        if len(inputString[3]) != 11:
            return line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="Format error!\nGunakan format /move MII2000 Friday 07:30-09:10"))

        time = inputString[3].split("-")
        print(time)

        try:
            db.siayank.update_one({'line_id': event.source.user_id, 'jadwal': { '$elemMatch': { "Kode": inputString[1]} } },
            {'$set': {'jadwal.$.Day': day, 'jadwal.$.Begin': time[0], 'jadwal.$.End': time[1]}})
            return line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="Jadwal Mata Kuliah berhasil di pindah!"))
        except pymongo.errors.OperationFailure as e:
            print(e)
            return line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="Kode Mata Kuliah tidak ditemukan!"))

    # /meet MII200302 meet.google.com/abcdef
    elif(etext[0:5] == '/meet' and etext.count(" ") == 2):
        inputString = etext.split(" ")
        print(inputString)
        try:
            db.siayank.update_one({'line_id': event.source.user_id, 'jadwal': { '$elemMatch': { "Kode": inputString[1]} } },
            {'$set': {'jadwal.$.Link': inputString[2]}})
            return line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="Link meeting berhasil ditambahkan!"))
        except pymongo.errors.OperationFailure as e:
            print(e)
            return line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="Kode Mata Kuliah tidak ditemukan!"))

    # /absen MII2012312 form.glee
    elif(etext[0:6] == '/absen' and etext.count(" ") == 2):
        inputString = etext.split(" ")
        print(inputString)
        try:
            db.siayank.update_one({'line_id': event.source.user_id, 'jadwal': { '$elemMatch': { "Kode": inputString[1]} } },
            {'$set': {'jadwal.$.Absen': inputString[2]}})
            return line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="Link absen berhasil ditambahkan!"))
        except pymongo.errors.OperationFailure as e:
            print(e)
            return line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="Kode Mata Kuliah tidak ditemukan!"))
    
    else:
        return line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="Upload jadwal untuk mendapatkan pengingat setiap harinya!\nMenambahkan link meet :\n/meet KODE_MATKUL link_meet\nMenambahkan link presensi :\n/absen KODE_MATKUL link_presensi"))

        



def getNama(id):

    try:
        print("Token: "+os.environ.get("ACCESS_TOKEN"))
        headers = {'Authorization': 'Bearer '+os.environ.get("ACCESS_TOKEN")}
        
        with httpx.Client() as client:
            resps = client.get('https://api.line.me/v2/bot/profile/'+id, headers=headers)
            
        res_json = resps.json()
        print(res_json)
        print("Ini : "+res_json['displayName'])
        return res_json['displayName']

    except httpx.HTTPError as exc:
        print(f"Error while requesting {exc.request.url!r}.")
    





if __name__ == "__main__":
    app.run(debug=True)
    # asyncio.run(callback())