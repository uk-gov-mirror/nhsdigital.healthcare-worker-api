from integration_tests.config.base_environment import EnvironmentConfig


class FtEnvironmentConfig(EnvironmentConfig):
    client_id = "KG8XEhXyL0iHP3wN8hKM6KVgDInd2DX0"

    def __init__(self):
        super(FtEnvironmentConfig, self).__init__(self.client_id)
        self.base_url = f"https://internal-dev.api.service.nhs.uk/healthcare-worker"
        self.realm_url = "https://internal-dev.api.service.nhs.uk/oauth2/token"
