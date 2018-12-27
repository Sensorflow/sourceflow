import requests
import gzip as compressor
from unqlite import UnQLite
from itertools import chain, islice
import json
from datetime import datetime

def chunks(iterable, size=1000):
    iterator = iter(iterable)
    for first in iterator:
        yield chain([first], islice(iterator, size - 1))


def json_converter(o):
    if isinstance(o, bytes):
        return o.decode()
    if isinstance(o, datetime):
        return o.__str__()


class SinkflowClient(object):
    def __init__(self, api_key, host="nexus.sinkflow.com", secure=False, local_storage="sinkflow.db"):
        self.base_path = "{schema}://{host}/api".format(schema="https" if secure else "http", host=host)
        self.db = UnQLite(local_storage)
        self.collection = self.db.collection('r')
        if not self.collection.exists():
            self.collection.create()

        self.api_key = api_key

    def available(self):
        r = requests.get(self.base_path + "/status")
        return r.status_code == 200

    def sink(self, data):
        if "date" not in data:
            data["date"] = datetime.now().isoformat()
        else:
            data["date"] = data["date"].isoformat()
        self.collection.store(data)

    def dump(self, batch_size=1000):

        for chunk in chunks(self.collection.all(), size=batch_size):
            keys = []
            data = []
            for d in chunk:
                keys.append(d["__id"])
                del d["__id"]
                data.append(d)

            data = json.dumps(data, default=json_converter)

            d = compressor.compress(data.encode())
            headers = {
                'content-encoding': 'gzip',
                'authorization': 'Bearer :' + self.api_key
            }

            r = requests.post(self.base_path, data=d, headers=headers)
            if r.status_code == 200:
                for i in keys:
                    self.collection.delete(i)
            else:
                raise Exception(r.text)
