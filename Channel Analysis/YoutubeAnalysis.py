#Import GoogleApiClient for making API calls
import googleapiclient.discovery
import requests
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

#Api_Key
# api_key = 'AIzaSyC3JjC9Bib8t9uDC8kJ3NZ########'
api_key='AIzaSyDEWbHZKw1av7CEIYbiOKm27WIujUACck4'

#ChannelForAnalysis
channels = ['UCsTcErHg8oDvUnTzoqsYeNw','UCBJycsmduvYEL83R_U4JriQ','UCXuqSBlHAE6Xw-yeJA0Tunw','UCMiJRAwDNSNzuYeN2uWa0pA','UCXGgrKt94gR6lmN4aN3mYTg','UCVYamHliCI9rw1tHR1xbkfw',
            'UC9fSZHEh6XsRpX-xJc6lT3A','UCOhHO2ICt0ti9KAh-QHvttQ']

#ChannelData function send requests to youtube channel resource using list methods which 
#Returns a collection of zero or more channel resources that match the request criteria.
#Response is parsed and store in required format using list of dictionaries
def ChannelData(channels):
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)

    request = youtube.channels().list(part="snippet,contentDetails,statistics",id=','.join(channels))
    response = request.execute()
    
    Channel_data = []
    for items in response['items']:
        data = dict(
            Channel_name = items['snippet']['title'], 
            Channel_Created = items['snippet']['publishedAt'],
            Channel_country = items['snippet'].get('country'),
            Channel_uploads = items['contentDetails']['relatedPlaylists']['uploads'],
            Channel_viewcount = items['statistics']['viewCount'],
            Channel_subcount = items['statistics']['subscriberCount'],
            Channel_vidcount = items['statistics']['videoCount']

        )
        Channel_data.append(data)
    return Channel_data

#VideoMetaDetails Function extracts playlist id and calls VideoMetaData function on each playlistId to extract details of all videos of a 
#particular channel from youtube playlistitems resource and stores the parsed data in Master_Videolist 

def VideoMetaDetails(Channel_Data):
    
    Master_Videolist = []

    for items in Channel_Data:
        Video_data = VideoMetaData(items['Channel_uploads'])
        
        for i in range(len(Video_data)):
            for item in Video_data[i]['items']:
                data = dict(
                    Video_id = item["contentDetails"]["videoId"],
                    Video_published_date = item["contentDetails"]["videoPublishedAt"],
                    Channel_name = item["snippet"]["channelTitle"],
                    Video_description = item['snippet']["description"],
                    Video_position = item['snippet']["position"]
                    )
                Master_Videolist.append(data)
    return Master_Videolist

#VideoMetaData Function - Make api calls to PlaylistItems where PlaylistId from each channel is passed as an arguement by VideoMetaDetails function
#The function handles pagination using NextPageToken extracted from response
#Video details for each playlist in appended and Video_data list of all video details of all channels is returned to VideoMetaDetails function for data extraction

def VideoMetaData(Channel_uploads,page_token = None):
    Video_data = []
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
    request = youtube.playlistItems().list(
        part="snippet,contentDetails",
        maxResults=50,
        playlistId=Channel_uploads, 
        pageToken = page_token)
  
    response_playlist = request.execute()
    Video_data.append(response_playlist)

    #Set boolean flag Next as true, for pagination
    next = True
    #set next_page to NextPageToken 
    next_page = response_playlist['nextPageToken']
    

    while next:
        next_page = response_playlist.get('nextPageToken')
        

        #Set Next flag to false on None encounter of NextPageToken
        if next_page is None:
    
            next = False

        else:
        #Perform API call with NextPageToken passed as PageToken Filter parameter
         request = youtube.playlistItems().list(
            part="snippet,contentDetails",
            maxResults=50,
            playlistId=Channel_uploads, 
            pageToken = next_page)
         
        response_playlist = request.execute()
        Video_data.append(response_playlist)
     

    return Video_data

#Video_Details function makes api call for 50 VideoIds, VideoIds are passed as an arguement by GetVideoStats function
#Respective response is parsed and data is extracted for video Statistics
#Extracted video statistics details are returned as list datatype to GetVideoStats 
def Video_Details(video_id):
  Video_stats = []
  youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
  request = youtube.videos().list(part="snippet,contentDetails,statistics",
                                  id=','.join(video_id))
  response = request.execute()
  for item in response['items']:
    data = dict(
        Video_id = item['id'],
        Video_Channel_title = item['snippet'].get("channelTitle"),
        Stats_Comment = item['statistics'].get('commentCount'),
        Stats_Fav = item['statistics'].get("favoriteCount"),
        Stats_Like = item['statistics'].get("likeCount"),
        Stats_view =item['statistics'].get("viewCount")

    )
    Video_stats.append(data)
  
  return Video_stats

#GetVideoStats --- Extract VideoIDs length for a particular channel and pass VideoIds as arguement to Video_details function in batch of 50ids per call
#Recived response is converted to Dataframe and concatinated in batches of each individual channel video statistics
def GetVideoStats(Colname):
    limit = len(list(MasterVideoDF[MasterVideoDF['Channel_name'] == Colname]['Video_id']))
    MasterVideoStats = []
    for i in range(0,limit, 50):
        if i >= (limit - 50):
            Video_list = list(MasterVideoDF[MasterVideoDF['Channel_name'] == Colname ]['Video_id'])[i:limit]
        else:
            Video_list = list(MasterVideoDF[MasterVideoDF['Channel_name'] == Colname ]['Video_id'])[i:i+50]
        
        VideoStats = Video_Details(Video_list)
        MasterVideoStats.append(VideoStats)

    length_videostats = len(MasterVideoStats)
    for i in range(length_videostats):
        if i == 0 :
            MasterStatistics = pd.DataFrame(MasterVideoStats[i])
        else:
            MasterStatistics = pd.concat([MasterStatistics,pd.DataFrame(MasterVideoStats[i])])

    return MasterStatistics

print('Started')
#Set Channel_Data by passing channel ids to ChannelData Function
Channel_Data = ChannelData(channels)
Channel_DataDF = pd.DataFrame(Channel_Data)
Channel_DataDF.to_csv('C:/Users/USER/Desktop/Youtube/Channel-Analysis-using-Youtube-Data-API-main/ChannelData.csv')

#Set Master_Videolist by passing channel_data to VideoMetaDetails function
Master_Videolist = VideoMetaDetails(Channel_Data)

#Extract CSV 'VideoDetails' containing VideoIds and other metadata for videos of respective channels
MasterVideoDF = pd.DataFrame(Master_Videolist)
MasterVideoDF.to_csv('C:/Users/USER/Desktop/Youtube/Channel-Analysis-using-Youtube-Data-API-main/VideoDetails.csv')

#Call GetVideoStats function on each channel to get Video Statistics Details
VideoStatistics = pd.DataFrame()
for i in MasterVideoDF.Channel_name.unique():
  videodf = GetVideoStats(i)
  VideoStatistics = pd.concat([VideoStatistics,videodf])

#Extract CSV 'VideoStatistics' containing details on each video statistics
VideoStatistics.to_csv('C:/Users/USER/Desktop/Youtube/Channel-Analysis-using-Youtube-Data-API-main/VideoStatistics.csv')
print('Success')
