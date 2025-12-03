import os
import time
import requests
import psycopg2
from datetime import datetime, timedelta, timezone

# --- CẤU HÌNH ENVIRONMENT ---
AUTH_TOKEN = os.getenv("AUTH_TOKEN")
ZONE = "US-CAL-LDWP"
# Mặc định backfill 30 ngày nếu không có dữ liệu
HISTORY_DAYS = int(os.getenv("HISTORY_DAYS", 30)) 

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

def get_db_connection():
    """Tạo kết nối đến PostgreSQL."""
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

def fetch_data_from_api(url, params, max_retries=3):
    """Gọi API ElectricityMaps với Retry."""
    headers = {"auth-token": AUTH_TOKEN}
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30) # Tăng timeout vì response có thể nặng
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                wait_time = 5 * (attempt + 1)
                print(f"[WARN] Rate limit! Đợi {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"[ERROR] API Code {response.status_code}: {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Lỗi kết nối: {e}")
            time.sleep(2)
    return None

def save_to_db(data_item):
    """
    Lưu 1 record vào DB.
    FIX: Đổi sang dùng powerConsumptionBreakdown để lấy dữ liệu tiêu thụ (bao gồm nhập khẩu).
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        dt_str = data_item.get('datetime') 
        zone_id = data_item.get('zone')
        
        # Carbon Intensity
        carbon = data_item.get('carbonIntensity', 0) 
        
        # --- THAY ĐỔI Ở ĐÂY ---
        # Ưu tiên lấy Consumption (Tiêu thụ)
        # Nếu Consumption không có thì mới lấy Production (dự phòng)
        consumption = data_item.get('powerConsumptionBreakdown', {}) or {}
        production = data_item.get('powerProductionBreakdown', {}) or {}
        
        # Dùng consumption làm nguồn chính
        source_data = consumption if consumption else production
        
        # Helper để lấy giá trị an toàn
        def get_val(key):
            val = source_data.get(key)
            return val if val is not None else 0

        solar = get_val('solar')
        wind = get_val('wind')
        gas = get_val('gas')
        unknown = get_val('unknown')
        hydro = get_val('hydro')
        biomass = get_val('biomass')
        nuclear = get_val('nuclear')
        geothermal = get_val('geothermal')
        
        # Debug: In ra nếu thấy dữ liệu vẫn bằng 0 để kiểm tra
        if solar == 0 and wind == 0 and gas == 0:
            print(f"[WARN] Data is all zeros for {dt_str}. Check API response.")

        sql = """
            INSERT INTO electricity_measurements 
            (datetime, zone, carbon_intensity, solar_mw, wind_mw, gas_mw, unknown_mw, 
             hydro_mw, biomass_mw, nuclear_mw, geothermal_mw)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (datetime) DO UPDATE SET
                carbon_intensity = EXCLUDED.carbon_intensity,
                solar_mw = EXCLUDED.solar_mw,
                wind_mw = EXCLUDED.wind_mw,
                gas_mw = EXCLUDED.gas_mw,
                unknown_mw = EXCLUDED.unknown_mw,
                hydro_mw = EXCLUDED.hydro_mw,
                biomass_mw = EXCLUDED.biomass_mw,
                nuclear_mw = EXCLUDED.nuclear_mw,
                geothermal_mw = EXCLUDED.geothermal_mw;
        """
        cur.execute(sql, (dt_str, zone_id, carbon, solar, wind, gas, unknown, 
                          hydro, biomass, nuclear, geothermal))
        conn.commit()
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"[DB ERROR] {e} | Data: {dt_str}")
        
def run_realtime_job():
    """Job chính: Lấy dữ liệu mới nhất (Giữ nguyên)."""
    print(f"--- Starting Realtime Job: {datetime.now()} ---")
    url = "https://api.electricitymaps.com/v3/power-breakdown/latest"
    params = {"zone": ZONE}
    data = fetch_data_from_api(url, params)
    
    if data:
        save_to_db(data)
        print(f"[SUCCESS] Realtime data saved for {data.get('datetime')}")
    else:
        print("[INFO] Không lấy được dữ liệu Realtime.")

def run_backfill_job(force_start_date=None):
    """
    Job phụ: Dùng API /past-range để lấy cục dữ liệu lớn 1 lần.
    """
    print("--- Starting Bulk Backfill Job (Range API) ---")
    
    now_utc = datetime.now(timezone.utc)
    
    # 1. Xác định Start Date
    if force_start_date:
        start_date = datetime.strptime(force_start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        print(f"⚠️ FORCED BACKFILL from: {start_date}")
    else:
        # Check DB xem dữ liệu mới nhất là khi nào
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT MAX(datetime) FROM electricity_measurements WHERE zone = %s;", (ZONE,))
            result = cur.fetchone()
            cur.close()
            conn.close()
            latest_db_time = result[0] if result else None
        except Exception:
            latest_db_time = None

        if latest_db_time:
            if latest_db_time.tzinfo is None:
                latest_db_time = latest_db_time.replace(tzinfo=timezone.utc)
            start_date = latest_db_time + timedelta(hours=1)
        else:
            start_date = now_utc - timedelta(days=HISTORY_DAYS)

    # 2. Xác định End Date (Là hiện tại)
    # Lưu ý: API ElectricityMaps giới hạn range tối đa là 10 ngày (240 giờ) mỗi lần gọi.
    # Nên chúng ta cần chia nhỏ nếu khoảng thời gian > 10 ngày.
    
    current_chunk_start = start_date
    
    while current_chunk_start < now_utc:
        # Lấy tối đa 10 ngày mỗi lần gọi (để an toàn với API limit)
        chunk_end = min(current_chunk_start + timedelta(days=10), now_utc)
        
        # Format ISO string cho API
        start_str = current_chunk_start.isoformat()
        end_str = chunk_end.isoformat()
        
        print(f"📥 Fetching range: {start_str} -> {end_str}")
        
        url = "https://api.electricitymaps.com/v3/power-breakdown/past-range"
        params = {
            "zone": ZONE,
            "start": start_str,
            "end": end_str
        }
        
        response_json = fetch_data_from_api(url, params)
        
        if response_json and 'data' in response_json:
            items = response_json['data']
            print(f"   -> Received {len(items)} records. Saving to DB...")
            
            # Lưu vào DB
            for item in items:
                # API trả về item có key 'datetime', 'powerProductionBreakdown'... khớp với logic save
                save_to_db(item)
                
            print(f"   ✅ Batch saved.")
        else:
            print("   ⚠️ No data received or API error.")
        
        # Move to next chunk
        current_chunk_start = chunk_end
        
        # Nghỉ xíu để ko spam API
        time.sleep(1)

    print("--- Backfill Job Completed ---")