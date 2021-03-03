from lib.flask_via.routers.default import Pluggable
from lib.flask_via.routers.restful import Resource
from .views import *
from .apis import *


routes = [
    Resource('/sign', APIRegister, 'APISign'),
    Resource('/get', APIRegister),
    Resource('/post', APISignin),
]

