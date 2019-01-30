from logging import Filter


class ResultFilter(Filter):
    def __init__(self, app):
        self.app = app
        super(ResultFilter, self).__init__()

    def filter(self, record):
        extra = record.__dict__
        return "result_key" in extra.keys()
