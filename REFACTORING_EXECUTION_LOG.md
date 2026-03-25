# 리팩터링 실행 로그

## 목적

이 문서는 `AGENTS.md`와 `PROJECT_REVIEW_AND_REFACTORING_PLAN.md`를 기준으로 작성했다.
이번 리팩터링의 목표는 현재 extension의 동작 흐름을 유지하면서 효율성, 가독성, 유지보수성을 높이는 것이다.

이번 작업에서 가장 우선적으로 다룬 구조적 대상은 기존 `TimeTravelCore` 객체였다.
이 객체는 아래처럼 서로 다른 책임을 한 곳에 모으고 있었다.

- 설정 파일 로드
- trajectory CSV 로드 및 조회
- 재생 상태 관리
- stage object 위치 반영
- summarization camera 제어
- event summary 로드 및 후처리

## 분석 요약

리팩터링 이전의 프로젝트는 하나의 중심 객체가 순수 데이터 로직과 Omniverse 의존 로직을 동시에 들고 있는 구조였다.
이 구조는 실제로 다음과 같은 문제를 만들고 있었다.

- 한 부분만 수정해도 로딩, 재생, stage 조작, 이벤트 처리까지 함께 영향을 받을 가능성이 컸다.
- 순수 로직을 Omniverse 없이 분리 검증하기 어려웠다.
- 내부 상태 필드가 많고 역할이 섞여 있어 처음 보는 사람이 흐름을 빠르게 이해하기 어려웠다.

프로젝트 리뷰 문서에서는 이 문제를 `TimeTravelCore`의 기능별 분해로 해결하는 방향을 제안하고 있었다.
이번 리팩터링은 그 방향을 따르되, 외부 인터페이스를 크게 흔들지 않는 방식으로 진행했다.
즉, `TimeTravelCore`의 공개 메서드는 최대한 유지하면서 내부 구현을 기능별 객체로 분리했다.

## 리팩터링 작업 내용

### 1. 기존 object를 기능별 object로 분화

기존 God Object 성격의 `TimeTravelCore` 내부 책임을 아래와 같이 분리했다.

- `app_config.py`
  - `ExtensionConfig` 도입
  - config 파싱과 경로 해석을 한곳에서 처리
  - 여러 위치에 흩어져 있던 dict 접근과 경로 보정 로직 제거

- `trajectory_repository.py`
  - CSV 로드, timestamp 파싱, timestamp 포맷팅, Last Known Value 조회 담당
  - trajectory 데이터 관련 책임을 playback/stage 처리와 분리

- `playback_controller.py`
  - 재생 구간, 현재 시간, progress, 재생 속도, event 기반 재생 흐름 담당
  - 재생 규칙이 다른 책임과 섞이지 않도록 분리

- `stage_object_controller.py`
  - stage 접근, astronaut prim 생성, object 위치 반영, camera 생성/이동, stage cleanup 담당
  - Omniverse 의존 로직을 순수 데이터 로직과 분리

- `event_summary_service.py`
  - event list 로드와 JSON 결과의 event list 변환 담당
  - event 후처리를 playback/stage 갱신 로직과 분리

이 분화의 목적은 “기존 기능을 바꾸는 것”이 아니라 “기존 기능을 더 작은 책임 단위로 나눠서 수정 비용과 부작용 가능성을 줄이는 것”에 있다.

### 2. `TimeTravelCore`를 facade로 전환

`TimeTravelCore`는 더 이상 모든 작업을 직접 수행하지 않는다.
대신 외부에서 보이는 기존 API를 유지하면서 내부적으로는 분리된 서비스 객체들에게 작업을 위임하는 facade 역할을 맡도록 변경했다.

이렇게 한 이유는 다음과 같다.

- `window.py`, `extension.py` 등 기존 호출부를 크게 흔들지 않기 위해
- 리팩터링 범위를 통제해 기능 회귀 위험을 줄이기 위해
- 이후 추가 리팩터링을 단계적으로 이어갈 수 있도록 하기 위해

### 3. extension startup 코드 정리

`extension.py`는 이전에 `self._core._config`에 직접 접근하고 있었다.
이를 `should_auto_generate()` 같은 명시적인 메서드 호출로 바꾸었다.

이 변경의 목적은 다음과 같다.

- extension 레이어가 core 내부 구현 세부사항에 직접 의존하지 않게 하기 위해
- startup 코드가 “무엇을 판단하는지” 더 분명하게 드러나도록 하기 위해

### 4. 비-Kit 환경에서의 import 안정성 보완

