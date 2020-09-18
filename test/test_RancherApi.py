import unittest
from unittest.mock import MagicMock
from io import BytesIO
import requests
import logging
from RancherProjectManager.RancherApi import RancherApi, RancherResponseError

class TestRancherApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.INFO, filename='/dev/null')

    def setUp(self):
        requests.get = MagicMock()
        requests.post = MagicMock()
        self.sut = RancherApi('myaddress', 'mykey', 'mysecret')

    def test_get_returns_data(self):
        happy_response = requests.Response()
        happy_response.status_code = 200
        happy_response.raw = BytesIO(b"{\"data\":\"mydata\"}")
        requests.get = MagicMock(return_value=happy_response)

        response = self.sut._get('mypath')

        self.assertEqual('mydata', response['data'])
        requests.get.assert_called_once()
        requests.get.assert_called_with('myaddressmypath', auth = ("mykey", "mysecret"))

    def test_get_with_403_raises_err(self):
        denied_response = requests.Response()
        denied_response.status_code = 403
        requests.get = MagicMock(return_value=denied_response)
        with self.assertRaises(requests.HTTPError):
            response = self.sut._get("mypath")

    def test_get_with_500_raises_err(self):
        err_response = requests.Response()
        err_response.status_code = 500
        requests.get = MagicMock(return_value=err_response)
        with self.assertRaises(requests.HTTPError):
            response = self.sut._get("mypath")

    def test_get_returns_invalid_json_raises_err(self):
        invalid_response = requests.Response()
        invalid_response.status_code = 200
        invalid_response.raw = BytesIO(b"not json")
        requests.get = MagicMock(return_value=invalid_response)
        with self.assertRaises(RancherResponseError):
            response = self.sut._get("mypath")

    def test_get_project_calls_get_with_project_arg(self):
        project = { 'name': 'My Project', 'id': 'p-asd123' }
        project_response = requests.Response()
        project_response.status_code = 200
        project_response.json = lambda: { 'data': [ project ] }
        requests.get = MagicMock(return_value=project_response)

        retVal = self.sut.get_project('My Project')

        self.assertEqual(project, retVal)
        requests.get.assert_called_once()
        requests.get.assert_called_with('myaddress/projects?name=My Project', auth = ("mykey", "mysecret"))

    def test_get_project_no_match_returns_none(self):
        empty_response = requests.Response()
        empty_response.status_code = 200
        empty_response.json = lambda: { 'data': [ ] }
        requests.get = MagicMock(return_value=empty_response)

        retVal = self.sut.get_project('My Project')

        self.assertEqual(None, retVal)
        requests.get.assert_called_once()
        requests.get.assert_called_with('myaddress/projects?name=My Project', auth = ("mykey", "mysecret"))

    def test_get_project_multiple_match_returns_first(self):
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

    def test_get_project_not_list_raises_err(self):
        project = { 'name': 'My Project', 'id': 'p-asd123' }
        empty_response = requests.Response()
        empty_response.status_code = 200
        empty_response.json = lambda: { 'data': project }
        requests.get = MagicMock(return_value=empty_response)

        with self.assertRaises(RancherResponseError):
            response = self.sut.get_project('My Project')

        requests.get.assert_called_once()
        requests.get.assert_called_with('myaddress/projects?name=My Project', auth = ("mykey", "mysecret"))

    def test_create_project_none_name_raises_err(self):
        requests.get = MagicMock()
        requests.post = MagicMock()

        with self.assertRaises(TypeError):
            response = self.sut.create_project(None, "my cluster")

        requests.get.assert_not_called()
        requests.post.assert_not_called()

    def test_create_project_none_cluster_raises_err(self):
        requests.get = MagicMock()
        requests.post = MagicMock()

        with self.assertRaises(TypeError):
            response = self.sut.create_project("My project", None)

        requests.get.assert_not_called()
        requests.post.assert_not_called()

    def test_create_project_cluster_does_not_exist_raises_err(self):
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

    def test_create_project_cluster_malformed_raises_err(self):
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

    def test_create_project_permission_denied_raises_err(self):
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

    def test_create_project_server_err_raises_err(self):
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

    def test_create_project_looks_up_cluster_and_returns_new_project(self):
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

if __name__ == '__main__':
    unittest.main()
