from .server.content_integrity_environment import ContentIntegrityEnvironment

class ContentIntegrityEnv:
    def __init__(self):
        self.env = ContentIntegrityEnvironment()

    def reset(self, task_level=None):
        return self.env.reset(task_level=task_level)

    def step(self, action):
        return self.env.step(action)

    @property
    def state(self):
        return self.env.state