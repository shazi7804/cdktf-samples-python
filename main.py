#!/usr/bin/env python
from constructs import Construct
from cdktf import App, TerraformStack, Token, TerraformOutput
from imports.aws import (AwsProvider, Instance, Subnet, Vpc, IamRole, IamRolePolicyAttachment, IamInstanceProfile,
                         DefaultRouteTable, DataAwsAmi, InternetGateway, Route, SecurityGroup, SecurityGroupRule)
import json

class MyStack(TerraformStack):
    def __init__(self, scope: Construct, ns: str):
        super().__init__(scope, ns)

        AwsProvider(self, 'Aws', region='us-east-1')

        tags={
            "CreateBy":"cdktf-samples-python",
            "SampleFrom":"https://github.com/shazi7804/cdktf-samples-python"
        }

        armAmi = DataAwsAmi(self, 'amazon-arm-linux',
            most_recent=True,
            owners=["amazon"],
            filter=[{
                        "name": "root-device-type",
                        "values": ["ebs"]
                    },
                    {
                        "name": "virtualization-type",
                        "values": ["hvm"]
                    },
                    {
                        "name": "name",
                        "values": ["amzn2-ami-hvm-2.0.20200722.0-arm64*"]
                    }])
        
        # define resources here
        vpc = Vpc(self, 'vpc',
            enable_dns_hostnames=True,
            cidr_block='10.0.0.0/16',
            tags=tags)

        igw = InternetGateway(self, 'internetGateway',
            vpc_id=Token().as_string(vpc.id),
            tags=tags)

        subnet = Subnet(self, 'subnet',
            vpc_id=Token().as_string(vpc.id),
            cidr_block="10.0.0.0/24",
            availability_zone="us-east-1a",
            map_public_ip_on_launch=True,
            tags=tags)
        
        routeTable = DefaultRouteTable(self, 'routeTable',
            default_route_table_id=Token().as_string(vpc.default_route_table_id),
            tags=tags)

        route = Route(self, 'route', 
            route_table_id=Token().as_string(routeTable.id),
            destination_cidr_block="0.0.0.0/0",
            gateway_id=Token().as_string(igw.id))

        # instance resources
        sg = SecurityGroup(self, 'bastionSecurityGroup',
            name="bastion-sg",
            vpc_id=Token().as_string(vpc.id),
            tags=tags)

        sgInboundRule = SecurityGroupRule(self, 'bastionInbound',
            type="ingress",
            cidr_blocks=["0.0.0.0/0"],
            from_port=22,
            to_port=22,
            protocol="ssh",
            security_group_id=Token().as_string(sg.id))
        
        sgOutboundRule = SecurityGroupRule(self, 'bastionOutbound',
            type="egress",
            cidr_blocks=["0.0.0.0/0"],
            from_port=0,
            to_port=65535,
            protocol="-1",
            security_group_id=Token().as_string(sg.id))

        # reading JSON policy to create sts assuume role
        with open('templates/ec2_assume_role_policy.json') as data:
            sts_assume_policy = json.load(data)
            role = IamRole(self, 'bastionRole', 
                            assume_role_policy=str(json.dumps(sts_assume_policy)))
        
        # iterating through config to create policy attachment objects
        manage_policies={
            "ssm": 'arn:aws:iam::aws:policy/service-role/AmazonEC2RoleforSSM',
            "s3": 'arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess'}
            
        for policy, arn in manage_policies.items():
            IamRolePolicyAttachment(self, 'bastion-{0}-attachment'.format(policy),
                                    role=role.id, 
                                    policy_arn=arn)
        
        instance_profile = IamInstanceProfile(self, 'instanceProfile', role=role.id)

        bastion = Instance(self, 'bastion',
          ami=armAmi.id, 
          instance_type="t4g.nano",
          subnet_id=Token().as_string(subnet.id),
          vpc_security_group_ids=[Token().as_string(sg.id)],
          iam_instance_profile=instance_profile.id,
          tags=tags)

        TerraformOutput(self, 'bastion_public_ip', value=bastion.public_ip)



app = App()
MyStack(app, "cdktf-samples-python")

app.synth()
