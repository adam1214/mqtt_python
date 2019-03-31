# -*- coding: utf-8 -*-

import paho.mqtt.client as mqtt
import time, signal, sys, threading
from db_Handler import DBHandler
import pymysql
import ChatRoom, Record
import identifier as idf
import importlib
import datetime
import fcm
import os
import io
from PIL import Image

#importlib.reload(sys)
#sys.setdefaultencoding('utf-8')

client = None

mqtt_loop = False


###################################

def on_message(client, userdata, message):
    topic = message.topic
    if topic.split("/")[1] == idf.SendImg :
        msg = message.payload
    elif topic.split("/")[1] == idf.ChangeUserIcon :
        msg = message.payload
    else :
        msg = str(message.payload.decode("utf-8"))
    thread = threading.Thread(target = hall, args = (topic, msg))
    thread.start()

def on_log(client, userdata, level, buf):
    print ("log : %s" % (buf))

###################################

def mqtt_client_thread():
    signal.signal(signal.SIGTERM, stop)
    #signal.signal(signal.SIGQUIT, stop)
    signal.signal(signal.SIGINT,  stop)  # Ctrl-C

    heartBeat = 0

    global mqtt_loop, client
    client_id = "gardenia"
    client = mqtt.Client(client_id,False)

    client.on_message = on_message
    client.on_log = on_log

    host_name = "140.116.82.52"
    client.connect(host_name,1883)

    topic = "IDF/+/+"
    client.subscribe(topic)
    topic = "IDF/SendImg/+/+"
    client.subscribe(topic)
    topic = "IDF/RecordImgBack/+/+"
    client.subscribe(topic)
    topic = "Service/+/+"
    client.subscribe(topic)

    mqtt_loop = True
    cnt = 0
    '''
    while mqtt_loop:
        client.loop()
        cnt += 1
        if cnt > 20:
            heartBeat += 1
            print ("HeartBeat = %d" % (heartBeat))
            try:
                client.reconnect()
            except:
                time.sleep(1)
            cnt = 0
    print("quit mqtt thread")
    client.disconnect()
    '''
    client.loop_forever()

###################################

def hall(topic, msg) :
    print("-------  into hall  -------\n")
    conn = DBHandler.connect()
    cursor = conn.cursor()
    db = DBHandler(conn,cursor)
    category = topic.split("/")[0]
    identifier = topic.split("/")[1]
    user = topic.split("/")[2]

    if   category == "IDF" :
        if   identifier == idf.FriendIcon :
            friendIcon(db, topic, user, msg)
        elif identifier == idf.Initialize :
            initialize(db, topic, user)
        elif identifier == idf.GetUserData :
            getUserData(db, topic, user)
        elif identifier == idf.GetUserIcon :
            getUserIcon(db, topic, user)
        elif identifier == idf.AddFriend :
            addFriend(db, topic, user, msg)
        elif identifier == idf.AddGroup :
            addGroup(db, topic, user, msg)
        elif identifier == idf.DeleteFriend :
            deleteFriend(db, topic, user, msg)
        elif identifier == idf.WithdrawFromGroup :
            withdrawFromGroup(db, topic, user, msg)
        elif identifier == idf.SendMessage :
            sendMessage(db, topic, user, msg)
        elif identifier == idf.DeleteMessage :
            deleteMessage(db, topic, user, msg)
        elif identifier == idf.SendImg :
            sendImg(db, topic, user, msg)
        elif identifier == idf.GetRecord :
            getRecord(db, topic, user, msg)
        elif identifier == idf.RecordImgBack :
            RecordImgBack(db, topic, user, msg)
        elif identifier == idf.Login :
            login(db, topic, user, msg)
        elif identifier == idf.InviteFriend :
            inviteFriend(db, topic, msg)
        elif identifier == idf.SubmitFCMToken :
            submitFCMToken(db, user, msg)
        elif identifier == idf.GetAuth :
            getAuth(db, topic, user, msg)
        elif identifier == idf.AddPoster :
            addPoster(db, topic, user, msg)
        elif identifier == idf.GetPoster :
            getPoster(db, topic, user, msg)
        elif identifier == idf.GetPosterReply :
            getPosterReply(db, topic, user, msg)
        elif identifier == idf.DeletePoster :
            deletePost(db, topic, user, msg)
        elif identifier == idf.DeletePosterReply :
            deleteReply(db, topic, user, msg)
        elif identifier == idf.ChangeUserIcon :
            changeUserIcon(db, topic, user, msg)
        elif identifier == idf.ChangeUserName :
            changeUserName(db, topic, user, msg)

    elif category == "Service" :
        if   identifier == idf.AddFriendNotification :
            addFriendNotification(topic, user, msg)

