import unittest
from unittest.mock import MagicMock, call
from io import BytesIO
import requests
import logging
from RancherProjectManager import *

class TestRancherApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.INFO, filename='/dev/null')

    def setUp(self):
        requests.get = MagicMock()
        requests.post = MagicMock()
        self.sut = RancherApi('myaddress', 'mykey', 'mysecret')

class Test_Get(TestRancherApi):
    def test_returns_data(self):
        happy_response = requests.Response()
        happy_response.status_code = 200
        happy_response.raw = BytesIO(b"{\"data\":\"mydata\"}")
        requests.get = MagicMock(return_value=happy_response)

        response = self.sut._get('mypath')

        self.assertEqual('mydata', response['data'])
        requests.get.assert_called_once()
        requests.get.assert_called_with('myaddressmypath', auth = ("mykey", "mysecret"))

    def test_with_403_raises_err(self):
        denied_response = requests.Response()
        denied_response.status_code = 403
        requests.get = MagicMock(return_value=denied_response)
        with self.assertRaises(requests.HTTPError):
            response = self.sut._get("mypath")

    def test_with_500_raises_err(self):
        err_response = requests.Response()
        err_response.status_code = 500
        requests.get = MagicMock(return_value=err_response)
        with self.assertRaises(requests.HTTPError):
            response = self.sut._get("mypath")

    def test_returns_invalid_json_raises_err(self):
        invalid_response = requests.Response()
        invalid_response.status_code = 200
        invalid_response.raw = BytesIO(b"not json")
        requests.get = MagicMock(return_value=invalid_response)
        with self.assertRaises(RancherResponseError):
            response = self.sut._get("mypath")

class Test_Post(TestRancherApi):
    def test_returns_data(self):
        happy_response = requests.Response()
        happy_response.status_code = 200
        happy_response.raw = BytesIO(b"{\"data\":\"mydata\"}")
        requests.post = MagicMock(return_value=happy_response)
        payload = {'data': 'value'}

        response = self.sut._post('mypath', payload)

        self.assertEqual('mydata', response['data'])
        requests.post.assert_called_once()
        requests.post.assert_called_with('myaddressmypath',
                            auth = ("mykey", "mysecret"),
                            json = payload)
        
    def test_http_err_throws_err(self):
        sad_response = requests.Response()
        sad_response.status_code = 403
        requests.post = MagicMock(return_value=sad_response)
        payload = {'data': 'value'}

        with self.assertRaises(requests.exceptions.HTTPError):
            response = self.sut._post('mypath', payload)

        requests.post.assert_called_once()
        requests.post.assert_called_with('myaddressmypath',
                            auth = ("mykey", "mysecret"),
                            json = payload)

    def test_body_not_json_throws_err(self):
        malformed_response = requests.Response()
        malformed_response.status_code = 200
        malformed_response.raw = BytesIO(b"not a json")
        requests.post = MagicMock(return_value=malformed_response)
        payload = {'data': 'value'}

        with self.assertRaises(RancherResponseError):
            response = self.sut._post('mypath', payload)

        requests.post.assert_called_once()
        requests.post.assert_called_with('myaddressmypath',
                            auth = ("mykey", "mysecret"),
                            json = payload)

class Test_Delete(TestRancherApi):
    def test_returns_data(self):
        happy_response = requests.Response()
        happy_response.status_code = 200
        happy_response.raw = BytesIO(b"{\"data\":\"mydata\"}")
        requests.delete = MagicMock(return_value=happy_response)

        response = self.sut._delete('mypath')

        self.assertEqual('mydata', response['data'])
        requests.delete.assert_called_once()
        requests.delete.assert_called_with('myaddressmypath', auth = ("mykey", "mysecret"))

    def test_with_403_raises_err(self):
        denied_response = requests.Response()
        denied_response.status_code = 403
        requests.delete = MagicMock(return_value=denied_response)

        with self.assertRaises(requests.HTTPError):
            response = self.sut._delete("mypath")

    def test_returns_invalid_json_raises_err(self):
        invalid_response = requests.Response()
        invalid_response.status_code = 200
        invalid_response.raw = BytesIO(b"not json")
        requests.delete = MagicMock(return_value=invalid_response)
        with self.assertRaises(RancherResponseError):
            response = self.sut._delete("mypath")

