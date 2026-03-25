# Time Travel Summarization Project Review and Refactoring Plan

## 목적

이 문서는 [OMNIVERSE_SDK_IMPROVEMENTS.md](./OMNIVERSE_SDK_IMPROVEMENTS.md)의 1차 분석을 기준점으로 삼아, 현재 `gist.netai.time_travel_summarization` 프로젝트 전체를 다시 점검한 결과를 정리한 것이다.

핵심 결론은 다음과 같다.

- 1차 분석의 방향은 전반적으로 타당하다.
- 특히 `TimeTravelCore` 집중도, stage lifecycle, UI thread 경계, overlay 구조 문제는 실제 코드에서도 그대로 확인된다.
- 여기에 더해 현재 프로젝트는 패키징/테스트/환경 의존성/산출물 관리 측면에서 즉시 정리해야 할 운영 리스크를 안고 있다.
- 따라서 리팩토링은 "기능 확장"보다 먼저 "배포 가능성, 테스트 가능성, 상태 일관성"을 회복하는 방향으로 진행하는 것이 맞다.

## 전체 평가

### 강점

- Omniverse Kit extension의 주요 축을 실제로 모두 사용하고 있다.
  - extension lifecycle
  - `omni.ui` 기반 제어 UI
  - `omni.usd` 및 USD prim 조작
  - viewport overlay
  - update stream / stage event stream
- 데이터 기반 타임라인 재생, event 기반 요약, VLM 후처리까지 기능 흐름은 명확하다.
- `event_post_processing_core.py`처럼 Omniverse 비의존 로직으로 분리 가능한 씨앗이 일부 이미 존재한다.

### 약점

- 핵심 상태와 SDK 연동이 과도하게 한 클래스와 몇 개의 window 클래스에 뭉쳐 있다.
- 테스트, 패키징, 문서, 실제 import 경로가 서로 어긋나 있어 신뢰 가능한 배포/검증 루프가 없다.
- 외부 환경 의존성이 강한데 검증, fallback, 설정 모델이 약하다.
- 저장소 안에 실행 산출물과 캐시가 함께 섞여 있어 재현성과 유지보수성이 떨어진다.

### 현재 성숙도 평가

- 기능 프로토타입으로는 의미가 있다.
- 그러나 "장기 유지되는 Omniverse extension" 관점에서는 아직 구조 안정화 이전 단계다.
- 현재 상태에서 기능을 더 얹으면 회귀 가능성과 reload/stage 전환 불안정성이 빠르게 커질 가능성이 높다.

## 1차 분석 문서와의 일치 여부

다음 항목들은 1차 문서의 판단이 현재 코드와 직접적으로 일치하는 부분이다.

### 1. God Object 문제는 실제로 심각하다

`gist/netai/time_travel_summarization/core.py`의 `TimeTravelCore`는 다음을 동시에 담당한다.

- config 로드
- CSV 로드 및 timestamp 관리
- playback 상태 관리
- stage prim transform 반영
- summarization camera 생성 및 이동
- event list 로드
- event JSON 후처리 orchestration
- astronaut prim 생성 및 삭제

관련 위치:

- `core.py:13`
- `core.py:56`
- `core.py:153`
- `core.py:300`
- `core.py:662`
- `core.py:739`
- `core.py:799`

이는 1차 문서의 "TimeTravelCore 분해" 제안이 단순 개선이 아니라 필수 구조조정임을 의미한다.

### 2. Stage lifecycle은 부분 대응만 되어 있고, 상태 모델은 불완전하다

현재 stage open/close를 일부 구독하고 있지만, lifecycle 대응이 컨트롤러 단위로 정리되어 있지 않다.

- overlay는 `OPENED`, `CLOSED` 이벤트를 구독한다.
- core는 stage를 필요 시 즉석 조회하는 방식과 cached stage를 혼용한다.
- startup 시 camera 생성 시도를 하고, shutdown 시 prim 삭제까지 수행한다.

관련 위치:

- `view_overlay_core.py:138`
- `view_overlay_core.py:264`
- `view_overlay_core.py:267`
- `extension.py:101`
- `core.py:56`
- `core.py:662`

