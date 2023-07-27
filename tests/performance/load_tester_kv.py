import logging
import os
from uuid import uuid4

import dotenv
import google.auth.transport.requests
import google.oauth2.id_token
from faker import Faker
from locust import FastHttpUser, task
from locust.exception import RescheduleTask

from spannermc.lib import log

logger = log.get_logger()

fake = Faker()

dotenv.load_dotenv(".env")


def get_id_token(audience: str | None = None) -> str:
    """Get an ID token for making service requests."""
    auth_req = google.auth.transport.requests.Request()
    return google.oauth2.id_token.fetch_id_token(auth_req, audience)


id_token = get_id_token(os.environ.get("TEST_TOKEN_AUDIENCE", "http://localhost:8000/"))


class WebsiteTestUser(FastHttpUser):  # type: ignore
    network_timeout = 30.0
    connection_timeout = 30.0

    def __init__(self, environment):
        self.id_token = id_token
        super().__init__(environment)

    @staticmethod
    def unique_value() -> str:
        return str(uuid4())

    @staticmethod
    def unique_key() -> str:
        return str(uuid4())

    def on_start(self):
        # set up urls

        # urls used in task
        self.kv_create_url = f"{self.host}api/kv"
        self.kv_get_by_key_url = f"{self.host}api/kv/"

        # set headers with access token
        self.headers = {
            "X-Serverless-Authorization": f"Bearer {self.id_token}",
        }

    def on_stop(self):
        pass

    @task
    def kv_write_read_check(self):
        # add event to api
        unique_value = self.unique_value()
        unique_key = self.unique_key()
        logging.debug("kv_create: event = %s", unique_value)
        with self.client.post(
            self.kv_create_url,
            json={"key": unique_key, "value": unique_value},
            headers=self.headers,
            catch_response=True,
        ) as response:
            if response.status_code != 201:
                error_msg = (
                    f"kv_create: response.status_code = {response.status_code}, expected 201, kv_key = {unique_value}"
                )
                logging.error(error_msg)
                response.failure(error_msg)
                raise RescheduleTask()

            response_dict = response.json()
            if "key" not in response_dict:
                logger.info(response_dict)
                error_msg = f"kv_create: key not in response_dict, kv_key = {unique_value}"
                logging.error(error_msg)
                response.failure(error_msg)
                raise RescheduleTask()

            kv_key = response_dict["key"]
            logging.debug("kv_create: for kv_key = %s, kv_key = %s", unique_value, kv_key)

        # get event from api and check
        with self.client.get(
            f"{self.kv_get_by_key_url}{kv_key}",
            headers=self.headers,
            name=self.kv_get_by_key_url + "kv_key",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                error_msg = f"kv_get_by_id: response.status_code = {response.status_code}, expected 200, kv_key = {unique_value}"
                logging.error(error_msg)
                response.failure(error_msg)
                raise RescheduleTask()

            if "value" not in response_dict:
                logger.info(response_dict)
                error_msg = f"kv_get_by_id: data not in response_dict, kv_key = {unique_value}"
                logging.error(error_msg)
                response.failure(error_msg)
                raise RescheduleTask()

            kv_value_returned = response_dict["value"]
            logging.debug("kv_get_by_id: for kv_key = %s, kv_key_returned = %s", kv_key, kv_value_returned)

            if kv_value_returned != unique_value:
                error_msg = f"kv_get_by_id: kv_key_returned = {kv_value_returned} not equal kv_key = {unique_value}"
                logging.error(error_msg)
                response.failure(error_msg)
                raise RescheduleTask()
