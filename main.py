#!/usr/bin/env python3

from RancherProjectManager import *
import argparse
import logging

def main():
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description='Watches and annotates namespaces to assign them to Rancher projects',
                                        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-a', '--rancher-addr', required=True,
            help='Address of your rancher API. Include the protocol and API path element (ex. https://rancher.sandbox.motus.com/v3)')
    parser.add_argument('-k', '--rancher-key', required=True,
            help='The name of your rancher API key (username)')
    parser.add_argument('-s', '--rancher-secret', default=None,
            help='The secret token of your rancher API key (password). If omitted, this can instead loaded from a secret mounted at /var/rancher-project-mgmt')
    parser.add_argument('-t', '--project-name-annotation',
            default='rancher-project-mgmt.motus.com/project-name',
            help='The namespace annotation that this controller will check for and act upon')
    parser.add_argument('-p', '--project-id-annotation',
            default='field.cattle.io/projectId',
            help='The annotation, typically controlled by Rancher, that this controller will update to assign namespaces to projects')
    parser.add_argument('-d', '--default-cluster',
            default='local',
            help='The name of the cluster that new projects will be created in, by default')
    parser.add_argument('-c', '--cluster-name-annotation',
            default='rancher-project-mgmt.motus.com/cluster-name',
            help='The annotation used to specify what cluster a project should be created in, if it doesn\'t already exist')
    parser.add_argument('-o', '--owners-annotation',
            default='rancher-project-mgmt.motus.com/owners',
            help='The annotation that holds a comma-separated list of groups or usernames, who will be granted owner on the project for a namespace')

    args = parser.parse_args()
    
    if args.rancher_secret is None:
        rancher_key_file = '/var/rancher-project-mgmt/rancher-secret'
        logging.info(f'Loading rancher API key from {rancher_key_file}')
        secret_file_handle = open(rancher_key_file, "r")
        args.rancher_secret = secret_file_handle.read()
        secret_file_handle.close()

    logging.info('Starting up...')
    rancher = RancherApi(args.rancher_addr, args.rancher_key, args.rancher_secret)
    projectManager = RancherProjectManagement(rancher,
                            args.project_name_annotation,
                            args.project_id_annotation,
                            args.default_cluster,
                            args.cluster_name_annotation,
                            args.owners_annotation)
    projectManager.watch()

if __name__ == "__main__":
    main()