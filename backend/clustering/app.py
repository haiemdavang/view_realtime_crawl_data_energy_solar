import os
import pandas as pd
from sqlalchemy import create_engine, text
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# --- CẤU HÌNH ENVIRONMENT ---
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

# Connection String
DB_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}"

def get_db_engine():
    return create_engine(DB_URL)

def bulk_update_db(engine, df, table_name, key_column, target_column='cluster_id'):
    """
    Kỹ thuật Bulk Update: Tạo bảng tạm -> Insert -> Update -> Drop.
    Nhanh gấp 100 lần so với Update từng dòng.
    """
    if df.empty: return 0
    
    temp_table = f"temp_{table_name}_clusters"
    
    # Chuẩn bị dữ liệu update
    update_df = df[[key_column, target_column]].copy()
    if 'datetime' in key_column:
        update_df[key_column] = update_df[key_column].astype(str)

    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # 1. Tạo bảng tạm & Insert
            update_df.to_sql(temp_table, conn, if_exists='replace', index=False)
            
            # 2. Update từ bảng tạm sang bảng chính
            if key_column == 'datetime':
                where_clause = f"main.{key_column}::text = temp.{key_column}"
            else:
                where_clause = f"main.{key_column} = temp.{key_column}"

            # Cần đảm bảo cột cluster_id tồn tại trong bảng chính trước
            # (Thường DB Admin phải alter table add column cluster_id int trước)
            
            sql = text(f"""
                UPDATE {table_name} AS main
                SET {target_column} = temp.{target_column}
                FROM {temp_table} AS temp
                WHERE {where_clause};
            """)
            
            result = conn.execute(sql)
            
            # 3. Dọn dẹp
            conn.execute(text(f"DROP TABLE IF EXISTS {temp_table}"))
            trans.commit()
            return result.rowcount
        except Exception as e:
            trans.rollback()
            print(f"❌ Bulk Update Error: {e}")
            raise e

def process_measurements_clustering(engine):
    print("🔹 Running Measurements Clustering...")
    try:
        # 1. Load Data
        query = "SELECT datetime, solar_mw, wind_mw, gas_mw, carbon_intensity FROM electricity_measurements"
        df = pd.read_sql(query, engine)
        
        if df.empty:
            print("⚠️ No measurements data found.")
            return
            
        # 2. Preprocessing
        features = ['solar_mw', 'wind_mw', 'gas_mw', 'carbon_intensity']
        X = df[features].fillna(0)
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # 3. K-Means
        kmeans = KMeans(n_clusters=3, random_state=42, n_init='auto')
        df['cluster_id'] = kmeans.fit_predict(X_scaled)

        # 4. Save to DB
        updated = bulk_update_db(engine, df, 'electricity_measurements', 'datetime')
        print(f"✅ Measurements: Updated {updated} rows.")
        return True
    except Exception as e:
        print(f"❌ Error in Measurements Clustering: {e}")
        return False

def process_predictions_clustering(engine):
    print("🔹 Running Predictions Clustering...")
    try:
        # 1. Load Data
        # Cần check xem bảng có tồn tại không để tránh lỗi crash
        try:
            query = "SELECT id, predicted_solar_mw FROM solar_predictions"
            df = pd.read_sql(query, engine)
        except Exception:
            print("⚠️ Table 'solar_predictions' does not exist yet.")
            return

        if df.empty:
            print("⚠️ No prediction data found.")
            return

        # 2. Preprocessing
        X = df[['predicted_solar_mw']].fillna(0)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # 3. K-Means
        kmeans = KMeans(n_clusters=3, random_state=42, n_init='auto')
        df['cluster_id'] = kmeans.fit_predict(X_scaled)

        # 4. Save to DB
        updated = bulk_update_db(engine, df, 'solar_predictions', 'id')
        print(f"✅ Predictions: Updated {updated} rows.")
        return True
    except Exception as e:
        print(f"❌ Error in Predictions Clustering: {e}")
        return False

def run_clustering_job():
    print("--- Starting Clustering Job ---")
    try:
        engine = get_db_engine()
        
        # Chạy tuần tự 2 task
        task1 = process_measurements_clustering(engine)
        task2 = process_predictions_clustering(engine)
        
        engine.dispose()
        
        if task1 or task2:
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ Critical Job Error: {e}")
        return False