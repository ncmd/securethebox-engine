#!/usr/bin/env python
from threading import Lock
from flask import Flask, render_template, session, request, \
    copy_current_request_context
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect
import time
import os
from datetime import datetime, timedelta
import requests
import json
import jwt

async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()

"""
Kubernetes needs to be online for the engine to work

Need to fix on disconnect; there is a game of no socket data because client disconnected

Should be sending results to firebase
Client should be getting information from firebase

IMPORTANT API's
/api/Users - done
/api/BasketItems - done
/rest/basket/12076/checkout - done
/product/search?
/api/Products
/api/Baskets
/rest/Basket
/api/Complaints
/file-upload
/ftp

"""

# This is the main thread that will ccommunicate to client
def background_thread():
   check_app_status()


# check if app is online/offline
def check_app_status():
    
    while True:
        print("CHECK APP STATUS")
        # setting sleep to 15 seconds should not cause downtime
        # time.sleep(5)
        time.sleep(0.5)
        socketio.sleep(0.5)
        # count += 1
        timenow = datetime.now()
        print("START TIME:",timenow.isoformat(' ', 'seconds'))
        try:
            response = requests.request("GET", 'http://nginx-modsecurity-charles.us-west1-a.securethebox.us')
            print('RESPONSE STATUS CODE:',response.status_code)
            if response.status_code == 200:
                auth_result, auth_token, basket_id = check_rest_user_login(timenow)
                basket_results = check_api_basketitems(auth_token,basket_id)
                checkout_results = check_rest_basket_checkout(auth_token, basket_id)
                user_count = check_user_registered(auth_token)
                user_active = check_user_active()
                print("TIME:",str(timenow.isoformat(' ', 'seconds')),str((timenow+timedelta(seconds=1)).isoformat(' ', 'seconds')))
                print('VARIABLES:',auth_result, basket_id,basket_results,checkout_results,user_count, user_active)
                socketio.emit('my_response', {'app_status':'online', 'api_user_login':auth_result, 'basket_result':basket_results, 'checkout_results':checkout_results, 'user_count':user_count,'user_active':user_active,'startTime':str(timenow.isoformat(' ', 'seconds')), 'endTime':str((timenow+timedelta(seconds=1)).isoformat(' ', 'seconds')), 'title':'up'})
                endtimenow = datetime.now()
                print("END TIME:",endtimenow.isoformat(' ', 'seconds'))
            else:
                print("SUM TING WONG")
                socketio.emit('my_response', {'app_status':'offline', 'api_user_login':"failed", 'basket_result':"failed", 'checkout_results':"failed", 'user_count':0,'user_active':0,'startTime':str(timenow.isoformat(' ', 'seconds')), 'endTime':str((timenow+timedelta(seconds=1)).isoformat(' ', 'seconds')), 'title':'down'})
                endtimenow = datetime.now()
                print("END TIME:",endtimenow.isoformat(' ', 'seconds'))
        except:
            print('SUM TING REALLLY WONG')
            socketio.emit('my_response', {'app_status':'offline', 'api_user_login':"failed", 'basket_result':"failed", 'checkout_results':"failed", 'user_count':0, 'user_active':0,'startTime':str(timenow.isoformat(' ', 'seconds')), 'endTime':str((timenow+timedelta(seconds=1)).isoformat(' ', 'seconds')), 'title':'down'})
            endtimenow = datetime.now()
            print("END TIME:",endtimenow.isoformat(' ', 'seconds'))

def create_app_user():
    # print("Trying request...")
    try:
        headers = {'Content-Type': "application/json"}
        payload = "{\"email\": \"test@securethebox.us\", \"password\": \"changemestb\"}"
        response = requests.request("POST", "http://juice-shop-charles.us-west1-a.securethebox.us/api/Users", data=payload,headers=headers)
        json_response = json.loads(response.json())
        # print("json_response:",json_response)
    except:
        print("Failed user creation request or user")

