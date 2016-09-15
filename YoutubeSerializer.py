import os
import os.path as path

from yattag import Doc, indent

from util import Log


class PerformanceSerializer:
    def __init__(self, output_dir):
        self.performance_meta_dir = os.path.join(output_dir, "performances")
        self.full_performance_meta_dir = os.path.join(output_dir, "full_performance")
        if not os.path.exists(self.full_performance_meta_dir):
            os.makedirs(self.full_performance_meta_dir)
        if not os.path.exists(self.performance_meta_dir):
            os.makedirs(self.performance_meta_dir)

    def save_full_performance(self, performance, video):
        """
        Create an XML file of performance metadata that Dalet will be happy with

        """
        doc, tag, text = Doc().tagtext()

        output_dir = self.full_performance_meta_dir

        #self.logs.log_performance(performance)

        doc.asis('<?xml version="1.0" encoding="UTF-8"?>')
        with tag('titles'):
            with tag('title'):
                name = '_'.join([performance.artist_credit, performance.recorded, video.performance_title])
                with tag('Name'):
                    text(name)
                dist_cat = '_'.join([performance.recorded, performance.artist_credit])
                with tag('KEXPDistributionCategory'):
                    text(dist_cat)
                with tag('KEXPArtist'):
                    text(performance.artist_id)
                with tag('KEXPLivePerformance'):
                    text(str(performance.lpl_item_code))
                with tag('KEXPContentType'):
                    text(video.content_type)
                with tag('KEXPArtistCredit'):
                    text(performance.artist_credit)
                # with tag('Title'):
                #     text(performance.title)
                # with tag('KEXPYouTubeId'):
                #     text(performance.id)
                # with tag('KEXPYouTubeURL'):
                #     text(performance.url)
                # with tag('KEXPYoutubeTitle'):
                #     text(performance.video_title)

        formatted_data = indent(doc.getvalue())
        output_file = path.join(output_dir, video.item_code + ".xml")
        with open(output_file, "wb") as f:
            f.write(formatted_data.encode("UTF-8"))

    def save_performance(self, performance, video):
        """
        Create an XML file of performance metadata that Dalet will be happy with

        """
        doc, tag, text = Doc().tagtext()

        output_dir = self.performance_meta_dir

        #self.logs.log_performance(performance)

        doc.asis('<?xml version="1.0" encoding="UTF-8"?>')
        with tag('titles'):
            with tag('title'):
                name = '_'.join([performance.artist_credit, performance.recorded, video.performance_title])
                with tag('Name'):
                    text(name)
                dist_cat = '_'.join([performance.recorded, performance.artist_credit])
                with tag('KEXPDistributionCategory'):
                    text(dist_cat)
                with tag('KEXPArtist'):
                    text(performance.artist_id)
                with tag('KEXPLivePerformance'):
                    text(str(performance.lpl_item_code))
                with tag('KEXPContentType'):
                    text(video.content_type)
                with tag('KEXPArtistCredit'):
                    text(performance.artist_credit)

                # youtube-specific metadata - needs checking??
                with tag('KEXPYouTubeTitle'):
                    text(video.video_title)
                with tag('KEXPYouTubeCategory'):
                    text(video.category)
                with tag('KEXPYouTubeDescription'):
                    text(video.description)
                with tag('KEXPYouTubeStatus'):
                    text(video.status)
                    # with tag('Title'):
                    #     text(performance.title)
                    # with tag('KEXPYouTubeId'):
                    #     text(performance.id)
                    # with tag('KEXPYouTubeURL'):
                    #     text(performance.url)
                    # with tag('KEXPYoutubeTitle'):
                    #     text(performance.video_title)

        formatted_data = indent(doc.getvalue())
        output_file = path.join(output_dir, video.item_code + ".xml")
        with open(output_file, "wb") as f:
            f.write(formatted_data.encode("UTF-8"))


