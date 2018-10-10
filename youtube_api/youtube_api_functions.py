import pandas as pd
import os
import inspect
import datetime



def write_local(df, filename, filedir):
    OUTDIR = filedir + '/out/'
    if not os.path.exists(OUTDIR):
        os.makedirs(OUTDIR)  
    df.to_csv(OUTDIR+filename+'.csv',index=False)


def playlists(youtube,config):
    items = []
    response = youtube.playlists().list(
        part='snippet,contentDetails',
        channelId=CHANNEL_ID,
        maxResults=50
    ).execute()

    items.extend(response['items'])

    while 'nextPageToken' in response.keys(): 
      response = youtube.playlists().list(
      	  part='snippet,contentDetails',
          channelId=CHANNEL_ID,
          maxResults=50,
          pageToken=response['nextPageToken']
      ).execute()     	
      items.extend(response['items'])  
      
    index = 0
    columnName = ['playlistId','playlistName','publishedAt']
    df = pd.DataFrame(items, columns=columnName)
    for item in items:
      df.loc[index] = [item['id'],item['snippet']['title'],item['snippet']['publishedAt']]
      index = index+1
    
    fileName = inspect.stack()[0][3]
    write_local(df,fileName,config['root'])
    
    return df 


def playlist_video(youtube,playlist,config):
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'   
    all_videos = []

    for play in playlist:
      video = []

      response = youtube.playlistItems().list(
      	  part='snippet,contentDetails',
          maxResults=50,
          playlistId=play
      ).execute()
      
      video.extend(response['items'])

      while 'nextPageToken' in response.keys(): 
      	response = youtube.playlistItems().list(
        	part='snippet,contentDetails',
        	maxResults=50,
        	playlistId=play,
        	pageToken=response['nextPageToken']
        	).execute()
      	video.extend(response['items'])  
        
      all_videos.extend(video)
      
    
    columnName = ['videoId','videoName','description','playlistId','videoPublishedAt']
    df = pd.DataFrame(columns = columnName) 
    index = 0
    for item in all_videos:
      snippet = item["snippet"]
      df.loc[index] = [item["contentDetails"]["videoId"],snippet["title"],snippet["description"],snippet["playlistId"],snippet["publishedAt"]]
      index = index +1
    
    fileName = inspect.stack()[0][3]
    write_local(df, fileName, config['root'])
    
    return df   


def video(youtube,videos,config):
	columns = ['videoId','tags','categoryId','duration','viewCount','likeCount','dislikeCount','favoriteCount','commentCount']
	columns_sinppet = ['tags','categoryId']
	columns_content = ['duration']
	columns_stat = ['viewCount','likeCount','dislikeCount','favoriteCount','commentCount']

	columnName= ['videoId','tags','categoryId','duration','views','like','dislike','favorite','comment']
	df = pd.DataFrame(columns=columns)  
	index = 0

	for videoId in videos:
		response = youtube.videos().list(part='snippet,contentDetails,statistics',id=videoId).execute()

		snippet = response["items"][0]["snippet"]
		stat = response["items"][0]["statistics"]
		content = response["items"][0]["contentDetails"]

		df.at[index,'videoId'] = videoId

		for column in columns_sinppet:
			if column in snippet.keys():
				df.at[index, column] = snippet[column]
			else:
				df.at[index, column] = 0
		for column in columns_content:
			if column in content.keys():
				df.at[index, column] = content[column]
			else:
				df.at[index, column] = 0

		for column in columns_stat:
			if column in stat.keys():
				df.at[index, column] = stat[column]
			else:
				df.at[index, column] = 0
		index = index + 1
	df.columns = columnName

	fileName = inspect.stack()[0][3]
	write_local(df, fileName, config['root'])

	return df


def comment(youtube, videos, config):
  	all_comments = [] 
  	for videoId in videos:
  		try:
  			comment = []
  			response = youtube.commentThreads().list(
  				part='snippet,replies',
            		videoId = videoId, 
            		maxResults = 50).execute()
  			comment.extend(response['items'])
  			while 'nextPageToken' in response.keys():
  				response = youtube.commentThreads().list(
              		part='snippet,replies',
              		videoId = videoId, 
              		maxResults = 50,
              		pageToken=response['nextPageToken']).execute()
  				comment.extend(response['items'])
  			all_comments.append(comment)
  		except:
  			pass

  	columnName = ['commentId','totalReplyCount','authorChannelId','authorUrl','authorName','comment','likes','publishedAt','updatedAt','videoId']
  	df = pd.DataFrame(columns=columnName)
  	index = 0
  	count = 0
  	for video_comments in all_comments:
  		count=count+1
  		for one_comment in video_comments:
  			topcomment = one_comment["snippet"]["topLevelComment"]
  			snippet = topcomment["snippet"]
  			
  			df.loc[index] = [topcomment['id'],one_comment['snippet']['totalReplyCount'],snippet['authorChannelId']['value'],snippet['authorChannelUrl'],snippet['authorDisplayName'],snippet['textDisplay'],snippet['likeCount'],snippet['publishedAt'],snippet['updatedAt'],snippet['videoId']]
  			index = index +1
  	fileName = inspect.stack()[0][3]
  	write_local(df, fileName, config['root'])
  	return df


def reply(youtube,topcomments,config):
    all_replies = []
    
    for index, row in topcomments.iterrows():
        if row.totalReplyCount>0:
            response = youtube.comments().list(part='snippet', parentId=row.commentId, maxResults=50).execute()
            all_replies.extend(response["items"])
        
            while 'nextPageToken' in response.keys():
                response = youtube.comments().list(part='snippet', parentId=row['commentId'], 
                                                   maxResults=50, pageToken=response['nextPageToken']).execute()
                all_replies.extend(response["items"])
        else:
          continue

    columnName = ['replyId','authorName','authorChannelUrl','authorChannelId',
    			  'reply','likes','publishedAt','updatedAt','commentId']
    df = pd.DataFrame(columns=columnName)
    index = 0

    for reply in all_replies:
        snippet = reply['snippet']
        df.loc[index] = [reply['id'],snippet['authorDisplayName'],snippet['authorChannelUrl'],
                         snippet['authorChannelId']['value'],snippet['textDisplay'],
                         snippet['likeCount'],snippet['publishedAt'],snippet['updatedAt'],
                         snippet['parentId']]
        index = index +1

    fileName = inspect.stack()[0][3]
    write_local(df, fileName, config['root'])


def execute_api_request(client_library_function, **kwargs):
  response = client_library_function(
    **kwargs
  ).execute()
  return response


def channel_stat(youtube,config):
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    response = execute_api_request(
        youtube.reports().query,
        ids='channel==UClIFqsmxnwVNNlsvjH1D1Aw', 
        startDate='2007-10-29',
        endDate=datetime.datetime.utcnow().strftime('%Y-%m-%d'),
        dimensions='day',
        metrics='views,estimatedMinutesWatched,averageViewDuration,comments,likes,dislikes,shares,subscribersGained,subscribersLost',
        sort='day'
  )

    columnHeaders = response['columnHeaders']
    columnName = list(column['name'] for column in columnHeaders)
    df = pd.DataFrame(response['rows'],columns=columnName)

    fileName = inspect.stack()[0][3]
    write_local(df, fileName, config['root'])