`__init__.py`는 Omniverse 런타임이 없는 환경에서도 순수 Python 모듈 일부를 import할 수 있도록 조정했다.

이 변경의 목적은 다음과 같다.

- 순수 로직 모듈을 Omniverse 없이 검증 가능하게 하기 위해
- 패키지 import와 Kit runtime 의존성을 완전히 묶어두지 않기 위해

### 5. 기존 샘플 테스트 제거 및 smoke test로 교체

기존 `test_hello_world.py`는 현재 프로젝트와 맞지 않는 샘플 테스트였다.
존재하지 않는 API와 UI를 검증하고 있어 실제 유지보수에 도움이 되지 않았다.

이를 `test_refactoring_smoke.py`로 교체했고, 아래 항목을 최소 수준으로 검증하도록 바꾸었다.

- config 로드
- trajectory repository 로드 및 조회
- playback progress clamp 동작

이 변경의 목적은 다음과 같다.

- 현재 코드베이스와 맞지 않는 테스트를 제거하기 위해
- 분리한 순수 로직을 최소한이라도 회귀 검증할 수 있게 하기 위해

## 왜 이 변경이 필요했는가

이전 구조에서는 거의 모든 책임이 하나의 mutable object 안에 들어 있었다.
그 결과, 수정 비용이 크고 부작용 위험도 높았으며, 읽는 사람 입장에서도 코드 의도를 빠르게 파악하기 어려웠다.

이번 구조 분해가 필요했던 이유는 다음과 같다.

- 책임을 눈에 보이게 분리하기 위해
- 경로 처리, timestamp 처리, 상태 관리 같은 반복 책임을 줄이기 위해
- 순수 로직과 Omniverse 의존 로직의 경계를 더 명확하게 만들기 위해
- 이후 유지보수와 확장 시 변경 영향을 좁히기 위해

## 기능 유지 관점에서 확인한 내용

이번 리팩터링은 `TimeTravelCore`를 외부 통합 지점으로 남겨두는 방식으로 진행했다.
즉, 기능 자체를 바꾸기보다 내부 구조를 바꾸는 데 집중했다.

기능 유지 관점에서 확인한 항목은 다음과 같다.

- `window.py`는 여전히 `TimeTravelCore`를 통해 동작한다.
- `extension.py`는 여전히 하나의 core 인스턴스를 생성해 사용한다.
- 시간 재생과 stage 갱신은 기존과 같은 상위 메서드 흐름을 유지한다.
- event summary 로드와 event JSON 처리 기능도 core facade를 통해 계속 접근 가능하다.

추가 검증으로 아래를 수행했다.

- 분리된 순수 Python 모듈에 대한 smoke test 추가
- 수정된 주요 모듈에 대한 Python compilation 확인

## 기대 효과

### 효율성

- 반복되던 파싱과 데이터 조회 책임이 한 곳으로 모였다.
- playback 로직이 stage 처리 및 event 파일 처리와 섞이지 않게 되었다.

### 가독성

- 각 파일이 하나의 주요 책임을 중심으로 읽히게 되었다.
- 내부 상태의 의미와 데이터 흐름을 추적하기 쉬워졌다.

### 유지보수성

- config, playback, event 처리 규칙을 서로 독립적으로 수정할 수 있게 되었다.
- 순수 로직은 Omniverse runtime 없이도 검증하기 쉬워졌다.
- facade 구조를 유지했기 때문에 이후 추가 리팩터링을 단계적으로 진행할 수 있다.

## 남아 있는 리스크와 후속 개선 포인트

- `view_overlay_core.py`는 아직도 stage subscription, scene 구성, overlay 업데이트 책임이 한 파일에 섞여 있다.
- `VLMClientWindow`는 여전히 worker thread에서 UI 상태를 직접 갱신하고 있어 thread-safe 정리가 필요하다.
- `EventProcessingWindow`도 현재는 UI 경로에서 동기 처리되고 있다.
- `event_list`, `intermediate_results`, `video` 같은 산출물 디렉터리가 여전히 패키지 코드와 같은 위치에 있어 output root 정책 정리가 필요하다.

## 결론

이번 리팩터링은 큰 폭의 재작성보다, 적은 변경으로 구조적 효과를 크게 만드는 방향에 초점을 맞췄다.
핵심 object를 기능별 object로 분화하면서도 extension 외부에서 사용하는 API는 유지했다.

그 결과 현재 프로젝트는 기존 동작 흐름을 유지하면서도,
다음 유지보수 사이클에서 더 적은 위험으로 이해하고 수정할 수 있는 구조에 가까워졌다.
