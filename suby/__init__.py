import sys

from suby.proxy_module import ProxyModule as ProxyModule


sys.modules[__name__].__class__ = ProxyModule
