from slowapi import Limiter
from slowapi.util import get_remote_address

# Shared rate limiter configured to bucket requests by client IP.
limiter = Limiter(key_func=get_remote_address)