def login(db, topic, user, msg) :
    global client
    result = db.login(msg)
    if result == True :
        msg = "True," + msg
    else :
        msg = "False"
    topic_re = "%s/Re" % (topic)
    client.publish(topic_re,msg,2,False)

def friendIcon(db, topic, user, msg) :
    global client
    ID = msg.split(":")[1]
    img_path = db.getUserImagePath(ID)
    img = getImageByPath(img_path)
    topic_re = "%s/Re" % (topic)
    topic_re = topic_re.replace("FriendIcon","FriendIcon," + msg)
    client.publish(topic_re,img,2,False)

def initialize(db, topic, user) :
    global client
    L = db.getInitInfo(user)
    topic_re = "%s/Re" % (topic)
    msg = ""
    for i in range(0,len(L)) :
        R = L[i]
        Rmsg = db.getLastMSG(R.code)
        Rmsg_Date = db.getLastMSGTime(R.code)
        if i == 0 :
            msg += ("%s\t%s\t%s\t%s\t%s\t%s" % (R.code, R.roomName, R.memberID, R.type, Rmsg, Rmsg_Date))
        else :
            msg += ("\r%s\t%s\t%s\t%s\t%s\t%s" % (R.code, R.roomName, R.memberID, R.type, Rmsg, Rmsg_Date))
        #print(R.memberID)
        i = i + 1
    client.publish(topic_re,msg,2,False)

def getUserData(db, topic, user) :
    global client
    msg = db.getName(user)
    topic_re = "%s/Re" % (topic)
    client.publish(topic_re,msg,2,False)

def getUserIcon(db, topic, user) :
    global client
    img_path = db.getUserImagePath(user)
    msg = getImageByPath(img_path)
    topic_re = "%s/Re" % (topic)
    client.publish(topic_re,msg,2,False)

def addFriend(db, topic, user, friend) :
    global client
    result = db.addFriend(user,friend)
    topic_re = "%s/Re" % (topic)
    if result == True :
        last = db.getLast(user,"F") #code
        name = db.getName(friend)
        msg = "true/%s/%s/%s/1" % (name,friend,last)
        client.publish(topic_re,msg,2,False)

        topic_re = topic_re.replace(user,friend)
        name = db.getName(user)
        msg = "true/%s/%s/%s/2" % (name,user,last)
        client.publish(topic_re,msg,2,False)
    else :
        client.publish(topic_re,"false")

def deleteFriend(db, topic, user, msg) :
    global client
    friendID = msg.split("/")[0]
    code = msg.split("/")[1]
    result = db.deleteFriend(user, friendID, code)

    topic_re = "%s/Re" % (topic)
    if result == True :
        client.publish(topic_re,"true/1")

        topic_re = topic_re.replace(user,friendID)
        MSG = "true/2/%s" % (user)
        client.publish(topic_re,MSG)
    else :
        client.publish(topic_re,"false")

def addGroup(db, topic, user, member_str) :
    global client
    L = member_str.split("\t")
    groupName = L[0]
    L.remove(L[0])
    result = db.createChatRoom(L,"G",groupName)
    topic_re = "%s/Re" % (topic)
    if result == True :
        last = db.getLast(user,"G") #code/GroupName
        code = last.split("/")[0]
        memberID = db.getRoomMember(code)
        s = user
        for ID in L :
            topic_re = topic_re.replace(s,ID)
            s = ID
            if ID == user :
                msg = "true/%s/%s/1" % (last,memberID)
            else :
                msg = "true/%s/%s/2" % (last,memberID)
            client.publish(topic_re,msg)
    else :
        client.publish(topic_re,"false")

def withdrawFromGroup(db, topic, user, code) :
    global client
    result = db.withdrawFromGroup(user, code)
    topic_re = "%s/Re" % (topic)
    if result == True :
        client.publish(topic_re,"true")
        notifyMemberChange(db, code)
    else :
        client.publish(topic_re,"false")

