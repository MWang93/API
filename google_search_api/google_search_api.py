import os
import csv
import sys
import hashlib
import argparse
import pandas as pd
from flatten_json import flatten
from datetime import date, datetime, timedelta
from googleapiclient import sample_tools

date_format = "%Y-%m-%d"

argparser = argparse.ArgumentParser(add_help=False)
argparser.add_argument('property_uri', type=str, help=('Site or app URI to query data for (including trailing slash).'))
argparser.add_argument('start_date', type=str, help=('Start date of the requested date range in YYYY-MM-DD format.'))
argparser.add_argument('end_date', type=str, help=('End date of the requested date range in YYYY-MM-DD format.'))

def main():
  argv = argv_prepared()
  service, flags = sample_tools.init(
      argv, 'webmasters', 'v3', __doc__, __file__, parents=[argparser],
      scope='https://www.googleapis.com/auth/webmasters.readonly') 
  save_file_to_local(flags)
  save_file_to_s3(flags) 

def argv_prepared():
  property_uri = 'https://www.example.com/'
  now = datetime.now()
  start = now + timedelta(days=-2)
  start_date = start.strftime(date_format)
  end = now + timedelta(days=-1)
  end_date = end.strftime(date_format)
  return [__file__, property_uri, start_date, end_date]

def hash_id(keys, search_date):
  hashKey = str(keys) + '@' + str(search_date)
  id = hashlib.sha256(hashKey.encode('utf-8')).hexdigest()
  return id

def save_file_to_local(flags):
  DIR = 'tmp/'
  OUT_DIR = DIR + 'Out/'
  TITLE = 'Top 1000 Queries.csv' 
  FILE_OUT_DIR = OUT_DIR + flags.start_date + ' to ' + flags.end_date + ' ' + TITLE
  if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR) 
  
  keys = ['id','search_date', 'keys', 'position', 'ctr', 'impressions', 'clicks']
  with open(FILE_OUT_DIR, 'w', encoding='utf8') as output:
    dict_writer = csv.DictWriter(output, keys)
    dict_writer.writeheader()
    rows = get_rows(flags,'local')
    dict_writer.writerows(rows)

def save_file_to_s3(flags):#ready for s3
  column_name = ['id', 'search_date', 'keys', 'position', 'ctr', 'impressions', 'clicks']
  rows = get_rows(flags,'s3')
  dic_flattened = [flatten(dic) for dic in rows]
  df = pd.DataFrame(dic_flattened, columns = column_name)

def get_rows(flags, loc):
  delta, start = time_range(flags.start_date,flags.end_date)
  i = 1
  all_rows = []
  
  while i <= delta: 
      flags.start_date = start.strftime(date_format)
      end = start + timedelta(days=1)
      flags.end_date = end.strftime(date_format)
      if loc == 'local': 
        print("saving %s google search data to local..." %flags.start_date)
      else:
        print("saving %s google search data to s3..." %flags.start_date)

      argv1 = [__file__, flags.property_uri, flags.start_date, flags.end_date]  
      service, flags = sample_tools.init(
          argv1, 'webmasters', 'v3', __doc__, __file__, parents=[argparser],
          scope='https://www.googleapis.com/auth/webmasters.readonly') 
    
      request = create_request(start_date=flags.start_date, end_date=flags.end_date)
      response = execute_request(service, flags.property_uri, request)
      
      rows = format_rows(response,flags)
      
      for row in rows:
        row['id'] = hash_id(row['keys'], row['search_date'])        
        all_rows.append(row)
      i = i+1 
      start = datetime.strptime(flags.end_date, date_format)

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

def format_rows(response,flags):
  if 'rows' not in response:
    print("%s google search data is empty......" %flags.start_date)
    rows = []
  else: 
    rows = response['rows']
    for row in rows:
      keys = ''
      if 'keys' in row:
        keys = u','.join(row['keys'])
        row['keys'] = keys
        row['search_date'] = flags.start_date
  return rows

if __name__ == '__main__':
  main()