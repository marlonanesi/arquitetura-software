package lunalog.dockerfile_test

import data.lunalog.dockerfile
import rego.v1

bom := [
	{"Cmd": "from", "Value": ["python:3.12-slim"]},
	{"Cmd": "copy", "Value": [".", "/app"]},
	{"Cmd": "user", "Value": ["10001"]},
	{"Cmd": "cmd", "Value": ["python", "app.py"]},
]

test_dockerfile_conforme if {
	count(dockerfile.deny) == 0 with input as bom
}

test_base_latest_reprova if {
	some m in dockerfile.deny with input as [{"Cmd": "from", "Value": ["python:latest"]}, {"Cmd": "user", "Value": ["app"]}]
	contains(m, "base-latest")
}

test_sem_user_reprova if {
	some m in dockerfile.deny with input as [{"Cmd": "from", "Value": ["python:3.12-slim"]}]
	contains(m, "sem-user")
}

test_user_root_reprova if {
	some m in dockerfile.deny with input as [{"Cmd": "from", "Value": ["python:3.12-slim"]}, {"Cmd": "user", "Value": ["root"]}]
	contains(m, "user-root")
}

test_add_com_url_reprova if {
	entrada := array.concat(bom, [{"Cmd": "add", "Value": ["https://exemplo.test/pacote.tgz", "/opt"]}])
	some m in dockerfile.deny with input as entrada
	contains(m, "add-url")
}
