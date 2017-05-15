#!/usr/bin/python

DOCUMENTATION = '''
---
module: iam_alias
short_description: Manage IAM account aliases
description:
     - Allows for the addition/deletion of alias names of AWS accounts.
version_added: "2.2.1.0"
requirements: [ boto3 ]
options:
  aws_account_alias:
    description:
      - If set, changes AWS account alias name. If this parameter is not set, role does nothing.
  aws_account_state:
    description:
      - Changes AWS account alias name if set to present. If set to absent, removes account alias.
    default: present
    choices: [ "preset", "absent"]

  access_key_id:
    description:
      - Access key for the AWS account to which you want to add the account alias.
  aws_secret_key:
    description:
      - Secrete Key for the AWS account to which you want to add the account alias
author:
    - "Shahbaz Nazir (@shahbazn)"

'''

EXAMPLES = '''
# Basic alias creation example
tasks:
- name: Create AWS account alias
  iam_alias:
    aws_account_alias: "{{ aws_account_alias }}" 
    aws_account_state: present
    aws_access_key: "{{ aws_access_key_id }}"
    aws_secret_key: "{{ aws_secret_key }}"
  register: aws_alias_status
'''

try:
    import boto3
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

SERVICE = "iam"

def boto_exception(err):
    '''generic error message handler'''
    if hasattr(err, "error_message"):
        error = err.error_message
    elif hasattr(err, "message"):
        error = err.message
    else:
        error = "%s: %s" % (Exception, err)

    return error

def get_user_id(module, client):
	try:
		resp = client.get_user()
		user_id = resp["User"]["UserId"]
	except Exception as err:
		error_message = boto_exception(err)
		module.fail_json(msg=error_message)

	return user_id

def get_account_alias(module, client):
	try:
		resp = client.list_account_aliases()
		aliases = resp["AccountAliases"]

		if aliases:
			alias = aliases[0]
		else:
			alias = ""
	except Exception as err:
		error_message = boto_exception(err)
		module.fail_json(msg=error_message)

	return alias

def set_account_alias(module, client, alias):
	try:
		resp = client.create_account_alias(
			AccountAlias=alias)
		changed = True
	except Exception as err:
		error_message = boto_exception(err)
		module.fail_json(msg=str(err))

	return changed

def delete_account_alias(module, client, alias):
	try:
		resp = client.delete_account_alias(
			AccountAlias=alias)
		changed = True
	except Exception as err:
		error_message = boto_exception(err)
		module.fail_json(msg=str(err))

	return changed

def main():
    argument_spec = dict(
    	aws_account_alias=dict(default=None, required=False),
        aws_account_state=dict(
            default=None, required=True, choices=["present", "absent"]),
        aws_access_key=dict(default=None, required=True),
        aws_secret_key=dict(default=None, required=True),
    )

    module = AnsibleModule(
        argument_spec=argument_spec
        )

    if not HAS_BOTO:
        module.fail_json(msg='This module requires boto3, please install it')

    aws_account_alias = module.params.get('aws_account_alias')
    aws_account_state = module.params.get('aws_account_state')
    aws_access_key_id = module.params.get('aws_access_key')
    aws_secret_key = module.params.get('aws_secret_key')

    # Test for empty string values not covered by
    # required=True parameter condition
    if not aws_access_key_id:
    	module.fail_json(msg="empty value for required argument: aws_access_key_id")

    if not aws_secret_key:
    	module.fail_json(msg="empty value for required argument: aws_secret_key")

    client = aws_client(SERVICE,
    	aws_access_key_id=aws_access_key_id,
    	aws_secret_access_key=aws_secret_key)

    # Initialize variables to track module exit state
    changed = False
    user_id = get_user_id(module, client)
    current_account_alias = get_account_alias(module, client)

    # Module need to make changes only if 'aws_account_alias' is set
    if aws_account_alias:

	    # Module should only set alias if 'aws_account_alias'
	    # is not already set to the required value
	    if aws_account_alias != current_account_alias and aws_account_state=="present":
	    	changed = set_account_alias(module, client, aws_account_alias)
	    	current_account_alias = aws_account_alias

	    # Module should only delete alias if 'current_account_alias'
	    # is already set to the given 'aws_account_alias' value
	    elif aws_account_alias == current_account_alias and aws_account_state=="absent":
	    	changed = delete_account_alias(module, client, aws_account_alias)
	    	current_account_alias = get_account_alias(module, client)

    # Set module exit state
    module.exit_json(changed=changed,
    	aws_account_id=user_id,
    	aws_account_alias=current_account_alias
    	)



from ansible.module_utils.basic import *
from botocore.exceptions import ClientError
from boto3 import client as aws_client

if __name__ == '__main__':
    main()