def check_rest_user_login(timenow):
    # time.sleep(5)
    # print('CHECK REST USER LOGIN')
    try:
        payload = "{\"email\": \"test@securethebox.us\", \"password\": \"changemestb\"}"
        headers = {'Content-Type': "application/json"}
        response = requests.request("POST", "http://juice-shop-charles.us-west1-a.securethebox.us/rest/user/login", data=payload, headers=headers)
        json_response = json.loads(response.text)
        if json_response['authentication']['umail'] == "test@securethebox.us":
            auth_result = "success"
            auth_token = json_response['authentication']['token']
            basket_id =  json_response['authentication']['bid']
            # print("AUTH_RESULT:",auth_result)
            # print("AUTH_TOKEN:",auth_token)
            # print("BASKET_ID:",basket_id)
            return auth_result, auth_token, basket_id
        else:
            print("SUM TING WONG - check_rest_user_login")
            create_app_user()
            auth_result = "failed"
            auth_token = "none"
            return auth_result, auth_token
    except:
        print("SUM TING WONG - check_rest_user_login")
        create_app_user()
        # create_app_user()
        auth_result = "failed"
        auth_token = "none"
        return auth_result, auth_token

def check_api_basketitems(auth_token,basket_id):
    # time.sleep(5)
    # print('CHECK API BASKETITEMS')
    headers = {
        'content-type': "application/json",
        'Authorization': "Bearer "+auth_token,
        }
    if auth_token != "none":
        try:
            url = "http://juice-shop-charles.us-west1-a.securethebox.us/api/BasketItems"
            payload = "{ \"BasketId\": "+str(basket_id)+", \"ProductId\": 2, \"quantity\": 1 }"
            response = requests.request("POST", url, data=payload, headers=headers)
            json_response = json.loads(response.text)
            # print("ADD BASKET RESPONSE",response)
            if json_response['status'] == "success":
                # print("ADDED ITEM TO BASKET!")
                return "success"
            else:
                print("SUM TING WONG - check_api_basketitems")
                return "failed"
        except:
            print("SUM TING WONG - check_api_basketitems")
            return "failed"

def check_rest_basket_checkout(auth_token, basket_id):
    # time.sleep(5)
    # print('CHECK REST BASKET CHECKOUT')
    headers = {
        'content-type': "application/json",
        'Authorization': "Bearer "+auth_token,
        }
    if auth_token != "none":
        try:
            url = "http://juice-shop-charles.us-west1-a.securethebox.us/rest/basket/"+str(basket_id)+"/checkout"
            response = requests.request("POST", url, headers=headers)
            json_response = json.loads(response.text)
            # print("CHECKOUT BASKET RESPONSE",response)
            if 'orderConfirmation' in json_response:
                # print("BASKET CHECKOUT!")
                return "success"
            else:
                print("SUM TING WONG - check_rest_basket_checkout")
                return "failed"
        except:
            print("SUM TING WONG - check_rest_basket_checkout")
            return "failed"

def check_user_registered(auth_token):
    # time.sleep(5)
    # print('CHECK USER REGISTERED')
    headers = {
        'Authorization': "Bearer "+auth_token,
        }
    if auth_token != "none":
        try:
            url = "http://juice-shop-charles.us-west1-a.securethebox.us/api/Users"
            response = requests.request("GET", url, headers=headers)
            json_response = json.loads(response.text)
            if 'status' in json_response:
                user_count = len(json_response['data'])
                return int(user_count)
            else:
                print("SUM TING WONG - check_user_registered")
                return 0
        except:
            print("SUM TING WONG - check_user_registered")
            return 0

# simulate an active user
def check_user_active():
    url = "http://nginx-modsecurity-charles.us-west1-a.securethebox.us/nginx_status"

    headers = {
        'Host': "nginx-modsecurity-charles.us-west1-a.securethebox.us",
        'accept-encoding': "gzip, deflate",
        'Connection': "keep-alive"
        }

    response = requests.request("GET", url, headers=headers)
    responseLines = response.text.splitlines()
    activeConnectionRaw = responseLines[0].split(":")
    print("RESPONSE:",int(activeConnectionRaw[1])) 
    return int(activeConnectionRaw[1])


@socketio.on_error()
def error_handler(e):
    print("ERROR OCCURRED:",e)
    pass
    # timenow = datetime.now()
    # socketio.emit('my_response', {'app_status':'offline', 'startTime':str(timenow.isoformat()), 'endTime':str(timenow+timedelta(seconds=1)), 'title':'down'})

@socketio.on('connect')
def test_connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)

@socketio.on('disconnect')
def test_disconnect():
    print("CLIENT DISCONNECTED")
    # global thread
    
    # with thread_lock:
    #     if thread is None:
    #         thread = socketio.start_background_task(background_thread)
    # try:
    #     print("Trying thread again")
    # except:
    #     print("Something happened...")

if __name__ == '__main__':
    socketio.run(app, port=6600, debug=False)
