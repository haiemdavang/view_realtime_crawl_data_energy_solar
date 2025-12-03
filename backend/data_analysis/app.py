import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sklearn.preprocessing import MinMaxScaler
from statsmodels.tsa.seasonal import seasonal_decompose

# --- CẤU HÌNH ENVIRONMENT ---
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
# Connection String cho SQLAlchemy
DB_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}"

def init_analysis_db(engine):
    """Khởi tạo bảng nếu chưa tồn tại"""
    sql_analysis = """
    CREATE TABLE IF NOT EXISTS electricity_analysis_results (
        datetime TIMESTAMP PRIMARY KEY,
        solar_mw FLOAT, wind_mw FLOAT, gas_mw FLOAT,
        solar_trend FLOAT, solar_seasonal FLOAT, solar_residual FLOAT,
        solar_normalized FLOAT, wind_normalized FLOAT
    );
    """
    sql_correlation = """
    CREATE TABLE IF NOT EXISTS electricity_correlations (
        id SERIAL PRIMARY KEY,
        feature_x VARCHAR(50), feature_y VARCHAR(50),
        correlation_value FLOAT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        with engine.connect() as conn:
            conn.execute(text(sql_analysis))
            conn.execute(text(sql_correlation))
            conn.commit()
        print("--> [INIT] DB Tables Checked.")
    except Exception as e:
        print(f"--> [INIT ERROR] {e}")

def analyze_correlation(df, engine):
    """Tính toán ma trận tương quan và lưu vào DB"""
    print("🔍 Running Correlation Analysis...")
    cols = ['solar_mw', 'wind_mw', 'gas_mw', 'solar_trend', 'solar_seasonal', 'solar_residual']
    existing_cols = [c for c in cols if c in df.columns]
    
    if not existing_cols:
        return

    # Tính toán
    corr_matrix = df[existing_cols].corr()
    
    # Chuyển đổi sang dạng Long Format (x, y, value)
    corr_long = corr_matrix.stack().reset_index()
    corr_long.columns = ['feature_x', 'feature_y', 'correlation_value']

    try:
        with engine.connect() as conn:
            conn.execute(text("TRUNCATE TABLE electricity_correlations"))
            conn.commit()
        
        corr_long.to_sql('electricity_correlations', engine, if_exists='append', index=False, method='multi')
        print(f"--> Saved {len(corr_long)} correlation records.")
    except Exception as e:
        print(f"❌ Error saving correlations: {e}")

def run_analysis_job():
    """Hàm chính: Thực hiện Analysis Pipeline"""
    print("--- Starting Analysis Job ---")
    try:
        engine = create_engine(DB_URL)
        init_analysis_db(engine)
        
        # 1. LOAD DATA
        query = "SELECT datetime, solar_mw, wind_mw, gas_mw FROM electricity_measurements ORDER BY datetime ASC"
        df = pd.read_sql(query, engine)
        
        if df.empty or len(df) < 24:
            print("⚠️ Not enough data for analysis (< 24 records).")
            return

        # 2. PREPROCESSING
        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True)
        
        # Resample theo giờ và điền dữ liệu thiếu
        df_clean = df.resample('h').mean().interpolate(method='linear').fillna(0)

        # 3. DECOMPOSITION (Seasonal)
        # Khởi tạo giá trị mặc định
        df_clean['solar_trend'] = 0.0
        df_clean['solar_seasonal'] = 0.0
        df_clean['solar_residual'] = 0.0

        # Chỉ chạy decompose nếu đủ dữ liệu (2 chu kỳ = 48h)
        if len(df_clean) >= 48:
            try:
                decomposition = seasonal_decompose(df_clean['solar_mw'], model='additive', period=24)
                df_clean['solar_trend'] = decomposition.trend.fillna(0)
                df_clean['solar_seasonal'] = decomposition.seasonal.fillna(0)
                df_clean['solar_residual'] = decomposition.resid.fillna(0)
            except Exception as e:
                print(f"⚠️ Decompose failed: {e}")
        
        # Tính tương quan
        analyze_correlation(df_clean, engine)

        # 4. NORMALIZATION (Cho AI Model sau này)
        scaler = MinMaxScaler()
        df_clean[['solar_normalized', 'wind_normalized']] = scaler.fit_transform(df_clean[['solar_mw', 'wind_mw']])

        # 5. STORE RESULTS
        df_final = df_clean.reset_index().fillna(0)
        
        with engine.connect() as conn:
            conn.execute(text("TRUNCATE TABLE electricity_analysis_results"))
            conn.commit()
            
        df_final.to_sql('electricity_analysis_results', engine, if_exists='append', index=False, method='multi')
        print("--> Analysis pipeline completed successfully.")

    except Exception as e:
        print(f"❌ Critical Error in Analysis Job: {e}")
        raise e 