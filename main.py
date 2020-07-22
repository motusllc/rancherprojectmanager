import requests
import pprint
from kubernetes import client, config, watch
import os

project_name_annotation = 'rancher-project-mgmt.motus.com/project-name'
project_id_annotation = 'field.cattle.io/projectId'

rancher_addr = 'https://' + os.environ['RANCHER_ADDR'] + '/v3'
rancher_key = os.environ['RANCHER_KEY']
rancher_secret = os.environ['RANCHER_SECRET']

def rancher_get(path):
    r = requests.get(rancher_addr + path, auth = (rancher_key, rancher_secret))
    return r.json()['data']

def create_project(project_name):
    cluster_id = rancher_get('/cluster?id=local')[0]['id']
    r = requests.post(rancher_addr + '/projects', auth = (rancher_key, rancher_secret), 
                        data = { 'name': project_name, 'clusterId': cluster_id })
    return r.json()

def main():
    config.load_kube_config()
    kubeapi = client.CoreV1Api()
    watcher = watch.Watch()
    for ns_event in watcher.stream(kubeapi.list_namespace):
        if ns_event['type'] != 'MODIFIED':
            continue
        
        ns = ns_event['object']
        annotations = ns.metadata.annotations
        if project_name_annotation not in annotations:
            continue

        project_name = annotations[project_name_annotation]
        project = next(iter(rancher_get('/projects?name=' + project_name)), None)

        if project is None:
            print(f'Namespace {ns.metadata.name} requested project named {project_name} which didn\'t exist, creating now')
            project = create_project(project_name)
        
        project_id = project['id']
        if project_id_annotation in annotations and annotations[project_id_annotation] == project_id:
            continue

        print(f'Annotating namespace {ns.metadata.name} for requested project named {project_name} with its ID {project_id}')
        annotations[project_id_annotation] = project_id
        kubeapi.patch_namespace(ns.metadata.name, ns)

if __name__ == "__main__":
    main()