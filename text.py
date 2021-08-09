from twilio.rest import Client 
from configparser import ConfigParser
import os

def send_text(phone_number:str, message:str):
    # Parse data from congif.ini
    current_path = str(os.path.dirname(os.path.realpath(__file__))) # Gets current file location
    config = ConfigParser()
    config.read(os.path.join(current_path,'config.ini'))

    account_sid = config.get("twilio","account_sid")
    auth_token = config.get("twilio","auth_token")
    messaging_service_sid = config.get("twilio","messaging_service_sid")
    
    # Change to your Twilio account sid and auth token
    account_sid = account_sid
    auth_token = auth_token 
    client = Client(account_sid, auth_token) 
    
    message = client.messages.create(  
                                # Change to your Twilio messaging_service_sid
                                messaging_service_sid=messaging_service_sid,
                                body=message,       
                                to=phone_number,
                            ) 
    
    print(message.sid)