class TestGetProject(TestRancherApi):
    def test_calls_get_with_project_arg(self):
        project = { 'name': 'My Project', 'id': 'p-asd123' }
        project_response = requests.Response()
        project_response.status_code = 200
        project_response.json = lambda: { 'data': [ project ] }
        requests.get = MagicMock(return_value=project_response)

        retVal = self.sut.get_project('My Project')

        self.assertEqual(project, retVal)
        requests.get.assert_called_once()
        requests.get.assert_called_with('myaddress/projects?name=My Project', auth = ("mykey", "mysecret"))

    def test_no_match_returns_none(self):
        empty_response = requests.Response()
        empty_response.status_code = 200
        empty_response.json = lambda: { 'data': [ ] }
        requests.get = MagicMock(return_value=empty_response)

        retVal = self.sut.get_project('My Project')

        self.assertEqual(None, retVal)
        requests.get.assert_called_once()
        requests.get.assert_called_with('myaddress/projects?name=My Project', auth = ("mykey", "mysecret"))

    def test_multiple_match_returns_first(self):
        project = { 'name': 'My Project', 'id': 'p-asd123' }
        project2 = { 'name': 'My Project', 'id': 'p-abc456' }
        empty_response = requests.Response()
        empty_response.status_code = 200
        empty_response.json = lambda: { 'data': [ project2, project ] }
        requests.get = MagicMock(return_value=empty_response)

        retVal = self.sut.get_project('My Project')

        self.assertEqual(project2, retVal)
        requests.get.assert_called_once()
        requests.get.assert_called_with('myaddress/projects?name=My Project', auth = ("mykey", "mysecret"))

    def test_not_list_raises_err(self):
        project = { 'name': 'My Project', 'id': 'p-asd123' }
        empty_response = requests.Response()
        empty_response.status_code = 200
        empty_response.json = lambda: { 'data': project }
        requests.get = MagicMock(return_value=empty_response)

        with self.assertRaises(RancherResponseError):
            response = self.sut.get_project('My Project')

        requests.get.assert_called_once()
        requests.get.assert_called_with('myaddress/projects?name=My Project', auth = ("mykey", "mysecret"))

