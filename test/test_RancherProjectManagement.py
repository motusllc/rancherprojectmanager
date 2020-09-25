from kubernetes import config, watch
from kubernetes.client.models.v1_namespace import V1Namespace
from kubernetes.client.models.v1_object_meta import V1ObjectMeta
from kubernetes.client.models.v1_namespace_list import V1NamespaceList
import unittest
import logging
from unittest.mock import MagicMock, call
from RancherProjectManager import *

class TestRancherProjectManagement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.INFO, filename='/dev/null')

    def setUp(self):
        config.load_kube_config = MagicMock()
        watch.Watch = MagicMock()
        self.rancherMock = MagicMock()
        self.sut = RancherProjectManagement(self.rancherMock,
                'project-name-annotation',
                'project-id-annotation',
                'default-cluster',
                'cluster-name-annotation',
                'owners-annotation')
        self.sut.kubeapi = MagicMock()

class TestProcessNamespace(TestRancherProjectManagement):
    def test_no_annotations_noop(self):
        namespace = V1Namespace(metadata=V1ObjectMeta(name='mynamespace', annotations={
        }))

        self.sut.process_namespace(namespace)

        self.rancherMock.get_project.assert_not_called()
        self.rancherMock.create_project.assert_not_called()
        self.sut.kubeapi.patch_namespace.assert_not_called()

    def test_correct_annotations_just_verifies(self):
        namespace = V1Namespace(metadata=V1ObjectMeta(name='mynamespace', annotations={
            'project-name-annotation': 'my project',
            'project-id-annotation': 'p-123abc'
        }))
        self.rancherMock.get_project = MagicMock(return_value={ 'id': 'p-123abc' })

        self.sut.process_namespace(namespace)

        self.rancherMock.get_project.assert_called_once()
        self.rancherMock.get_project.assert_called_with('my project')
        self.rancherMock.create_project.assert_not_called()
        self.sut.kubeapi.patch_namespace.assert_not_called()

    def test_project_exists_write_pid_annotation(self):
        namespace = V1Namespace(metadata=V1ObjectMeta(name='mynamespace', annotations={
            'project-name-annotation': 'my project'
        }))
        self.rancherMock.get_project = MagicMock(return_value={ 'id': 'p-123abc' })

        self.sut.process_namespace(namespace)

        self.rancherMock.get_project.assert_called_once()
        self.rancherMock.get_project.assert_called_with('my project')
        self.rancherMock.create_project.assert_not_called()
        self.sut.kubeapi.patch_namespace.assert_called_once()
        self.sut.kubeapi.patch_namespace.assert_called_with('mynamespace', namespace)

        self.assertEqual(namespace.metadata.annotations['project-id-annotation'], 'p-123abc')

    def test_just_pid_annotation_leaves_it_alone(self):
        namespace = V1Namespace(metadata=V1ObjectMeta(name='mynamespace', annotations={
            'project-id-annotation': 'p-123abc'
        }))

        self.sut.process_namespace(namespace)

        self.rancherMock.get_project.assert_not_called()
        self.rancherMock.create_project.assert_not_called()
        self.sut.kubeapi.patch_namespace.assert_not_called()

    def test_project_not_found_creates_project(self):
        namespace = V1Namespace(metadata=V1ObjectMeta(name='mynamespace', annotations={
            'project-name-annotation': 'my project'
        }))
        self.rancherMock.get_project = MagicMock(return_value=None)
        self.rancherMock.create_project = MagicMock(return_value={ 'id': 'p-123abc' })

        self.sut.process_namespace(namespace)

        self.rancherMock.get_project.assert_called_once()
        self.rancherMock.get_project.assert_called_with('my project')
        self.rancherMock.create_project.assert_called_once()
        self.rancherMock.create_project.assert_called_with('my project', 'default-cluster')
        self.sut.kubeapi.patch_namespace.assert_called_once()
        self.sut.kubeapi.patch_namespace.assert_called_with('mynamespace', namespace)

        self.assertEqual(namespace.metadata.annotations['project-id-annotation'], 'p-123abc')

    def test_pid_wrong_write_pid_annotation(self):
        namespace = V1Namespace(metadata=V1ObjectMeta(name='mynamespace', annotations={
            'project-name-annotation': 'my project',
            'project-id-annotation': 'p-987xyz'
        }))
        self.rancherMock.get_project = MagicMock(return_value={ 'id': 'p-123abc' })

        self.sut.process_namespace(namespace)

        self.rancherMock.get_project.assert_called_once()
        self.rancherMock.get_project.assert_called_with('my project')
        self.rancherMock.create_project.assert_not_called()
        self.sut.kubeapi.patch_namespace.assert_called_once()
        self.sut.kubeapi.patch_namespace.assert_called_with('mynamespace', namespace)

        self.assertEqual(namespace.metadata.annotations['project-id-annotation'], 'p-123abc')

    def test_special_cluster_creates_project_in_special_cluster(self):
        namespace = V1Namespace(metadata=V1ObjectMeta(name='mynamespace', annotations={
            'project-name-annotation': 'my project',
            'cluster-name-annotation': 'my-other-cluster',
        }))
        self.rancherMock.get_project = MagicMock(return_value=None)
        self.rancherMock.create_project = MagicMock(return_value={ 'id': 'p-123abc' })

        self.sut.process_namespace(namespace)

        self.rancherMock.get_project.assert_called_once()
        self.rancherMock.get_project.assert_called_with('my project')
        self.rancherMock.create_project.assert_called_once()
        self.rancherMock.create_project.assert_called_with('my project', 'my-other-cluster')
        self.sut.kubeapi.patch_namespace.assert_called_once()
        self.sut.kubeapi.patch_namespace.assert_called_with('mynamespace', namespace)

        self.assertEqual(namespace.metadata.annotations['project-id-annotation'], 'p-123abc')

    def test_new_owner_annotation_adds_owner(self):
        namespace = V1Namespace(metadata=V1ObjectMeta(name='mynamespace', annotations={
            'project-name-annotation': 'my project',
            'project-id-annotation': 'p-123abc',
            'owners-annotation': 'jdoe',
        }))
        jane = RancherPrincipal({ 'id': 'jdoe', 'name': 'Jane Doe', 'principalType': 'user' })
        self.rancherMock.get_project = MagicMock(return_value={ 'id': 'p-123abc' })
        self.rancherMock.get_project_owners = MagicMock(return_value=[])
        self.rancherMock.search_principal = MagicMock(return_value=jane)
        self.rancherMock.add_project_owner = MagicMock()

        self.sut.process_namespace(namespace)

        self.rancherMock.get_project.assert_called_once()
        self.rancherMock.get_project.assert_called_with('my project')
        self.rancherMock.get_project_owners.assert_called_once()
        self.rancherMock.get_project_owners.assert_called_with('p-123abc')
        self.rancherMock.search_principal.assert_called_once()
        self.rancherMock.search_principal.assert_called_with('jdoe')
        self.rancherMock.add_project_owner.assert_called_once()
        self.rancherMock.add_project_owner.assert_called_with('p-123abc', jane)


    def test_second_owner_adds_new(self):
        namespace = V1Namespace(metadata=V1ObjectMeta(name='mynamespace', annotations={
            'project-name-annotation': 'my project',
            'project-id-annotation': 'p-123abc',
            'owners-annotation': 'aaardvark,jdoe',
        }))
        jane = RancherPrincipal({ 'id': 'jdoe', 'name': 'Jane Doe', 'principalType': 'user' })
        alex = RancherPrincipal({ 'id': 'aaardvark', 'name': 'Alex Aardvark', 'principalType': 'user' })
        self.rancherMock.get_project = MagicMock(return_value={ 'id': 'p-123abc' })
        self.rancherMock.search_principal = MagicMock()
        self.rancherMock.search_principal.side_effect = lambda x: jane if x == 'jdoe' else alex if x == 'aaardvark' else None
        self.rancherMock.get_project_owners = MagicMock(return_value=[ jane ])
        self.rancherMock.add_project_owner = MagicMock()

        self.sut.process_namespace(namespace)

        self.rancherMock.get_project.assert_called_once()
        self.rancherMock.get_project.assert_called_with('my project')
        self.rancherMock.get_project_owners.assert_called_once()
        self.rancherMock.get_project_owners.assert_called_with('p-123abc')
        self.assertEqual(self.rancherMock.search_principal.call_count, 2)
        self.rancherMock.search_principal.assert_has_calls([call('aaardvark'), call('jdoe')])
        self.rancherMock.add_project_owner.assert_called_once()
        self.rancherMock.add_project_owner.assert_called_with('p-123abc', alex)

    def test_change_second_owner_add_new_and_remove_old(self):
        namespace = V1Namespace(metadata=V1ObjectMeta(name='mynamespace', annotations={
            'project-name-annotation': 'my project',
            'project-id-annotation': 'p-123abc',
            'owners-annotation': 'aaardvark,ssmith',
        }))
        jane = RancherPrincipal({ 'id': 'jdoe', 'name': 'Jane Doe', 'principalType': 'user' })
        alex = RancherPrincipal({ 'id': 'aaardvark', 'name': 'Alex Aardvark', 'principalType': 'user' })
        sally = RancherPrincipal({ 'id': 'ssmith', 'name': 'Sally Smith', 'principalType': 'user' })
        self.rancherMock.get_project = MagicMock(return_value={ 'id': 'p-123abc' })
        self.rancherMock.search_principal = MagicMock()
        self.rancherMock.search_principal.side_effect = lambda x: sally if x == 'ssmith' else alex if x == 'aaardvark' else None
        self.rancherMock.get_project_owners = MagicMock(return_value=[ alex, jane ])
        self.rancherMock.add_project_owner = MagicMock()
        self.rancherMock.remove_project_owner = MagicMock()

        self.sut.process_namespace(namespace)

        self.rancherMock.get_project.assert_called_once()
        self.rancherMock.get_project.assert_called_with('my project')
        self.rancherMock.get_project_owners.assert_called_once()
        self.rancherMock.get_project_owners.assert_called_with('p-123abc')
        self.assertEqual(self.rancherMock.search_principal.call_count, 2)
        self.rancherMock.search_principal.assert_has_calls([call('aaardvark'), call('ssmith')])
        self.rancherMock.add_project_owner.assert_called_once()
        self.rancherMock.add_project_owner.assert_called_with('p-123abc', sally)
        self.rancherMock.remove_project_owner.assert_called_once()
        self.rancherMock.remove_project_owner.assert_called_with('p-123abc', jane)

    def test_unknown_owner_skips(self):
        namespace = V1Namespace(metadata=V1ObjectMeta(name='mynamespace', annotations={
            'project-name-annotation': 'my project',
            'project-id-annotation': 'p-123abc',
            'owners-annotation': 'aaardvark,jdoe',
        }))
        jane = RancherPrincipal({ 'id': 'jdoe', 'name': 'Jane Doe', 'principalType': 'user' })
        self.rancherMock.get_project = MagicMock(return_value={ 'id': 'p-123abc' })
        self.rancherMock.search_principal = MagicMock()
        self.rancherMock.search_principal.side_effect = lambda x: jane if x == 'jdoe' else None
        self.rancherMock.get_project_owners = MagicMock(return_value=[ jane ])
        self.rancherMock.add_project_owner = MagicMock()
        self.rancherMock.remove_project_owner = MagicMock()

        self.sut.process_namespace(namespace)

        self.rancherMock.get_project.assert_called_once()
        self.rancherMock.get_project.assert_called_with('my project')
        self.rancherMock.get_project_owners.assert_called_once()
        self.rancherMock.get_project_owners.assert_called_with('p-123abc')
        self.assertEqual(self.rancherMock.search_principal.call_count, 2)
        self.rancherMock.search_principal.assert_has_calls([call('aaardvark'), call('jdoe')])
        self.rancherMock.add_project_owner.assert_not_called()
        self.rancherMock.remove_project_owner.assert_not_called()

    def test_no_annotation_ignores_existing_owners(self):
        namespace = V1Namespace(metadata=V1ObjectMeta(name='mynamespace', annotations={
            'project-name-annotation': 'my project',
            'project-id-annotation': 'p-123abc',
        }))
        alex = RancherPrincipal({ 'id': 'aaardvark', 'name': 'Alex Aardvark', 'principalType': 'user' })
        sally = RancherPrincipal({ 'id': 'ssmith', 'name': 'Sally Smith', 'principalType': 'user' })
        self.rancherMock.get_project = MagicMock(return_value={ 'id': 'p-123abc' })
        self.rancherMock.get_project_owners = MagicMock(return_value=[ alex, sally ])
        self.rancherMock.add_project_owner = MagicMock()
        self.rancherMock.remove_project_owner = MagicMock()

        self.sut.process_namespace(namespace)

        self.rancherMock.get_project.assert_called_once()
        self.rancherMock.get_project.assert_called_with('my project')
        self.rancherMock.add_project_owner.assert_not_called()
        self.rancherMock.remove_project_owner.assert_not_called()

