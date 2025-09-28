사용 예제
==========

이 문서는 Asset Allocation Portfolio Management 시스템의 다양한 사용 예제를 제공합니다.

기본 사용 예제
--------------

단일 전략 실행
~~~~~~~~~~~~~~

.. code-block:: python

   from portfolio import execute_haa_strategy

   # HAA 전략 실행
   result = execute_haa_strategy()
   if result:
       print("HAA 전략 결과:")
       for asset, percentage in result.items():
           print(f"  {asset}: {percentage:.2f}%")

여러 전략 실행
~~~~~~~~~~~~~~

.. code-block:: python

   from portfolio import (
       execute_haa_strategy,
       execute_kaw_strategy,
       execute_baa_strategy
   )

   strategies = {
       "HAA": execute_haa_strategy,
       "KAW": execute_kaw_strategy,
       "BAA": execute_baa_strategy
   }

   results = {}
   for name, strategy_func in strategies.items():
       try:
           result = strategy_func()
           if result:
               results[name] = result
               print(f"{name} 전략 성공: {len(result)}개 자산")
       except Exception as e:
           print(f"{name} 전략 실패: {e}")

고급 사용 예제
--------------

커스텀 데이터로 전략 실행
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from strategies import HAAStrategy
   from services import DataService

   # 커스텀 데이터 서비스
   data_service = DataService()

   # 특정 기간의 데이터 가져오기
   start_date = "2023-01-01"
   end_date = "2023-12-31"

   data = data_service.get_financial_data(
       tickers=["SPY", "IWM", "IEFA", "IEMG"],
       start_date=start_date,
       end_date=end_date
   )

   # HAA 전략 실행
   strategy = HAAStrategy()
   result = strategy.calculate_allocation(data)
   print(f"커스텀 데이터 결과: {result}")

전략 조합 및 가중평균
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def combine_strategies(strategy_results, weights=None):
       """여러 전략의 결과를 가중평균으로 조합"""
       if not strategy_results:
           return {}

       if weights is None:
           weights = [1.0] * len(strategy_results)

       # 모든 자산 수집
       all_assets = set()
       for result in strategy_results:
           all_assets.update(result.keys())

       # 가중평균 계산
       combined = {}
       for asset in all_assets:
           weighted_sum = 0
           total_weight = 0

           for i, result in enumerate(strategy_results):
               if asset in result:
                   weighted_sum += result[asset] * weights[i]
                   total_weight += weights[i]

           if total_weight > 0:
               combined[asset] = weighted_sum / total_weight

       return combined

   # 전략 결과 조합
   haa_result = execute_haa_strategy()
   kaw_result = execute_kaw_strategy()

   if haa_result and kaw_result:
       # 50:50 가중평균
       combined = combine_strategies([haa_result, kaw_result], [0.5, 0.5])
       print("조합된 결과:", combined)

성능 모니터링과 함께 실행
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from utils.performance_monitor import PerformanceMonitor
   from utils.logging_config import LoggingConfig

   # 성능 모니터 초기화
   monitor = PerformanceMonitor()

   # 로깅 설정
   LoggingConfig.setup(level="INFO")

   def monitored_strategy_execution():
       """성능 모니터링과 함께 전략 실행"""
       with monitor.time_function("total_execution"):
           # 데이터 검색
           with monitor.time_function("data_retrieval"):
               data_service = DataService()
               data = data_service.get_financial_data(["SPY", "IWM", "IEFA"])

           # 전략 실행
           with monitor.time_function("strategy_calculation"):
               strategy = HAAStrategy()
               result = strategy.calculate_allocation(data)

           # 결과 로깅
           LoggingConfig.log_strategy_execution(
               strategy_name="HAA",
               execution_time=monitor.get_execution_time("strategy_calculation"),
               success=True,
               allocation_result=result
           )

           return result

   # 실행 및 성능 통계 확인
   result = monitored_strategy_execution()
   stats = monitor.get_summary()

   print("성능 통계:")
   for func_name, exec_time in stats.items():
       print(f"  {func_name}: {exec_time:.2f}초")