class TestCreateProject(TestRancherApi):
    def test_none_name_raises_err(self):
        requests.get = MagicMock()
        requests.post = MagicMock()

        with self.assertRaises(TypeError):
            response = self.sut.create_project(None, "my cluster")

        requests.get.assert_not_called()
        requests.post.assert_not_called()

    def test_none_cluster_raises_err(self):
        requests.get = MagicMock()
        requests.post = MagicMock()

        with self.assertRaises(TypeError):
            response = self.sut.create_project("My project", None)

        requests.get.assert_not_called()
        requests.post.assert_not_called()

    def test_cluster_does_not_exist_raises_err(self):
        empty_response = requests.Response()
        empty_response.status_code = 200
        empty_response.json = lambda: { 'data': [] }
        requests.get = MagicMock(return_value=empty_response)
        requests.post = MagicMock()

        with self.assertRaises(ValueError):
            response = self.sut.create_project('My Project', 'My nonexistant cluster')

        requests.get.assert_called_once()
        requests.get.assert_called_with('myaddress/cluster?id=My nonexistant cluster', auth = ("mykey", "mysecret"))
        requests.post.assert_not_called()

    def test_cluster_malformed_raises_err(self):
        malformed_response = requests.Response()
        malformed_response.status_code = 200
        malformed_response.json = lambda: { 'data': [ { "not_an_id": "c-137" } ] }
        requests.get = MagicMock(return_value=malformed_response)
        requests.post = MagicMock()

        with self.assertRaises(RancherResponseError):
            response = self.sut.create_project('My Project', 'My cluster')

        requests.get.assert_called_once()
        requests.get.assert_called_with('myaddress/cluster?id=My cluster', auth = ("mykey", "mysecret"))
        requests.post.assert_not_called()

    def test_permission_denied_raises_err(self):
        cluster_response = requests.Response()
        cluster_response.status_code = 200
        cluster_response.json = lambda: { 'data': [ { "id": "c-137" } ] }
        denied_response = requests.Response()
        denied_response.status_code = 403
        requests.get = MagicMock(return_value=cluster_response)
        requests.post = MagicMock(return_value=denied_response)

        with self.assertRaises(requests.HTTPError):
            response = self.sut.create_project('My Project', 'My cluster')

        requests.get.assert_called_once()
        requests.get.assert_called_with('myaddress/cluster?id=My cluster', auth = ("mykey", "mysecret"))
        requests.post.assert_called_once()
        requests.post.assert_called_with('myaddress/projects', auth = ("mykey", "mysecret"),
                                            json = { 'name': 'My Project', 'clusterId': 'c-137' })

    def test_server_err_raises_err(self):
        cluster_response = requests.Response()
        cluster_response.status_code = 200
        cluster_response.json = lambda: { 'data': [ { "id": "c-137" } ] }
        err_response = requests.Response()
        err_response.status_code = 500
        requests.get = MagicMock(return_value=cluster_response)
        requests.post = MagicMock(return_value=err_response)

        with self.assertRaises(requests.HTTPError):
            response = self.sut.create_project('My Project', 'My cluster')

        requests.get.assert_called_once()
        requests.get.assert_called_with('myaddress/cluster?id=My cluster', auth = ("mykey", "mysecret"))
        requests.post.assert_called_once()
        requests.post.assert_called_with('myaddress/projects', auth = ("mykey", "mysecret"),
                                            json = { 'name': 'My Project', 'clusterId': 'c-137' })

    def test_looks_up_cluster_and_returns_new_project(self):
        cluster_response = requests.Response()
        cluster_response.status_code = 200
        cluster_response.json = lambda: { 'data': [ { "id": "c-137" } ] }
        project_response = requests.Response()
        project_response.status_code = 200
        project_response.json = lambda: { "id": "p-123abc" }
        requests.get = MagicMock(return_value=cluster_response)
        requests.post = MagicMock(return_value=project_response)

        response = self.sut.create_project('My Project', 'My cluster')

        requests.get.assert_called_once()
        requests.get.assert_called_with('myaddress/cluster?id=My cluster', auth = ("mykey", "mysecret"))
        requests.post.assert_called_once()
        requests.post.assert_called_with('myaddress/projects', auth = ("mykey", "mysecret"),
                                            json = { 'name': 'My Project', 'clusterId': 'c-137' })

        self.assertEqual(response['id'], 'p-123abc')

class TestSearchPrincipal(TestRancherApi):
    def test_retrieve_user(self):
        self.sut._post = MagicMock(return_value={ 'data': [
            { 'id': 'jdoe', 'name': 'Jane Doe', 'principalType': 'user' }]})

        response = self.sut.search_principal('jdoe')

        self.sut._post.assert_called_once()
        self.sut._post.assert_called_with('/principals?action=search', { 'name': 'jdoe', 'principalType': None })
        self.assertEqual('jdoe', response.id)
        self.assertEqual('Jane Doe', response.name)
        self.assertEqual('user', response.type)
        self.assertEqual(False, response.is_group)

    def test_no_results_returns_none(self):
        self.sut._post = MagicMock(return_value={ 'data': []})

        response = self.sut.search_principal('jdoe')

        self.sut._post.assert_called_once()
        self.sut._post.assert_called_with('/principals?action=search', { 'name': 'jdoe', 'principalType': None })
        self.assertIsNone(response)

    def test_malformed_data_throw_err(self):
        self.sut._post = MagicMock(return_value={ 'data': [{ 'badkey': 'baddata' }]})

        with self.assertRaises(RancherResponseError):
            response = self.sut.search_principal('jdoe')

        self.sut._post.assert_called_once()
        self.sut._post.assert_called_with('/principals?action=search', { 'name': 'jdoe', 'principalType': None })

    def test_none_arg_throws_err(self):
        self.sut._post = MagicMock()

        with self.assertRaises(TypeError):
            response = self.sut.search_principal(None)

        self.sut._post.assert_not_called()