class TrackPerformanceSerializer:
    def __init__(self, output_dir):
        self.performance_meta_dir = os.path.join(output_dir, "performances")
        if not os.path.exists(self.performance_meta_dir):
            os.makedirs(self.performance_meta_dir)

    def save_performance(self, performance):
        """
        Create an XML file of performance metadata that Dalet will be happy with

        """
        doc, tag, text = Doc().tagtext()

        output_dir = self.performance_meta_dir

        self.logs.log_performance(performance)

        doc.asis('<?xml version="1.0" encoding="UTF-8"?>')
        with tag('titles'):
            with tag('title'):
                with tag('ItemCode'):
                    text(performance.item_code)
                with tag('Key1'):
                    text(performance.item_code)
                with tag('Title'):
                    text(performance.title)
                with tag('KEXPYouTubeId'):
                    text(performance.id)
                with tag('KEXPYouTubeURL'):
                    text(performance.url)
                with tag('KEXPVideoTitle'):
                    text(performance.video_title)

                with tag('KEXPArtist'):
                    text(performance.artist_id)
                with tag('KEXPArtistCredit'):
                    text(performance.artist)

                with tag('KEXPContentType'):
                    text(performance.content_type)

        formatted_data = indent(doc.getvalue())
        output_file = path.join(output_dir, performance.item_code + ".xml")
        with open(output_file, "wb") as f:
            f.write(formatted_data.encode("UTF-8"))

    def save_artist(self, artist, members):
        """
        Create an XML file of artist metadata that Dalet will be happy with.
        
        If the artist is a group that has multiple members, not an individual, 
        all member metadata (for artists new to this batch) will also be generated.
        
        :param artist: Processed metadata from MusicBrainz for 'main' artist
        :param members: Processed artist metadata from MusicBrainz for any members of 'artist'
        :param output_dir: Output directory to write XML file to
        """

        output_dir = self.artist_meta_dir
        
        # get metadata for artist and, if artist is a group
        # all group members (that have not yet had metadata generated this batch)
        
        self.logs.log_artist(artist, members)
        
        doc, tag, text = Doc().tagtext()

        doc.asis('<?xml version="1.0" encoding="UTF-8"?>')
        with tag('Titles'):
            for member in members:
                with tag('GlossaryValue'):
                    self.save_one_artist(member, tag, text)

            with tag('GlossaryValue'):
                self.save_one_artist(artist, tag, text)

                if artist.group_members:
                    for member in artist.group_members:
                        with tag('KEXPMember'):
                            text(member)

        formatted_data = indent(doc.getvalue())

        output_file = path.join(output_dir, 'a' + artist.item_code + ".xml")
        with open(output_file, "wb") as f:
            f.write(formatted_data.encode("UTF-8"))


    def save_one_artist(self, artist, tag, text):
        """
        Save the metadata for one artist

        :param artist: Processed artist metadata from MusicBrainz
        :param tag: Yattag 'tag' 
        :param text: Yattag 'text'
        """
        # mandatory fields
        with tag('Key1'):
            text(artist.item_code)
        with tag('ItemCode'):
            text(artist.item_code)
        with tag('title'):
            text(Util.stringCleanup(artist.title))
        with tag('GlossaryType'):
            text(artist.glossary_type)
        with tag('KEXPName'):
            text(artist.name)
        with tag('KEXPSortName'):
            text(artist.sort_name)
        with tag('KEXPMBID'):
            text(artist.id)
            
        # optional fields

        if len(artist.alias_list) > 0:
            for alias in artist.alias_list:
                with tag('KEXPAlias'):
                    text(alias)

        if artist.annotation > '':
                with tag('KEXPAnnotation'):
                    text(artist.annotation)

        if artist.disambiguation > '':
            with tag('KEXPDisambiguation'):
                text(artist.disambiguation)

        if artist.type > '':
            with tag('KEXPArtistType'):
                text(artist.type)
                
        with tag('KEXPBeginArea'):
            text(artist.begin_area.name)
        with tag('KEXPBeginAreaMBID'):
            text(artist.begin_area.id)

        with tag('KEXPBeginDate'):
            text(artist.begin_date)
        with tag('KEXPEndDate'):
            text(artist.end_date)
        if artist.ended:
            with tag('KEXPEnded'):
                text(artist.ended)

        with tag('KEXPCountry'):
            text(artist.country.name)
        with tag('KEXPCountryMBID'):
            text(artist.country.id)
            
        with tag('KEXPEndArea'):
            text(artist.end_area.name)
        with tag('KEXPEndAreaMBID'):
            text(artist.end_area.id)

        if len(artist.ipi_list) > 0:
            for code in artist.ipi_list:
                with tag('KEXPIPICode'):
                    text(code)

        if len(artist.isni_list) > 0:
            for code in artist.isni_list:
                with tag('KEXPISNICode'):
                    text(code)

        if len(artist.url_relation_list) > 0:
            for link in artist.url_relation_list:
                with tag('KEXPLink'):
                    text(link)