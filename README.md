Here’s a detailed README.md for your GitHub repo that provides a full overview of your Serverless Troubleshooting Dashboard project. It’s organized, includes setup instructions for rebuilding, and assumes you’ll include your existing code files (troubleshooting_lambda.py and dashboard_lambda.py). I’ve kept it clear and professional, with steps to recreate it from scratch using your code.
markdown
# Serverless Troubleshooting Dashboard

A serverless AWS project that monitors Lambda timeouts and S3 latency, logs issues to DynamoDB, and displays them on an S3-hosted dashboard. Built to showcase AWS Cloud Support skills with automation, cost-efficiency, and a user-friendly UI.

## Project Overview

This project automates troubleshooting for serverless applications using AWS services. It consists of two Lambda functions: one for diagnostics and logging, and another for generating a web dashboard. EventBridge schedules daily runs, keeping costs at ~$0.0011/month outside the Free Tier.

### Features
- **Diagnostics:** Monitors Lambda (`test123`) timeouts and S3 latency, logging to DynamoDB.
- **Automation:** Runs daily via EventBridge (`rate(1 day)`).
- **Dashboard:** Displays up to 50 recent issues in Pacific Time, hosted on S3 with CSS/JS styling.
- **Resilience:** Handles invalid data with fallback logic.

### Architecture
- **Lambda 1 (`troubleshooting-lambda`):** Checks `test123` logs and S3 latency, writes to `TroubleshootingLogs` DynamoDB table.
- **Lambda 2 (`dashboard-lambda`):** Queries DynamoDB, generates `index.html`, uploads to S3 bucket `userdata-webserver`.
- **EventBridge:** Triggers both Lambdas daily.
- **DynamoDB:** Stores issues (`Timestamp`, `Issue`, `Details`).
- **S3:** Hosts static dashboard and assets (`styles.css`, `script.js`).