class TestGetProjectMembers(TestRancherApi):
    def test_gets_members(self):
        self.sut._get = MagicMock()
        self.sut._get.side_effect = lambda x: {
            '/projectroletemplatebindings?projectId=p-abc123&roleTemplateId=my-role':
                { 'data': [ { 'groupPrincipalId': 'developers', 'userPrincipalId': None },
                            { 'groupPrincipalId': None, 'userPrincipalId': 'jdoe' }]},
            '/principals/jdoe':
                { 'id': 'jdoe', 'name': 'Jane Doe', 'principalType': 'user' },
            '/principals/developers':
                { 'id': 'developers', 'name': 'Developers', 'principalType': 'group' }
            }[x]

        response = self.sut.get_project_members('p-abc123', 'my-role')

        self.assertEqual(3, self.sut._get.call_count)
        self.sut._get.assert_has_calls([
            call('/projectroletemplatebindings?projectId=p-abc123&roleTemplateId=my-role'),
            call('/principals/developers'),
            call('/principals/jdoe')])
        self.assertEqual(2, len(response))
        self.assertEqual('developers', response[0].id)
        self.assertEqual('Developers', response[0].name)
        self.assertEqual('group', response[0].type)
        self.assertEqual(True, response[0].is_group)
        self.assertEqual('jdoe', response[1].id)
        self.assertEqual('Jane Doe', response[1].name)
        self.assertEqual('user', response[1].type)
        self.assertEqual(False, response[1].is_group)

    def test_no_members_returns_empty_list(self):
        self.sut._get = MagicMock(return_value={ 'data': []})

        response = self.sut.get_project_members('p-abc123', 'my-role')

        self.sut._get.assert_called_once()
        self.sut._get.assert_called_with('/projectroletemplatebindings?projectId=p-abc123&roleTemplateId=my-role')
        self.assertEqual(0, len(response))

    def test_malformed_member_throws_err(self):
        self.sut._get = MagicMock(return_value={ 'data': [{ 'bad data': 'bad value' }]})

        with self.assertRaises(RancherResponseError):
            response = self.sut.get_project_members('p-abc123', 'my-role')

        self.sut._get.assert_called_once()
        self.sut._get.assert_called_with('/projectroletemplatebindings?projectId=p-abc123&roleTemplateId=my-role')
    
    def test_none_project_throws_err(self):
        self.sut._get = MagicMock()

        with self.assertRaises(TypeError):
            response = self.sut.get_project_members(None, 'my-role')

        with self.assertRaises(TypeError):
            response = self.sut.get_project_members('p-abc123', None)

        self.sut._get.assert_not_called()

class TestAddProjectMember(TestRancherApi):
    def test_add_new_member_checks_and_adds(self):
        resp = { 'data', 'value' }
        self.sut._get = MagicMock(return_value={ 'data': [] })
        self.sut._post = MagicMock(return_value=resp)
        jane = RancherPrincipal({ 'id': 'jdoe', 'name': 'Jane Doe', 'principalType': 'user' })

        response = self.sut.add_project_member('p-abc123', 'my-role', jane)

        self.sut._get.assert_called_once()
        self.sut._get.assert_called_with('/projectroletemplatebindings?userPrincipalId=jdoe&projectId=p-abc123&roleTemplateId=my-role')
        self.sut._post.assert_called_once()
        self.sut._post.assert_called_with('/projectroletemplatebindings', {
                                'projectId': 'p-abc123', 
                                'userPrincipalId': 'jdoe',
                                'roleTemplateId': 'my-role' })
        self.assertEqual(resp, response)

    def test_add_new_group_member_checks_and_adds(self):
        resp = { 'data', 'value' }
        self.sut._get = MagicMock(return_value={ 'data': [] })
        self.sut._post = MagicMock(return_value=resp)
        devs = RancherPrincipal({ 'id': 'developers', 'name': 'Developers', 'principalType': 'group' })

        response = self.sut.add_project_member('p-abc123', 'my-role', devs)

        self.sut._get.assert_called_once()
        self.sut._get.assert_called_with('/projectroletemplatebindings?groupPrincipalId=developers&projectId=p-abc123&roleTemplateId=my-role')
        self.sut._post.assert_called_once()
        self.sut._post.assert_called_with('/projectroletemplatebindings', {
                                'projectId': 'p-abc123', 
                                'groupPrincipalId': 'developers',
                                'roleTemplateId': 'my-role' })
        self.assertEqual(resp, response)

    def test_member_already_present_does_nothing(self):
        self.sut._get = MagicMock(return_value={ 'data': [ { 'userPrincipalId': 'jdoe' } ] })
        self.sut._post = MagicMock()
        jane = RancherPrincipal({ 'id': 'jdoe', 'name': 'Jane Doe', 'principalType': 'user' })

        response = self.sut.add_project_member('p-abc123', 'my-role', jane)

        self.sut._get.assert_called_once()
        self.sut._get.assert_called_with('/projectroletemplatebindings?userPrincipalId=jdoe&projectId=p-abc123&roleTemplateId=my-role')
        self.sut._post.assert_not_called()

    def test_args_none_throws_err(self):
        self.sut._get = MagicMock()
        self.sut._post = MagicMock()
        jane = RancherPrincipal({ 'id': 'jdoe', 'name': 'Jane Doe', 'principalType': 'user' })

        with self.assertRaises(TypeError):
            response = self.sut.add_project_member(None, 'my-role', jane)

        with self.assertRaises(TypeError):
            response = self.sut.add_project_member('p-123abc', None, jane)

        with self.assertRaises(TypeError):
            response = self.sut.add_project_member('p-123abc', 'my-role', None)
        
        self.sut._get.assert_not_called()
        self.sut._post.assert_not_called()

        
