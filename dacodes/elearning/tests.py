import json
import os

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class LogicTests(APITestCase):
    def setUp(self):
        self.__dir_path = os.path.dirname(os.path.realpath(__file__))

    def load_json(self, file_name):
        json_data = open("{}/fixtures/{}".format(self.__dir_path, file_name))
        return json.load(json_data)

    def test_logic(self):
        url = reverse('logic_test')
        data = self.load_json('logic.json')
        response = self.client.post(url, data, format='json')

        #Assert status response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        #Assert valid response
        valid_response = self.load_json('logic_results.json')
        response.render()
        json_response = json.loads(response.content)
        self.assertEqual(json_response, valid_response)