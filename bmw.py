#! /usr/bin/env python

import requests
import json
import urllib
import boto3
import logging
import sys
import pickle

logging.basicConfig(filename='/root/bmw/bmw.log',
                            filemode='a',
                            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.INFO)

BASE_URL = 'b2vapi.bmwgroup.us'

def getToken(BASE_URL, username, password):
    try:
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Content-Length": "124",
            "Connection": "Keep-Alive",
            "Host": BASE_URL,
            "Accept-Encoding": "gzip",
            "Authorization": "Basic blF2NkNxdHhKdVhXUDc0eGYzQ0p3VUVQOjF6REh4NnVuNGNEanli"
                             "TEVOTjNreWZ1bVgya0VZaWdXUGNRcGR2RFJwSUJrN3JPSg==",
            "Credentials": "nQv6CqtxJuXWP74xf3CJwUEP:1zDHx6un4cDjybLENN3kyfumX2kEYigWPcQpdvDRpIBk7rOJ",
            "User-Agent": "okhttp/2.60"}

        data = {
            'grant_type': 'password',
            'scope': 'authenticate_user vehicle_data remote_services',
            'username': username,
            'password': password}

        data = urllib.parse.urlencode(data)
        url = 'https://' + BASE_URL + '/webapi/oauth/token'
        r = requests.post(url, data=data, headers=headers)

        if r.status_code == 200:
            logging.info('Access token acquired')
            return r.json()['access_token']
        else:
            raise ValueError('Unable to login')

    except Exception as msg:
        logging.error(msg)
        sys.exit(1)

def getBattery(BASE_URL, token, vin):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_1_1 like Mac OS X) AppleWebKit/604.3.5 (KHTML, like Gecko) Version/11.0 Mobile/15B150 Safari/604.1',
                    'Authorization': 'Bearer ' + token}

        url = 'https://' + BASE_URL + '/webapi/v1/user/vehicles/' + vin + '/status'

        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            status = r.json()
            chargingLevelHv = status['vehicleStatus']['chargingLevelHv']
            remainingRangeElectricMls = status['vehicleStatus']['remainingRangeElectricMls']
            connectionStatus = status['vehicleStatus']['connectionStatus']
            chargingStatus = status['vehicleStatus']['chargingStatus']
            logging.info('Battery data retreived successfully')
            return chargingLevelHv, remainingRangeElectricMls, connectionStatus, chargingStatus
        else:
            raise ValueError('Unable to retreive battery data from vehicle')

    except Exception as msg:
        logging.error(msg)
        sys.exit(1)

def sendSMS(mobile_number, message, aws_access_key_id, aws_secret_access_key, aws_region_name):
    try:
        client = boto3.client(
            'sns',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region_name
        )
        client.publish(
            PhoneNumber=mobile_number,
            Message=message
        )
        logging.info('SMS message sent successfully')
    except Exception as msg:
        logging.error(msg)
        sys.exit(1)

def getCredentials():
    with open('/root/bmw/credentials.json', 'r') as cf:
        credentials = json.load(cf)
    return credentials

def getLastPercent():
    try:
        with open ('/root/bmw/last_percent', 'rb') as lp:
            last_percent = pickle.load(lp)
        logging.info(f'last_percent loaded with a value of {last_percent}')
        return last_percent

    except FileNotFoundError:

        logging.error('last_percent file not found')

        with open('/root/bmw/last_percent', 'wb') as lp:
            pickle.dump(0, lp)

        logging.info('last_percent file created with value of 0')

        with open ('/root/bmw/last_percent', 'rb') as lp:
            last_percent = pickle.load(lp)
        return last_percent

def setLastPercent(chargingLevelHv):
    try:
        with open('/root/bmw/last_percent', 'wb') as lp:
            pickle.dump(chargingLevelHv, lp)

        logging.info(f'last_percent file updated with {chargingLevelHv}')

    except Exception as msg:
        logging.error(msg)
        sys.exit(1)

try:
    last_percent = int(getLastPercent())
    credentials = getCredentials()
    token = getToken(BASE_URL, credentials['username'], credentials['password'])
    chargingLevelHv, remainingRangeElectricMls, connectionStatus, chargingStatus = getBattery(BASE_URL, token, credentials['vin'])
    message = 'My 2014 BMW i3 Status:\n' + f'Battery: {chargingLevelHv}% ({remainingRangeElectricMls} mi) - {connectionStatus}/{chargingStatus}'

    if chargingLevelHv > last_percent and chargingLevelHv == 100:
        setLastPercent(chargingLevelHv)
        logging.info(message)
        sendSMS(credentials['mobile_number'], message, credentials['aws_access_key_id'], credentials['aws_secret_access_key'], credentials['aws_region_name'])
    elif chargingLevelHv > last_percent and remainingRangeElectricMls == 40:
        setLastPercent(chargingLevelHv)
        logging.info(message)
        sendSMS(credentials['mobile_number'], message, credentials['aws_access_key_id'], credentials['aws_secret_access_key'], credentials['aws_region_name'])
    else:
        setLastPercent(chargingLevelHv)
        logging.info(message)
        #sendSMS(credentials['mobile_number'], message, credentials['aws_access_key_id'], credentials['aws_secret_access_key'], credentials['aws_region_name'])
        #print(message)

except Exception as msg:
    logging.error(msg)
    sys.exit(1)