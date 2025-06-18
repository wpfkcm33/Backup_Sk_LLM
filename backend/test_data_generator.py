import oracledb
import random
from datetime import datetime, timedelta
from decimal import Decimal

def setup_oracle_client():
    """Oracle 클라이언트 초기화"""
    try:
        oracledb.init_oracle_client(lib_dir="/home/humandeep/oracle/instantclient_21_8")
        print("✅ Oracle 클라이언트 초기화 성공")
        return True
    except Exception as e:
        print(f"❌ Oracle 클라이언트 초기화 실패: {e}")
        return False

def get_connection():
    """데이터베이스 연결"""
    try:
        connection = oracledb.connect(
            user='system',           # testuser → system으로 변경
            password='Test123',      # testpass123 → Test123으로 변경
            dsn='localhost:1521/XE'
        )
        print("✅ 데이터베이스 연결 성공")
        return connection
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        return None

def create_test_tables(connection):
    """테스트 테이블 생성"""
    cursor = connection.cursor()
    
    # 테이블 삭제 (이미 존재하는 경우)
    tables_to_drop = [
        'QMS_RAT_YMQT_N', 'QMS_RAT_CUST', 'QMS_GBW_VIEW', 
        'HCOB_COMM_CD_N', 'HCOB_CAL'
    ]
    
    for table in tables_to_drop:
        try:
            cursor.execute(f"DROP TABLE {table} CASCADE CONSTRAINTS")
            print(f"🗑️ 기존 테이블 {table} 삭제")
        except:
            pass  # 테이블이 없으면 무시
    
    # HCOB_CAL 테이블 생성
    cursor.execute("""
        CREATE TABLE HCOB_CAL (
            FISCAL_DAY VARCHAR2(8) PRIMARY KEY,
            PLAN_YEAR VARCHAR2(4),
            PLAN_HALF VARCHAR2(6),
            PLAN_QUARTER VARCHAR2(6),
            PLAN_MONTH VARCHAR2(6),
            JULIAN_DAY NUMBER(5),
            FISCAL_WEEK VARCHAR2(6),
            PLAN_WEEK VARCHAR2(6),
            WEEK_DAY NUMBER(5),
            CAL_GRP1 VARCHAR2(50),
            CAL_GRP2 VARCHAR2(50),
            CAL_GRP3 VARCHAR2(50),
            CAL_GRP4 VARCHAR2(50),
            CRE_PGM_TYP VARCHAR2(50),
            CRE_PGM_NM VARCHAR2(200),
            FST_CREATOR_ID VARCHAR2(100),
            FST_CRE_DTTM VARCHAR2(14),
            LAST_MDFYR_ID VARCHAR2(100),
            LAST_MDFY_DTTM VARCHAR2(14)
        )
    """)
    
    # HCOB_COMM_CD_N 테이블 생성
    cursor.execute("""
        CREATE TABLE HCOB_COMM_CD_N (
            COMM_CD_DIV VARCHAR2(50),
            COMM_CD VARCHAR2(50),
            USE_YN VARCHAR2(1),
            GMDM_CD_YN VARCHAR2(1),
            PRIMARY KEY (COMM_CD_DIV, COMM_CD)
        )
    """)
    
    # QMS_GBW_VIEW 테이블 생성
    cursor.execute("""
        CREATE TABLE QMS_GBW_VIEW (
            PLAN_QUARTER VARCHAR2(20),
            HIQ1_APP_CD VARCHAR2(20),
            HIQ1_CUST_CD VARCHAR2(20),
            AMT NUMBER,
            ACTUAL VARCHAR2(20),
            SCORE VARCHAR2(20),
            MAX_SCORE VARCHAR2(20),
            PRIMARY KEY (PLAN_QUARTER, HIQ1_APP_CD, HIQ1_CUST_CD)
        )
    """)
    
    # QMS_RAT_CUST 테이블 생성
    cursor.execute("""
        CREATE TABLE QMS_RAT_CUST (
            HIQ1_CUST_CD VARCHAR2(20),
            HIQ1_APP_CD VARCHAR2(20),
            APP_CD VARCHAR2(200),
            MODE_GRP VARCHAR2(20),
            USE_YN VARCHAR2(20),
            LAST_MDFY_DT DATE,
            LAST_MDFY_ID VARCHAR2(20),
            MEMO CLOB,
            PRIMARY KEY (HIQ1_CUST_CD, HIQ1_APP_CD, APP_CD)
        )
    """)
    
    # QMS_RAT_YMQT_N 테이블 생성
    cursor.execute("""
        CREATE TABLE QMS_RAT_YMQT_N (
            HIQ1_APP_CD VARCHAR2(20),
            HIQ1_CUST_CD VARCHAR2(20),
            YM_QT VARCHAR2(20),
            REVENUE VARCHAR2(20),
            FORECAST VARCHAR2(20),
            ACTUAL VARCHAR2(20),
            SCORE VARCHAR2(20),
            FILE_GROUP_ID VARCHAR2(50),
            FILE_UPLOAD_USER VARCHAR2(20),
            EXPECTED_DATE DATE,
            PRIMARY KEY (HIQ1_APP_CD, HIQ1_CUST_CD, YM_QT)
        )
    """)
    
    connection.commit()
    cursor.close()
    print("✅ 모든 테이블 생성 완료")

