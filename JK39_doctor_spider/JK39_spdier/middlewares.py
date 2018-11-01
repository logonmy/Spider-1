
import random
from settings import USER_AGENT_LIST


class UserAgentMiddleware(object):
    def process_request(self, request, spider):
        user_agent = random.choice(USER_AGENT_LIST)
        request.headers.setdefault("User-Agent", user_agent)

