#!/usr/bin/env python3
"""
Delete VPC and all associated resources
"""

import boto3
import time
import sys

def delete_vpc_infrastructure(vpc_id, region='ap-south-1'):
    ec2 = boto3.client('ec2', region_name=region)
    
    print(f"Deleting VPC: {vpc_id}")
    
    try:
        # Delete NAT Gateways
        print("Deleting NAT Gateways...")
        nat_gateways = ec2.describe_nat_gateways(
            Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
        )['NatGateways']
        
        for nat in nat_gateways:
            if nat['State'] != 'deleted':
                print(f"  Deleting NAT Gateway: {nat['NatGatewayId']}")
                ec2.delete_nat_gateway(NatGatewayId=nat['NatGatewayId'])
        
        if nat_gateways:
            print("  Waiting for NAT Gateways to delete (this takes 1-2 minutes)...")
            time.sleep(90)
        
        # Release Elastic IPs
        print("Releasing Elastic IPs...")
        addresses = ec2.describe_addresses(
            Filters=[{'Name': 'domain', 'Values': ['vpc']}]
        )['Addresses']
        
        for addr in addresses:
            if 'NetworkInterfaceId' not in addr:
                print(f"  Releasing EIP: {addr['PublicIp']}")
                ec2.release_address(AllocationId=addr['AllocationId'])
        
        # Delete subnets
        print("Deleting Subnets...")
        subnets = ec2.describe_subnets(
            Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
        )['Subnets']
        
        for subnet in subnets:
            print(f"  Deleting Subnet: {subnet['SubnetId']}")
            ec2.delete_subnet(SubnetId=subnet['SubnetId'])
        
        # Delete route tables (except main)
        print("Deleting Route Tables...")
        route_tables = ec2.describe_route_tables(
            Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
        )['RouteTables']
        
        for rt in route_tables:
            if not any(assoc.get('Main') for assoc in rt.get('Associations', [])):
                print(f"  Deleting Route Table: {rt['RouteTableId']}")
                ec2.delete_route_table(RouteTableId=rt['RouteTableId'])
        
        # Detach and delete Internet Gateways
        print("Deleting Internet Gateways...")
        igws = ec2.describe_internet_gateways(
            Filters=[{'Name': 'attachment.vpc-id', 'Values': [vpc_id]}]
        )['InternetGateways']
        
        for igw in igws:
            print(f"  Detaching IGW: {igw['InternetGatewayId']}")
            ec2.detach_internet_gateway(
                InternetGatewayId=igw['InternetGatewayId'],
                VpcId=vpc_id
            )
            print(f"  Deleting IGW: {igw['InternetGatewayId']}")
            ec2.delete_internet_gateway(InternetGatewayId=igw['InternetGatewayId'])
        
        # Delete VPC
        print(f"Deleting VPC: {vpc_id}")
        ec2.delete_vpc(VpcId=vpc_id)
        
        print("\n" + "="*60)
        print("VPC Infrastructure Deleted Successfully!")
        print("="*60)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    vpc_id = 'vpc-0712817f3d1637c90'
    delete_vpc_infrastructure(vpc_id, region='ap-south-1')
