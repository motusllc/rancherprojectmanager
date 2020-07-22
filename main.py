#!/usr/bin/env python3

from rancher import Rancher
from kubernetes import client, config, watch
import argparse

def main():
    parser = argparse.ArgumentParser(description='Watches and annotates namespaces to assign them to Rancher projects')
    parser.add_argument('-a', '--rancher-addr', required=True,
            help='Address of your rancher API. Include the protocol and API path element (ex. https://rancher.sandbox.motus.com/v3)')
    parser.add_argument('-k', '--rancher-key', required=True,
            help='The name of your rancher API key (username)')
    parser.add_argument('-s', '--rancher-secret', default=None,
            help='The secret token of your rancher API key (password). If omitted, this can instead loaded from a secret mounted at /var/rancher-project-mgmt')
    parser.add_argument('-t', '--project-name-annotation',
            default='rancher-project-mgmt.motus.com/project-name',
            help='The namespace annotation that this controller will check for and act upon')
    parser.add_argument('-i', '--project-id-annotation',
            default='field.cattle.io/projectId',
            help='The annotation, typically controlled by Rancher, that this controller will update to assign namespaces to projects')

    args = parser.parse_args()
    
    if args.rancher_secret is None:
        secret_file_handle = open("/var/rancher-project-mgmt/rancher-secret", "r")
        args.rancher_secret = secret_file_handle.read()
        secret_file_handle.close()

    rancher = Rancher(args.rancher_addr, args.rancher_key, args.rancher_secret)
    config.load_kube_config()
    kubeapi = client.CoreV1Api()
    watcher = watch.Watch()

    for ns_event in watcher.stream(kubeapi.list_namespace):
        # We don't care if it's not a modify event
        if ns_event['type'] != 'MODIFIED':
            continue
        
        # We don't care if we don't see our annotation
        ns = ns_event['object']
        annotations = ns.metadata.annotations
        if args.project_name_annotation not in annotations:
            continue

        # Retrive the existing rancher project
        project_name = annotations[args.project_name_annotation]
        project = rancher.get_project(project_name)

        # Create the rancher project if necessary
        if project is None:
            print(f'Namespace {ns.metadata.name} requested project named {project_name} which didn\'t exist, creating now')
            project = rancher.create_project(project_name, 'local')
        
        # We don't need to do anything if it's already annotated correctly
        project_id = project['id']
        if args.project_id_annotation in annotations and annotations[args.project_id_annotation] == project_id:
            continue

        # Patch the project ID on there
        print(f'Annotating namespace {ns.metadata.name} for requested project named {project_name} with its ID {project_id}')
        annotations[args.project_id_annotation] = project_id
        kubeapi.patch_namespace(ns.metadata.name, ns)

if __name__ == "__main__":
    main()