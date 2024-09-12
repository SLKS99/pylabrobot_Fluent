import os
from os.path import dirname, join

# https://github.com/protocolbuffers/protobuf/issues/3002#issuecomment-325459597
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

resource_dir = join(dirname(__file__), "resources")
