from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from typing import List

# returns a service object
def authorize():
    # If modifying these scopes, delete the file token.pickle.
    SCOPES = ['https://www.googleapis.com/auth/gmail.labels', 'https://www.googleapis.com/auth/gmail.modify', 'https://www.googleapis.com/auth/gmail.readonly']

    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=43728)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('gmail', 'v1', credentials=creds)

# download message ids for query, following pagination. return list of message ids
def query(service, query:str):
    page = None
    ids = []
    while True:
        msgs = service.users().messages().list(userId='me', q=query, pageToken=page).execute()
        for element in msgs['messages']:
            ids.append(element['id'])
        if 'nextPageToken' in msgs:
            page = msgs['nextPageToken']
        else:
            break
        
    return ids

# returns a list of message ids
def query_todos(service):
    return query(service, 'label:todo -label:[Imap]/Archive label:inbox')

# Removes inbox label from a message
def archive(service, id:str):
    service.users().messages().modify(userId='me', id=id, body={'removeLabelIds':['INBOX']}).execute()

# attach timestamps and subject lines to messages, filling/referring to pickled cache
def fetch_metadata(service, ids: List[str]):
    import pickle
    from time import sleep
    from datetime import datetime

    # load cache if it exists
    cache = {}
    if os.path.exists('messagecache.pkl'):
        with open('messagecache.pkl', 'rb') as cachefile:
            cache = pickle.load(cachefile)

    # load ids into results dictionary, stripping duplicates automatically
    metadata = {key:None for key in ids}
    # load metadata for each id either from cache or from gmail request
    for id in ids:
        if id in cache:
            metadata[id] = cache[id]
        else:
            msg = service.users().messages().get(userId='me', id=id, format='full').execute()
            sleep(0.2) # rate limit our requests to 5 per second
            msgdata = {'internalDate': datetime.fromtimestamp(int(msg['internalDate'])/1000)}

            # get subject
            headers = msg['payload']['headers']
            subject = 'No subject'
            for header in headers:
                if header['name'] == 'Subject':
                    subject = header['value']
            msgdata['subject'] = subject

            # cache downloaded metadata
            cache[id] = msgdata

            metadata[id] = msgdata
    
    # save cache
    with open('messagecache.pkl', 'w+b') as cachefile:
        pickle.dump(cache, cachefile)
    
    return metadata


def calc_days_ago(metadata):
    from datetime import datetime
    datetoday = datetime(datetime.today().year, datetime.today().month, datetime.today().day)
    for id in metadata:
        metadata[id]['age'] = (datetoday - metadata[id]['internalDate']).days + 1
    return metadata