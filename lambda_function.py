import boto3
import os
import requests
import time
from datetime import datetime

# Global AWS clients
lambda_client = boto3.client('lambda')
cloudwatch = boto3.client('logs')
dynamodb = boto3.resource('dynamodb')

# Environment variables
TARGET_LAMBDA = os.environ.get('test_lambda', 'test123')
S3_URL = os.environ.get('s3_url', 'https://userdata-webserver.s3.us-west-1.amazonaws.com/test.txt')
DYNAMODB_TABLE = os.environ.get('dynamodb_table', 'TroubleshootingLogs')
TABLE = dynamodb.Table(DYNAMODB_TABLE)

def check_network():
    print(f"🔍 Checking S3: {S3_URL}")
    start_time = time.monotonic()
    try:
        response = requests.get(S3_URL, timeout=2)
        latency = (time.monotonic() - start_time) * 1000
        current_time = int(time.time() * 1000)
        print(f"✅ S3 latency: {latency:.2f} ms | Time: {datetime.utcfromtimestamp(current_time / 1000).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        return {'timestamp': current_time, 'issue': 'High S3 latency', 'latency_ms': latency} if latency > 100 else None
    except requests.RequestException as e:
        print(f"❌ S3 failed: {e}")
        return {'timestamp': int(time.time() * 1000), 'issue': 'S3 connectivity error', 'error': str(e)}

def log_issues_to_dynamodb(issues):
    if not issues:
        print("ℹ️ No issues to log.")
        return
    try:
        with TABLE.batch_writer() as batch:
            for issue in issues:
                batch.put_item(Item={
                    'Timestamp': str(issue['timestamp']),
                    'Issue': issue['issue'],
                    'Details': str(issue.get('latency_ms', issue.get('error', 'N/A')))
                })
        print(f"✅ Logged {len(issues)} issues to DynamoDB: {issues}")
    except Exception as e:
        print(f"❌ DynamoDB batch error: {e}")

def get_lambda_logs(log_group, start_time=int(time.time() - 86400) * 1000, limit=50):  # 24 hours
    try:
        response = cloudwatch.filter_log_events(
            logGroupName=log_group,
            startTime=start_time,
            limit=limit
        )
        issues = [
            {'timestamp': log['timestamp'], 'issue': 'Lambda timeout'}
            for log in response.get('events', [])
            if 'error' in log['message'].lower() or 'timeout' in log['message'].lower()
        ]
        while 'nextToken' in response and len(issues) < limit:
            response = cloudwatch.filter_log_events(
                logGroupName=log_group,
                startTime=start_time,
                limit=limit,
                nextToken=response['nextToken']
            )
            issues.extend([
                {'timestamp': log['timestamp'], 'issue': 'Lambda timeout'}
                for log in response.get('events', [])
                if 'error' in log['message'].lower() or 'timeout' in log['message'].lower()
            ])
        return issues[:limit]
    except Exception as e:
        print(f"❌ Log retrieval error: {e}")
        return []

def lambda_handler(event, context):
    print(f"🔍 Event: {event}")  # Debug line
    print(f"🔍 Checking Lambda: {TARGET_LAMBDA}")
    log_group = f'/aws/lambda/{TARGET_LAMBDA}'
    issues = get_lambda_logs(log_group)

    network_issue = check_network()
    if network_issue:
        issues.append(network_issue)

    log_issues_to_dynamodb(issues)

    print(f"✅ Completed: {len(issues)} issues found.")
    return {'status': 'checked', 'issues': issues}