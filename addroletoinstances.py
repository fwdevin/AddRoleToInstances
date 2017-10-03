# This script adds a role to all instances in a VPC. If the instance
# has a different role than the given role, it will replace the
# role with the given role.
#
# 2017 Devin S.

#!/usr/local/bin/python3

import boto3

region =  str(input('Enter the region: \n'))
vpcId = str(input('Enter the vpc-id: \n'))
profileARN =  str(input('Enter the instance profile ARN: \n'))

ec2 = boto3.client('ec2', region_name=region)

print('Getting instances...\n')

instanceList = ec2.describe_instances(
    Filters = [
        {
            'Name': 'vpc-id',
            'Values': [
                vpcId
            ]
        }
    ]
)

print('Checking for and adding/replacing roles...\n')

instancesWithRoles = {}
changingInstances = []

instances = instanceList['Reservations']

for instance in instances:
    x = instance['Instances']
    y = x[0]
    if 'IamInstanceProfile' in y:
        if y['IamInstanceProfile']['Arn'] == profileARN:
            continue
        else:
            instancesWithRoles[str(y['InstanceId'])] = str(y['IamInstanceProfile']['Arn'])
            instanceId = y['InstanceId']
            associations = ec2.describe_iam_instance_profile_associations(
                Filters = [
                    {
                        'Name': 'instance-id',
                        'Values': [
                            instanceId
                        ]
                    }
                ]
            )
            x = associations['IamInstanceProfileAssociations']
            for state in x:
                if state['State'] == 'associated':
                    associationId = state['AssociationId']
                    ec2.replace_iam_instance_profile_association(
                        IamInstanceProfile = {
                            'Arn': profileARN
                        },
                        AssociationId = associationId
                    )
                else:
                    if y['InstanceId'] not in changingInstances:
                        changingInstances.append(str(y['InstanceId']))
                        continue
    else:
        ec2.associate_iam_instance_profile(
            IamInstanceProfile = {
                'Arn': profileARN
            },
            InstanceId = y['InstanceId']
        )

if len(changingInstances) > 0:
    for x in changingInstances:
        if x in instancesWithRoles:
            del instancesWithRoles[x]

if ((len(instancesWithRoles) > 0) and (len(changingInstances) > 0)):
    print('Finished. These instances had roles that were changed to ' + profileARN + ':\n' + str(instancesWithRoles) + '\n')
    print("These instance's roles may have been recently changed and couldn't be replaced: \n" + str(changingInstances) + '\n' + 'Please try again later.\n')
elif len(instancesWithRoles) > 0:
    print('Finished. These instances had roles that were changed to ' + profileARN + ':\n' + str(instancesWithRoles) + '\n')
elif len(changingInstances) > 0:
    print("Finished. These instance's roles may have been recently changed and couldn't be replaced: \n" + str(changingInstances) + '\n' + 'Please try again later.\n')
else:
    print('Finished.')