def sendMessage(db, topic, user, msg) :
    global client
    topic_splitLine = topic.split("/")
    msg_splitLine = msg.split("\t")
    code = msg_splitLine[0]
    sender = msg_splitLine[1]
    text = msg_splitLine[2]
    t = db.storeRecord(code,sender,text)
    msg = msg + "\t" + datetime.datetime.strftime(t, '%Y-%m-%d %H:%M:%S')
    receiver = db.getReceiverList(code)
    for R in receiver:
        topic_re = "%s/%s/%s/Re" % (topic_splitLine[0], topic_splitLine[1], R)
        client.publish(topic_re,msg)
        if R != user :
            token = db.findFCMToken(R)
            if token != "e" :
                name = db.getName(user)
                fcm.push_notify_to_one(token,name,text,code)

def sendImg(db, topic, user, imgBytes) :
    tsl = topic.split("/")
    code = tsl[3]
    path = "./image/%s/%s/" % (code, user)
    mkdir(path)
    time_float = time.time()
    path = "%s%s" % (path, time_float)  #I don't want the '.' in the float, next line replace
    path = path.replace(".", "")        #it will make the "./path/" to "/path"
    path = ".%s.%s" % (path, "jpeg")    #so need to add the '.' back in the head
    image = Image.open(io.BytesIO(imgBytes))
    image.save(path)

    t = db.storeRecord(code, user, path, 'img')
    t_str = datetime.datetime.strftime(t, '%Y-%m-%d %H:%M:%S')
    receiver = db.getReceiverList(code)
    for R in receiver:
        topic_re = "%s/%s/%s/%s/%s/%s/Re" % (tsl[0], tsl[1], R, user, code, t_str)
        client.publish(topic_re, imgBytes, 2, False)
        if R != user :
            token = db.findFCMToken(R)
            if token != "e" :
                name = db.getName(user)
                fcm.push_notify_to_one(token,name,"a new image",code)

def getRecord(db, topic, user, code) :
    global client
    L = db.getRecord(code)
    topic_re = "%s/Re" % (topic)
    msg = ""
    for i in range(0,len(L)) :
        R = L[i]
        if i == 0:
            msg += "%s\t%s\t%s\t%s" % (R.sender, R.MSG, R.time, R.type)
        else :
            msg += "\r%s\t%s\t%s\t%s" % (R.sender, R.MSG, R.time, R.type)
        i = i + 1
    client.publish(topic_re,msg,2,False)

def RecordImgBack(db, topic, user, path) :
    global client
    image = getImageByPath(path)
    topic_re = "%s/Re" % (topic)
    client.publish(topic_re, image, 2, False)

def inviteFriend(db, topic, msg) :
    global client
    code = msg.split("\t")[0]
    member = msg.split("\t")[1]
    mList = member.split(",")
    flag = False
    for i in range(0, len(mList)) :
        memberID = mList[i]
        if memberID == "" :
            break
        else :
            roomName = db.getRoomName(code)
            result = db.hasRoom(memberID, code)
            if result == False:
                flag = True
                db.inviteNewFriend(code,roomName,memberID)
                sendNewChatroom(db,code,roomName,memberID)
    if flag == True:
        notifyMemberChange(db,code)

def sendNewChatroom(db, code, roomName, memberID) :
    global client
    topic = "IDF/SendNewChatroom/%s/Re" % (memberID)
    member = db.getRoomMember(code)
    Rmsg = db.getLastMSG(code)
    Rmsg_Date = db.getLastMSGTime(code)
    msg = "%s\t%s\t%s\t%s\t%s\t%s" % (code, roomName, member,"G", Rmsg, Rmsg_Date)
    client.publish(topic,msg,2,False)

def notifyMemberChange(db, code) :
    global client
    memberID = db.getRoomMember(code)
    mList = memberID.split("-")
    for i in range(0,len(mList)) :
        member = mList[i]
        if member == "" :
            break
        else :
            msg = code + "\t" + memberID
            topic = "IDF/MemberChange/%s/Re" % (member)
            #print(msg)
            client.publish(topic,msg,2,False)

