from kubernetes import client, config, watch
from kubernetes.client.models.v1_namespace import V1Namespace
import logging
import requests
from typing import List
import os
from .RancherApi import RancherApi, RancherResponseError

class RancherProjectManagement:
    def __init__(self, rancher: RancherApi, project_name_annotation: str, project_id_annotation: str, default_cluster: str, cluster_name_annotation: str, owners_annotation: str, workload_managers_annotation: str):
        self.rancher = rancher
        self.project_name_annotation = project_name_annotation
        self.project_id_annotation = project_id_annotation
        self.default_cluster = default_cluster
        self.cluster_name_annotation = cluster_name_annotation
        self.owners_annotation = owners_annotation
        self.workload_managers_annotation = workload_managers_annotation
        if os.getenv('KUBERNETES_SERVICE_HOST'):
            config.load_incluster_config()
        else:
            config.load_kube_config()
        self.kubeapi = client.CoreV1Api()

    def watch(self):
        # Check 'em all at startup
        logging.info("Checking all namespaces")
        namespaces = self.kubeapi.list_namespace()
        for ns in namespaces.items:
            self.process_namespace(ns)

        # Watch for more changes going forward
        logging.info("Watching for additional namespace changes")
        watcher = watch.Watch()
        for ns_event in watcher.stream(self.kubeapi.list_namespace):
            try:
                if ns_event['type'] == 'MODIFIED':
                    self.process_namespace(ns_event['object'])
            except (requests.HTTPError, RancherResponseError, ValueError, KeyError) as e:
                logging.exception("ERROR processing namespace event - raw event: " + str(ns_event))
            except Exception as e:
                logging.exception("FATAL ERROR processing namespace event - raw event: " + str(ns_event))
                raise

    def process_namespace(self, namespace: V1Namespace):
        logging.info(f'Inspecting namespace {namespace.metadata.name}...')

        # We don't care if we don't see our annotation
        annotations = namespace.metadata.annotations
        if self.project_name_annotation not in annotations:
            return

        # Retrive the existing rancher project
        project_name = annotations[self.project_name_annotation]
        project = self.rancher.get_project(project_name)

        # Create the rancher project if necessary
        if project is None:
            logging.info(f'Namespace {namespace.metadata.name} requested project named {project_name} which didn\'t exist, creating now')

            # Check if there's a special cluster we're supposed to use
            cluster = self.default_cluster
            if self.cluster_name_annotation in annotations:
                cluster = annotations[self.cluster_name_annotation]

            project = self.rancher.create_project(project_name, cluster)

        project_id = project['id']

        # Add/remove project owner(s)
        if self.owners_annotation in annotations:
            self.handle_project_role(namespace.metadata.name, project_id, 'project-owner', annotations[self.owners_annotation].split(','))

        # Add/remove workload managers(s)
        if self.workload_managers_annotation in annotations:
            self.handle_project_role(namespace.metadata.name, project_id, 'workloads-manage', annotations[self.workload_managers_annotation].split(','))
        
        # We don't need to do anything else if it's already annotated correctly
        if self.project_id_annotation in annotations and annotations[self.project_id_annotation] == project_id:
            return

        # Patch the project ID on there
        logging.info(f'Annotating namespace {namespace.metadata.name} for requested project named {project_name} with its ID {project_id}')
        annotations[self.project_id_annotation] = project_id
        self.kubeapi.patch_namespace(namespace.metadata.name, namespace)
    
    def handle_project_role(self, namespace: str, project_id: str, rolename: str, members: List[str]):
        resolved_members = []
        for member in members:
            resolved_member = self.rancher.search_principal(member)
            if resolved_member is None:
                logging.warning(f'Could not find a user or group in Rancher matching \"{member}\" for namespace {namespace}')
                continue
            resolved_members.append(resolved_member)
        existing_members = self.rancher.get_project_members(project_id, rolename)
        
        new_members = set(resolved_members).difference(existing_members)
        old_members = set(existing_members).difference(resolved_members)

        for member in new_members:
            resp = self.rancher.add_project_member(project_id, rolename, member)
            logging.info(f'Added {member.type} {member.name} as an owner for project {project_id} over namespace {namespace}')

        for member in old_members:
            resp = self.rancher.remove_project_member(project_id, rolename, member)
            logging.info(f'Removed {member.type} {member.name} as an owner for project {project_id} over namespace {namespace}')