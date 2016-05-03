import os
memcache_host = os.getenv("MEMCACHE", None)
if memcache_host:
    import socket
    memcache_host = socket.gethostbyname(memcache_host)
    import pylibmc
else:
    import pylru

__all__ = ["get_cache"]

def get_cache(size=10000):
    if memcache_host:
        host = memcache_host.split(":")
        kw = {
            "binary": True,
            "behaviors": {"tcp_nodelay": True, "ketama": True},
        }
        return pylibmc.Client(host, **kw)
    else:
        return pylru.lrucache(size)



