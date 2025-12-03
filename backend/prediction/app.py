import os
import joblib
import numpy as np
import pandas as pd
import psycopg2
import tensorflow as tf
from datetime import datetime, timedelta

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

BASE_DIR = os.environ.get('LAMBDA_TASK_ROOT', '')
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'solar_mlp.keras')
SCALER_PATH = os.path.join(BASE_DIR, 'models', 'scaler.pkl')

model = None
scaler = None

print("⏳ Initializing Prediction Service...")
try:
    # Load model Keras (chỉ load 1 lần
    model = tf.keras.models.load_model(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    print("✅ Model & Scaler loaded successfully.")
except Exception as e:
    print(f"⚠️ CRITICAL: Could not load model/scaler: {e}")

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS
    )

def fetch_recent_data():
    """
    Lấy dữ liệu lịch sử để tính toán features (Lag, Trend...).
    Cần lấy dư ra (ví dụ 100 dòng) để đảm bảo tính đủ Lag 24h.
    """
    query = """
        SELECT datetime, solar_mw, solar_trend, solar_seasonal, solar_normalized 
        FROM electricity_analysis_results
        ORDER BY datetime DESC LIMIT 100
    """
    try:
        conn = get_db_connection()
        df = pd.read_sql(query, conn)
        conn.close()
        # Đảo ngược lại để có thứ tự thời gian tăng dần (Cũ -> Mới)
        return df.iloc[::-1].reset_index(drop=True)
    except Exception as e:
        print(f"❌ DB Error: {e}")
        return pd.DataFrame()

def prepare_features(df):
    """
    Tạo input vector (1, 7) cho Model.
    Thứ tự feature phải KHỚP 100% với lúc train.
    """
    if len(df) < 25:
        print("⚠️ Not enough data history.")
        return None, None

    df['datetime'] = pd.to_datetime(df['datetime'])
    
    # Feature Engineering
    df['solar_mw_lag1'] = df['solar_mw'].shift(1)
    df['solar_mw_lag24'] = df['solar_mw'].shift(24)
    df['hour'] = df['datetime'].dt.hour
    df['day_of_week'] = df['datetime'].dt.dayofweek
    
    # Lấy dòng cuối cùng (Latest) hợp lệ
    valid_df = df.dropna().tail(1)
    
    if valid_df.empty:
        return None, None
        
    latest = valid_df.iloc[0]
    current_time = latest['datetime']
    
    # Tạo vector input chuẩn (1, 7)
    # Thứ tự: [Norm, Trend, Seasonal, Hour, Day, Lag1, Lag24]
    features = np.array([
        latest['solar_normalized'], 
        latest['solar_trend'],      
        latest['solar_seasonal'],   
        latest['hour'],             
        latest['day_of_week'],      
        latest['solar_mw_lag1'],    
        latest['solar_mw_lag24']    
    ]).reshape(1, -1)
    
    return features, current_time

def save_predictions(predictions, start_time):
    """Lưu kết quả dự báo 24h vào DB"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Tạo bảng prediction nếu chưa có
        cur.execute("""
            CREATE TABLE IF NOT EXISTS solar_predictions (
                id SERIAL PRIMARY KEY,
                prediction_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                target_time TIMESTAMP,
                predicted_solar_mw FLOAT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        values = []
        for i, val in enumerate(predictions):
            target_time = start_time + timedelta(hours=i + 1)
            val_mw = max(float(val), 0.0) # Không lấy số âm
            values.append((target_time, val_mw))
        
        # Batch Insert
        args_str = ','.join(cur.mogrify("(NOW(), %s, %s)", x).decode('utf-8') for x in values)
        cur.execute("INSERT INTO solar_predictions (prediction_time, target_time, predicted_solar_mw) VALUES " + args_str)
        
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ Saved predictions for next 24 hours.")
    except Exception as e:
        print(f"❌ Save Error: {e}")

def run_prediction_job():
    print(f"--- Starting Prediction Job: {datetime.now()} ---")
    
    if model is None:
        print("❌ Model is NOT loaded. Cannot predict.")
        return False

    # 1. Fetch Data
    df = fetch_recent_data()
    if df.empty: return False

    # 2. Prepare Features
    X_input, current_time = prepare_features(df)
    if X_input is None: 
        print("⚠️ Not enough valid data for feature engineering.")
        return False

    # 3. Predict using TensorFlow Model
    try:
        print(f"🔮 Predicting for time > {current_time}...")
        # Model trả về (1, 24) -> flatten thành (24,)
        preds = model.predict(X_input, verbose=0).flatten()
        
        save_predictions(preds, current_time)
        return True
    except Exception as e:
        print(f"❌ Prediction Logic Error: {e}")
        return False