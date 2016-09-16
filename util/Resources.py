import difflib
import re
import urllib
import uuid
import unicodedata
import os

import musicbrainzngs as ngs

from util import DateParsing

mb_search_url = "http://musicbrainz.org/search?query="
mb_search_terms = {"type": "artist", "method": "advanced"}

forbidden = ["!"]
url_forbidden = [":", "!", "\"", "+", "&"]

YOUTUBE_VIDEO_URL = "https://www.youtube.com/watch?v="
###########
#   this is only gonna work as long as the search-video-by-id url doesn't change
###########
YOUTUBE_UPLOADS_SEARCH_URL = "https://www.youtube.com/my_videos?o=U&sq=video_id%3A"
title_artist_dividor = " - "

recording_date_pattern = re.compile("recorded\s*")
CUTOFF = 0.4
ngs.set_useragent("hidat_audio_pipeline", "0.1")


__performances__ = dict()

class LplPerformance:
    max_tracks = 20
    edit_status = "uploaded"

    song_list = re.compile("\nSongs:")

    def __init__(self, element):
        self.videos = []
        self.full_performance = None

        edit = element["KEXPVideoEditStatus"]
        self.uploaded = False
        if edit:
            self.uploaded = edit.casefold() == self.edit_status

        self.recorded = element['KEXPDateRecorded']
        if self.recorded is not None:
            self.date_recorded = DateParsing.get_date(self.recorded)
        else:
            self.date_recorded = " "

        self.artist_credit, self.artist_id, self.num_tracks = None, None, 0

        if 'KEXPArtistCredit' in element:
            self.artist_credit = element['KEXPArtistCredit']
        self.lpl_item_code = element['ItemCode']
        if 'KEXPArtist' in element:
            self.artist_id = element['KEXPArtist']
        self.num_tracks = 0
        if 'KEXPTotalTracks' in element:
            self.num_tracks = int(element['KEXPTotalTracks'])
        self.tracks = [element['KEXPTrack0' + str(i)] if i < 10 else element['KEXPTrack' + str(i)]
                       for i in range(1,self.num_tracks)]

        self.mb_artist = None
        self.disambiguation = None
        self.mb_artists = dict()
        self.media_location = ""
        
    def find_file(self, root_dir):
        performances = os.listdir(root_dir)
        dir_name = self.artist_credit + " " + self.recorded
        matches = difflib.get_close_matches(dir_name, performances)
        self.media_location = os.path.join(root_dir, matches[0]) if len(matches) > 0 else ""
        
    def find_videos(self):
        if self.media_location:
            file_names = os.listdir(self.media_location)
            media = []
            for track in self.videos:
                matches = difflib.get_close_matches(track.file_name, file_names)
                if len(matches) > 0:
                    media.append(os.path.join(self.media_location, track.file_name))
            print([asciify(i) for i in media])
        
    def artist_search(self):
        try:
            if self.artist_credit not in self.mb_artists:
                query = artist_query_prep(self.artist_credit)
                mb_results = ngs.search_artists(query=query, limit=5)['artist-list']

                if len(mb_results) > 0:
                    artists = {a["name"]: a for a in mb_results}
                    a_name = difflib.get_close_matches(self.artist_credit, artists.keys(), cutoff=CUTOFF)[0]
                    if len(artists) < len(mb_results):
                        for a in mb_results:
                            if a["name"] == a_name:
                                artist = a
                                break
                    else:
                        artist = artists[a_name]
                    self.set_artist(artist)
            else:
                self.mb_artist = self.mb_artists[self.artist_credit]
                self.set_artist(self.mb_artist)

        except ngs.NetworkError:
            print('whoooops')

    def add_video(self, video_data):
        v = Video(video_data)

        title_norm = unicodedata.normalize('NFKD', v.video_title).casefold()
        artist_norm = unicodedata.normalize('NFKD', self.artist_credit).casefold()

        print(asciify(v.title))
        for t in self.tracks:
            track_norm = unicodedata.normalize('NFKD', t).casefold()
            if track_norm in title_norm and v.recorded == self.date_recorded:
                v.performance_title = t
                self.videos.append(v)
                return True
        if v.recorded == self.date_recorded and artist_norm in title_norm:
            v = FullPerformanceVideo(video_data)
            v.performance_title = "Full Performance"
            self.videos.append(v)
            return True
        return False

    def set_artist_id(self, mbid):
        video = self.videos[0]
        video.set_artist_id(mbid)
        self.artist_id = video.artist_id
        self.disambiguation = video.disambiguation
        for v in self.videos:
            v.set_artist(self.mb_artist)

    def set_artist(self, artist):
        if artist:
            self.mb_artist = artist
            self.disambiguation = ""
            if "disambiguation" in artist:
                self.disambiguation += artist["disambiguation"]
            else:
                if "area" in artist:
                    self.disambiguation += artist["area"]["name"] + " "
                if "type" in artist:
                    self.disambiguation += artist["type"] + " "
                if "life-span" in artist:
                    alive = artist["life-span"]
                    if "begin" in alive:
                        self.disambiguation += alive["begin"] + "-"
                    if "end" in alive:
                        self.disambiguation += alive["end"]
            self.artist_id = artist["id"]
            self.mb_artists[self.artist_credit] = artist
        for v in self.videos:
            v.set_artist(self.mb_artist)

    def mb_artist_search(self):
        return self.videos[0].mb_artist_search()


