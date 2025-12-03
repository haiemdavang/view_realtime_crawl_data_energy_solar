import os
import json
import boto3
from fastapi import FastAPI, Query, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
import numpy as np
from pydantic import BaseModel
from sqlalchemy import create_engine, text

load_dotenv()

app = FastAPI(
    title="Electricity Maps LA Analysis API",
    description="API for electricity data analysis of Los Angeles grid (AWS Lambda Integration)",
    version="2.0.0"
)

# --- CẤU HÌNH CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CẤU HÌNH DB ---
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "electricity_db"),
    "user": os.getenv("DB_USER", "cgdc"),
    "password": os.getenv("DB_PASS", "112acc"),
}

DATABASE_URL = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
engine = create_engine(DATABASE_URL)

# --- CẤU HÌNH AWS LAMBDA ---
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-1")

LAMBDA_MAPPING = {
    "ingestion": "ingestion-lambda",
    "analysis": "analysis-lambda",
    "prediction": "prediction-lambda",
    "clustering": "clustering-lambda"
}

# --- HELPER FUNCTIONS ---

def get_db_connection():
    """Tạo kết nối database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

def get_time_range(range_param: str) -> datetime:
    now = datetime.now()
    if range_param == "day": return now - timedelta(days=1)
    elif range_param == "week": return now - timedelta(weeks=1)
    elif range_param == "month": return now - timedelta(days=30)
    else: return now - timedelta(days=1)

def invoke_lambda_service(service_key: str, payload: Dict[str, Any] = {}):
    """
    Hàm dùng chung để kích hoạt AWS Lambda.
    - service_key: tên key trong LAMBDA_MAPPING (vd: 'ingestion')
    - payload: dữ liệu JSON gửi kèm (vd: {'action': 'run-now'})
    """
    function_name = LAMBDA_MAPPING.get(service_key)
    
    if not function_name:
        raise HTTPException(status_code=500, detail=f"Không tìm thấy cấu hình cho service '{service_key}'")

    print(f"[API] Đang kích hoạt Lambda: {function_name} với payload: {payload}", flush=True)

    try:
        # Tạo client boto3 kết nối với Lambda
        client = boto3.client('lambda', region_name=AWS_REGION)
        
        # Gọi Lambda
        # InvocationType='Event': Gọi kiểu bất đồng bộ (Fire & Forget).
        # API sẽ trả về kết quả ngay lập tức mà không cần chờ Lambda chạy xong (thích hợp cho task lâu).
        response = client.invoke(
            FunctionName=function_name,
            InvocationType='Event', 
            Payload=json.dumps(payload)
        )
        
        # StatusCode 202 nghĩa là AWS đã nhận lệnh thành công
        if response['StatusCode'] == 202:
            return {
                "success": True, 
                "message": f"Đã gửi lệnh kích hoạt đến {function_name}", 
                "aws_request_id": response.get("ResponseMetadata", {}).get("RequestId")
            }
        else:
            raise HTTPException(status_code=500, detail=f"AWS trả về status lạ: {response['StatusCode']}")
            
    except Exception as e:
        print(f"[API Error] Lỗi gọi Lambda: {str(e)}", flush=True)
        raise HTTPException(status_code=500, detail=f"Lỗi kích hoạt Lambda: {str(e)}")

# --- TRIGGER ENDPOINTS (GỌI LAMBDA) ---

@app.post("/trigger-ingestion")
async def trigger_ingestion(
    action: str = Body("realtime", embed=True), 
    start_date: Optional[str] = Body(None, embed=True)
):
    """
    Kích hoạt Service Ingestion (Thu thập dữ liệu).
    Body mẫu:
    {
      "action": "backfill",
      "start_date": "2025-11-01"
    }
    """
    payload = {"action": action}
    if start_date:
        payload["start_date"] = start_date
    return invoke_lambda_service("ingestion", payload)

@app.post("/trigger-analysis")
async def trigger_analysis():
    """Kích hoạt Service Analysis (Phân tích Trend, Seasonal)"""
    return invoke_lambda_service("analysis", {"action": "run-now"})

@app.post("/trigger-prediction")
async def trigger_prediction():
    """Kích hoạt Service Prediction (Dự báo AI)"""
    return invoke_lambda_service("prediction", {"action": "run-now"})

@app.post("/trigger-clustering")
async def trigger_clustering():
    """Kích hoạt Service Clustering (Phân cụm)"""
    return invoke_lambda_service("clustering", {"action": "run-now"})

# Giữ endpoint cũ để tương thích ngược (nếu cần)
# @app.post("/trigger-clustering")
# async def trigger_clustering_legacy():
#     return invoke_lambda_service("clustering", {"action": "run-now"})

# --- DATA ENDPOINTS (LẤY DỮ LIỆU) ---


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "Electricity Maps LA Analysis API"}


@app.get("/measurements")
async def get_measurements(range: str = Query("day", enum=["day", "week", "month"])):
    """
    Lấy dữ liệu đo lường từ bảng electricity_measurements
    - range: 'day' (24h), 'week' (7 ngày), 'month' (30 ngày)
    """
    start_time = get_time_range(range)
    
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    datetime,
                    zone,
                    solar_mw,
                    wind_mw,
                    gas_mw,
                    hydro_mw,
                    unknown_mw
                FROM electricity_measurements
                WHERE datetime >= %s
                ORDER BY datetime ASC
            """, (start_time,))
            
            rows = cur.fetchall()
            
            # Chuyển datetime thành ISO string
            for row in rows:
                row['datetime'] = row['datetime'].isoformat()
            
            return {
                "success": True,
                "range": range,
                "count": len(rows),
                "data": rows
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.get("/analysis")
async def get_analysis(range: str = Query("day", enum=["day", "week", "month"])):
    """
    Lấy kết quả phân tích từ bảng electricity_analysis_results
    - Bao gồm: trend, seasonal, normalized data
    """
    start_time = get_time_range(range)
    
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT *
                FROM electricity_analysis_results
                WHERE datetime >= %s
                ORDER BY datetime ASC
            """, (start_time,))
            
            rows = cur.fetchall()
            
            # Chuyển datetime thành ISO string
            for row in rows:
                if row.get('datetime'):
                    row['datetime'] = row['datetime'].isoformat()
            
            return {
                "success": True,
                "range": range,
                "count": len(rows),
                "data": rows
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/predictions")
async def get_predictions():
    """
    Lấy dự đoán solar cho 24h tới từ bảng solar_predictions
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 1. Kiểm tra bảng 'solar_predictions' có tồn tại không
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'solar_predictions'
                )
            """)
            table_exists = cur.fetchone()['exists']
            
            if not table_exists:
                return {
                    "success": True,
                    "message": "Predictions table (solar_predictions) not yet created",
                    "data": []
                }
            
            # 2. Query dữ liệu
            cur.execute("""
                SELECT id, prediction_time, target_time, predicted_solar_mw, cluster_id,created_at
                FROM solar_predictions
                WHERE target_time >= NOW()
                ORDER BY target_time ASC
                LIMIT 24
            """)
            
            rows = cur.fetchall()
            
            # 3. Format lại ngày giờ sang dạng chuỗi ISO để trả về JSON không bị lỗi
            for row in rows:
                if row.get('target_time'):
                    row['target_time'] = row['target_time'].isoformat()
                if row.get('prediction_time'):
                    row['prediction_time'] = row['prediction_time'].isoformat()
                if row.get('created_at'):
                    row['created_at'] = row['created_at'].isoformat()
            
            return {
                "success": True,
                "count": len(rows),
                "data": rows
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.get("/status/latest")
async def get_latest_status():
    """
    Lấy trạng thái mới nhất.
    Ưu tiên lấy cluster_id trực tiếp từ bản ghi đo lường mới nhất trong electricity_measurements.
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Lấy measurement mới nhất
            cur.execute("""
                SELECT *
                FROM electricity_measurements
                ORDER BY datetime DESC
                LIMIT 1
            """)
            latest_measurement = cur.fetchone()
            
            # Xử lý datetime
            if latest_measurement and latest_measurement.get('datetime'):
                latest_measurement['datetime'] = latest_measurement['datetime'].isoformat()
            
            # Tính tổng công suất
            total_mw = 0
            current_cluster_id = None

            if latest_measurement:
                # Tính tổng load
                for key in ['solar_mw', 'wind_mw', 'gas_mw', 'hydro_mw', 'unknown_mw']:
                    if latest_measurement.get(key):
                        total_mw += latest_measurement[key]
                
                # Lấy cluster_id trực tiếp từ measurement
                # Nếu là -1 (chưa phân cụm) hoặc None thì trả về None
                cid = latest_measurement.get('cluster_id')
                if cid is not None and cid != -1:
                    current_cluster_id = cid
            
            return {
                "success": True,
                "latest_measurement": latest_measurement,
                "total_power_mw": total_mw,
                "current_cluster_id": current_cluster_id, # Trả về field này rõ ràng cho frontend
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/analysis/correlations")
async def get_correlations():
    """
    Tính ma trận tương quan giữa các nguồn năng lượng
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Lấy dữ liệu 7 ngày gần nhất để tính correlation
            cur.execute("""
                SELECT 
                    COALESCE(solar_mw, 0) as solar_mw,
                    COALESCE(wind_mw, 0) as wind_mw,
                    COALESCE(gas_mw, 0) as gas_mw,
                    COALESCE(hydro_mw, 0) as hydro_mw
                FROM electricity_measurements
                WHERE datetime >= NOW() - INTERVAL '7 days'
                ORDER BY datetime ASC
            """)
            
            rows = cur.fetchall()
            
            if len(rows) < 10:
                return {
                    "success": True,
                    "message": "Not enough data for correlation (need at least 10 records)",
                    "correlations": None,
                    "data_points": len(rows)
                }
            
            # Tính correlation bằng Python
            columns = ['solar_mw', 'wind_mw', 'gas_mw', 'hydro_mw']
            data = {col: [] for col in columns}
            
            for row in rows:
                for col in columns:
                    val = row.get(col)
                    data[col].append(float(val) if val is not None else 0.0)
            
            # Tạo matrix và tính correlation
            matrix = np.array([data[col] for col in columns], dtype=np.float64)
            
            # Tính correlation với xử lý NaN/Inf
            with np.errstate(divide='ignore', invalid='ignore'):
                correlation_matrix = np.corrcoef(matrix)
            
            # Thay NaN và Inf bằng 0
            correlation_matrix = np.nan_to_num(correlation_matrix, nan=0.0, posinf=0.0, neginf=0.0)
            
            # Chuyển thành dict
            correlations = {}
            for i, col1 in enumerate(columns):
                correlations[col1] = {}
                for j, col2 in enumerate(columns):
                    val = correlation_matrix[i][j]
                    # Đảm bảo giá trị là số hợp lệ
                    if np.isnan(val) or np.isinf(val):
                        correlations[col1][col2] = 0.0
                    else:
                        correlations[col1][col2] = round(float(val), 4)
            
            return {
                "success": True,
                "columns": columns,
                "correlations": correlations,
                "data_points": len(rows)
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/clustering")
async def get_clustering_results(range: str = Query("week", enum=["day", "week", "month"])):
    """
    Lấy kết quả clustering từ cột cluster_id trong bảng electricity_measurements
    """
    start_time = get_time_range(range)
    
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Lấy dữ liệu có cluster_id
            cur.execute("""
                SELECT 
                    datetime,
                    zone,
                    solar_mw,
                    wind_mw,
                    gas_mw,
                    hydro_mw,
                    unknown_mw,
                    cluster_id
                FROM electricity_measurements
                WHERE datetime >= %s
                    AND cluster_id IS NOT NULL
                    AND cluster_id != -1
                ORDER BY datetime ASC
            """, (start_time,))
            
            rows = cur.fetchall()
            
            for row in rows:
                if row.get('datetime'):
                    row['datetime'] = row['datetime'].isoformat()
            
            # Thống kê số lượng mỗi cluster
            cluster_stats = {}
            for row in rows:
                cid = row.get('cluster_id')
                if cid is not None:
                    cluster_stats[cid] = cluster_stats.get(cid, 0) + 1
            
            return {
                "success": True,
                "range": range,
                "count": len(rows),
                "cluster_stats": cluster_stats,
                "data": rows
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.get("/clustering-prediction")
async def get_clustering_predictions():
    """
    Lấy kết quả clustering từ cột cluster_id trong bảng solar_predictions
    Chỉ trả về các dự đoán đã được phân cụm (cluster_id != -1)
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Kiểm tra bảng solar_predictions có tồn tại không
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'solar_predictions'
                )
            """)
            table_exists = cur.fetchone()['exists']
            
            if not table_exists:
                return {
                    "success": True,
                    "message": "Predictions table (solar_predictions) not yet created",
                    "data": []
                }
            
            # Lấy dữ liệu có cluster_id != -1
            cur.execute("""
                SELECT 
                    id,
                    prediction_time,
                    target_time,
                    predicted_solar_mw,
                    created_at,
                    cluster_id
                FROM solar_predictions
                WHERE cluster_id IS NOT NULL 
                    AND cluster_id != -1
                ORDER BY target_time ASC
            """)
            
            rows = cur.fetchall()
            
            # Format datetime thành ISO string
            for row in rows:
                if row.get('prediction_time'):
                    row['prediction_time'] = row['prediction_time'].isoformat()
                if row.get('target_time'):
                    row['target_time'] = row['target_time'].isoformat()
                if row.get('created_at'):
                    row['created_at'] = row['created_at'].isoformat()
            
            # Thống kê số lượng mỗi cluster
            cluster_stats = {}
            for row in rows:
                cid = row.get('cluster_id')
                if cid is not None and cid != -1:
                    cluster_stats[cid] = cluster_stats.get(cid, 0) + 1
            
            return {
                "success": True,
                "count": len(rows),
                "cluster_stats": cluster_stats,
                "data": rows
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/analysis/trend")
async def get_trend_analysis(range: str = Query("month", enum=["week", "month", "year"])):
    """
    API phục vụ vẽ biểu đồ Trend.
    Thực hiện Resampling dữ liệu để giảm nhiễu:
    - Nếu range = month/year -> Gom nhóm theo NGÀY (Daily Average)
    - Nếu range = week -> Gom nhóm theo GIỜ (Hourly Average)
    """
    start_time = get_time_range(range)
    
    # Xác định độ phân giải thời gian (Time Bucket)
    if range in ["month", "year"]:
        trunc_interval = "day"  # Gom theo ngày
    else:
        trunc_interval = "hour" # Gom theo giờ
        
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Query tính trung bình theo bucket
            query = f"""
                SELECT 
                    DATE_TRUNC('{trunc_interval}', datetime) as time_bucket,
                    AVG(COALESCE(solar_mw, 0) + COALESCE(wind_mw, 0) + COALESCE(gas_mw, 0) + COALESCE(hydro_mw, 0) + COALESCE(unknown_mw, 0)) as avg_load,
                    AVG(COALESCE(solar_mw, 0)) as avg_solar,
                    AVG(COALESCE(wind_mw, 0)) as avg_wind
                FROM electricity_measurements
                WHERE datetime >= %s
                GROUP BY time_bucket
                ORDER BY time_bucket ASC
            """
            cur.execute(query, (start_time,))
            rows = cur.fetchall()
            
            # Format datetime
            for row in rows:
                if row.get('time_bucket'):
                    row['timestamp'] = row['time_bucket'].isoformat()
                    del row['time_bucket'] # Xóa key cũ cho gọn
            
            return {
                "success": True,
                "range": range,
                "interval": trunc_interval,
                "data": rows
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/analysis/seasonal")
async def get_seasonal_analysis(range: str = Query("month", enum=["week", "month", "year"])):
    """
    API phục vụ vẽ biểu đồ Seasonal (Daily Profile).
    Gom nhóm dữ liệu theo giờ trong ngày (0-23h) để tìm ra mẫu hình tiêu thụ trung bình.
    """
    start_time = get_time_range(range)
    
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Query gom nhóm theo giờ (0-23)
            cur.execute("""
                SELECT 
                    EXTRACT(HOUR FROM datetime) as hour_of_day,
                    AVG(COALESCE(solar_mw, 0) + COALESCE(wind_mw, 0) + COALESCE(gas_mw, 0) + COALESCE(hydro_mw, 0) + COALESCE(unknown_mw, 0)) as avg_load,
                    AVG(COALESCE(solar_mw, 0)) as avg_solar,
                    AVG(COALESCE(wind_mw, 0)) as avg_wind,
                    COUNT(*) as data_points
                FROM electricity_measurements
                WHERE datetime >= %s
                GROUP BY hour_of_day
                ORDER BY hour_of_day ASC
            """, (start_time,))
            
            rows = cur.fetchall()
            
            # Format lại dữ liệu cho dễ dùng ở frontend
            formatted_data = []
            for row in rows:
                formatted_data.append({
                    "hour": int(row['hour_of_day']),
                    "hour_label": f"{int(row['hour_of_day']):02d}:00",
                    "avg_load": round(row['avg_load'], 2),
                    "avg_solar": round(row['avg_solar'], 2),
                    "avg_wind": round(row['avg_wind'], 2)
                })
            
            return {
                "success": True,
                "range": range,
                "data": formatted_data
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)