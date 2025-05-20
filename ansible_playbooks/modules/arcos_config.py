#!/usr/bin/python
# -*- coding: utf-8 -*-

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = '''
---
module: arcos_config
version_added: historical
description:
  - Test module
notes:
  - Test notes
options:
  name:
    description:
      - Name of the interface.
    required: true
  src:
    description:
      - The path to the configuration file or jinja2 template
author:
  - Ebben Aries <exa@arrcus.com>
  = Dave Thelen <dt@arrcus.com>
requirements:
  - TBD
'''

EXAMPLES = '''
- name: Render a jinja2 template onto ArcOS
  arcos_config:
    src: arcos_template.j2
'''
import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.config import NetworkConfig
# from ansible.module_utils.network.arcos.arcos import arcos_argument_spec

from arcapi import errors
from arcapi import manager
from arcapi.types import Encoding
from arcapi.types import Handler
from arcapi.types import LoadOperation
from arcapi.types import Mode

def get_candidate(module):
    candidate = ''
    if module.params['src']:
        candidate = module.params['src']
    return candidate

def get_validate(module):
    validate = False
    if module.params['validate']:
        validate = module.params['validate']
    return validate

def get_oper(module):
    oper = LoadOperation.MERGE
    if module.params['load_operation']:
        intended_oper = module.params['load_operation']
        if intended_oper.lower() == 'merge':
            oper = LoadOperation.MERGE
        elif intended_oper.lower() == 'override':
            oper = LoadOperation.OVERRIDE
        elif intended_oper.lower() == 'replace':
            oper = LoadOperation.REPLACE
    return oper

def get_mode(module):
    mode = Mode.PRIVATE
    if module.params['mode']:
        intended_mode = module.params['mode']
        if intended_mode.lower() == 'shared':
            mode = Mode.SHARED
        elif intended_mode.lower() == 'private':
            mode = Mode.PRIVATE
        elif intended_mode.lower() == 'exclusive':
            mode = Mode.EXCLUSIVE
    return mode


def get_timeout(module):
    timeout = 5
    if module.params['timeout']:
        timeout = module.params['timeout']
    return timeout

def run_module():
    module_args = dict(
        src=dict(type='path', default=None),
        load_operation=dict(choices=['merge', 'override', 'replace'],
                       default='merge'),
        mode=dict(choices=['private', 'shared', 'exclusive'],
                       default='private'),
        timeout=dict(type=int, required=False, default=5),
        arcos_cli=dict(type=bool, default=True),
        validate=dict(type=bool, default=False),
        comment=dict(type=str, default=None),
        lines=dict(type=list, default=None)
    )

    result = dict(
        changed=False,
        original_message='',
        message='',
        rc = None
         
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
     )

    check = False
    if module.check_mode:
        check = True

    if module.params['src'] or module.params['lines']:
        candidate = get_candidate(module)
        oper = get_oper(module)
        timeout = get_timeout(module)
        arcos_cli = module.params['arcos_cli']
        mode = get_mode(module)
        validate = module.params['validate']
        comment = module.params['comment'] if module.params['comment'] else ''

        m = manager.connect()
        if module.params['src']:
            r = m.load_config(filename=candidate, load_operation=oper,
                              cli=arcos_cli, timeout=timeout, check=check, mode=mode,
                              validate=validate, comment=comment)
        elif module.params['lines']:
            r = m.execute(module.params['lines'], cli=arcos_cli)


        if arcos_cli:
            if r.error == errors.Error.COMMIT_NO_MODIFICATIONS:
                result['changed'] = False 
                result['message'] = r.message
            elif r.error:
                result['message'] = r.message
                module.fail_json(msg=r.message, **result)
            else:
                result['message'] = r.message
                result['changed'] = True

        elif not arcos_cli:
           # commands being piped into confd_cli 
           # return a json encoded message
           arcapi_result = json.loads(r.message)
           result['arcos_cli'] = arcos_cli
           if arcapi_result['rc'] != 0:
               result['message'] = arcapi_result['message']
               result['rc'] = arcapi_result['rc']
               if module.params['fail_on_error']:
                   module.fail_json(msg=r.message, **result)
           else:
               result['rc'] = arcapi_result['rc']
               result['message'] = arcapi_result['message']
               result['changed'] = True

        if check:
            result['changed'] = False
            if module._diff:
                      
                result['diff'] = { 'prepared': ('\n').join(r.message.splitlines()[1:]) }
                
                result['changed'] = True

    result['failed'] = False
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
