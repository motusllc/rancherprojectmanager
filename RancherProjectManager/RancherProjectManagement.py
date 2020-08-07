from kubernetes import client, config, watch
import requests
import os
from .RancherApi import RancherResponseError

class RancherProjectManagement:
    def __init__(self, rancher, project_name_annotation, project_id_annotation, default_cluster, cluster_name_annotation):
        self.rancher = rancher
        self.project_name_annotation = project_name_annotation
        self.project_id_annotation = project_id_annotation
        self.default_cluster = default_cluster
        self.cluster_name_annotation = cluster_name_annotation
        if os.getenv('KUBERNETES_SERVICE_HOST'):
            config.load_incluster_config()
        else:
            config.load_kube_config()
        self.kubeapi = client.CoreV1Api()

    def watch(self):
        # Check 'em all at startup
        namespaces = self.kubeapi.list_namespace()
        for ns in namespaces.items:
            self.process_namespace(ns)

        # Watch for more changes going forward
        watcher = watch.Watch()
        for ns_event in watcher.stream(self.kubeapi.list_namespace):
            try:
                if ns_event['type'] == 'MODIFIED':
                    self.process_namespace(ns_event['object'])
            except (requests.HTTPError, RancherResponseError, ValueError, KeyError) as e:
                print("ERROR processing namespace event - raw event: " + str(ns_event))
                print(e)
            except Exception as e:
                print("FATAL ERROR processing namespace event - raw event: " + str(ns_event))
                print(e)
                raise

    def process_namespace(self, namespace):
        # We don't care if we don't see our annotation
        annotations = namespace.metadata.annotations
        if self.project_name_annotation not in annotations:
            return

        # Retrive the existing rancher project
        project_name = annotations[self.project_name_annotation]
        project = self.rancher.get_project(project_name)

        # Create the rancher project if necessary
        if project is None:
            print(f'Namespace {namespace.metadata.name} requested project named {project_name} which didn\'t exist, creating now')

            # Check if there's a special cluster we're supposed to use
            cluster = self.default_cluster
            if self.cluster_name_annotation in annotations:
                cluster = annotations[self.cluster_name_annotation]

            project = self.rancher.create_project(project_name, cluster)
        
        # We don't need to do anything if it's already annotated correctly
        project_id = project['id']
        if self.project_id_annotation in annotations and annotations[self.project_id_annotation] == project_id:
            return

        # Patch the project ID on there
        print(f'Annotating namespace {namespace.metadata.name} for requested project named {project_name} with its ID {project_id}')
        annotations[self.project_id_annotation] = project_id
        self.kubeapi.patch_namespace(namespace.metadata.name, namespace)