def get_performance(video):
    """
    Get the performance (videos by the same artist recorded on the same day, for now)
    that the video belongs to.
    """
    v = Video(video)
    if (v.title_artist, v.recorded) in __performances__:
        __performances__[(v.title_artist, v.recorded)].add_video(v)
    else:
        __performances__[(v.title_artist, v.recorded)] = FullPerformance(v)

    return __performances__[(v.title_artist, v.recorded)]


# class FullPerformance:
#     def __init__(self, video):
#         self.item_code = str(uuid.uuid4())
#         self.videos = [video]
#         self.title_artist, self.artist = video.title_artist, video.artist
#         self.mb_artist = video.mb_artist
#         self.artist_id = video.artist_id
#         self.recorded = video.recorded
#         self.disambiguation = video.disambiguation
#
#     def add_video(self, video):
#         self.videos.append(video)
#         self.set_artist(self.mb_artist)
#
#     def remove_video(self, videos):
#         videos.sort()
#         j = 0
#         removed_videos = []
#         for i in videos:
#             i -= j
#             removed_videos.append(self.videos.pop(i))
#             j += 1
#         return removed_videos
#
#     def artist_search(self):
#         self.videos[0].artist_search()
#         self.set_artist(self.videos[0].mb_artist)
#
#     def set_artist_id(self, mbid):
#         video = self.videos[0]
#         video.set_artist_id(mbid)
#         self.artist = video.artist
#         self.mb_artist = video.mb_artist
#         self.artist_id = video.artist_id
#         self.disambiguation = video.disambiguation
#         for v in self.videos:
#             v.set_artist(self.mb_artist)
#
#     def set_artist(self, artist):
#         video = self.videos[0]
#         video.set_artist(artist)
#         self.mb_artist = video.mb_artist
#         self.artist = video.artist
#         self.artist_id = video.artist_id
#         self.disambiguation = video.disambiguation
#         for v in self.videos:
#             v.set_artist(self.mb_artist)
#
#     def mb_artist_search(self):
#         return self.videos[0].mb_artist_search()

