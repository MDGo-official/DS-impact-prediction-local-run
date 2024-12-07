import os
import glob
import json

class JsonService:
    def __init__(self, source_path=None, output_path=None,fields=None):
        self.input_path=source_path
        self.output_path=output_path
        self.fields=fields

    def read(self):
        event_list = []
        files = glob.glob(os.path.join(self.input_path,'*.json'))
        for f in files:
            j = LoadJsonFromFile(f)
            event_list.append(j)
        return event_list

    def dump(self, dir, event, data):
        with open(os.path.join(dir, event + '_dump.json'), 'w') as fout:
            json.dump(data, fout, indent=2, ensure_ascii=False)

    @staticmethod
    def LoadJsonFromFile(filename):
        err = ValueError(f"Failed to load json from file: {filename}")
        try:
            with open(filename, 'r') as file:
                return json.load(file, encoding='utf-8')
        except:
            raise err
