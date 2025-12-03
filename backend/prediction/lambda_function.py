import json
from app import run_prediction_job

def lambda_handler(event, context):
    print("🚀 Lambda Prediction Triggered")
    
    success = run_prediction_job()
    
    if success:
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Prediction 24h Success'})
        }
    else:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Prediction Failed (Check CloudWatch logs)'})
        }