class TestWatch(TestRancherProjectManagement):
    def test_no_namespaces_does_nothing_and_watches(self):
        namespaces = V1NamespaceList(items=[])
        self.sut.kubeapi.list_namespace = MagicMock(return_value=namespaces)

        watchermock = MagicMock()
        watchermock.stream = MagicMock(return_value=[])
        watch.Watch = MagicMock(return_value=watchermock)

        self.sut.process_namespace = MagicMock()

        self.sut.watch()

        self.sut.process_namespace.assert_not_called()
        watchermock.stream.assert_called_once()
        watchermock.stream.assert_called_with(self.sut.kubeapi.list_namespace)

    def test_loops_over_initial_namespaces_and_watches(self):
        ns1 = V1Namespace(metadata=V1ObjectMeta(name='mynamespace'))
        ns2 = V1Namespace(metadata=V1ObjectMeta(name='mynamespace2'))
        namespaces = V1NamespaceList(items=[ ns1, ns2 ])
        self.sut.kubeapi.list_namespace = MagicMock(return_value=namespaces)
        
        watchermock = MagicMock()
        watchermock.stream = MagicMock(return_value=[])
        watch.Watch = MagicMock(return_value=watchermock)

        self.sut.process_namespace = MagicMock()

        self.sut.watch()

        self.assertEqual(self.sut.process_namespace.call_count, 2)
        self.sut.process_namespace.assert_has_calls([call(ns1), call(ns2)])
        watchermock.stream.assert_called_once()
        watchermock.stream.assert_called_with(self.sut.kubeapi.list_namespace)

    def test_loops_over_initial_namespaces_and_processes_MODIFIED_watch_hits(self):
        ns1 = V1Namespace(metadata=V1ObjectMeta(name='mynamespace'))
        ns2 = V1Namespace(metadata=V1ObjectMeta(name='mynamespace2'))
        namespaces = V1NamespaceList(items=[ ns1, ns2 ])
        self.sut.kubeapi.list_namespace = MagicMock(return_value=namespaces)
        
        watchermock = MagicMock()
        watchermock.stream = MagicMock(return_value=[
            { 'type': 'MODIFIED', 'object': ns2 },
            { 'type': 'DELETED', 'object': 'should not matter' },
            { 'type': 'MODIFIED', 'object': ns1 }
        ])
        watch.Watch = MagicMock(return_value=watchermock)

        self.sut.process_namespace = MagicMock()

        self.sut.watch()

        self.assertEqual(self.sut.process_namespace.call_count, 4)
        self.sut.process_namespace.assert_has_calls([call(ns1), call(ns2), call(ns2), call(ns1)])
        watchermock.stream.assert_called_once()
        watchermock.stream.assert_called_with(self.sut.kubeapi.list_namespace)

    def test_error_does_not_terminate_watch(self):
        ns1 = V1Namespace(metadata=V1ObjectMeta(name='mynamespace'))
        ns2 = V1Namespace(metadata=V1ObjectMeta(name='mynamespace2'))
        namespaces = V1NamespaceList(items=[ ns1, ns2 ])
        self.sut.kubeapi.list_namespace = MagicMock(return_value=namespaces)
        
        error_ns = V1Namespace(metadata=V1ObjectMeta(name='errornamespace'))
        watchermock = MagicMock()
        watchermock.stream = MagicMock(return_value=[
            { 'type': 'MODIFIED', 'object': ns2 },
            { 'type': 'MODIFIED', 'object': error_ns },
            { 'type': 'MODIFIED', 'object': ns1 }
        ])
        watch.Watch = MagicMock(return_value=watchermock)

        self.sut.process_namespace = MagicMock()
        self.sut.process_namespace.side_effect = lambda ns: exec('raise ValueError') if ns == error_ns else 0

        self.sut.watch()

        self.assertEqual(self.sut.process_namespace.call_count, 5)
        self.sut.process_namespace.assert_has_calls([call(ns1), call(ns2), call(ns2), call(error_ns), call(ns1)])
        watchermock.stream.assert_called_once()
        watchermock.stream.assert_called_with(self.sut.kubeapi.list_namespace)

if __name__ == '__main__':
    unittest.main()

