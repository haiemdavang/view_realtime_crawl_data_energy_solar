import logging
import json
from app import run_analysis_job

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info("🚀 Lambda Analysis Triggered!")
    try:
        # Gọi hàm xử lý chính
        run_analysis_job()
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Analysis Job Completed Successfully'})
        }
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }