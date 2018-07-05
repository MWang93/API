import os
import csv
import time
import hashlib
import httplib2
import pandas as pd
import webbrowser
from collections import OrderedDict
from flatten_json import flatten
from datetime import date, datetime, timedelta

from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from googleapiclient.discovery import build


DIR = 'tmp/' 
WEBMASTER_CREDENTIALS_FILE_PATH = DIR + "webmasters.dat"
CLIENT_SECREATE_FILE_PATH = DIR + 'client_secrets.json'
date_format = "%Y-%m-%d"

def main():
  argv = argv_prepared()
  
  #prepare the API service
  credentials = load_oauth2_credentials()
  service = create_search_console_client(credentials)
  
  save_file_to_local(argv,service)
  save_file_to_s3(argv,service) 

def acquire_new_oauth2_credentials():
    """
    Args:
        secrets_file. The file path to a JSON file of client secrets, containing:
            client_id; client_secret; redirect_uris; auth_uri; token_uri.
    Returns:
        credentials for use with Google APIs
    """
    flow = flow_from_clientsecrets(
        CLIENT_SECREATE_FILE_PATH,
        scope="https://www.googleapis.com/auth/webmasters.readonly",
        redirect_uri="urn:ietf:wg:oauth:2.0:oob")
    auth_uri = flow.step1_get_authorize_url()
    webbrowser.open(auth_uri)
    print("Please enter the following URL in a browser " + auth_uri)
    auth_code = input("Enter the authentication code: ")
    credentials = flow.step2_exchange(auth_code)
    return credentials

def load_oauth2_credentials():
    """
    Args:
        secrets_file. The file path to a JSON file of client secrets.
    Returns:
        credentials for use with Google APIs.
    Side effect:
        If the secrets file did not exist, fetch the appropriate credentials and create a new one.
    """
    storage = Storage(WEBMASTER_CREDENTIALS_FILE_PATH)
    credentials = storage.get()
    if credentials is None or credentials.invalid:
        credentials = acquire_new_oauth2_credentials()
    storage.put(credentials)
    return credentials

def create_search_console_client(credentials):
    """
    The search console client allows us to perform queries against the API.
    To create it, pass in your already authenticated credentials

    Args:
        credentials. An object representing Google API credentials.
    Returns:
        service. An object used to perform queries against the API.
    """
    http_auth = httplib2.Http()
    http_auth = credentials.authorize(http_auth)
    service = build('webmasters', 'v3', http=http_auth)
    return service

def argv_prepared():
  property_uri = 'https://www.example.com/'
  now = datetime.utcnow()
  start = now + timedelta(days=-2)
  start_date = start.strftime(date_format)
  end = now + timedelta(days=-1)
  end_date = end.strftime(date_format)
  return {'property_uri' : property_uri, 'start_date' : start_date, 'end_date' : end_date}

def hash_id(keys, search_date):
  hashKey = str(keys) + '@' + str(search_date)
  id = hashlib.sha256(hashKey.encode('utf-8')).hexdigest()
  return id

def save_file_to_local(argv, service):
  OUT_DIR = DIR + 'Out/'
  TITLE = 'Top1000Queries' 
  FILE_OUT_DIR = OUT_DIR + TITLE + '(' + argv['start_date'] + ')' + '.csv'
  if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR) 
  
  keys = ['id','search_date', 'keys', 'position', 'ctr', 'impressions', 'clicks']
  with open(FILE_OUT_DIR, 'w', encoding='utf8') as output:
    dict_writer = csv.DictWriter(output, keys)
    dict_writer.writeheader()
    rows = get_rows(argv, service, 'local')
    dict_writer.writerows(rows)

def save_file_to_s3(argv, service): #ready for s3
  column_name = ['id', 'search_date', 'keys', 'position', 'ctr', 'impressions', 'clicks']
  rows = get_rows(argv, service, 's3')
  dic_flattened = [flatten(dic) for dic in rows]
  df = pd.DataFrame(dic_flattened, columns = column_name)

def get_rows(argv, service, env):
  delta, start = time_range(argv['start_date'],argv['end_date'])
  i = 1
  all_rows = []
  
  while i <= delta: 
      argv['start_date'] = start.strftime(date_format)
      end = start + timedelta(days=1)
      argv['end_date'] = end.strftime(date_format)
      if env == 'local': 
        print("saving %s google search data to local..." %argv['start_date'])
      else:
        print("saving %s google search data to s3..." %argv['start_date'])

      request = create_request(start_date=argv['start_date'], end_date=argv['end_date'])
      response = execute_request(service, argv['property_uri'], request)
      
      rows = format_rows(response,argv)
      for row in rows:
        row['id'] = hash_id(row['keys'], row['search_date'])        
        all_rows.append(row)
      i = i+1 
      start = datetime.strptime(argv['end_date'], date_format)

  return all_rows 

def time_range(start_date, end_date):
  start = datetime.strptime(start_date, date_format)
  end = datetime.strptime(end_date, date_format)
  delta = end - start
  return delta.days, start

def create_request(start_date, end_date, dim=['query'], num=1000):
  request = {
        'startDate': start_date,
        'endDate': end_date,
        'dimensions': dim,
        'rowLimit': num
        }
  return request

def execute_request(service, property_uri, request):
  return service.searchanalytics().query(
    siteUrl=property_uri, body=request).execute()

def format_rows(response,argv):
  if 'rows' not in response:
    print("%s google search data is empty..." %argv['start_date'])
    rows = []
  else: 
    rows = response['rows']
    for row in rows:
      keys = ''
      if 'keys' in row:
        keys = u','.join(row['keys'])
        row['keys'] = keys
        row['search_date'] = argv['start_date']
  return rows

if __name__ == '__main__':
  main()