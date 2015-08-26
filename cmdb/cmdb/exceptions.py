import traceback

from cmdb.settings import logger


class ExceptionMiddleware(object):
    def process_exception(self, request, exception):
        logger.error(traceback.format_exc())
        return
