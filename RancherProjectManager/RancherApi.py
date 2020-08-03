import requests
from json.decoder import JSONDecodeError

class RancherApi:
    def __init__(self, address, key, secret):
        self.address = address
        self.key = key
        self.__secret = secret

    def get(self, path):
        url = self.address + path
        r = requests.get(url, auth = (self.key, self.__secret))

        r.raise_for_status()
        try:
            data = r.json()['data']
        except (JSONDecodeError, KeyError) as e: 
            raise RancherResponseError(url, r.content) from e
        return data

    def get_project(self, name):
        path = '/projects?name=' + name
        projects = self.get(path)

        if not isinstance(projects, list):
            raise RancherResponseError(self.address + path, projects)
        return next(iter(projects), None)

    def create_project(self, name, cluster):
        if name is None or cluster is None:
            raise TypeError("Project and cluster must not be None")
        
        clusters = self.get(f"/cluster?id={cluster}")
        if len(clusters) < 1:
            raise ValueError("No cluster by that name")
        
        cluster = clusters[0]
        if not 'id' in cluster:
            raise RancherResponseError(f"{self.address}/cluster?id={cluster}", clusters)

        cluster_id = cluster['id']
        r = requests.post(self.address + '/projects', auth = (self.key, self.__secret), 
                            data = { 'name': name, 'clusterId': cluster_id })
        r.raise_for_status()
        return r.json()

class RancherResponseError(Exception):
    def __init__(self, url, payload):
        super().__init__(f"Unexpected response content from rancher at {url}: {payload}")