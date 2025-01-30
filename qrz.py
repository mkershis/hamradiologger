import requests
import os
import sys
from bs4 import BeautifulSoup
import re
from datetime import datetime
import pandas as pd
from getpass import getpass

def promptCredentials() -> tuple[str,str,str]:
    ''' 
    Prompts user for credentials
    '''
    username = input('Enter your QRZ.com username: ')
    password = getpass('Enter your QRZ.com password: ')
    api_key = getpass('Enter your QRZ.com API Key: ')
    
    return username, password, api_key

def readCredentials() -> tuple[str,str,str]:
    '''
    Reads a user's QRZ.com username, password, and
    API key from the os environment variables. If they don't
    exist, then the user is prompted to enter them for the session.
    '''
    try:
        username = os.environ['QRZ_USERNAME']
    except KeyError:
        username = input('Enter your QRZ.com username: ')
    try:
        password = os.environ['QRZ_PASSWORD']
    except KeyError:
        password = getpass('Enter your QRZ.com password: ')
    try:
        api_key = os.environ['QRZ_API_KEY']
    except KeyError:
        api_key = getpass('Enter your QRZ.com API Key: ')
    
    return username, password, api_key

def establishSession(username: str, password: str) -> str:
    '''
    Establishes session for XML lookup, taking user callsign
    and password as input and returning a session key
    '''
    base_url = 'https://xmldata.qrz.com/xml/current'
    params = {'username':username, 'password':password}
    response = requests.get(base_url, params=params) 
    soup = BeautifulSoup(response.text, features='xml')
    if soup.Key is None:
        print('Couldn\'t establish session with QRZ.com. Terminating program...')
        sys.exit()
    else:
        session_key = soup.Key.string
    return session_key

def getData(soup: BeautifulSoup, tag_name: str) -> str:
    '''
    Checks to see if a item in the XML exists. Returns it if it's there.
    If it's not, returns an empty string. 

    This is needed because not every data field is returned in the XML,
    and this will help keep the program from breaking when the data
    stream is unpredictable 
    '''
    if soup.find(tag_name) is None:
        return ""
    # special conversion of 0/1 status codes to Yes, No, Unknown messages.
    # Mostly for EQSL, mail QSL and LOTW preferences, but can be extended to
    # other data fields by adding them to the if-in clause below
    elif tag_name in ('eqsl', 'mqsl', 'lotw'):
        if soup.find(tag_name).string == '1':
            return 'Yes'
        elif soup.find(tag_name).string == '0':
            return 'No'
        else:
            return 'Unknown'
    elif tag_name == 'class':
        # Do some nice formatting for the US licenses, otherwise just return the string
        if soup.find('class').string == 'T':
            return 'Technician'
        elif soup.find('class').string == 'G':
            return 'General'
        elif soup.find('class').string == 'E':
            return 'Amateur Extra'
    else:        
        return soup.find(tag_name).string
    
def lookupCallsign(callsign: str, session_key: str, username: str, password: str) -> int:
    '''
    Takes a callsign and prints metadata associated with that callsign
    returns 0 if successful, 1 if error. 
    '''
    base_url = 'https://xmldata.qrz.com/xml/current'
    params = {'s':session_key, 'callsign':callsign}
    response = requests.get(base_url, params=params)
    soup = BeautifulSoup(response.text, features='xml')

    # Print error message if it exists and immediately exit the function
    # Otherwise parse the XML and print results to screen
    if soup.Error is not None:   
        print(soup.Error.string)
        return 1
    elif soup.Key is None:
        session_key = establishSession(username, password)
        params = {'s':session_key, 'callsign':callsign}
        response = requests.get(base_url, params=params)
        soup = BeautifulSoup(response.text, features='xml')
    
    aliases = getData(soup, 'aliases')
    first_name = getData(soup, 'fname')
    last_name = getData(soup, 'name')
    full_name = (first_name + ' ' + last_name).strip()
    addr1 = getData(soup, 'addr1')
    addr2 = getData(soup, 'addr2')
    state = getData(soup, 'state')
    postal_code = getData(soup, 'zip')
    country = getData(soup, 'country')
    qsl_info = getData(soup, 'qslmgr')
    eqsl = getData(soup, 'eqsl')
    mqsl = getData(soup, 'mqsl')
    lotw = getData(soup, 'lotw')
    lic_class = getData(soup, 'class')

    result_string = f'Details for {callsign}:\n\nAliases: {aliases}\nLicense class: {lic_class}\n\n{full_name}\n{addr1}\n{addr2}, {state} {postal_code}\n{country}\n\nQSL Info: {qsl_info}\
                        \n\nQSL Preferences:\nLOTW?: {lotw}\neQSL?: {eqsl}\nMail?: {mqsl}'
    print(result_string)
    return 0

