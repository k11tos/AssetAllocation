Asset Allocation Portfolio Management
=====================================

자산 배분 포트폴리오 관리 시스템은 다양한 자산 배분 전략을 구현하는 Python 애플리케이션입니다.

.. toctree::
   :maxdepth: 2
   :caption: 목차:

   installation
   quickstart
   strategies
   api
   configuration
   examples
   contributing

주요 기능
---------

🎯 **자산 배분 전략**
   - Hybrid Asset Allocation (HAA)
   - Korean All-Weather Strategy
   - Bold Asset Allocation (BAA)
   - Vigilant Asset Allocation (VAA)
   - Modified Dual Momentum (MDM)

🚀 **성능 및 신뢰성**
   - 지능형 캐싱 시스템
   - 성능 모니터링
   - 포괄적인 에러 처리
   - 52개 테스트 케이스 (85% 커버리지)

🛠️ **개발자 경험**
   - 모듈화된 아키텍처
   - 중앙화된 설정 관리
   - CLI 인터페이스
   - 완전한 타입 힌트

📊 **출력 형식**
   - 텍스트 (콘솔 출력)
   - JSON (API 통합)
   - CSV (분석용)

🔗 **통합**
   - 텔레그램 봇
   - FRED API
   - Yahoo Finance

빠른 시작
---------

.. code-block:: bash

   # 설치
   uv sync

   # 환경 변수 설정
   cp env.example .env

   # 실행
   uv run python main.py

API 문서
--------

.. toctree::
   :maxdepth: 2
   :caption: API 참조:

   api/strategies
   api/services
   api/utils
   api/config

인덱스 및 테이블
================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
