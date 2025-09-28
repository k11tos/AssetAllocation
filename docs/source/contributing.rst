기여 가이드
============

Asset Allocation Portfolio Management 프로젝트에 기여해주셔서 감사합니다! 이 문서는 프로젝트에 기여하는 방법을 안내합니다.

기여 방법
----------

버그 리포트
~~~~~~~~~~~

버그를 발견하셨다면 다음 정보를 포함하여 이슈를 생성해주세요:

- **버그 설명**: 무엇이 잘못되었는지 명확한 설명
- **재현 단계**: 버그를 재현하는 단계별 방법
- **예상 결과**: 기대했던 결과
- **실제 결과**: 실제로 발생한 결과
- **환경 정보**: Python 버전, 운영체제, 의존성 버전
- **로그**: 관련된 로그나 에러 메시지

기능 요청
~~~~~~~~~

새로운 기능을 제안하시려면 다음을 포함해주세요:

- **기능 설명**: 원하는 기능에 대한 명확한 설명
- **사용 사례**: 이 기능이 왜 필요한지
- **구현 아이디어**: 가능한 구현 방법 (선택사항)
- **대안**: 고려해본 다른 해결책 (선택사항)

코드 기여
~~~~~~~~~

코드를 기여하시려면 다음 단계를 따르세요:

1. **Fork**: 저장소를 포크하세요
2. **브랜치 생성**: 새 기능 브랜치를 생성하세요
3. **개발**: 코드를 작성하고 테스트하세요
4. **테스트**: 모든 테스트가 통과하는지 확인하세요
5. **커밋**: 의미있는 커밋 메시지로 커밋하세요
6. **Pull Request**: PR을 생성하세요

개발 환경 설정
--------------

필수 요구사항
~~~~~~~~~~~~~

- Python 3.8 이상
- Git
- uv 또는 pip

개발 환경 구축
~~~~~~~~~~~~~~

1. **저장소 클론**:

.. code-block:: bash

   git clone https://github.com/your-username/AssetAllocation.git
   cd AssetAllocation

2. **개발 의존성 설치**:

.. code-block:: bash

   uv sync --dev
   # 또는
   pip install -r requirements-dev.txt

3. **Pre-commit 훅 설정**:

.. code-block:: bash

   pre-commit install

4. **환경 변수 설정**:

.. code-block:: bash

   cp env.example .env
   # .env 파일을 편집하여 테스트용 API 키 설정

코딩 스타일
-----------

Python 스타일 가이드
~~~~~~~~~~~~~~~~~~~~

이 프로젝트는 다음 스타일 가이드를 따릅니다:

- **PEP 8**: Python 공식 스타일 가이드
- **Black**: 코드 포맷터
- **isort**: import 정렬
- **flake8**: 린터

자동 포맷팅
~~~~~~~~~~~

코드 제출 전에 다음 명령어로 포맷팅을 확인하세요:

.. code-block:: bash

   # Black으로 포맷팅
   uv run black .

   # isort로 import 정렬
   uv run isort .

   # flake8로 린팅
   uv run flake8 .

Pre-commit 훅이 자동으로 이 작업들을 수행합니다.

타입 힌트
~~~~~~~~~

모든 함수와 메서드에 타입 힌트를 추가하세요:

.. code-block:: python

   from typing import Dict, List, Optional

   def calculate_allocation(data: Dict[str, float]) -> Dict[str, float]:
       """자산 배분을 계산합니다."""
       result: Dict[str, float] = {}
       # 구현...
       return result

문서화
~~~~~~

모든 공개 함수와 클래스에 docstring을 추가하세요:

.. code-block:: python

   def calculate_allocation(self, data: Dict[str, Any]) -> Dict[str, float]:
       """
       자산 배분을 계산합니다.

       Args:
           data: 자산별 모멘텀 스코어 데이터

       Returns:
           자산별 배분 비율 (퍼센트)

       Raises:
           DataValidationError: 데이터가 유효하지 않은 경우
       """
       pass

테스트 작성
-----------

테스트 요구사항
~~~~~~~~~~~~~~~

- 모든 새 기능에 대한 테스트 작성
- 테스트 커버리지 80% 이상 유지
- 의미있는 테스트 케이스 작성

테스트 실행
~~~~~~~~~~~

.. code-block:: bash

   # 모든 테스트 실행
   uv run python -m pytest tests/ -v

   # 커버리지와 함께 실행
   uv run python -m pytest tests/ --cov=. --cov-report=html

   # 특정 테스트 파일 실행
   uv run python -m pytest tests/test_strategies.py -v

테스트 작성 예제
~~~~~~~~~~~~~~~

.. code-block:: python

   import pytest
   from strategies import HAAStrategy
   from exceptions import DataValidationError

   class TestHAAStrategy:
       """HAA 전략 테스트 클래스"""

       def setup_method(self):
           """각 테스트 전에 실행"""
           self.strategy = HAAStrategy()

       def test_calculate_allocation_success(self):
           """정상적인 자산 배분 계산 테스트"""
           data = {
               "momentum_score_simple": {
                   "SPY": 0.1,
                   "IWM": 0.2,
                   "IEFA": 0.15,
                   "IEMG": 0.05
               }
           }

           result = self.strategy.calculate_allocation(data)

           assert result is not None
           assert len(result) == 4
           assert abs(sum(result.values()) - 100.0) < 0.01

       def test_calculate_allocation_invalid_data(self):
           """잘못된 데이터로 인한 예외 테스트"""
           with pytest.raises(DataValidationError):
               self.strategy.calculate_allocation({})

