설치 가이드
============

이 문서는 Asset Allocation Portfolio Management 시스템을 설치하는 방법을 설명합니다.

시스템 요구사항
----------------

- Python 3.8 이상
- pip 또는 uv 패키지 매니저
- Git (소스 코드 다운로드용)

Docker를 사용한 설치 (권장)
----------------------------

Docker를 사용하면 의존성 문제 없이 쉽게 설치할 수 있습니다.

1. 저장소 클론:

.. code-block:: bash

   git clone <repository-url>
   cd AssetAllocation

2. Docker 이미지 빌드:

.. code-block:: bash

   docker build -t asset-allocation .

3. 컨테이너 실행:

.. code-block:: bash

   # 기본 실행
   docker run --rm asset-allocation

   # 환경 변수와 함께 실행
   docker run --rm -e FRED_API_KEY=your_key asset-allocation

   # docker-compose 사용
   docker-compose up

Docker 이미지 특징
~~~~~~~~~~~~~~~~~~

- 🐧 **Alpine Linux**: 경량 베이스 이미지 (~386MB)
- 🏗️ **멀티스테이지 빌드**: 크기와 보안 최적화
- 🔒 **비루트 사용자**: 보안 강화
- 🏥 **헬스 체크**: 내장 모니터링
- 📦 **최소 의존성**: 런타임 패키지만 포함

로컬 설치
---------

uv를 사용한 설치 (권장)
~~~~~~~~~~~~~~~~~~~~~~~

1. 저장소 클론:

.. code-block:: bash

   git clone <repository-url>
   cd AssetAllocation

2. 의존성 설치:

.. code-block:: bash

   uv sync

3. 환경 변수 설정:

.. code-block:: bash

   cp env.example .env
   # .env 파일을 편집하여 API 키 설정

pip를 사용한 설치
~~~~~~~~~~~~~~~~~

1. 저장소 클론:

.. code-block:: bash

   git clone <repository-url>
   cd AssetAllocation

2. 가상환경 생성:

.. code-block:: bash

   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate

3. 의존성 설치:

.. code-block:: bash

   pip install -r requirements.txt

4. 환경 변수 설정:

.. code-block:: bash

   cp env.example .env
   # .env 파일을 편집하여 API 키 설정

환경 변수 설정
--------------

`.env` 파일을 생성하고 다음 변수들을 설정하세요:

.. code-block:: env

   # FRED API 키 (선택사항)
   FRED_API_KEY=your_fred_api_key_here

   # 텔레그램 봇 설정
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   TELEGRAM_CHAT_ID=your_telegram_chat_id_here

API 키 획득
-----------

FRED API 키
~~~~~~~~~~~

1. `Federal Reserve Economic Data <https://fred.stlouisfed.org/>`_ 웹사이트 방문
2. 계정 생성 및 로그인
3. API 키 요청
4. 받은 키를 `.env` 파일에 설정

텔레그램 봇 토큰
~~~~~~~~~~~~~~~

1. 텔레그램에서 `@BotFather`와 대화
2. `/newbot` 명령어로 새 봇 생성
3. 봇 이름과 사용자명 설정
4. 받은 토큰을 `.env` 파일에 설정

텔레그램 채팅 ID
~~~~~~~~~~~~~~~

1. 봇과 대화 시작
2. `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates` 방문
3. `chat.id` 값을 복사하여 `.env` 파일에 설정

설치 확인
---------

설치가 완료되면 다음 명령어로 확인할 수 있습니다:

.. code-block:: bash

   # 버전 확인
   uv run python -c "import portfolio; print('설치 완료!')"

   # 테스트 실행
   uv run python -m pytest tests/ -v

   # 메인 애플리케이션 실행
   uv run python main.py

문제 해결
---------

일반적인 문제들
~~~~~~~~~~~~~~~

**ImportError: No module named 'yfinance'**
   - 의존성이 제대로 설치되지 않았습니다. `uv sync` 또는 `pip install -r requirements.txt`를 실행하세요.

**API 키 오류**
   - `.env` 파일이 올바른 위치에 있는지 확인하세요.
   - API 키가 올바르게 설정되었는지 확인하세요.

**Docker 빌드 실패**
   - Docker가 실행 중인지 확인하세요.
   - 네트워크 연결을 확인하세요.

**권한 오류**
   - Linux/macOS에서 실행 권한을 확인하세요.
   - Windows에서 관리자 권한으로 실행해보세요.

추가 도움
---------

문제가 지속되면 다음을 확인하세요:

- `README.md` 파일의 최신 정보
- GitHub Issues에서 유사한 문제 검색
- 개발팀에 문의

다음 단계
---------

설치가 완료되면 :doc:`quickstart` 가이드를 참조하여 시스템 사용법을 학습하세요.
