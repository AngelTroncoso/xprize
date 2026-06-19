"""Run chat endpoint tests and print full JSON."""
import json
import urllib.request
from urllib.error import HTTPError


def call_chat(payload):
    req = urllib.request.Request(
        "http://localhost:8000/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except HTTPError as e:
        return e.code, json.loads(e.read())


def main():
    payload = {
        "student_id": "123e4567-e89b-12d3-a456-426614174000",
        "message": "Explicar OA_01 sobre números",
        "curso": "1° Básico",
        "asignatura": "Matemática",
    }
    status, response = call_chat(payload)
    print(f"Status: {status}")
    print(json.dumps(response, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()