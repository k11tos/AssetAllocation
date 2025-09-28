설정 가이드
============

이 문서는 Asset Allocation Portfolio Management 시스템의 설정 옵션들을 설명합니다.

환경 변수 설정
--------------

기본 환경 변수
~~~~~~~~~~~~~~

`.env` 파일에 다음 변수들을 설정하세요:

.. code-block:: env

   # FRED API 키 (선택사항)
   FRED_API_KEY=your_fred_api_key_here

   # 텔레그램 봇 설정
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   TELEGRAM_CHAT_ID=your_telegram_chat_id_here

고급 환경 변수
~~~~~~~~~~~~~~

.. code-block:: env

   # 로깅 레벨 설정
   LOG_LEVEL=INFO

   # 캐시 TTL 설정 (초)
   CACHE_TTL=3600

   # 성능 모니터링 활성화
   ENABLE_PERFORMANCE_MONITORING=true

   # 디버그 모드
   DEBUG=false

전략별 설정
-----------

HAA 전략 설정
~~~~~~~~~~~~~

.. code-block:: python

   HAA_CONFIG = HAAConfig(
       TICKERS={
           "SPY": 0.0,
           "IWM": 0.0,
           "IEFA": 0.0,
           "IEMG": 0.0,
           "TLT": 0.0,
           "IEF": 0.0,
           "PDBC": 0.0,
           "VNQ": 0.0,
           "TIP": 0.0
       },
       TOP_N=4,
       TIP_THRESHOLD=0.0
   )

KAW 전략 설정
~~~~~~~~~~~~~

.. code-block:: python

   KAW_CONFIG = KAWConfig(
       TICKERS={
           "TIGER S&P500": 0.0,
           "KOSEF 200TR": 0.0,
           "KODEX 골드선물(H)": 0.0,
           "TIGER 미국채 10년 선물": 0.0,
           "KOSEF 국고채 10년": 0.0
       },
       RISKY_MONTHS=[3, 4, 5, 6, 7, 8],
       SAFE_MONTHS=[9, 10, 11, 12, 1, 2]
   )

BAA 전략 설정
~~~~~~~~~~~~~

.. code-block:: python

   BAA_CONFIG = BAAConfig(
       ATTACKER_TICKERS=["QQQ", "IEFA", "IEMG", "AGG"],
       DEFENDER_TICKERS=["BIL", "IEF", "TLT", "LQD", "TIP", "BND", "DBC"],
       TOP_N=3,
       BIL_THRESHOLD=1.0
   )

VAA 전략 설정
~~~~~~~~~~~~~

.. code-block:: python

   VAA_CONFIG = VAAConfig(
       ATTACKER_TICKERS=["SPY", "IEFA", "IEMG", "AGG"],
       DEFENDER_TICKERS=["LQD", "IEF", "SHY"]
   )

캐시 설정
---------

캐시 매니저 설정
~~~~~~~~~~~~~~~~

.. code-block:: python

   from utils.cache_manager import CacheManager

   cache_manager = CacheManager(
       cache_dir="./cache",
       ttl=3600,  # 1시간
       max_size=100  # 최대 100개 항목
   )

캐시 통계 확인
~~~~~~~~~~~~~~

.. code-block:: python

   # 캐시 통계 확인
   stats = cache_manager.get_stats()
   print(f"캐시 히트율: {stats['hit_rate']:.2%}")
   print(f"캐시 크기: {stats['size']} 항목")

캐시 관리
~~~~~~~~~

.. code-block:: python

   # 캐시 초기화
   cache_manager.clear()

   # 특정 키 삭제
   cache_manager.delete("specific_key")

   # 캐시 정리 (만료된 항목 제거)
   cache_manager.cleanup()

로깅 설정
---------

로깅 레벨 설정
~~~~~~~~~~~~~~

.. code-block:: python

   from utils.logging_config import LoggingConfig

   # 로깅 설정 초기화
   LoggingConfig.setup(
       level="INFO",
       log_file="logs/asset_allocation.log",
       max_bytes=10*1024*1024,  # 10MB
       backup_count=5
   )

로깅 포맷 설정
~~~~~~~~~~~~~~

.. code-block:: python

   # 커스텀 로깅 포맷
   LoggingConfig.setup(
       level="DEBUG",
       format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
       log_file="logs/debug.log"
   )

구조화된 로깅
~~~~~~~~~~~~~