즉, 이벤트를 받고는 있지만 "stage가 바뀌었을 때 어떤 상태를 초기화하고 어떤 핸들을 버려야 하는가"가 명확한 계약으로 정리돼 있지 않다.

### 3. UI thread와 background task 경계가 안전하지 않다

`vlm_client_window.py`는 `threading.Thread`를 사용해 업로드/삭제/생성을 백그라운드로 돌리지만, worker thread 내부에서 UI 위젯 상태를 직접 갱신한다.

관련 위치:

- `vlm_client_window.py:79`
- `vlm_client_window.py:111`
- `vlm_client_window.py:143`
- `vlm_client_window.py:146`
- `vlm_client_window.py:189`

1차 문서의 "queue 기반 결과 전달 + main thread 반영" 제안은 그대로 유지해야 한다. # 현재 구조가 초래할 수 있는 문제점이 무엇인가? 수정 방향은 어떤 방향으로 수정되는건가?

### 4. Overlay 구조도 여전히 단일 클래스 집중형이다

`view_overlay_core.py`는 다음 책임을 거의 한 파일에서 처리한다.

- prim 직접 조회
- manipulator 구성
- stage event 구독
- scene build/cleanup
- frame update
- timestamp overlay UI

관련 위치:

- `view_overlay_core.py:15`
- `view_overlay_core.py:115`
- `view_overlay_core.py:307`
- `view_overlay_core.py:364`

overlay 대상이 늘어나거나 표시 정책이 복잡해지면 바로 유지보수 비용이 증가할 구조다.

## 이번 점검에서 추가로 확인된 핵심 문제

1차 문서에는 상대적으로 덜 드러났지만, 실제 프로젝트 관점에서는 아래 항목들이 우선순위가 높다.

### 1. 패키징 경로와 테스트 import 경로가 서로 맞지 않는다

현재 Python module 선언, premake 링크 경로, 테스트 import 경로가 서로 다르다.

- extension module 선언: `gist.netai.time_travel_summarization`
  - `config/extension.toml:38`
  - `config/extension.toml:39`
- premake 링크 대상: `netai`
  - `premake5.lua:7`
  - `premake5.lua:10`
- 테스트 import: `netai.timetravel_dreamai`
  - `tests/test_hello_world.py:23`

이 상태는 다음 문제를 만든다.

- 빌드/패키징 시 실제 Python 경로가 틀릴 수 있다.
- 테스트는 현재 코드 기준으로 거의 확실하게 깨진 상태다.
- README, 코드, extension 설정의 naming contract가 일관되지 않다.

이 항목은 구조개선 이전에 먼저 바로잡아야 한다.

### 2. 테스트가 현재 구현을 검증하지 못한다

`tests/test_hello_world.py`는 현재 프로젝트와 맞지 않는 템플릿 테스트로 보인다.

- 존재하지 않는 `some_public_function`을 호출한다.
- 현재 UI 구조와 무관한 `Add`, `Reset`, `Timetravel_dream_ai` selector를 찾는다.

관련 위치:

- `tests/test_hello_world.py:23`
- `tests/test_hello_world.py:39`
- `tests/test_hello_world.py:44`
- `tests/test_hello_world.py:48`
- `tests/test_hello_world.py:51`

즉, "테스트가 있다"가 아니라 "오해를 만드는 죽은 테스트가 있다"에 가깝다.

### 3. 환경 의존성이 강하지만 설정 모델과 검증이 약하다

현재 설정은 JSON과 환경변수에 흩어져 있으며, 경로와 서버 주소가 강하게 고정돼 있다.

- `config.json`의 `astronaut_usd`가 특정 `omniverse://10.38.38.32/...` 경로를 직접 참조한다.
- `vlm_client_core.py`는 `VIA_BACKEND`가 없으면 `http://10.38.38.40:8100`으로 고정된다.
- `auto_generate`가 기본 `true`라 stage 변경 시 부수효과가 크다.

관련 위치:

- `config.json:4`
- `config.json:6`
- `vlm_client_core.py:44`