캐시를 활용한 최적화
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from utils.cache_manager import CacheManager
   from services import DataService

   # 캐시 매니저 초기화
   cache_manager = CacheManager(ttl=3600)  # 1시간 TTL

   def get_cached_data(tickers):
       """캐시를 활용한 데이터 검색"""
       cache_key = f"financial_data_{'_'.join(sorted(tickers))}"

       # 캐시에서 확인
       cached_data = cache_manager.get(cache_key)
       if cached_data:
           print("캐시에서 데이터 로드")
           return cached_data

       # 캐시에 없으면 새로 검색
       print("새 데이터 검색")
       data_service = DataService()
       data = data_service.get_financial_data(tickers)

       # 캐시에 저장
       cache_manager.set(cache_key, data)
       return data

   # 사용 예제
   tickers = ["SPY", "IWM", "IEFA", "IEMG"]
   data = get_cached_data(tickers)
   print(f"데이터 크기: {len(data)} 항목")

텔레그램 통합 예제
-----------------

기본 메시지 전송
~~~~~~~~~~~~~~~

.. code-block:: python

   from services import CommunicationService

   # 텔레그램 서비스 초기화
   telegram = CommunicationService()

   # 간단한 메시지 전송
   telegram.send_message("포트폴리오 업데이트가 완료되었습니다! 🎉")

포맷된 포트폴리오 리포트 전송
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def send_portfolio_report(strategy_results):
       """포맷된 포트폴리오 리포트를 텔레그램으로 전송"""
       telegram = CommunicationService()

       # 헤더 메시지
       from datetime import datetime
       now = datetime.now()
       weekday = now.strftime("%A")

       header = f"📊 자산 배분 리포트\n📅 {now.strftime('%Y년 %m월 %d일')} ({weekday})"
       telegram.send_message(header)

       # 각 전략별 결과 전송
       for strategy_name, result in strategy_results.items():
           if not result:
               continue

           # 전략 헤더
           strategy_header = f"\n🎯 {strategy_name} Strategy"
           telegram.send_message(strategy_header)

           # 자산별 배분 (개별 메시지로 전송하여 줄바꿈 보장)
           for asset, percentage in result.items():
               emoji = get_asset_emoji(asset)
               message = f"{emoji} {asset}: {percentage:.2f}%"
               telegram.send_message(message)

       # 요약 메시지
       successful_strategies = sum(1 for r in strategy_results.values() if r)
       total_strategies = len(strategy_results)
       success_rate = (successful_strategies / total_strategies) * 100

       summary = f"\n성공률: {success_rate:.1f}% ({successful_strategies}/{total_strategies})"
       telegram.send_message(summary)

   def get_asset_emoji(asset):
       """자산별 이모지 반환"""
       emojis = {
           "SPY": "🇺🇸", "IWM": "🇺🇸", "IEFA": "🌍", "IEMG": "🌏",
           "TLT": "📊", "IEF": "📊", "PDBC": "🛢️", "VNQ": "🏠",
           "TIGER S&P500": "🐅", "KOSEF 200TR": "🇰🇷",
           "KODEX 골드선물(H)": "🥇", "TIGER 미국채 10년 선물": "📊",
           "KOSEF 국고채 10년": "🏛️"
       }
       return emojis.get(asset, "📈")

   # 사용 예제
   results = {
       "HAA": {"SPY": 25.0, "IWM": 25.0, "IEFA": 25.0, "IEMG": 25.0},
       "KAW": {"TIGER S&P500": 10.0, "KOSEF 200TR": 10.0}
   }
   send_portfolio_report(results)

CLI 사용 예제
-------------

기본 CLI 사용법
~~~~~~~~~~~~~~

.. code-block:: bash

   # 모든 전략 실행
   uv run asset-cli

   # 특정 전략만 실행
   uv run asset-cli --strategy haa
   uv run asset-cli --strategy kaw --strategy baa

   # 출력 형식 지정
   uv run asset-cli --output json
   uv run asset-cli --output csv
   uv run asset-cli --output text

   # 상세 로그와 함께 실행
   uv run asset-cli --verbose

