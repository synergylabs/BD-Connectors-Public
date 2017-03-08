import unittest
from building_depot import DataService, CenterService


api_key = 'fd7a39c3-69f1-48f3-99f1-540761a326a0'
auth_token = '85e693ab-a6fd-4129-80bb-10f9fc519e39'


class DataServiceTest(unittest.TestCase):

    def setUp(self):
        self.service = DataService('https://bd-datas1.ucsd.edu',
                                   api_key=api_key, auth_token=auth_token)

    def test_index(self):
        self.service.index()

    def test_info(self):
        self.service.info()

    def test_get_subscribers(self):
        self.service.get_subscribers()

    def test_list_sensors(self):
        s = self.service.list_sensors()
        print s

    def test_create_sensor(self):
        self.service.create_subscribers(username="sheimi")


class CenterServiceTest(unittest.TestCase):

    def setUp(self):
        self.service = CenterService('https://bd-central.ucsd.edu')

    def test_createsession(self):
        pass
        # self.service.create_session('sheimi@ucsd.edu', '')

    def test_createuser(self):
        return
        self.service.create_user(email="test@test.com",
                                 password="testtest",
                                 name="testuser",
                                 access_level=3,
                                 enabled=True)

    def test_viewsession(self):
        service = CenterService('https://bd-central.ucsd.edu',
                                api_key=api_key, auth_token=auth_token)
        print service.view_session()


def suite():
    suite = unittest.TestSuite()
    suite.addTests(unittest.makeSuite(DataServiceTest))
    suite.addTests(unittest.makeSuite(CenterServiceTest))
    return suite


if __name__ == '__main__':
    unittest.main()
