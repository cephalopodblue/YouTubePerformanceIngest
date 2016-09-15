import datetime
import os

            
class ProcessLog:

    type_index = 0
    id_index = 1
    name_index = 2

    def __init__(self, output_dir):
        """
        Write log of performance & artist XML meta
        """
        self.log_dir = output_dir
        
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
        # set up log file:
        date_time = datetime.datetime
        now = date_time.now()
        
        self.log_file = os.path.join(self.log_dir, now.strftime("filewalker_log_%d-%m-%y-%H%M%S%f.txt"))
                        
        # to prevent duplicates, we'll keep a set of item codes
        self.glossaries = set([])
    
    def log_performance(self, performance):
        log_items = self.log_list(performance)
        if log_items:
            log_items.append(performance.id)
            log_items.append(performance.search_url)
            self.save_log(self.log_file, log_items)
    
    def log_artist(self, artist, group_members = []):
        logs = list()
        log = self.log_list(artist)
        if log:
            logs.append(log)
        for member in group_members:
            log = self.log_list(member)
            if log:
                logs.append(log)
        self.save_log(self.log_file, logs)
            
    def log_list(self, content):
        """
        Returns a list of the format
            <content.type>  <content.item_code> <content.name>
        """
        if content.item_code not in self.glossaries:
            log_items = [str(content.content_type), str(content.item_code), str(content.title)]
            return log_items
        return None
            
    def save_log(self, log_file, log_items):
        if len(log_items) > 0:
            with open(log_file, 'ab') as file:
                if isinstance(log_items[0], str):
                    log = "\t".join(log_items)
                    log += "\r\n"
                    file.write(log.encode('UTF-8'))
                else:
                    for log in log_items:
                        log = "\t".join(log)
                        log += "\r\n"
                        file.write(log.encode('UTF-8'))
                        
