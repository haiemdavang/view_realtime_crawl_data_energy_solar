import logging
import json
from app import run_realtime_job, run_backfill_job

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    AWS Lambda Entry Point.
    Hỗ trợ payload: {"action": "backfill", "start_date": "2025-11-25"}
    """
    logger.info(f"🚀 Event Received: {json.dumps(event)}")
    
    action = 'realtime'
    force_start_date = None # Biến để chứa ngày bắt đầu (nếu có)
    
    # 1. Trích xuất tham số từ Event
    if isinstance(event, dict):
        # Trường hợp gọi trực tiếp (như boto3 invoke hoặc Test console)
        if 'action' in event:
            action = event['action']
            force_start_date = event.get('start_date') # Lấy start_date
            
        # Trường hợp gọi qua API Gateway Proxy (nếu có dùng)
        elif 'queryStringParameters' in event and event['queryStringParameters']:
             params = event['queryStringParameters']
             action = params.get('action', 'realtime')
             force_start_date = params.get('start_date')

    try:
        if action == 'backfill':
            # 2. Truyền start_date vào hàm xử lý
            logger.info(f"Triggering Backfill Job... (Start Date: {force_start_date})")
            run_backfill_job(force_start_date=force_start_date)
            message = f"Backfill job completed (Start: {force_start_date})."
        else:
            logger.info("Triggering Realtime Job...")
            run_realtime_job()
            message = "Realtime job completed."

        return {
            'statusCode': 200,
            'body': json.dumps({'message': message})
        }

    except Exception as e:
        logger.error(f"Function failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }