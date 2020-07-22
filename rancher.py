import requests

class Rancher:
    def __init__(self, address, key, secret):
        self.address = address
        self.key = key
        self.__secret = secret

    def get(self, path):
        r = requests.get(self.address + path, auth = (self.key, self.__secret))
        r.raise_for_status()
        return r.json()['data']

    def get_project(self, name):
        return next(iter(self.get('/projects?name=' + name)), None)

    def create_project(self, name, cluster):
        cluster_id = self.get(f"/cluster?id={cluster}")[0]['id']
        r = requests.post(self.address + '/projects', auth = (self.key, self.__secret), 
                            data = { 'name': name, 'clusterId': cluster_id })
        r.raise_for_status()
        return r.json()