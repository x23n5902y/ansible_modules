#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsmsys_file
short_description: Tweak settings in dsm.sys file
description:
     - Manage (add, remove, change) individual settings in an dsm.sys file without having
       to manage the file as a whole with, say, M(ansible.builtin.template) or M(ansible.builtin.assemble).

options:
  path:
    description:
      - Path to the dsm.sys file; this file is created if required.
    type: path
    required: true
    aliases: [ dest ]
  section:
    description:
      - Section name in dsm.sys file. This is added if C(state=present) automatically when
        a single value is being set.
      - If left empty or set to C(null), the I(option) will be placed before the first I(section).
      - Using C(null) is also required if the config format does not support sections.
    type: str
    required: true
  option:
    description:
      - If set (required for changing a I(value)), this is the name of the option.
      - May be omitted if adding/removing a whole I(section).
    type: str
  value:
    description:
      - The string value to be associated with an I(option).
      - May be omitted when removing an I(option).
    type: str
  backup:
    description:
      - Create a backup file including the timestamp information so you can get
        the original file back if you somehow clobbered it incorrectly.
    type: bool
    default: no
  state:
    description:
      - If set to C(absent) and I(exclusive) set to C(yes) all matching I(option) lines are removed.
      - If set to C(absent) and I(exclusive) set to C(no) the specified C(option=value) lines are removed,
        but the other I(option)s with the same name are not touched.
      - If set to C(present) and I(exclusive) set to C(no) the specified C(option=values) lines are added,
        but the other I(option)s with the same name are not touched.
      - If set to C(present) and I(exclusive) set to C(yes) all given C(option=values) lines will be
        added and the other I(option)s with the same name are removed.
    type: str
    choices: [ absent, present ]
    default: present
  create:
    description:
      - If set to C(no), the module will fail if the file does not already exist.
      - By default it will create the file if it is missing.
    type: bool
    default: yes
author:
    - Aleksandr Maslennikov (@ruabxbu)
'''

EXAMPLES = r'''
- name: Ensure "fav=lemonade is in section "drinks" in specified file
  dsmsys_file:
    path: /etc/conf
    section: drinks
    option: fav
    value: lemonade
    mode: '0600'
    backup: yes

- name: Ensure "temperature=cold is in section "drinks" in specified file
  dsmsys_file:
    path: /etc/anotherconf
    section: drinks
    option: temperature
    value: cold
    backup: yes

- name: Add "beverage=lemon juice" is in section "drinks" in specified file
  dsmsys_file:
    path: /etc/conf
    section: drinks
    option: beverage
    value: lemon juice
    mode: '0600'
    state: present
    exclusive: no

'''

import io
import os
import re
import tempfile
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_bytes, to_text

try:
    from ansible.module_utils.dsmsys_parser.operations import DsmsysOperations
    from ansible.module_utils.dsmsys_parser.transformers import TreeToJson
    from ansible.module_utils.dsmsys_parser.reconstructor import dict_to_config
    from ansible.module_utils.dsmsys_parser.standalone import Lark_StandAlone
    HAS_PARSER = True
except ImportError:
    HAS_PARSER = False
    


def do_ini(result, parser, module, filename, section=None, option=None, value=None,
           state='present', backup=False, create=True):
    if section:
        section = to_text(section)
    if option:
        option = to_text(option)

    diff = dict(
        before='',
        after='',
        before_header='%s (content)' % filename,
        after_header='%s (content)' % filename,
    )

    if not os.path.exists(filename):
        if not create:
            module.fail_json(rc=257, msg='Destination %s does not exist!' % filename)
        destpath = os.path.dirname(filename)
        if not os.path.exists(destpath) and not module.check_mode:
            os.makedirs(destpath)
        ini_lines = []
    else:
        with io.open(filename, 'r', encoding="utf-8-sig") as ini_file:
            ini_lines = [to_text(line) for line in ini_file.readlines()]

    if module._diff:
        diff['before'] = u''.join(ini_lines)

    changed = False
    before = ini_lines

    # ini file could be empty
    if not ini_lines:
        ini_lines.append(u'\n')

    # last line of file may not contain a trailing newline
    if ini_lines[-1] == u"" or ini_lines[-1][-1] != u'\n':
        ini_lines[-1] += u'\n'
        changed = True

    tree = parser.parse(''.join(ini_lines))
    json_repr = {}
    if tree.children:
        json_repr = tree.children[0]
    config = DsmsysOperations(json_repr)
    config_dict = config.read()

    if state == 'present' and section:
        if option and value:
            config.option.create(section, option, value)
            result = config.option.read(section, option)
        else:
            config.stanza.create(section)
            result = config.stanza.read(section)
        msg = 'changed'

    if state == 'absent':
        if section and not option and not value:
            config.stanza.delete(section)
        if section and option:
            config.option.delete(section, option)
        msg = 'changed'
        result = None

    if not state:
        result = config.read()
        msg = None

    # reassemble the ini_lines after manipulation
    ini_lines = dict_to_config(config_dict)
    after = ini_lines
    
    if before != after:
        changed = True

    if module._diff:
        diff['after'] = u''.join(ini_lines)

    backup_file = None
    if changed and not module.check_mode:
        if backup:
            backup_file = module.backup_local(filename)

        encoded_ini_lines = [to_bytes(line) for line in ini_lines]
        try:
            tmpfd, tmpfile = tempfile.mkstemp(dir=module.tmpdir)
            f = os.fdopen(tmpfd, 'wb')
            f.writelines(encoded_ini_lines)
            f.close()
        except IOError:
            module.fail_json(msg="Unable to create temporary file %s", traceback=traceback.format_exc())

        try:
            module.atomic_move(tmpfile, filename)
        except IOError:
            module.ansible.fail_json(msg='Unable to move temporary \
                                   file %s to %s, IOError' % (tmpfile, filename), traceback=traceback.format_exc())

    return (changed, backup_file, diff, msg, result)


def main(HAS_PARSER):
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(type='path', default="/opt/tivoli/tsm/client/ba/bin/dsm.sys", aliases=['dest']),
            section=dict(type='str', required=True),
            option=dict(type='str'),
            value=dict(type='str'),
            backup=dict(type='bool', default=False),
            state=dict(type='str', default=None, choices=['absent', 'present']),
            create=dict(type='bool', default=True)
        ),
        add_file_common_args=True,
        supports_check_mode=True,
    )

    path = module.params['path']
    section = module.params['section']
    option = module.params['option']
    value = module.params['value']
    state = module.params['state']
    backup = module.params['backup']
    create = module.params['create']
    try:
        parser = Lark_StandAlone(transformer=TreeToJson())
    except NameError:
        HAS_PARSER=False
    result = {}

    if not HAS_PARSER:
        module.fail_json(msg="Problems with optional imports from module_utils.standalone.py. Please ensure that ansible version is 2.9.20 and greater.")

    if state == 'present' and value is None:
        module.fail_json(msg="Parameter 'value' must be defined if state=present.")

    (changed, backup_file, diff, msg, result) = do_ini(result, parser, module, path, section, option, value, state, backup, create)

    if not module.check_mode and os.path.exists(path):
        file_args = module.load_file_common_arguments(module.params)
        changed = module.set_fs_attributes_if_different(file_args, changed)

    results = dict(
        changed=changed,
        diff=diff,
        msg=msg,
        path=path,
        result=result,
    )
    if backup_file is not None:
        results['backup_file'] = backup_file

    # Mission complete
    module.exit_json(**results)




if __name__ == '__main__':
    main(HAS_PARSER)