## Prerequisites
- AWS Account (post-Free Tier assumed).
- AWS CLI configured (`aws configure`).
- Python 3.9+ with `boto3` and `requests` (for `troubleshooting-lambda`).
- GitHub repo with code files: `troubleshooting_lambda.py`, `dashboard_lambda.py`.

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/serverless-troubleshooting-dashboard.git
cd serverless-troubleshooting-dashboard
2. Deploy troubleshooting-lambda
Code: troubleshooting_lambda.py
Requirements: Install requests locally:
bash
pip install requests -t .
cp troubleshooting_lambda.py .
zip -r function.zip .
Create Lambda:
bash
aws lambda create-function --function-name troubleshooting-lambda --runtime python3.9 --role arn:aws:iam::YOUR_ACCOUNT_ID:role/Diagnostic-Lamda-role-c0f41t91 --handler troubleshooting_lambda.lambda_handler --zip-file fileb://function.zip --region us-west-1
Environment Variables:
bash
aws lambda update-function-configuration --function-name troubleshooting-lambda --environment "Variables={test_lambda=test123,s3_url=https://userdata-webserver.s3.us-west-1.amazonaws.com/test.txt,dynamodb_table=TroubleshootingLogs}" --region us-west-1
IAM Role: Ensure Diagnostic-Lamda-role-c0f41t91 has:
json
{
    "Effect": "Allow",
    "Action": ["lambda:GetFunction", "logs:FilterLogEvents", "s3:GetObject", "dynamodb:PutItem"],
    "Resource": "*"
}
3. Create DynamoDB Table
bash
aws dynamodb create-table --table-name TroubleshootingLogs --attribute-definitions AttributeName=Timestamp,AttributeType=S --key-schema AttributeName=Timestamp,KeyType=HASH --billing-mode PAY_PER_REQUEST --region us-west-1
4. Deploy dashboard-lambda
Code: dashboard_lambda.py
Deploy:
bash
cp dashboard_lambda.py .
zip function.zip dashboard_lambda.py
aws lambda create-function --function-name dashboard-lambda --runtime python3.9 --role arn:aws:iam::YOUR_ACCOUNT_ID:role/Diagnostic-Lamda-role-c0f41t91 --handler dashboard_lambda.lambda_handler --zip-file fileb://function.zip --region us-west-1
Environment Variables:
bash
aws lambda update-function-configuration --function-name dashboard-lambda --environment "Variables={dynamodb_table=TroubleshootingLogs,s3_bucket=userdata-webserver}" --region us-west-1
IAM Update: Add to role:
json
{
    "Effect": "Allow",
    "Action": ["dynamodb:Scan", "s3:PutObject", "s3:PutObjectAcl"],
    "Resource": "*"
}
5. Configure S3 Bucket
Static Hosting:
Console: S3 > userdata-webserver > Properties > Enable static hosting > Index: index.html.
Bucket Policy:
bash
echo '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":"*","Action":"s3:GetObject","Resource":"arn:aws:s3:::userdata-webserver/*"}]}' > policy.json
aws s3api put-bucket-policy --bucket userdata-webserver --policy file://policy.json --region us-west-1
Assets: Upload CSS/JS (create locally first):
bash
aws s3 cp styles.css s3://userdata-webserver/assets/styles.css --acl public-read --region us-west-1
aws s3 cp script.js s3://userdata-webserver/assets/script.js --acl public-read --region us-west-1
6. Schedule with EventBridge
Create Rule:
bash
aws events put-rule --name CheckLambdaAndS3 --schedule-expression "rate(1 day)" --region us-west-1
Add Targets:
bash
aws events put-targets --rule CheckLambdaAndS3 --targets "Id=1,Arn=arn:aws:lambda:us-west-1:YOUR_ACCOUNT_ID:function:troubleshooting-lambda" "Id=2,Arn=arn:aws:lambda:us-west-1:YOUR_ACCOUNT_ID:function:dashboard-lambda" --region us-west-1
Permissions:
bash
aws lambda add-permission --function-name troubleshooting-lambda --statement-id EventBridgeInvoke --action "lambda:InvokeFunction" --principal events.amazonaws.com --source-arn arn:aws:events:us-west-1:YOUR_ACCOUNT_ID:rule/CheckLambdaAndS3 --region us-west-1
aws lambda add-permission --function-name dashboard-lambda --statement-id EventBridgeInvoke2 --action "lambda:InvokeFunction" --principal events.amazonaws.com --source-arn arn:aws:events:us-west-1:YOUR_ACCOUNT_ID:rule/CheckLambdaAndS3 --region us-west-1
7. Test the Setup
Manual Test:
Invoke troubleshooting-lambda with {} event to log issues.
Invoke dashboard-lambda with {} event to generate the dashboard.
View: http://userdata-webserver.s3-website-us-west-1.amazonaws.com
8. Pause (Optional)
Disable Rule:
bash
aws events disable-rule --name CheckLambdaAndS3 --region us-west-1
Re-enable:
bash
aws events enable-rule --name CheckLambdaAndS3 --region us-west-1
Files
troubleshooting_lambda.py: Diagnostics and logging Lambda.
dashboard_lambda.py: Dashboard generation Lambda.
styles.css: Dashboard styling (example in Setup #5).
script.js: Refresh button logic (example in Setup #5).
Cost
$0.0011/month (0.11 cents) with daily runs outside Free Tier.
Troubleshooting
No Data: Run test123 Lambda to generate timeouts, then re-run troubleshooting-lambda.
Dashboard Blank: Check S3 static hosting and bucket policy.
Errors: Review CloudWatch logs (/aws/lambda/troubleshooting-lambda, /aws/lambda/dashboard-lambda).
License
MIT License - feel free to adapt and share!
Replace YOUR_ACCOUNT_ID with your AWS account ID (e.g., ************ from your setup). Add your code files to the repo, and optionally include styles.css and script.js examples.
