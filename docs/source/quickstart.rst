빠른 시작 가이드
=================

이 가이드는 Asset Allocation Portfolio Management 시스템을 빠르게 시작하는 방법을 설명합니다.

기본 사용법
-----------

CLI를 통한 실행
~~~~~~~~~~~~~~~

가장 간단한 방법은 CLI를 사용하는 것입니다:

.. code-block:: bash

   # 모든 전략 실행
   uv run asset-cli

   # 특정 전략만 실행
   uv run asset-cli --strategy haa
   uv run asset-cli --strategy kaw

   # JSON 형식으로 출력
   uv run asset-cli --output json

   # 상세 로그와 함께 실행
   uv run asset-cli --verbose

Python 스크립트로 실행
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from portfolio import execute_haa_strategy, execute_kaw_strategy

   # HAA 전략 실행
   haa_result = execute_haa_strategy()
   if haa_result:
       print("HAA 전략 결과:", haa_result)

   # KAW 전략 실행
   kaw_result = execute_kaw_strategy()
   if kaw_result:
       print("KAW 전략 결과:", kaw_result)

출력 형식
---------

텍스트 형식 (기본)
~~~~~~~~~~~~~~~~~~

.. code-block:: text

   자산 배분 리포트
   2024년 01월 15일 (Monday)

   HAA Strategy
   🇺🇸 SPY: 25.00%
   🇺🇸 IWM: 25.00%
   🌍 IEFA: 25.00%
   🌏 IEMG: 25.00%

   KAW Strategy
   🐅 TIGER S&P500: 10.00%
   🇰🇷 KOSEF 200TR: 10.00%
   🥇 KODEX 골드선물(H): 15.00%
   📊 TIGER 미국채 10년 선물: 32.50%
   🏛️ KOSEF 국고채 10년: 32.50%

   성공률: 100.0% (2/2)

JSON 형식
~~~~~~~~~

.. code-block:: json

   {
     "timestamp": "2024-01-15T10:30:00",
     "strategies": {
       "HAA": {
         "SPY": 25.0,
         "IWM": 25.0,
         "IEFA": 25.0,
         "IEMG": 25.0
       },
       "KAW": {
         "TIGER S&P500": 10.0,
         "KOSEF 200TR": 10.0,
         "KODEX 골드선물(H)": 15.0,
         "TIGER 미국채 10년 선물": 32.5,
         "KOSEF 국고채 10년": 32.5
       }
     }
   }

CSV 형식
~~~~~~~~

.. code-block:: csv

   Strategy,Asset,Percentage
   HAA,SPY,25.00
   HAA,IWM,25.00
   HAA,IEFA,25.00
   HAA,IEMG,25.00
   KAW,TIGER S&P500,10.00
   KAW,KOSEF 200TR,10.00

전략별 사용법
-------------

HAA (Hybrid Asset Allocation) 전략
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

HAA 전략은 TIP을 시장 상황 지표로 사용하여 4개의 최고 성과 자산에 배분합니다.

.. code-block:: python

   from strategies import HAAStrategy

   strategy = HAAStrategy()
   data = {
       "momentum_score_simple": {
           "SPY": 0.1,
           "IWM": 0.2,
           "IEFA": 0.15,
           "IEMG": 0.05,
           "TLT": 0.3,
           "IEF": 0.25,
           "PDBC": 0.1,
           "VNQ": 0.2,
           "TIP": 0.1
       }
   }

   result = strategy.calculate_allocation(data)
   print(result)  # {'SPY': 25.0, 'IWM': 25.0, 'IEFA': 25.0, 'IEMG': 25.0}

KAW (Korean All-Weather) 전략
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

KAW 전략은 계절적 배분을 통해 한국 시장에 최적화된 자산 배분을 제공합니다.

.. code-block:: python

   from strategies import KoreanAllWeatherStrategy

   strategy = KoreanAllWeatherStrategy()
   result = strategy.calculate_allocation({})
   print(result)  # 계절에 따른 배분 결과

BAA (Bold Asset Allocation) 전략
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

BAA 전략은 모멘텀 스코어를 기반으로 공격적/방어적 자산을 선택합니다.

.. code-block:: python

   from strategies import BAAStrategy

   strategy = BAAStrategy()
   data = {
       "momentum_score": {...},
       "sma_12month": {...},
       "today_price": {...}
   }

   result = strategy.calculate_allocation(data)
   print(result)

VAA (Vigilant Asset Allocation) 전략
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

VAA 전략은 모든 모멘텀 스코어가 양수일 때 공격자 자산을, 그렇지 않을 때 방어자 자산을 선택합니다.

.. code-block:: python

   from strategies import VAAStrategy

   strategy = VAAStrategy()
   data = {
       "momentum_score": {...}
   }

   result = strategy.calculate_allocation(data)
   print(result)

고급 사용법
-----------

캐시 관리
~~~~~~~~~

.. code-block:: bash

   # 캐시 통계 확인
   uv run asset-cli --cache-stats

   # 캐시 초기화
   uv run asset-cli --clear-cache

성능 모니터링
~~~~~~~~~~~~~

.. code-block:: bash

   # 성능 통계 확인
   uv run asset-cli --performance

   # 상세 로그와 함께 실행
   uv run asset-cli --verbose

커스텀 티커 파일
~~~~~~~~~~~~~~~~

.. code-block:: bash

   # 커스텀 티커 파일 사용
   uv run asset-cli --tickers custom_tickers.json

텔레그램 통합
~~~~~~~~~~~~~

텔레그램 봇이 설정되어 있으면 자동으로 결과를 전송합니다:

.. code-block:: python

   from services import CommunicationService

   service = CommunicationService()
   service.send_message("포트폴리오 업데이트 완료!")

테스트 실행
-----------

.. code-block:: bash

   # 모든 테스트 실행
   uv run python -m pytest tests/ -v

   # 특정 테스트 파일 실행
   uv run python -m pytest tests/test_strategies.py -v

   # 커버리지와 함께 실행
   uv run python -m pytest tests/ --cov=. --cov-report=html

Docker 사용
-----------

.. code-block:: bash

   # Docker로 실행
   docker run --rm asset-allocation

   # 환경 변수와 함께 실행
   docker run --rm -e FRED_API_KEY=your_key asset-allocation

   # docker-compose 사용
   docker-compose up

문제 해결
---------

일반적인 문제들
~~~~~~~~~~~~~~~

**데이터 로드 실패**
   - 인터넷 연결을 확인하세요.
   - API 키가 올바르게 설정되었는지 확인하세요.

**전략 실행 실패**
   - 로그를 확인하여 구체적인 오류를 파악하세요.
   - 필요한 데이터가 충분한지 확인하세요.

**텔레그램 전송 실패**
   - 봇 토큰과 채팅 ID가 올바른지 확인하세요.
   - 봇이 채팅에 추가되었는지 확인하세요.

다음 단계
---------

- :doc:`strategies` - 각 전략의 상세한 설명
- :doc:`api` - API 참조 문서
- :doc:`configuration` - 설정 옵션
- :doc:`examples` - 고급 사용 예제
