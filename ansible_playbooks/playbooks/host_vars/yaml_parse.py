import yaml
import sys
import pprint
fn = sys.argv[1]

with open(fn) as fp:
    try:
        pprint.pprint(yaml.safe_load(fp))
    except yaml.YAMLError as exc:
        print (exc)
