import logging
import os
import random
import string

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
    def unique_event() -> str:
        return fake.text()

    @staticmethod
    def unique_email() -> str:
        random_string = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))  # noqa: S311
        return f"{random_string}{fake.email()}"

    @staticmethod
    def unique_name() -> str:
        return fake.name()

    def on_start(self):
        # set up urls

        register_url = f"{self.host}api/access/signup"
        get_token_url = f"{self.host}api/access/login"
        # urls used in task
        self.events_create_url = f"{self.host}api/events"
        self.events_get_by_id_url = f"{self.host}api/events/"

        # get unique email
        email = self.unique_email()
        name = self.unique_name()
        password = "abcdefghi"  # noqa: S105

        # register
        response = self.client.post(
            register_url,
            json={"email": email, "password": password, "name": name},
            headers={"X-Serverless-Authorization": f"Bearer {self.id_token}"},
        )
        if response.status_code != 201:
            error_msg = f"register: response.status_code = {response.status_code}, expected 201"
            logging.error(error_msg)

        # get_token
        # - username instead of email
        # - x-www-form-urlencoded (instead of json)
        response = self.client.post(
            get_token_url,
            data={"username": email, "password": password},
            headers={"X-Serverless-Authorization": f"Bearer {self.id_token}"},
        )
        access_token = response.json()["access_token"]
        logging.debug("get_token: for email = %s, access_token = %s", email, access_token)

        # set headers with access token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Serverless-Authorization": f"Bearer {self.id_token}",
        }

    def on_stop(self):
        pass

    # enable this dummy task to develop 'on_start'
    # @task
    def dummy(self):
        pass

    @task
    def events_write_read_check(self):
        # add event to api
        event_message = self.unique_event()
        logging.debug("event_create: event = %s", event_message)
        with self.client.post(
            self.events_create_url,
            json={"message": event_message},
            headers=self.headers,
            catch_response=True,
        ) as response:
            if response.status_code != 201:
                error_msg = f"events_create: response.status_code = {response.status_code}, expected 201, event_message = {event_message}"
                logging.error(error_msg)
                response.failure(error_msg)
                raise RescheduleTask()

            response_dict = response.json()
            if "id" not in response_dict:
                logger.info(response_dict)
                error_msg = f"events_create: id not in response_dict, event_message = {event_message}"
                logging.error(error_msg)
                response.failure(error_msg)
                raise RescheduleTask()

            event_id = response_dict["id"]
            logging.debug("events_create: for event_message = %s, event_id = %s", event_message, event_id)

        # get event from api and check
        with self.client.get(
            f"{self.events_get_by_id_url}{event_id}",
            headers=self.headers,
            name=self.events_get_by_id_url + "uuid",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                error_msg = f"events_get_by_id: response.status_code = {response.status_code}, expected 200, event_message = {event_message}"
                logging.error(error_msg)
                response.failure(error_msg)
                raise RescheduleTask()

            if "message" not in response_dict:
                logger.info(response_dict)
                error_msg = f"events_get_by_id: data not in response_dict, event_message = {event_message}"
                logging.error(error_msg)
                response.failure(error_msg)
                raise RescheduleTask()

            event_message_returned = response_dict["message"]
            logging.debug(
                "events_get_by_id: for event_id = %s, event_message_returned = %s", event_id, event_message_returned
            )

            if event_message_returned != event_message:
                error_msg = f"events_get_by_id: event_message_returned = {event_message_returned} not equal event_message = {event_message}"
                logging.error(error_msg)
                response.failure(error_msg)
                raise RescheduleTask()
