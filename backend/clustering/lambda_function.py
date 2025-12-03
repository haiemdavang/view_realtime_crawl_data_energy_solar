import json
from app import run_clustering_job

def lambda_handler(event, context):
    print("🚀 Lambda Clustering Triggered")
    
    # Chạy hàm logic
    success = run_clustering_job()
    
    if success:
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Clustering tasks completed successfully'})
        }
    else:
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Clustering finished with no updates (check logs)'})
        }