def insert_calendar_data(connection):
    """날짜 공통 테이블 데이터 삽입"""
    cursor = connection.cursor()
    
    # 2024년 4분기부터 2025년 1분기까지 날짜 데이터 생성
    calendar_data = [
        ('20241001', '2024', '2024H2', '202404', '202410', 275, '202440', '202440', 1, 'A', '0', 'B', 'C'),
        ('20241015', '2024', '2024H2', '202404', '202410', 289, '202442', '202442', 2, 'B', '1', 'A', 'C'),
        ('20241101', '2024', '2024H2', '202404', '202411', 306, '202444', '202444', 3, 'C', '0', 'B', 'A'),
        ('20241115', '2024', '2024H2', '202404', '202411', 320, '202446', '202446', 4, 'A', '1', 'C', 'B'),
        ('20241201', '2024', '2024H2', '202404', '202412', 336, '202448', '202448', 5, 'B', '0', 'A', 'C'),
        ('20241215', '2024', '2024H2', '202404', '202412', 350, '202450', '202450', 6, 'C', '1', 'B', 'A'),
        ('20250101', '2025', '2025H1', '202501', '202501', 1, '202501', '202501', 1, 'A', '0', 'B', 'C'),
        ('20250215', '2025', '2025H1', '202501', '202502', 46, '202507', '202507', 2, 'B', '1', 'A', 'C'),
        ('20250301', '2025', '2025H1', '202501', '202503', 60, '202509', '202509', 3, 'C', '0', 'B', 'A'),
    ]
    
    for data in calendar_data:
        cursor.execute("""
            INSERT INTO HCOB_CAL 
            (FISCAL_DAY, PLAN_YEAR, PLAN_HALF, PLAN_QUARTER, PLAN_MONTH, JULIAN_DAY, 
             FISCAL_WEEK, PLAN_WEEK, WEEK_DAY, CAL_GRP1, CAL_GRP2, CAL_GRP3, CAL_GRP4,
             CRE_PGM_TYP, CRE_PGM_NM, FST_CREATOR_ID, FST_CRE_DTTM, LAST_MDFYR_ID, LAST_MDFY_DTTM)
            VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, :12, :13, 
                    'ETL', 'SP_ETL_HCOB_CAL', 'SAP DS', :1 || '083551', 'SAP DS', :1 || '083551')
        """, data)
    
    connection.commit()
    cursor.close()
    print("✅ 날짜 공통 테이블 데이터 삽입 완료")

def insert_common_code_data(connection):
    """공통코드 테이블 데이터 삽입"""
    cursor = connection.cursor()
    
    common_codes = [
        ('COM_20004', '209', 'Y', 'N'),
        ('COM_20004', '210', 'Y', 'Y'),
        ('COM_20004', '211', 'N', 'N'),
        ('CUQ_00004', 'SERVER', 'Y', 'N'),
        ('CUQ_00004', 'CLIENT', 'Y', 'N'),
        ('CUQ_00004', 'HBM', 'Y', 'Y'),
        ('APP_TYPE', 'SV', 'Y', 'N'),
        ('APP_TYPE', 'CL', 'Y', 'N'),
        ('APP_TYPE', 'HB', 'Y', 'N'),
    ]
    
    cursor.executemany("""
        INSERT INTO HCOB_COMM_CD_N (COMM_CD_DIV, COMM_CD, USE_YN, GMDM_CD_YN)
        VALUES (:1, :2, :3, :4)
    """, common_codes)
    
    connection.commit()
    cursor.close()
    print("✅ 공통코드 테이블 데이터 삽입 완료")

