import boto3
import os
import time
import json
from datetime import datetime, timedelta

# AWS Clients
dynamodb = boto3.resource('dynamodb')
DYNAMODB_TABLE = os.environ.get('dynamodb_table', 'TroubleshootingLogs')
TABLE = dynamodb.Table(DYNAMODB_TABLE)

def get_recent_logs(limit=50, lookback_hours=24):
    """Fetch recent logs efficiently using Query (NOT Scan)"""
    try:
        # Define time window (last 96 hours)
        now = int(time.time() * 1000)
        lookback_time = now - (lookback_hours * 60 * 60 * 1000)  # Convert hours to ms

        # Query for logs within time range
        response = TABLE.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('Timestamp').gte(str(lookback_time)),
            Limit=limit,
            ScanIndexForward=False  # Get latest logs first
        )
        logs = response.get('Items', [])

        print(f"✅ Retrieved {len(logs)} logs from DynamoDB")
        return logs
    except Exception as e:
        print(f"❌ DynamoDB query error: {e}")
        return []

def lambda_handler(event, context):
    """Lambda function returns logs in JSON"""
    print("🔍 Fetching recent logs...")

    logs = get_recent_logs(limit=10, lookback_hours=96)

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(logs)
    }
