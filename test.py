        manage_policies={
            "ssm": 'arn:aws:iam::aws:policy/service-role/AmazonEC2RoleforSSM',
            "s3": 'arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess'}
            
        for policy, arn in manage_policies.items():
            print(policy, arn)