def insert_gbw_view_data(connection):
    """GBW VIEW 테이블 데이터 삽입"""
    cursor = connection.cursor()
    
    # 고객 매핑 정보
    customers = [
        ('G669', 'AMD'), ('G113', 'GOOGLE'), ('G150', 'APPLE'), 
        ('G932', 'AMAZON'), ('G118', 'HUAWEI'), ('G010', 'HP INC'),
        ('G021', 'ACER'), ('G163', 'MICROSOFT'), ('G020', 'DELL'), 
        ('G959', 'XIAOMI')
    ]
    
    app_types = ['HBM', 'SERVER', 'CLIENT']
    quarters = ['202404', '202501']
    
    gbw_data = []
    for quarter in quarters:
        for app_type in app_types:
            for cust_code, cust_name in customers[:7]:  # 일부 고객만 사용
                amt = random.randint(2000000, 10000000)
                actual = str(random.randint(1, 5))
                score = str(random.randint(60, 100))
                max_score = '100'
                
                gbw_data.append((quarter, app_type, cust_code, amt, actual, score, max_score))
    
    cursor.executemany("""
        INSERT INTO QMS_GBW_VIEW 
        (PLAN_QUARTER, HIQ1_APP_CD, HIQ1_CUST_CD, AMT, ACTUAL, SCORE, MAX_SCORE)
        VALUES (:1, :2, :3, :4, :5, :6, :7)
    """, gbw_data)
    
    connection.commit()
    cursor.close()
    print("✅ GBW VIEW 테이블 데이터 삽입 완료")

def insert_rating_customer_data(connection):
    """Rating 관리 고객 테이블 데이터 삽입"""
    cursor = connection.cursor()
    
    customers = [
        ('G113', 'GOOGLE'), ('G150', 'APPLE'), ('G669', 'AMD'), 
        ('G932', 'AMAZON'), ('G118', 'HUAWEI'), ('G010', 'HP INC'),
        ('G021', 'ACER'), ('G163', 'MICROSOFT'), ('G020', 'DELL'), 
        ('G959', 'XIAOMI')
    ]
    
    app_mappings = {
        'SERVER': 'SV',
        'CLIENT': 'CL', 
        'HBM': 'HB'
    }
    
    rating_cust_data = []
    for cust_code, cust_name in customers:
        for hiq1_app, app_cd in app_mappings.items():
            memo = f"{cust_name} {hiq1_app} Application"
            rating_cust_data.append((
                cust_code, hiq1_app, app_cd, 'CUQ_00004', 'Y', 
                datetime.now(), '2050853', memo
            ))
    
    cursor.executemany("""
        INSERT INTO QMS_RAT_CUST 
        (HIQ1_CUST_CD, HIQ1_APP_CD, APP_CD, MODE_GRP, USE_YN, LAST_MDFY_DT, LAST_MDFY_ID, MEMO)
        VALUES (:1, :2, :3, :4, :5, :6, :7, :8)
    """, rating_cust_data)
    
    connection.commit()
    cursor.close()
    print("✅ Rating 관리 고객 테이블 데이터 삽입 완료")