고급 CLI 사용법
~~~~~~~~~~~~~~

.. code-block:: bash

   # 캐시 관리
   uv run asset-cli --cache-stats
   uv run asset-cli --clear-cache

   # 성능 모니터링
   uv run asset-cli --performance

   # 커스텀 티커 파일 사용
   uv run asset-cli --tickers custom_tickers.json

   # 특정 기간 데이터 사용
   uv run asset-cli --start-date 2023-01-01 --end-date 2023-12-31

Docker 사용 예제
---------------

기본 Docker 실행
~~~~~~~~~~~~~~~

.. code-block:: bash

   # Docker 이미지 빌드
   docker build -t asset-allocation .

   # 기본 실행
   docker run --rm asset-allocation

   # 환경 변수와 함께 실행
   docker run --rm \
     -e FRED_API_KEY=your_key \
     -e TELEGRAM_BOT_TOKEN=your_token \
     -e TELEGRAM_CHAT_ID=your_chat_id \
     asset-allocation

Docker Compose 사용
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # docker-compose로 실행
   docker-compose up

   # 백그라운드 실행
   docker-compose up -d

   # 로그 확인
   docker-compose logs -f

   # 서비스 중지
   docker-compose down

볼륨 마운트를 통한 데이터 영속성
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # 캐시와 로그를 호스트에 저장
   docker run --rm \
     -v $(pwd)/cache:/app/cache \
     -v $(pwd)/logs:/app/logs \
     asset-allocation

테스트 예제
-----------

단위 테스트 실행
~~~~~~~~~~~~~~~

.. code-block:: bash

   # 모든 테스트 실행
   uv run python -m pytest tests/ -v

   # 특정 테스트 파일 실행
   uv run python -m pytest tests/test_strategies.py -v

   # 특정 테스트 함수 실행
   uv run python -m pytest tests/test_strategies.py::TestHAAStrategy::test_calculate_allocation -v

커버리지와 함께 테스트
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # HTML 커버리지 리포트 생성
   uv run python -m pytest tests/ --cov=. --cov-report=html

   # 터미널에서 커버리지 확인
   uv run python -m pytest tests/ --cov=. --cov-report=term

   # 특정 모듈만 커버리지 확인
   uv run python -m pytest tests/ --cov=strategies --cov-report=html

통합 테스트 예제
~~~~~~~~~~~~~~~

.. code-block:: python

   import pytest
   from portfolio import execute_haa_strategy
   from services import DataService

   def test_integration_haa_strategy():
       """HAA 전략 통합 테스트"""
       # 실제 데이터로 테스트
       data_service = DataService()
       data = data_service.get_financial_data(["SPY", "IWM", "IEFA", "IEMG"])

       # 전략 실행
       result = execute_haa_strategy()

       # 결과 검증
       assert result is not None
       assert len(result) == 4  # 4개 자산
       assert abs(sum(result.values()) - 100.0) < 0.01  # 총합 100%

       # 모든 배분이 양수인지 확인
       for percentage in result.values():
           assert percentage > 0

성능 테스트 예제
~~~~~~~~~~~~~~~

.. code-block:: python

   import time
   from utils.performance_monitor import PerformanceMonitor

   def performance_test():
       """성능 테스트 실행"""
       monitor = PerformanceMonitor()

       # 여러 번 실행하여 평균 성능 측정
       execution_times = []
       for i in range(10):
           with monitor.time_function(f"execution_{i}"):
               result = execute_haa_strategy()
           execution_times.append(monitor.get_execution_time(f"execution_{i}"))

       # 통계 계산
       avg_time = sum(execution_times) / len(execution_times)
       min_time = min(execution_times)
       max_time = max(execution_times)

       print(f"평균 실행 시간: {avg_time:.2f}초")
       print(f"최소 실행 시간: {min_time:.2f}초")
       print(f"최대 실행 시간: {max_time:.2f}초")

       # 성능 기준 확인
       assert avg_time < 5.0, "평균 실행 시간이 5초를 초과했습니다"

   performance_test()
