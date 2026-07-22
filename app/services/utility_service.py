import base64
import hashlib
import json
import csv
import io
import difflib
import datetime

def format_json(raw_json: str, minify: bool = False) -> str:
    parsed = json.loads(raw_json)
    if minify:
        return json.dumps(parsed, separators=(',', ':'))
    return json.dumps(parsed, indent=4)

def csv_to_json(csv_str: str) -> str:
    reader = csv.DictReader(io.StringIO(csv_str))
    return json.dumps([row for row in reader], indent=4)

def json_to_csv(json_str: str) -> str:
    data = json.loads(json_str)
    if not isinstance(data, list) or len(data) == 0:
        return ""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    return output.getvalue()

def base64_encode(data: bytes) -> str:
    return base64.b64encode(data).decode("utf-8")

def base64_decode(encoded_str: str) -> bytes:
    return base64.b64decode(encoded_str.encode("utf-8"))

def hash_string(text: str, algo: str = "sha256") -> str:
    h = hashlib.new(algo.lower())
    h.update(text.encode("utf-8"))
    return h.hexdigest()

def generate_diff(text1: str, text2: str) -> str:
    diff = difflib.HtmlDiff()
    return diff.make_file(text1.splitlines(), text2.splitlines())

def convert_timestamp(ts: float) -> str:
    dt = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc)
    return dt.isoformat()