def submitFCMToken(db, user, token) :
    db.submitFCMToken(user, token)

def getAuth(db, topic, user, code) :
    keeper = db.getClassKeeper(code)
    if keeper != "" :
        topic_re = "%s/Re" % (topic)
        if keeper == user :
            client.publish(topic_re, "1", 2, False)
        else :
            client.publish(topic_re, "0", 2, False)
    else :
        print("error getting Auth")

def addPoster(db, topic, user, msg) :
    global client
    code = msg.split("\t")[0]
    theme = msg.split("\t")[1]
    content = msg.split("\t")[2]
    type_t = msg.split("\t")[3]
    t = db.storePoster(code, user, theme, content, type_t)
    msg = msg + "\t" + user + "\t" + datetime.datetime.strftime(t, '%Y-%m-%d %H:%M:%S')
    receiver = db.getReceiverList(code)
    for R in receiver :
        topic_re = "IDF/AddPoster/%s/Re" % (R)
        client.publish(topic_re, msg)


def getPoster(db, topic, user, code) :
    global client
    L = db.fetchPost(code)
    topic_re = "%s/Re" % (topic)
    msg = ""
    for i in range(0, len(L)) :
        R = L[i]
        if i == 0 :
            msg += "%s\t%s\t%s\t%s\t%s" % (R.sender, R.theme, R.MSG, R.time, R.type)
        else :
            msg += "\r%s\t%s\t%s\t%s\t%s" % (R.sender, R.theme, R.MSG, R.time, R.type)

    client.publish(topic_re, msg, 2, False)

def getPosterReply(db, topic, user, msg) :
    global client
    code = msg.split("\t")[0]
    theme = msg.split("\t")[1]
    L = db.fetchPostReply(code, theme)
    topic_re = "%s/Re" % (topic)
    msg = ""
    for i in range(0, len(L)) :
        R = L[i]
        if i == 0 :
            msg += "%s\t%s\t%s\t%s\t%s" % (R.sender, R.theme, R.MSG, R.time, R.type)
        else :
            msg += "\r%s\t%s\t%s\t%s\t%s" % (R.sender, R.theme, R.MSG, R.time, R.type)

    client.publish(topic_re, msg, 2, False)

def deletePost(db, topic, user, msg) :
    code = msg.split("\t")[0]
    theme = msg.split("\t")[1]
    db.deletePost(code, theme)

def deleteReply(db, topic, user, msg) :
    code = msg.split("\t")[0]
    theme = msg.split("\t")[1]
    content = msg.split("\t")[2]
    db.deleteReply(user, code, theme, content)

def changeUserIcon(db, topic, user, imgBytes) :
    global client

    img_path = db.getUserImagePath(user)
    image = Image.open(io.BytesIO(imgBytes))
    try :
        image.save(img_path)
    except KeyError :
        print("KeyError On Image.Save")
    except IOError :
        print("IOError On Image.Save")
    else :
        topic_re = "%s/Re" % (topic)
        client.publish(topic_re, imgBytes, 2, False)

def changeUserName(db, topic, user, newName) :
    global client

    result = db.changeUserName(user, newName)
    topic_re = "%s/Re" % (topic)
    if result == True :
        msg = "OK\t%s" % (newName)
        client.publish(topic_re, msg, 2, False)
    else :
        client.publish(topic_re, "Error", 2, False)

def deleteMessage(db, topic, user, msg) :
    code = msg.split("\t")[0]
    time = msg.split("\t")[1]
    db.deleteMessage(user, code, time)

###################################

def addFriendNotification(topic, user, friendName) :
    global client
    topic_re = "%s/Re" % (topic)
    msg = friendName
    client.publish(topic_re,msg,2,False)

def mkdir(path) :
    path = os.path.abspath(path)
    folder = os.path.exists(path)
    if not folder :
        os.makedirs(path)

def getImageByPath(path) :
    with io.BytesIO() as bimg :
        with Image.open(path) as img :
            img.save(bimg, 'JPEG')
        image = bimg.getvalue()
    return image

###################################

def stop(*args) :
    global mqtt_loop
    mqtt_loop = False
    client.disconnect()
###################################

if __name__ == "__main__":

    mqtt_client_thread()

    print("exit program")
    sys.exit(0)