def adifParse(response: requests.Response) -> tuple[list, int]:
    '''
    Takes the API response and parses out the ADIF data
    for each qso found. Returns QSO data (as a list of
    dictionaries) as well as the number of QSOs as derived from
    the length of the final QSO list.
    '''
    qso_list = []
    adif_regex = re.compile(r'&lt;(\w+):(\d+)&gt;(.+)')

    response_qsos = response.text.split('\n\n')
    for qso in response_qsos:
        adif_parsed = adif_regex.findall(qso)
        if adif_parsed:
            adif = {}
            for line in adif_parsed:
                adif[line[0]] = line[2]
            qso_list.append(adif)
    qso_count = len(qso_list)
    
    return qso_list, qso_count

def parseStatus(response: requests.Response) -> dict:
    '''
    Uses REGEX to parse out the status message and extract
    the values into a dictionary
    '''
    status = {}
    status_regex = re.compile(r'(\w+)=(\w+)')
    status_parsed = status_regex.findall(response.text)

    if status_parsed:
        for line in status_parsed:
            status[line[0]] = line[1]
    
    return status

def queryLog(callsign: str, api_key: str) -> None:
    '''
    Query log for prior contacts with callsign
    '''
    base_url = 'https://logbook.qrz.com/api'
    params = {'KEY':api_key,'ACTION':'FETCH','OPTION':f'CALL:{callsign}'}
    response = requests.get(base_url, params=params)
    #print(response.text)
    #status, qso_list = parseResponse(response)
    qso_list, qso_count = adifParse(response)
    
    if qso_count > 0:
        print(f"\nYou worked {callsign.upper()} {qso_count} time(s) on the following date(s):\n")
        for qso in qso_list:
            qso_date = dateParse(qso['qso_date'])
            time_on = qso['time_on']
            time_off = qso['time_off']
            band = qso['band']
            mode = qso['mode']
            print(f'\t{qso_date} between {time_on}-{time_off} UTC on {band.upper()} {mode.upper()}')
    else:
        print(f"\nYou are working {callsign.upper()} for the first time!")

def dateParse(date_string: str) -> str:
    '''
    Given a date string from QRZ,
    Return a nicely formatted string
    '''
    date = datetime.strptime(date_string, '%Y%m%d')
    clean_date = date.strftime('%a %b %d, %Y')
    return clean_date

def addContact(api_key: str, callsign: str, mode: str, band: str, date: str, time_on: str, time_off: str, rst_sent: str, rst_rcvd: str) -> None:
    '''
    Adds contact to logbook, taking in all the relevant data fields and encoding it in an
    ADIF format
    '''
    base_url = 'https://logbook.qrz.com/api'
    # Coding the ADIF string requires that you specify the character lengths of each variable
    # Hence why you see all the len(x) statements below
    adif = f'<band:{len(band)}>{band}\
            <band_rx:{len(band)}>{band}\
            <mode:{len(mode)}>{mode}\
            <qso_date:{len(date)}>{date}\
            <call:{len(callsign)}>{callsign}\
            <mode:{len(mode)}>{mode}\
            <time_on:{len(time_on)}>{time_on}\
            <time_off:{len(time_off)}>{time_off}\
            <rst_sent:{len(rst_sent)}>{rst_sent}\
            <rst_rcvd:{len(rst_rcvd)}>{rst_rcvd}<eor>'
    params = {'KEY':api_key, 'ACTION':'INSERT', 'ADIF':adif}
    response = requests.get(base_url, params=params)
    status = parseStatus(response)
    if status['RESULT']=='OK':
        print(f'Contact with {callsign} logged successfully.')
        input('\nHit Enter to continue.')
    else:
        print(f'Couldn\'t log contact with {callsign}')
        input('\nHit Enter to continue.')

def queryAll(api_key: str) -> pd.DataFrame:
    '''
    Queries your logbook and returns all contacts as a pandas DataFrame.
    Per the QRZ.com documentation, it uses paging to search in groups of 250
    '''
    base_url = 'https://logbook.qrz.com/api'
    max = 250
    qso_df = pd.DataFrame()
    params = {'KEY':api_key,'ACTION':'FETCH', 'OPTION':f'MAX:{max},AFTERLOGID:{0}'}

    response = requests.get(base_url, params=params)

    qsos, qso_count = adifParse(response)
    status = parseStatus(response)
    
    for qso in qsos:
        qso_df = pd.concat([qso_df, pd.DataFrame(qso, index=[0])])
    while qso_count == 250:
        init_id = qso['app_qrzlog_logid']
        params = {'KEY':api_key,'ACTION':'FETCH', 'OPTION':f'MAX:{max},AFTERLOGID:{init_id}'}
        response = requests.get(base_url, params=params)
        status = parseStatus(response)
        
        qsos, qso_count = adifParse(response)
        
        for qso in qsos:
            qso_df = pd.concat([qso_df, pd.DataFrame(qso, index=[0])])

    # Return pandas DataFrame, dropping any duplicate log ids
    # For some reason subsequent calls return the last id from the 
    # previous call resulting in n - 1 duplicates when n is the number of loops
    return qso_df.drop_duplicates(subset=['app_qrzlog_logid'])

def main():
    #placeholder function mainly for debugging and testing functions
    return
    

if __name__ == "__main__":
    main()