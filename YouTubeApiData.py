import os
import sys
import json
from util import DateParsing

import httplib2

from oauth2client import client
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow
from apiclient.discovery import build

CLIENT_SECRETS_FILE = "client_secrets.json"
SCOPE = "https://www.googleapis.com/auth/youtube.readonly"
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"
MISSING_MESSAGE = "You can't do anything since there is no client secrets file."
MAX_RESULTS = 20


class VideoData:
    require_auth = ["fileDetails", "processingDetails", "suggestions"]

    parts = ["contentDetails", "id", "localizations", "recordingDetails",
             "snippet", "statistics", "status", "topicDetails"]

    def __init__(self, store=None):
        """
        Get all metadata available for a video & dump all metadata to JSON files.
        :return:
        """

        if not store:
            store = sys.argv[0]

        self.current_page = None
        self.channel_id = ''
        self.playlist_id = ''

        self.current_results_file = os.path.join(store, "old_results.json")
        if os.path.exists(self.current_results_file):
            with open(self.current_results_file, "r") as f:
                results = json.load(f)
                self.current_page = results["current_page"]
                self.playlist_id = results["playlist_id"]

        flow = client.flow_from_clientsecrets(CLIENT_SECRETS_FILE, message=MISSING_MESSAGE,
                                              scope=SCOPE)

        storage = Storage(os.path.join(store, "-oauth2.json"))

        credentials = storage.get()

        if not credentials or credentials.invalid:
            flags = argparser.parse_args()
            credentials = run_flow(flow, storage, flags)

        self.youtube = build(API_SERVICE_NAME, API_VERSION, http=credentials.authorize(httplib2.Http()))
        self.get_ids_request = None

    def full_performance_search(self, performance, max_results=MAX_RESULTS, all_meta=False):

        videos = []

        if not self.channel_id:
            # get 'my uploaded videos' ID
            channel = self.youtube.channels().list(
                mine=True,
                part="snippet").execute()

            self.channel_id = channel["items"][0]["id"]

        # search for videos
        query = performance.artist_credit
        if performance.date_recorded:
            get_videos_request = self.youtube.search().list(
                channelId=self.channel_id,
                part="snippet",
                q = query,
                type="video",
                maxResults=max_results,
                publishedAfter=DateParsing.date_rfc(performance.date_recorded)
            )
        else:
            get_videos_request = self.youtube.search().list(
                channelId=self.channel_id,
                part="snippet",
                type="video",
                maxResults=max_results,
                q = query,
            )

        # while get_videos_request:
        videos_response = get_videos_request.execute()
        videos += videos_response['items']

            # get_videos_request = self.youtube.search().list_next(get_videos_request, videos_response)

        return videos

    def next_videos_meta(self, max_results=MAX_RESULTS, all_meta=False, meta=None):

        if not self.playlist_id:
            # get 'my uploaded videos' ID
            playlist = self.youtube.channels().list(
                mine=True,
                part="contentDetails").execute()

            self.playlist_id = playlist["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

        if not self.get_ids_request:
            # get playlistitems for video ids
            if self.current_page:
                self.get_ids_request = self.youtube.playlistItems().list(
                    part="contentDetails",
                    playlistId=self.playlist_id,
                    maxResults=max_results,
                    pageToken=self.current_page
                )
            else:
                self.get_ids_request = self.youtube.playlistItems().list(
                    part="contentDetails",
                    playlistId=self.playlist_id,
                    maxResults=max_results
                )

        while self.get_ids_request:
            ids_response = self.get_ids_request.execute()
            video_ids = [item["contentDetails"]["videoId"] for item in ids_response["items"]]

            videos = self.get_videos(video_ids, all_meta, meta)

            with open(self.current_results_file, "w+") as f:
                json.dump({"playlist_id": self.playlist_id, "current_page": self.current_page}, f)

            yield videos

            if "nextPageToken" in ids_response:
                self.current_page = ids_response["nextPageToken"]
            self.get_ids_request = self.youtube.playlistItems().list_next(self.get_ids_request, ids_response)

        raise StopIteration()

    def get_videos(self, ids, all_meta=False, meta=None):
        if meta:
            parts = meta
        elif all_meta:
            parts = self.parts + self.require_auth
        else:
            parts = self.parts

        videos_request = self.youtube.videos().list(
            id=", ".join(ids),
            part=", ".join(parts),
            maxResults=30
        )

        videos = videos_request.execute()

        return videos["items"]