from integration_tests.config.base_environment import EnvironmentConfig


class SandboxEnvironmentConfig(EnvironmentConfig):
    client_id = ""

    def __init__(self):
        super(SandboxEnvironmentConfig, self).__init__(self.client_id)
        self.base_url = "https://sandbox.api.service.nhs.uk/healthcare-worker"
