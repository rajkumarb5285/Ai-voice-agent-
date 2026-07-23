import logging

class Dummy:
    pass

class MockLogger:
    def __init__(self):
        self.logger = logging.getLogger("voice_agent")

    def bind(self, **kwargs):
        return self

    def unbind(self, *args):
        return self

    def info(self, event, **kwargs):
        self.logger.info(f"{event} {kwargs}")

    def warning(self, event, **kwargs):
        self.logger.warning(f"{event} {kwargs}")

    def error(self, event, **kwargs):
        self.logger.error(f"{event} {kwargs}")

    def debug(self, event, **kwargs):
        self.logger.debug(f"{event} {kwargs}")

    def fatal(self, event, **kwargs):
        self.logger.fatal(f"{event} {kwargs}")

    def critical(self, event, **kwargs):
        self.logger.critical(f"{event} {kwargs}")

def get_logger(*args, **kwargs):
    return MockLogger()

def configure(*args, **kwargs):
    pass

def make_filtering_bound_logger(*args, **kwargs):
    return MockLogger

class PrintLoggerFactory:
    pass

# Mocking submodules
contextvars = Dummy()
contextvars.merge_contextvars = lambda *args, **kwargs: None

processors = Dummy()
processors.add_log_level = lambda *args, **kwargs: None
processors.TimeStamper = lambda *args, **kwargs: None
processors.JSONRenderer = lambda *args, **kwargs: None

dev = Dummy()
dev.ConsoleRenderer = lambda *args, **kwargs: None