문제는 단순 하드코딩 자체보다, 잘못된 환경일 때 사용자에게 어떤 값이 필수이고 어떤 값이 선택인지 명확히 설명되지 않는다는 점이다. # Readme에 추가 바람

### 4. 실행 산출물과 캐시가 저장소 구조에 혼재되어 있다

현재 패키지 내부에 다음이 함께 존재한다.

- `__pycache__`
- `video/`
- `vlm_outputs/`
- `intermediate_results/`
- `event_list/`
- `temp/`

이는 다음 문제를 만든다.

- 코드와 산출물의 경계가 흐려진다.
- 리뷰 시 노이즈가 커진다.
- extension 배포 산출물에 불필요한 파일이 섞이기 쉽다.
- `.gitignore`도 현재 프로젝트 전용 운영 규칙보다는 임시 산출물 나열에 가까워 관리 기준이 약하다.

### 5. Window 단위 polling 갱신이 많고 상태 흐름이 명시적이지 않다

`extension.py`의 frame update가 매번 core와 main window를 갱신하고, overlay는 자체적으로 또 frame update를 구독한다.

관련 위치:

- `extension.py:101`
- `extension.py:108`
- `window.py` 전반
- `view_overlay_core.py:360`
- `view_overlay_core.py:364`

현재 구조는 동작은 단순하지만, state mutation 경로가 분산되어 디버깅 난도가 올라간다.

## 리팩토링 우선순위

### P0. 바로 정리해야 하는 항목

#### 1. 패키지/모듈/빌드 경로 통일

해야 할 일:

- Python import canonical name을 하나로 확정한다. # canonical name이 무엇이며 왜 하나로 확정해야하는가?
- `config/extension.toml`, `premake5.lua`, README, 테스트 import를 모두 같은 이름으로 맞춘다.
- `premake5.lua`의 링크 경로가 실제 디렉터리 구조와 일치하도록 수정한다.

권장 방향:

- 실제 코드 구조를 기준으로 `gist.netai.time_travel_summarization`를 canonical path로 유지하는 편이 안전하다.

#### 2. 템플릿 테스트 제거 후 smoke test 재작성

해야 할 일:

- 현재 `test_hello_world.py`는 삭제하거나 전면 교체한다. #테스트가 꼭 필요한가?
- 최소한 아래 smoke test를 만든다.
  - extension startup/shutdown
  - main window 생성
  - config load 실패 시 graceful handling
  - stage 없는 상태에서 overlay/core가 예외 없이 동작하는지

#### 3. UI thread-safe 규칙 확립

해야 할 일:

- background thread는 결과 객체만 생산한다.
- UI 위젯 갱신은 update callback 혹은 main-thread dispatch에서만 수행한다.
- `VLMClientWindow`와 `EventProcessingWindow`에 공통 task result queue를 도입한다.

### P1. 구조를 지탱하는 핵심 분해

#### 1. `TimeTravelCore` 분해

권장 분리안:

- `ExtensionConfig`
- `TrajectoryRepository`
- `PlaybackController`
- `StageObjectController`
- `SummarizationCameraController`
- `EventSummaryService`
- `TimeTravelFacade` 또는 `AppController`

원칙:

- pure Python 로직과 Omniverse 의존 로직을 나눈다.
- window는 facade/controller만 바라보게 한다.
- stage 접근은 controller 계층으로 제한한다. #이러한 원칙을 설계한 이유는?

#### 2. Stage lifecycle manager 도입

해야 할 일:

- stage opened/closed/reloaded 시점별로 초기화 규칙을 문서화한다.
- stage-bound resource를 한곳에서 등록/해제한다.
- prim handle, subscription, overlay scene, camera 상태를 lifecycle 단위로 정리한다. #lifecycle 단위로 정리해야하는 이유는?

권장 객체:

- `StageSessionManager`
- `SubscriptionRegistry`
- `Disposable` 또는 `shutdown()/dispose()` contract

#### 3. Overlay 구조 재구성

해야 할 일:

- tracked prim registry와 scene renderer를 분리한다.
- time overlay와 object label overlay를 분리한다.
- build/rebuild/update 책임을 나눈다.

권장 분리안:

