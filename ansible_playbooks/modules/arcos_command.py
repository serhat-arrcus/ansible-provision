#!/usr/bin/python
# -*- coding: utf-8 -*-

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = '''
---
module: arcos_command
version_added: historical
description:
  - Test module
notes:
  - Test notes
options:
  command:
    description:
      - Test command
author:
  - Ebben Aries <exa@arrcus.com>
  - Dave Thelen <dt@arrcus.com>
'''

import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import transform_commands, to_lines


from arcapi import errors
from arcapi import manager
from arcapi.types import Encoding
from arcapi.types import Handler

def get_cli(module):
    cli = True
    if module.params['cli']:
        cli = module.params['cli']
    return cli

def get_encoding(module):
    encoding = Encoding.JSON
    if module.params['encoding']:
        intended_encoding = module.params['encoding']
        if intended_encoding.lower() == 'json':
            encoding = Encoding.JSON
        elif intended_encoding.lower() == 'text':
            encoding = Encoding.TEXT
        elif intended_encoding.lower() == 'xml':
            encoding = Encoding.XML
    return encoding


def run_module():
    module_args = dict(
        commands=dict(type='list', aliases=['command']),
        cli=dict(type=bool, default=True),
        encoding=dict(type='str', choices=['json', 'xml', 'text'],
                      default='json')
    )

    results = dict(
        changed=False,
        commands = []
    )

    command_output = dict(
        message='',
        message_lines='',
        stdout='',
        stdout_lines='',
        command=''
    )


    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        module.exit_json(**result)
    cli = get_cli(module)
    encoding = get_encoding(module)
    commands = transform_commands(module) 

    m = manager.connect()
    stdout = []
    for command in commands:
        r = m.command(command=command['command'], encoding=encoding, cli=cli)

        command_output['command'] = command['command']

        if r.error:
            result = {}
            result['failed'] = True
            result['message'] = r.error
            module.fail_json(msg=r.message, **result)
        try:
            if encoding == Encoding.JSON:
                command_output['message'] = json.loads(r.message)
            elif encoding == Encoding.TEXT:
                command_output['message'] = (r.message)
                command_output['message_lines'] = r.message.splitlines()
        except ValueError:
            # some cli commands will return null
            command_output['message'] = r.message
            command_output['message_lines'] = r.message.splitlines()

        command_output['stdout'] = command_output['message']
        command_output['stdout_lines'] = command_output['message_lines']
        stdout.append(command_output)

    results['commands'] = stdout
    results['changed'] = False
    results['failed'] = False
    module.exit_json(**results)

def main():
    run_module()

if __name__ == '__main__':
    main()