.. code-block:: python

   from utils.logging_config import LoggingConfig

   # 전략 실행 로깅
   LoggingConfig.log_strategy_execution(
       strategy_name="HAA",
       execution_time=1.23,
       success=True,
       allocation_result={"SPY": 25.0, "IWM": 25.0}
   )

   # 데이터 검색 로깅
   LoggingConfig.log_data_retrieval(
       source="yahoo_finance",
       tickers=["SPY", "IWM"],
       success=True,
       data_count=2
   )

성능 모니터링 설정
------------------

성능 모니터 활성화
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from utils.performance_monitor import PerformanceMonitor

   # 성능 모니터 초기화
   monitor = PerformanceMonitor()

   # 함수 실행 시간 측정
   with monitor.time_function("data_retrieval"):
       data = get_financial_data(tickers)

   # 성능 통계 확인
   stats = monitor.get_summary()
   print(f"평균 실행 시간: {stats['data_retrieval']:.2f}초")

성능 임계값 설정
~~~~~~~~~~~~~~~

.. code-block:: python

   # 성능 경고 임계값 설정
   monitor.set_threshold("data_retrieval", 5.0)  # 5초

   # 임계값 초과 시 경고
   if monitor.get_execution_time("data_retrieval") > 5.0:
       print("경고: 데이터 검색 시간이 임계값을 초과했습니다!")

보안 설정
---------

입력 검증 설정
~~~~~~~~~~~~~~

.. code-block:: python

   from utils.security import SecurityManager

   security_manager = SecurityManager()

   # 입력 검증
   safe_input = security_manager.sanitize_input(user_input)

   # HTML 허용 (텔레그램 메시지용)
   safe_html = security_manager.sanitize_input(html_content, allow_html=True)

API 키 검증
~~~~~~~~~~

.. code-block:: python

   # API 키 유효성 검사
   if not security_manager.validate_api_key(api_key):
       raise ValueError("유효하지 않은 API 키입니다")

텔레그램 설정
-------------

봇 설정
~~~~~~~

.. code-block:: python

   from services.communication_service import CommunicationService

   # 텔레그램 서비스 초기화
   telegram_service = CommunicationService()

   # 메시지 전송
   telegram_service.send_message("포트폴리오 업데이트 완료!")

메시지 포맷 설정
~~~~~~~~~~~~~~~

.. code-block:: python

   # 메시지 포맷 설정
   message = """
   📊 자산 배분 리포트
   📅 2024년 01월 15일

   🎯 HAA Strategy
   🇺🇸 SPY: 25.00%
   🇺🇸 IWM: 25.00%
   """

   telegram_service.send_message(message)

Docker 설정
-----------

Docker Compose 설정
~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   version: '3.8'
   services:
     asset-allocation:
       build: .
       environment:
         - FRED_API_KEY=${FRED_API_KEY}
         - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
         - TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID}
       volumes:
         - ./cache:/app/cache
         - ./logs:/app/logs
       restart: unless-stopped

Dockerfile 설정
~~~~~~~~~~~~~~~

.. code-block:: dockerfile

   FROM python:3.11-alpine

   WORKDIR /app

   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   COPY . .

   CMD ["python", "main.py"]

설정 검증
---------

설정 유효성 검사
~~~~~~~~~~~~~~~

.. code-block:: python

   from config import validate_config

   # 설정 검증
   try:
       validate_config()
       print("설정이 올바르게 구성되었습니다")
   except ValueError as e:
       print(f"설정 오류: {e}")

필수 설정 확인
~~~~~~~~~~~~~

.. code-block:: python

   # 필수 환경 변수 확인
   required_vars = ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]

   for var in required_vars:
       if not os.getenv(var):
           print(f"경고: {var} 환경 변수가 설정되지 않았습니다")

설정 최적화
-----------

성능 최적화
~~~~~~~~~~~

.. code-block:: python

   # 캐시 TTL 최적화
   CACHE_TTL = 3600  # 1시간

   # 배치 크기 최적화
   BATCH_SIZE = 10

   # 동시 요청 수 제한
   MAX_CONCURRENT_REQUESTS = 5

메모리 최적화
~~~~~~~~~~~~

.. code-block:: python

   # 캐시 크기 제한
   MAX_CACHE_SIZE = 100

   # 로그 파일 크기 제한
   MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB

   # 백업 파일 수 제한
   MAX_BACKUP_COUNT = 5