class TestRemoveProjectMember(TestRancherApi):
    def test_remove_member_checks_and_removes(self):
        resp = { 'data', 'value' }
        self.sut._get = MagicMock(return_value={ 'data': [ { 'id': 'ptrb-xyz' } ] })
        self.sut._delete = MagicMock(return_value=resp)
        jane = RancherPrincipal({ 'id': 'jdoe', 'name': 'Jane Doe', 'principalType': 'user' })

        response = self.sut.remove_project_member('p-abc123', 'my-role', jane)

        self.sut._get.assert_called_once()
        self.sut._get.assert_called_with('/projectroletemplatebindings?userPrincipalId=jdoe&projectId=p-abc123&roleTemplateId=my-role')
        self.sut._delete.assert_called_once()
        self.sut._delete.assert_called_with('/projectroletemplatebindings/ptrb-xyz')
        self.assertEqual(resp, response)

    def test_remove_group_member_checks_and_removes(self):
        resp = { 'data', 'value' }
        self.sut._get = MagicMock(return_value={ 'data': [ { 'id': 'ptrb-xyz' } ] })
        self.sut._delete = MagicMock(return_value=resp)
        devs = RancherPrincipal({ 'id': 'developers', 'name': 'Developers', 'principalType': 'group' })

        response = self.sut.remove_project_member('p-abc123', 'my-role', devs)

        self.sut._get.assert_called_once()
        self.sut._get.assert_called_with('/projectroletemplatebindings?groupPrincipalId=developers&projectId=p-abc123&roleTemplateId=my-role')
        self.sut._delete.assert_called_once()
        self.sut._delete.assert_called_with('/projectroletemplatebindings/ptrb-xyz')
        self.assertEqual(resp, response)

    def test_member_not_present_does_nothing(self):
        self.sut._get = MagicMock(return_value={ 'data': [] })
        self.sut._delete = MagicMock()
        jane = RancherPrincipal({ 'id': 'jdoe', 'name': 'Jane Doe', 'principalType': 'user' })

        response = self.sut.remove_project_member('p-abc123', 'my-role', jane)

        self.sut._get.assert_called_once()
        self.sut._get.assert_called_with('/projectroletemplatebindings?userPrincipalId=jdoe&projectId=p-abc123&roleTemplateId=my-role')
        self.sut._delete.assert_not_called()

    def test_args_none_throws_err(self):
        self.sut._get = MagicMock()
        self.sut._delete = MagicMock()
        jane = RancherPrincipal({ 'id': 'jdoe', 'name': 'Jane Doe', 'principalType': 'user' })

        with self.assertRaises(TypeError):
            response = self.sut.remove_project_member(None, 'my-role', jane)

        with self.assertRaises(TypeError):
            response = self.sut.remove_project_member('p-123abc', None, jane)

        with self.assertRaises(TypeError):
            response = self.sut.remove_project_member('p-123abc', 'my-role', None)
        
        self.sut._get.assert_not_called()
        self.sut._delete.assert_not_called()


if __name__ == '__main__':
    unittest.main()