새 전략 추가
-----------

전략 클래스 구조
~~~~~~~~~~~~~~~

새 전략을 추가할 때는 다음 구조를 따르세요:

.. code-block:: python

   from strategies.base_strategy import BaseStrategy
   from typing import Dict, Any

   class NewStrategy(BaseStrategy):
       """새 전략 클래스"""

       def __init__(self):
           super().__init__()
           self.name = "New Strategy"

       def calculate_allocation(self, data: Dict[str, Any]) -> Dict[str, float]:
           """자산 배분을 계산합니다."""
           # 전략 로직 구현
           pass

       def get_required_data_keys(self) -> List[str]:
           """필요한 데이터 키를 반환합니다."""
           return ["momentum_score", "price_data"]

       def validate_data(self, data: Dict[str, Any]) -> None:
           """데이터 유효성을 검사합니다."""
           # 데이터 검증 로직
           pass

전략 설정 추가
~~~~~~~~~~~~~

`config.py`에 새 전략의 설정을 추가하세요:

.. code-block:: python

   @dataclass
   class NewStrategyConfig:
       """새 전략 설정"""
       TICKERS: Dict[str, float] = field(default_factory=dict)
       PARAMETER1: float = 0.0
       PARAMETER2: int = 10

   # 전역 설정 인스턴스
   NEW_STRATEGY_CONFIG = NewStrategyConfig()

테스트 추가
~~~~~~~~~~

새 전략에 대한 테스트를 `tests/test_strategies.py`에 추가하세요:

.. code-block:: python

   class TestNewStrategy:
       """새 전략 테스트 클래스"""

       def test_calculate_allocation(self):
           """자산 배분 계산 테스트"""
           pass

       def test_validate_data(self):
           """데이터 검증 테스트"""
           pass

문서 업데이트
~~~~~~~~~~~~

- `strategies.rst`에 새 전략 설명 추가
- `api/strategies.rst`에 API 문서 추가
- `examples.rst`에 사용 예제 추가

Pull Request 가이드
------------------

PR 생성 전 체크리스트
~~~~~~~~~~~~~~~~~~~~

- [ ] 모든 테스트가 통과하는가?
- [ ] 코드가 스타일 가이드를 따르는가?
- [ ] 타입 힌트가 추가되었는가?
- [ ] 문서가 업데이트되었는가?
- [ ] 커밋 메시지가 명확한가?

PR 제목 규칙
~~~~~~~~~~~

PR 제목은 다음 형식을 따르세요:

- `feat: 새 기능 추가`
- `fix: 버그 수정`
- `docs: 문서 업데이트`
- `test: 테스트 추가`
- `refactor: 코드 리팩토링`
- `perf: 성능 개선`

PR 설명 템플릿
~~~~~~~~~~~~~

.. code-block:: markdown

   ## 변경 사항
   - 변경된 내용을 명확히 설명

   ## 테스트
   - [ ] 기존 테스트 통과
   - [ ] 새 테스트 추가
   - [ ] 수동 테스트 완료

   ## 체크리스트
   - [ ] 코드 스타일 확인
   - [ ] 타입 힌트 추가
   - [ ] 문서 업데이트
   - [ ] 커밋 메시지 명확

코드 리뷰
---------

리뷰어 가이드라인
~~~~~~~~~~~~~~~~

- **코드 품질**: 가독성, 성능, 보안
- **테스트**: 충분한 테스트 커버리지
- **문서**: 명확한 docstring과 주석
- **일관성**: 프로젝트 스타일과 일치

리뷰어 체크리스트
~~~~~~~~~~~~~~~

- [ ] 코드가 요구사항을 만족하는가?
- [ ] 테스트가 적절한가?
- [ ] 성능에 문제가 없는가?
- [ ] 보안 취약점이 없는가?
- [ ] 문서가 명확한가?

기여자 인정
----------

기여자들은 다음에 인정됩니다:

- **코드 기여자**: 코드를 기여한 개발자
- **버그 리포트**: 중요한 버그를 발견한 사용자
- **문서 기여자**: 문서를 개선한 기여자
- **테스트 기여자**: 테스트를 추가한 기여자

라이선스
--------

이 프로젝트는 교육 및 연구 목적으로 사용됩니다. 기여하시는 코드는 동일한 라이선스 하에 배포됩니다.

문의
----

질문이나 제안이 있으시면 다음으로 연락하세요:

- GitHub Issues: 버그 리포트 및 기능 요청
- GitHub Discussions: 일반적인 질문 및 토론
- 이메일: 프로젝트 관리자에게 직접 연락

감사합니다
----------

프로젝트에 기여해주셔서 감사합니다! 여러분의 기여가 이 프로젝트를 더 나은 도구로 만들어줍니다.
