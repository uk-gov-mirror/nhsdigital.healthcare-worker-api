from integration_tests.config.base_environment import EnvironmentConfig


class IntEnvironmentConfig(EnvironmentConfig):
    client_id = "ODriiJhfHAWm7RvqSEnURCJ9exwVkfCN"

    def __init__(self):
        super(IntEnvironmentConfig, self).__init__(self.client_id)
        self.base_url = "https://int.api.service.nhs.uk/healthcare-worker"
        self.realm_url = "https://int.api.service.nhs.uk/oauth2/token"
