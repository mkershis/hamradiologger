import argparse
from datetime import datetime, timezone
import os
import time
import qrz
import sys

parser = argparse.ArgumentParser()
parser.add_argument('-p','--prompt',dest='prompt_user',default=False,type=bool, help='Prompt for credentials')

args = parser.parse_args()
if args.prompt_user == True:
    print('Program set to prompt user for credentials:\n\n')
    username, password, api_key = qrz.promptCredentials()
else:
    username, password, api_key = qrz.readCredentials()

session_key = qrz.establishSession(username, password)
os.system('cls')

print('Welcome to Ham Radio Logger')
print('Created by Matt Kershis, W2MDK')
print('Copyright 2024\n\n\n')
print('This program provides an API to QRZ.com with the following functionality:\n')
print('\t- Lookup basic metadata for a given callsign')
print('\t- Return data on prior contacts with a given callsign ')
print('\t- Log new contacts with a given callsign\n\n\n')
print('\nNote: User input to the program is not case sensitive.\nFeel free to type in all lower case for efficiency.\n')
# use .upper() and .lower() throughout to enforce data consistency regardless of user input
band = input('Enter the band you are using (e.g. 10m, 40m): ').upper()
mode = input('Enter the mode you are using (e.g. FT8, SSB): ').upper()

#Track lookups and logged contacts to report back to user later
lookups = 0
contacts_logged = 0

#start the clock to get session run time later on
beginning_time = time.time()
while True:
    os.system('cls')
    callsign = input('Enter the callsign you wish to search for ("q" to quit): ').upper()
    if callsign == '':
        print('You entered a blank callsign. Please try again.')
        time.sleep(2)
    elif callsign == 'Q':
        break
    else:
        status = qrz.lookupCallsign(callsign, session_key, username, password)
        lookups += 1
        #If status shows that a callsign isn't found, don't ask user to log contact
        if status == 1:
            time.sleep(1)
            log_contact = 'n'
        else:
            qrz.queryLog(callsign, api_key)
            log_contact = input(f'\nDo you wish to start a contact with {callsign} (y/n)?: ').lower()

        if log_contact == 'y':
            start = datetime.now(timezone.utc)
            date = start.strftime('%Y%m%d')
            time_on = start.strftime('%H%M')

            rst_sent = input('Enter the signal report you sent to the other station (e.g. 59): ')
            rst_rcvd = input('Enter the signal report you received from the other station: ')
            input('Hit enter to end the QSO')
            
            time_off = datetime.now(timezone.utc).strftime('%H%M')
            qrz.addContact(api_key, callsign, mode, band, date, time_on, time_off, rst_sent, rst_rcvd)
            contacts_logged += 1
            keep_searching = input('Search for another contact (y/n)?: ').lower()
            if keep_searching == 'y':
                pass
            else:
                break
        else:
            pass
ending_time = time.time()
duration = ending_time - beginning_time
runtime_string = time.strftime('%H:%M:%S', time.gmtime(duration))

os.system('cls')
print(f'You looked up {lookups} callsign(s) and logged {contacts_logged} contact(s) in a total runtime of {runtime_string} (h:m:s)')
print('Session terminated.')