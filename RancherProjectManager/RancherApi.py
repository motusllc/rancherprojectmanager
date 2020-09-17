import requests
import logging
import urllib.parse
from .RancherPrincipal import RancherPrincipal
from json.decoder import JSONDecodeError

class RancherApi:
    def __init__(self, address, key, secret):
        self.address = address
        self.key = key
        self.__secret = secret

    def _get(self, path):
        url = self.address + path
        logging.debug(f"Sending GET request to {url}...")
        r = requests.get(url, auth = (self.key, self.__secret))
        r.raise_for_status()
        try:
            data = r.json()
        except (JSONDecodeError, KeyError) as e: 
            raise RancherResponseError(url, r.content) from e
        logging.debug(f"GET request returned payload: {data}")
        return data

    def _post(self, path, body):
        logging.debug(f"Sending POST request to {url}...")
        url = self.address + path
        r = requests.post(url, auth = (self.key, self.__secret), json = body)
        r.raise_for_status()
        try:
            json_obj = r.json()
        except JSONDecodeError as e:
            raise RancherResponseError(url, r.content) from e
        logging.debug(f"POST request returned payload: {json_obj}")
        return json_obj

    def _delete(self, path):
        url = self.address + path
        logging.debug(f"Sending DELETE request to {url}...")
        r = requests.delete(url, auth = (self.key, self.__secret))
        r.raise_for_status()
        try:
            json_obj = r.json()
        except JSONDecodeError as e:
            raise RancherResponseError(url, r.content) from e
        logging.debug(f"DELETE request returned payload: {json_obj}")
        return json_obj

    def get_project(self, name):
        path = '/projects?name=' + name
        projects = self._get(path)['data']

        if not isinstance(projects, list):
            raise RancherResponseError(self.address + path, projects)
        return next(iter(projects), None)

    def create_project(self, name, cluster):
        if name is None or cluster is None:
            raise TypeError("Project and cluster must not be None")
        
        clusters = self._get(f"/cluster?id={cluster}")['data']
        if len(clusters) < 1:
            raise ValueError("No cluster by that name")
        
        cluster = clusters[0]
        if not 'id' in cluster:
            raise RancherResponseError(f"{self.address}/cluster?id={cluster}", clusters)

        cluster_id = cluster['id']
        r = self._post('/projects', { 'name': name, 'clusterId': cluster_id })
        return r

    def search_principal(self, owner):
        if owner is None:
            raise TypeError("owner must not be None")

        response = self._post('/principals?action=search', { 'name': owner, 'principalType': None })
        try:
            matches = response['data']
        except KeyError as e:
            raise RancherResponseError('/principals?action=search', response) from e

        return RancherPrincipal(matches[0]) if len(matches) > 0 else None

    def get_project_owners(self, project_id):
        if project_id is None:
            raise TypeError("project_id must not be None")
        prtbs = self._get(f"/projectroletemplatebindings?projectId={project_id}&roleTemplateId=project-owner")['data']
        principals = []
        for prtb in prtbs:
            id = prtb['groupPrincipalId'] if prtb['groupPrincipalId'] is not None else prtb['userPrincipalId']
            url_safe_id = urllib.parse.quote_plus(id)

            try:
                principal = self._get(f"/principals/{url_safe_id}")
                principals.append(RancherPrincipal(principal))
            except requests.exceptions.HTTPError as e:
                logging.error('Encountered error attempting to retrieve security principal information, my auth token may not have the required access!')
                raise RancherResponseError(f"/principals/{url_safe_id}", None) from e
        return principals

    def add_project_owner(self, project_id, owner):
        if project_id is None or owner is None:
            raise TypeError("project_id and owner must not be None")

        id_key = 'groupPrincipalId' if owner.is_group else 'userPrincipalId'

        existing_owner_role_bindings = self._get(f"/projectroletemplatebindings?{id_key}={owner.id}&" + 
                                                    f"projectId={project_id}&" + 
                                                    "roleTemplateId=project-owner")['data']
        if len(existing_owner_role_bindings) > 0:
            return # Already good-to-go
        
        resp = self._post('/projectroletemplatebindings', { 
                                    'projectId': f"{project_id}", 
                                    id_key: owner.id,
                                    'roleTemplateId': 'project-owner' })
        return resp

    def remove_project_owner(self, project_id, owner):
        if project_id is None or owner is None:
            raise TypeError("project_id and owner must not be None")

        id_key = 'groupPrincipalId' if owner.is_group else 'userPrincipalId'

        existing_owner_role_bindings = self._get(f"/projectroletemplatebindings?{id_key}={owner.id}&" + 
                                                    f"projectId={project_id}&" + 
                                                    "roleTemplateId=project-owner")['data']
        if len(existing_owner_role_bindings) == 0:
            return # Already good-to-go
        
        resp = self._delete(f"/projectroletemplatebindings/{existing_owner_role_bindings[0]['id']}")
        return resp

class RancherResponseError(Exception):
    def __init__(self, url, payload):
        super().__init__(f"Unexpected response content from rancher at {url}: {payload}")