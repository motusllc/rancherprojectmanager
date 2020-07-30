from kubernetes import client, config, watch

class RancherProjectManagement:
    def __init__(self, rancher, project_name_annotation, project_id_annotation, default_cluster, cluster_name_annotation):
        self.rancher = rancher
        self.project_name_annotation = project_name_annotation
        self.project_id_annotation = project_id_annotation
        self.default_cluster = default_cluster
        self.cluster_name_annotation = cluster_name_annotation
        config.load_kube_config()
        self.kubeapi = client.CoreV1Api()

    def watch(self):
        watcher = watch.Watch()

        for ns_event in watcher.stream(self.kubeapi.list_namespace):
            self.process_event(ns_event)

    def process_event(self, ns_event):
        # We don't care if it's not a modify event
        if ns_event['type'] != 'MODIFIED':
            return
        
        # We don't care if we don't see our annotation
        ns = ns_event['object']
        annotations = ns.metadata.annotations
        if self.project_name_annotation not in annotations:
            return

        # Retrive the existing rancher project
        project_name = annotations[self.project_name_annotation]
        project = self.rancher.get_project(project_name)

        # Create the rancher project if necessary
        if project is None:
            print(f'Namespace {ns.metadata.name} requested project named {project_name} which didn\'t exist, creating now')

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
        print(f'Annotating namespace {ns.metadata.name} for requested project named {project_name} with its ID {project_id}')
        annotations[self.project_id_annotation] = project_id
        self.kubeapi.patch_namespace(ns.metadata.name, ns)