def insert_rating_quarterly_data(connection):
    """Rating 분기별 데이터 테이블 삽입"""
    cursor = connection.cursor()
    
    customers = ['G113', 'G150', 'G669', 'G932', 'G118', 'G010', 'G021', 'G163', 'G020', 'G959']
    app_types = ['SERVER', 'CLIENT', 'HBM']
    quarters = ['202404', '202501']
    
    rating_data = []
    for quarter in quarters:
        for app_type in app_types:
            for cust_code in customers[:8]:  # 일부 고객만 사용
                revenue = str(random.randint(1, 5))
                forecast = str(random.randint(1, 5))
                actual = str(random.randint(1, 5))
                score = str(random.randint(55, 100))
                
                # UUID 형태의 파일 그룹 ID 생성
                file_group_id = f"{random.randint(10000000, 99999999):08X}-{random.randint(1000, 9999):04X}-{random.randint(1000, 9999):04X}-{random.randint(1000, 9999):04X}-{random.randint(100000000000, 999999999999):012X}"
                
                expected_date = datetime(2025, 3, 4) if quarter == '202501' else datetime(2024, 12, 4)
                
                rating_data.append((
                    app_type, cust_code, quarter, revenue, forecast, actual, score,
                    file_group_id, '2012853', expected_date
                ))
    
    cursor.executemany("""
        INSERT INTO QMS_RAT_YMQT_N 
        (HIQ1_APP_CD, HIQ1_CUST_CD, YM_QT, REVENUE, FORECAST, ACTUAL, SCORE, 
         FILE_GROUP_ID, FILE_UPLOAD_USER, EXPECTED_DATE)
        VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10)
    """, rating_data)
    
    connection.commit()
    cursor.close()
    print("✅ Rating 분기별 데이터 테이블 데이터 삽입 완료")

def verify_data(connection):
    """삽입된 데이터 검증"""
    cursor = connection.cursor()
    
    print("\n📊 데이터 삽입 결과 확인:")
    print("=" * 50)
    
    # 각 테이블별 레코드 수 확인
    tables = ['HCOB_CAL', 'HCOB_COMM_CD_N', 'QMS_GBW_VIEW', 'QMS_RAT_CUST', 'QMS_RAT_YMQT_N']
    
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"📋 {table}: {count}건")
    
    print("\n🔍 주요 고객별 Rating 현황:")
    print("-" * 70)
    
    customer_mapping = {
        'G113': 'GOOGLE', 'G150': 'APPLE', 'G669': 'AMD', 'G932': 'AMAZON',
        'G118': 'HUAWEI', 'G010': 'HP INC', 'G021': 'ACER', 'G163': 'MICROSOFT',
        'G020': 'DELL', 'G959': 'XIAOMI'
    }
    
    cursor.execute("""
        SELECT HIQ1_CUST_CD, HIQ1_APP_CD, YM_QT, ACTUAL, SCORE
        FROM QMS_RAT_YMQT_N
        ORDER BY YM_QT DESC, SCORE DESC
    """)
    
    for row in cursor.fetchall():
        cust_code, app_code, quarter, actual, score = row
        cust_name = customer_mapping.get(cust_code, cust_code)
        print(f"{cust_name:12} | {app_code:8} | {quarter} | 실적:{actual} | 점수:{score}")
    
    print("\n📈 분기별 평균 점수:")
    print("-" * 50)
    
    cursor.execute("""
        SELECT YM_QT, HIQ1_APP_CD, COUNT(*) as cnt, 
               ROUND(AVG(TO_NUMBER(SCORE)), 1) as avg_score
        FROM QMS_RAT_YMQT_N
        GROUP BY YM_QT, HIQ1_APP_CD
        ORDER BY YM_QT DESC, avg_score DESC
    """)
    
    for row in cursor.fetchall():
        quarter, app_type, count, avg_score = row
        print(f"{quarter} | {app_type:8} | {count:2}건 | 평균점수: {avg_score}")
    
    cursor.close()

def main():
    """메인 함수"""
    print("🚀 Oracle 테스트 데이터 생성 시작")
    print("=" * 60)
    
    # Oracle 클라이언트 초기화
    if not setup_oracle_client():
        return
    
    # 데이터베이스 연결
    connection = get_connection()
    if not connection:
        return
    
    try:
        # 테이블 생성
        create_test_tables(connection)
        
        # 데이터 삽입
        insert_calendar_data(connection)
        insert_common_code_data(connection)
        insert_gbw_view_data(connection)
        insert_rating_customer_data(connection)
        insert_rating_quarterly_data(connection)
        
        # 데이터 검증
        verify_data(connection)
        
        print("\n🎉 모든 테스트 데이터 생성 완료!")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        connection.rollback()
    
    finally:
        connection.close()
        print("✅ 데이터베이스 연결 종료")

if __name__ == "__main__":
    main()