class Video:

    mb_artists = {}
    content_type = "KEXP Live Performance Track Video"

    def __init__(self, video):
        self.item_code = str(uuid.uuid4())
        snip = video["snippet"]
        self.video_title = snip["title"]
        self.description = snip["description"]
        self.category = ""
        if "categoryId" in snip:
            self.category = snip["categoryId"]
        self.published = snip["publishedAt"]

        self.status = ""
        if "status" in video:
            self.status = video["status"]["privacyStatus"]
        try:
            self.id = video['id']['videoId']
        except TypeError:
            self.id = video["id"]
        self.item_code = self.id
        self.url = YOUTUBE_VIDEO_URL + self.id
        self.search_url = YOUTUBE_UPLOADS_SEARCH_URL + self.id
        parsed_title = self.video_title.split(title_artist_dividor)
        self.title_artist, self.title, self.artist = "", "", ""
        try:
            self.file_name = video["fileDetails"]["fileName"]
        except KeyError:
            self.file_name = ""
        self.mb_artist = None
        self.artist_id = None
        self.disambiguation = ""
        self.whoops = False
        self.performance_title = ""

        self.recorded = DateParsing.get_date(snip["description"])

        if len(parsed_title) > 0:
            self.title_artist = parsed_title[0]
        if len(parsed_title) > 1:
            self.title = parsed_title[1]
        if len(parsed_title) > 2:
            self.whoops = True

    def artist_search(self):
        try:
            if self.title_artist not in self.mb_artists:
                query = artist_query_prep(self.title_artist)
                mb_results = ngs.search_artists(query=query, limit=5)['artist-list']

                if len(mb_results) > 0:
                    artists = {a["name"]: a for a in mb_results}
                    a_name = difflib.get_close_matches(self.title_artist, artists.keys(), cutoff=CUTOFF)[0]
                    if len(artists) < len(mb_results):
                        for a in mb_results:
                            if a["name"] == a_name:
                                artist = a
                                break
                    else:
                        artist = artists[a_name]
                    self.set_artist(artist)
            else:
                self.mb_artist = self.mb_artists[self.title_artist]
                self.set_artist(self.mb_artist)

        except ngs.NetworkError:
            print('whoooops')

    def set_artist_id(self, mbid):
        if is_mbid(mbid):
            try:
                artist_meta = ngs.get_artist_by_id(mbid)
                artist = artist_meta["artist"]
                self.set_artist(artist)
            except ngs.ResponseError as e:
                raise e
            except ngs.NetworkError as e:
                raise e

    def set_artist(self, artist):
        if artist:
            self.mb_artist = artist
            self.artist = artist["name"]
            self.disambiguation = ""
            if "disambiguation" in artist:
                self.disambiguation += artist["disambiguation"]
            else:
                if "area" in artist:
                    self.disambiguation += artist["area"]["name"] + " "
                if "type" in artist:
                    self.disambiguation += artist["type"] + " "
                if "life-span" in artist:
                    alive = artist["life-span"]
                    if "begin" in alive:
                        self.disambiguation += alive["begin"] + "-"
                    if "end" in alive:
                        self.disambiguation += alive["end"]
            self.artist_id = artist["id"]
            self.mb_artists[self.title_artist] = artist

    def mb_artist_search(self):
        query = artist_query_prep(self.title_artist)
        for r in url_forbidden:
            rep = "%s%s" %("%", hex(ord(r))[2:])
            query = query.replace(r, rep)
        query = query.replace(" ", "+")
        search_url = "%s%s&%s" %( mb_search_url, query, urllib.parse.urlencode(mb_search_terms) )
        return search_url

    def file_search(self):
        # need: list of possible folder locations
        locations = []
        possible_file_names = [self.video_title, self.file_name]
        folder_name_elements = [self.artist, self.recorded]
        found = []

        for location in locations:
            folders = []
            for root, dirs, files in os.walk(location):
                # go over directories, looking for artist
                for d in dirs:
                    match = True
                    for element in folder_name_elements:
                        match = match and element in d
                    if match:
                        folders.append(os.path.join(root, d))
            # go over potential folders, looking for video title or file name
            for f in folders:
                for file_name in possible_file_names:
                    found += [os.path.join(f, m) for m in difflib.get_close_matches(file_name, os.listdir(f))]


class FullPerformanceVideo(Video):

    content_type = "KEXP Live Performance Full Performance Video"


def artist_query_prep(artist):
    for r in forbidden:
        replacement = "%s%s" % ("%", hex(ord(r))[2:])
        a = artist.replace(r, replacement)
    # possible errors in spacing - replace whitespace w/ wildcard characters
    query = "%s \"%s\"" % (artist, artist)
    return query


def is_mbid(mbid):
    """
    Check that 's' looks like an MBID
    """
    try:
        mbid = uuid.UUID(mbid)
        good = True
    except ValueError as e:
        good = False
    except AttributeError:
        good = False

    return good


def asciify(string):
    s = unicodedata.normalize('NFKD', string).encode('ascii', 'ignore').decode()
    return s