- `OverlayRegistry`
- `ObjectLabelOverlay`
- `TimeHudOverlay`
- `OverlayController`

### P2. 운영 품질과 확장성 개선

#### 1. 설정 모델 정식화

해야 할 일:

- JSON을 바로 dict로 들고 다니지 말고 typed config 객체로 변환한다.  #과거에 어땠으며 어떤 문제가 있었고, 왜 변환하는가?
- 필수/선택 설정을 나눈다.
- validation과 기본값 정책을 명확히 한다. 

예시:

- dataset path
- USD asset path
- backend URL
- auto-generate 여부
- default camera policy
- output directory policy

#### 2. 산출물 디렉터리 재배치

권장 방향:
 
- 코드 패키지 내부가 아니라 extension 루트 하위 `artifacts/` 또는 사용자 지정 output root로 이동 #artifacts가 무엇인가?
- 런타임 산출물과 소스 자산을 분리 #소스 자산에는 어떤 항목이 있나?

예시:

- `artifacts/video/`
- `artifacts/vlm_outputs/`
- `artifacts/event_list/`
- `artifacts/intermediate_results/`

#### 3. 문서 정비

현재 README는 의도와 워크플로우 설명은 많지만, 실제 import 경로/배포 구조/환경 요구사항과 어긋난 부분이 있다.

정리 대상:

- canonical package name
- 필수 환경 변수
- 필수 외부 서비스
- stage 준비 조건
- 지원하는 workflow와 비지원 범위

## 권장 아키텍처 방향

### 제안 구조

```text
extension.py
  -> AppController
      -> ExtensionConfig
      -> StageSessionManager
      -> PlaybackController
      -> TrajectoryRepository
      -> StageObjectController
      -> SummarizationCameraController
      -> EventSummaryService
      -> BackgroundTaskService
      -> OverlayController
      -> WindowPresenter(s)
```

### 설계 원칙

- `extension.py`는 wiring만 담당
- core domain은 Omniverse 없이 테스트 가능 # 왜 Omniverse 없이 테스트를 해야하는가?
- stage/viewport/UI는 adapter 또는 controller 계층에 한정
- window는 상태 표시와 사용자 입력 전달만 담당
- 백그라운드 작업은 UI와 직접 결합하지 않음

## 실행 순서 제안

### 1단계: 배포/검증 루프 복구

- 패키지 경로 통일
- premake 링크 수정
- 템플릿 테스트 제거
- smoke test 작성 # 테스트가 꼭 필요한가?
- `.gitignore`와 산출물 폴더 정책 정리

### 2단계: 상태 분리

- `TimeTravelCore`에서 repository/playback/stage adapter 분리
- config dataclass 도입 #이유는?
- background task queue 도입 #이유는?

### 3단계: Omniverse lifecycle 정리

- stage lifecycle manager 도입
- overlay/controller dispose contract 통일
- camera/prim/subscription cleanup 순서 고정

### 4단계: 기능 단위 고도화

- overlay filtering / selection 연동 #무슨 의미인가?
- event processing pure logic 확장 #무슨 확장을 의미하나?
- performance logging 및 profiling 추가 

## 최종 판단

이 프로젝트는 Omniverse SDK를 실제 문제에 연결한 점에서 가치가 크다. 다만 현재는 "기능이 있는 프로토타입"과 "안정적으로 유지되는 extension" 사이에 있고, 그 경계에서 가장 큰 비용은 기능 부족이 아니라 구조 일관성 부족이다.

따라서 다음 원칙으로 정리하는 것이 맞다.

1. 먼저 패키징, 테스트, thread-safety를 바로잡는다.
2. 그 다음 `TimeTravelCore`를 분해해 SDK 의존성과 순수 로직을 분리한다.#SDK 의존성과 순수로직을 분리를 왜 해야하는가?
3. 이후 stage lifecycle과 overlay를 컨트롤러 중심 구조로 재편한다.

이 순서를 따르면 1차 분석 문서의 목표였던 "Omniverse SDK를 더 깊이 이해하고 설계에 반영한 프로젝트"에 훨씬 가까워질 수 있다.
