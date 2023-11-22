from .server import WebUI

import flask
flask.json.provider.DefaultJSONProvider.sort_keys = False