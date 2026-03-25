# Stage Access and Lifecycle Analysis

## 목적

이 문서는 현재 `gist.netai.time_travel_summarization` 프로젝트를 기준으로 다음을 자세히 설명한다.

- 현재 stage 접근이 어디에서 어떻게 일어나는지
- 현재 `_core.py` / `_window.py` 분리가 어떤 수준까지 되어 있는지
- 왜 지금의 분리만으로는 충분하지 않은지
- 어떤 식으로 구조를 재편해야 하는지
- 현재 lifecycle이 기능별로 어떻게 관리되는지
- 개선 방향과 그렇게 해야 하는 이유

## 결론 요약

현재 프로젝트는 표면적으로는 `_core.py`가 로직, `_window.py`가 UI를 담당하는 구조로 보인다. 그러나 실제로는 이 분리가 "UI 코드 분리" 수준에 머물러 있고, 아래 세 가지 분리가 충분히 되어 있지 않다.

- pure logic 와 Omniverse stage 조작의 분리
- feature orchestration 과 feature-specific controller의 분리
- lifecycle 관리와 기능 구현의 분리

즉, 지금도 어느 정도 분리는 되어 있지만, 장기 유지보수 가능한 구조라고 보기에는 아직 한 단계 더 쪼개야 한다.

가장 큰 문제는 `TimeTravelCore`와 `ViewOverlay`가 단순 core가 아니라 다음을 동시에 수행한다는 점이다.

- application state 보관
- 파일 로드
- stage 접근 및 prim 조작
- camera 생성/이동
- feature orchestration
- lifecycle 일부 처리
- UI가 호출할 API 제공

이 구조는 "창과 로직을 분리한 상태"이지만 "애플리케이션 계층과 stage adapter 계층을 분리한 상태"는 아니다.

## 1. 현재 구조 개요

현재 주요 구성은 다음과 같다.

- `extension.py`
  - extension startup/shutdown orchestration
  - main update subscription 생성
  - 각 core/window 객체 생성 및 연결
- `core.py`
  - 타임트래블 메인 기능 대부분
  - trajectory 데이터 로드
  - playback 상태 관리
  - stage object 위치 갱신
  - camera 생성 및 이동
  - event list 로드 및 event processing orchestration
  - prim 생성/삭제
- `window.py`
  - time travel UI
  - 사용자 입력을 `TimeTravelCore`에 직접 전달
- `view_overlay_core.py`
  - overlay stage 이벤트 처리
  - prim 추적
  - scene view build/cleanup
  - frame update
  - time HUD 표시
- `view_overlay_window.py`
  - overlay 표시 옵션 UI
- `vlm_client_core.py`
  - VLM 서버 통신
  - 결과 저장
- `vlm_client_window.py`
  - VLM 업로드/삭제/생성 UI
  - background thread 생성
- `event_post_processing_core.py`
  - JSON 파싱 및 event 통합의 순수 로직 일부
- `event_post_processing_window.py`
  - 후처리 실행 UI

## 2. 현재 stage 접근 상태

### 2.1 stage에 직접 접근하는 객체

현재 직접적으로 `omni.usd.get_context()` 또는 `get_stage()`를 사용하고 stage/prim을 조작하는 주요 객체는 아래와 같다.

#### 1. `TimeTravelCore`

직접 수행하는 작업:

- USD context 저장 #usd context 저장이 구체적으로 뭘 한다는거지?
- stage 가져오기
- camera prim 조회/생성
- actor prim 조회
- prim transform 수정
- TimeTravel prim 생성/삭제
- 전체 camera 순회 및 visibility 변경 #카메라 위치를 바꾼다는 뜻인가?

주요 위치:

- `core.py:50`
- `core.py:59`
- `core.py:65`
- `core.py:72`
- `core.py:302`
- `core.py:318`
- `core.py:537`
- `core.py:546`
- `core.py:662`
- `core.py:669`
- `core.py:673`
- `core.py:697`
- `core.py:707`
- `core.py:712`
- `core.py:781`
- `core.py:787`

#### 2. `ViewOverlay`

직접 수행하는 작업:

- stage event stream 구독
- stage 존재 여부 확인
- parent prim 조회
- scene build/cleanup
- viewport scene view 등록/제거

주요 위치:

- `view_overlay_core.py:124`
- `view_overlay_core.py:138`
- `view_overlay_core.py:148`
- `view_overlay_core.py:264`
- `view_overlay_core.py:267`
- `view_overlay_core.py:316`
- `view_overlay_core.py:322`
- `view_overlay_core.py:356`

#### 3. `ObjectIDManipulator`

직접 수행하는 작업:

- 생성 시 stage 조회
- prim path로 prim 조회
- prim world transform 읽기
- frame마다 prim 위치 다시 계산

주요 위치:

- `view_overlay_core.py:24`
- `view_overlay_core.py:25`
- `view_overlay_core.py:42`
- `view_overlay_core.py:94`

### 2.2 stage에 직접 접근하지 않지만 stage 변경을 유발하는 객체

#### 1. `extension.py`

직접 stage를 만지지는 않지만, 아래 호출을 통해 stage 변경을 유발한다.

- `auto_generate_astronauts()`
- `clear_timetravel_objects()`
- overlay 생성
- core update 호출

주요 위치:

- `extension.py:49`
- `extension.py:101`
- `extension.py:177`

#### 2. `TimeTravelWindow`

window는 stage를 직접 모르지만 아래 메서드를 호출함으로써 stage 변경을 간접 유발한다.

- `set_current_time()`
- `set_progress()`
- `go_to_next_event()`
- `load_events_from_positions_jsonl()`

이 메서드들 내부에서 `TimeTravelCore`가 stage object update 또는 camera 이동을 수행한다.

주요 위치:

- `window.py:133`
- `window.py:146`
- `window.py:163`
- `window.py:180`

#### 3. `EventProcessingWindow`

직접 stage를 만지지 않지만 `process_event_json()`을 호출하고, 이 작업은 core의 메모리 trajectory 상태와 결합되어 있다.

주요 위치:

- `event_post_processing_window.py:82`

### 2.3 현재 stage 접근의 특징

현재 stage 접근 방식의 특징은 다음과 같다.

#### 1. 접근 지점이 제한되어 있기는 하다

좋은 점은 모든 window가 stage를 직접 만지는 구조는 아니라는 점이다. stage 조작은 주로 `core.py`와 `view_overlay_core.py`에 모여 있다.

이것은 전혀 분리가 안 된 상태는 아니라는 뜻이다.

#### 2. 하지만 "controller 계층으로 제한"된 상태는 아니다

이유는 다음과 같다.

- `TimeTravelCore`는 controller라기보다 god object에 가깝다.
- state 보관, 데이터 조회, event 처리, camera 제어, prim 생성/삭제가 한 객체에 섞여 있다.
- `ViewOverlay`도 overlay renderer라기보다 lifecycle + registry + renderer + updater를 모두 포함한다.

즉, stage 접근이 특정 파일에 모여 있기는 하지만, 역할이 명확히 나뉜 controller 계층으로 정리된 것은 아니다.

#### 3. stage 참조 사용 방식이 일관되지 않다

현재는 아래 두 방식이 혼용된다.

- cached `self._stage` 사용
- 메서드마다 `self._usd_context.get_stage()` 재조회

이 방식은 stage reload 시 stale reference 위험을 높인다. 어떤 메서드는 오래된 stage를 붙잡고 있고, 어떤 메서드는 새 stage를 가져올 수 있기 때문이다.

## 3. 지금의 `_core.py` / `_window.py` 분리만으로 충분한가

결론부터 말하면 충분하지 않다.

다만 모든 `_core.py`를 무조건 더 쪼개야 한다는 뜻은 아니다. 기능별로 상황이 다르다.

### 3.1 어느 정도 잘 나뉜 부분

#### 1. `vlm_client_core.py` / `vlm_client_window.py`

이 둘은 상대적으로 역할 분리가 잘 되어 있다.

- core는 서버 통신과 파일 저장 담당
- window는 UI 구성과 사용자 입력 담당

물론 `window`가 thread-safe하지 않다는 문제는 있지만, 책임 분리 자체는 비교적 명확하다.

#### 2. `event_post_processing_core.py`

이 파일은 pure logic 분리의 좋은 출발점이다.

- JSON 파싱
- timestamp/object id 변환
- event 통합

즉, Omniverse 밖으로 뺄 수 있는 계산 로직이 이미 일부 분리되어 있다.

### 3.2 더 분해가 필요한 부분

#### 1. `TimeTravelCore`

현재 `TimeTravelCore`는 단순한 "기능 core"가 아니다. 사실상 아래 계층이 다 섞여 있다.

- config storage
- data repository
- playback state
- stage adapter
- camera controller
- event summary service
- actor generation service
- application facade

따라서 이 객체는 반드시 더 분해하는 것이 맞다.

#### 2. `ViewOverlay`

현재 `ViewOverlay`도 다음이 섞여 있다.

- stage lifecycle 대응 #이게 구체적으로 어떤 작업을 뜻하는것인가??
- tracked prim registry 구성 #이것도 구체적으로 어떤 작업을 뜻하는것인가?
- scene view renderer
- frame update loop
- HUD 표시
- visibility state

overlay도 renderer/controller/lifecycle를 분리해야 한다.

### 3.3 왜 `_core.py` / `_window.py`만으로는 부족한가

이 분리는 기본적으로 "UI 코드와 기능 코드를 나눈다"는 수준이다.  
하지만 지금 프로젝트에서 더 중요한 분리는 아래와 같다.

#### 1. domain logic vs Omniverse adapter

예:

- timestamp 계산
- playback 계산
- event list 정렬
- object id 매핑

이것들은 Omniverse가 없어도 돌아가야 한다. # 왜 omniverse 가 없어도 돌아가야하는가? 왜 omniverse가 없는 상황을 가정해야하는가? 게다가 playback 계산은 rendering이 완료된 시점의 신호를 받아서 계산하는 구조 아닌가?

반면 아래는 Omniverse adapter에 속한다.

- stage에서 prim 찾기
- prim transform 반영
- camera prim 생성
- scene view 등록

이 둘이 섞이면 테스트가 무거워지고 오류 원인 분리가 어려워진다. # omniverse extension인데 omniverse 없는 테스트가 무슨 의미인가??

#### 2. application orchestration vs feature implementation

예:

- "재생 시간을 바꾼다"는 use case orchestration
- "그 시간의 actor position을 stage에 반영한다"는 구체 구현

지금은 `TimeTravelCore` 하나가 둘 다 하고 있다.

#### 3. lifecycle management vs business logic

예:

- stage가 닫힐 때 overlay를 정리하는 일
- extension shutdown 때 subscription을 끊는 일

이것은 business logic가 아니라 lifecycle 관리다.  
지금은 기능 구현 클래스가 이런 책임까지 같이 지고 있다.

## 4. 어떤 식으로 재편성해야 하는가

추천 방향은 "기능별 core/window" 구조를 완전히 버리는 것이 아니라, 그 위에 한 계층을 더 넣는 것이다.

즉, 아래처럼 재편하는 것이 좋다.

## 4.1 권장 계층 구조

```text
extension.py
  -> AppController
      -> ExtensionConfig
      -> StageSessionManager
      -> PlaybackController
      -> TrajectoryRepository
      -> EventSummaryService
      -> StageObjectController
      -> SummarizationCameraController
      -> OverlayController
      -> BackgroundTaskService
      -> WindowPresenter / WindowModel
```

### 계층별 역할

#### 1. `extension.py`

역할:

- wiring
- startup/shutdown 진입점
- app-level subscription 등록

하지 말아야 할 일:

- feature 로직 직접 실행
- core 내부 state 직접 수정
- private attribute 접근

#### 2. `AppController`

역할:

- 사용자 use case orchestration
- startup/shutdown 흐름 제어
- stage opened/closed 이벤트 수신 후 각 controller 호출 

예:

- "초기 데이터 로드"
- "time slider 이동"
- "next event 이동"
- "event summary mode 활성화"

#### 3. `TrajectoryRepository`

역할:

- CSV 로드
- timestamp 정렬
- 특정 시간의 위치 데이터 반환
- LKV 처리

이 객체는 stage를 전혀 몰라야 한다.

#### 4. `PlaybackController`

역할:

- 현재 시간
- 재생 여부
- 재생 속도
- progress 계산
- event playback mode 상태

이 객체도 stage를 몰라야 한다.

#### 5. `StageObjectController`

역할:

- prim path 관리
- actor prim 생성/삭제
- prim transform 반영

이 객체만 stage object를 직접 만지게 한다.

#### 6. `SummarizationCameraController`

역할:

- summarization camera 생성
- camera transform 관리
- event 위치 기반 이동

camera 관련 stage 접근은 여기로 몰아야 한다.

#### 7. `OverlayController`

역할:

- stage opened/closed에 따라 overlay build/cleanup
- tracked prim registry 유지
- HUD update

내부적으로는 다시 나눌 수 있다.

- `OverlayRegistry`
- `ObjectLabelOverlay`
- `TimeHudOverlay`

#### 8. `WindowPresenter` 또는 `WindowModel`

역할:

- UI가 소비할 값 가공
- 버튼 활성/비활성 상태 계산
- window가 직접 core 상태를 조합하지 않도록 함

### 4.2 현재 파일을 어떻게 매핑할 수 있는가

#### 현재 `core.py`에서 분리할 대상

- config 관련 -> `ExtensionConfig`
- trajectory 관련 -> `TrajectoryRepository`
- playback 관련 -> `PlaybackController`
- stage actor update 관련 -> `StageObjectController`
- camera 관련 -> `SummarizationCameraController`
- event json 처리 orchestration -> `EventSummaryService`
- 기능 연결 -> `AppController`

#### 현재 `window.py`의 방향

지금처럼 window가 core를 직접 호출하는 대신:

- window는 presenter/controller 인터페이스만 호출
- UI 갱신은 presenter model을 읽어서 수행

예:

```python
self._app_controller.set_progress(progress)
state = self._presenter.get_time_travel_view_state()
```

#### 현재 `vlm_client_window.py`의 방향

분해 폭은 `TimeTravelCore`보다 작아도 된다. 다만 다음은 추가해야 한다.

- `BackgroundTaskService`
- task result queue
- UI state model

즉, 이 부분은 "더 분해해야 한다"기보다 "thread boundary를 분리해야 한다"가 핵심이다.

## 5. 왜 이렇게 재편해야 하는가

### 5.1 테스트 가능성

지금 구조에서는 playback 계산을 검증하려 해도 `TimeTravelCore` 안에 stage/camera/event 로직이 같이 들어 있다.  
분리하면 아래처럼 테스트할 수 있다.

- `TrajectoryRepository` 단위 테스트
- `PlaybackController` 단위 테스트
- `EventSummaryService` 단위 테스트
- `StageObjectController`는 integration test

### 5.2 오류 원인 분리

지금은 오류가 나면 아래가 한 덩어리로 보인다.

- timestamp 계산 문제인지
- stage가 없는 문제인지
- prim path 문제인지
- event data 문제인지

분리 후에는 어떤 계층에서 실패했는지 구분이 훨씬 쉬워진다.

### 5.3 lifecycle 안정성

stage가 열리고 닫히는 순간, 살아 있어야 하는 객체와 버려야 하는 객체를 구분하려면 stage 접근 코드가 controller 쪽에 모여 있어야 한다.  
지금처럼 여러 객체가 stage를 임의로 들고 있으면 cleanup 정책이 흐려진다.

### 5.4 변경 비용 감소

예를 들어 actor 생성 정책을 astronaut에서 다른 asset으로 바꾸고 싶을 때, 지금은 config, core, overlay, lifecycle 영향을 한꺼번에 봐야 한다.  
분리 후에는 `StageObjectController`와 관련 config 중심으로 영향 범위를 좁힐 수 있다.

## 6. 현재 lifecycle은 기능별로 어떻게 관리되고 있는가

## 6.1 Extension 전체 lifecycle

### startup

현재 startup 흐름:

1. `TimeTravelCore()` 생성
2. core 생성 시 summarization camera 생성 시도
3. config 로드
4. `auto_generate`가 켜져 있으면 astronaut prim 자동 생성
5. trajectory 데이터 로드
6. main window 생성
7. event processing window 생성
8. VLM client core/window 생성
9. overlay 생성 시도
10. app update subscription 등록
11. earliest time으로 stage 세팅

주요 위치:

- `extension.py:35`
- `extension.py:39`
- `extension.py:46`
- `extension.py:49`
- `extension.py:53`
- `extension.py:56`
- `extension.py:60`
- `extension.py:65`
- `extension.py:72`
- `extension.py:97`
- `extension.py:105`

### shutdown

현재 shutdown 흐름:

1. update subscription 제거
2. window destroy
3. event window destroy
4. VLM window destroy
5. VLM core 참조 해제
6. overlay control destroy
7. overlay shutdown
8. `core.clear_timetravel_objects()` 호출

주요 위치:

- `extension.py:114`
- `extension.py:123`
- `extension.py:132`
- `extension.py:141`
- `extension.py:152`
- `extension.py:161`
- `extension.py:175`

### 문제점

- startup 때 core 생성과 동시에 camera 생성 시도가 일어난다.
- startup 때 stage가 없으면 camera 생성은 조용히 skip되고, 이후 재생성 책임이 명확하지 않다.
- shutdown 때 `clear_timetravel_objects()`로 stage를 직접 정리하는데, 이 동작은 "extension이 만든 prim만 정리"인지 "현재 stage에서 관리 중인 것만 정리"인지 계약이 명확하지 않다. # extension이 만든 prim만 정리해야한다.

## 6.2 Time Travel 기능 lifecycle

현재 이 기능은 명시적인 stage lifecycle을 거의 갖고 있지 않다.

### 현재 방식

- 필요할 때마다 `get_stage()` 호출
- `_stage` 캐시를 일부 재사용
- 사용자가 시간 이동/재생을 할 때마다 즉시 stage object 갱신
- event 이동 시 camera도 즉시 이동

대표 메서드:

- `_create_summarization_camera()`
- `update_stage_objects()`
- `_move_summarization_camera_to_event()`
- `clear_timetravel_objects()`
- `create_astronaut_prim()`
- `hide_all_cameras()`

### 문제점

- stage opened/closed를 TimeTravel 기능 자체는 구독하지 않는다.
- stage reload 이후 `_prim_map`은 살아 있지만 실제 prim은 새 stage에 없을 수 있다.
- `_stage` 캐시가 유효한지 확인하는 구조가 일관되지 않다.
- actor/camera 생성 시점과 재활용 시점이 lifecycle 이벤트와 연결되어 있지 않다.

즉, TimeTravel 기능은 lifecycle-aware가 아니라 "필요할 때 stage를 가져와서 해보는 구조"에 가깝다. # 이게 왜 문제가 되는가? 

## 6.3 Overlay 기능 lifecycle

overlay는 현재 기능 중 lifecycle 관리가 가장 명시적이다.

### 현재 방식

- 생성 시 stage event stream 구독
- stage가 이미 열려 있으면 즉시 build
- `OPENED`에서 build
- `CLOSED`에서 cleanup
- 별도 update subscription으로 frame 갱신

주요 위치:

- `view_overlay_core.py:138`
- `view_overlay_core.py:148`
- `view_overlay_core.py:264`
- `view_overlay_core.py:267`
- `view_overlay_core.py:360`

### 장점

- 최소한 stage open/close에 반응한다.
- scene view cleanup 경로가 있다.

### 문제점

- tracked prim registry와 scene renderer가 분리되지 않았다.
- `ObjectIDManipulator`가 생성 시 stage/prim을 잡아두므로 stage reload에 취약하다.
- `TimeTravel_Objects` prim이 없으면 그냥 반환하고 이후 재시도 전략이 없다.
- overlay build 타이밍이 actor prim 생성 시점과 명시적으로 연결되어 있지 않다. 

즉, overlay는 lifecycle 인식은 있지만, feature lifecycle과 stage content lifecycle을 함께 관리하지는 못하고 있다.

## 6.4 Event Processing 기능 lifecycle

현재는 별도 lifecycle이 거의 없다.

### 현재 방식

- window 버튼 클릭 시 즉시 `core.process_event_json()` 호출
- 처리 결과를 파일로 저장
- core의 in-memory trajectory 데이터에 의존

문제점:

- 이 기능은 stage 자체는 안 만지지만, core 내부 메모리 상태에 결합되어 있다.
- startup 시 데이터가 안 로드되어 있거나, 다른 dataset으로 교체된 경우 어떤 상태가 유효한지 명확하지 않다.

즉, stage lifecycle보다는 application state lifecycle에 묶여 있다.

## 6.5 VLM Client 기능 lifecycle

### 현재 방식

- extension startup 때 core/window 생성
- button click 때 background thread 생성
- thread 완료 시 window UI 직접 갱신
- shutdown에서는 window destroy와 core 참조 해제만 수행

문제점:

- background task lifecycle과 UI lifecycle이 분리되지 않았다.
- shutdown 시 worker가 살아 있으면 어떻게 될지 명확하지 않다.
- thread-safe하지 않은 UI 갱신이 있다.

즉, stage lifecycle 문제는 적지만 task lifecycle 문제는 있다.

## 7. lifecycle 관점에서 구체적으로 어떻게 정리해야 하는가

핵심은 기능별로 "무엇을 하느냐"보다 "언제 생성되고 언제 버려져야 하느냐"를 먼저 정의하는 것이다.

## 7.1 lifecycle 층위 분리

아래 세 층위로 나누는 것이 좋다.

### 1. Extension lifecycle

시점:

- `on_startup`
- `on_shutdown`

대상:

- window
- app controller
- config
- global subscriptions
- task service

정책:

- startup에서 생성
- shutdown에서 무조건 dispose

### 2. Stage session lifecycle

시점:

- stage opened
- stage closed
- stage reloaded

대상:

- current stage reference
- stage-bound prim handle
- scene view
- overlay registry
- stage subscriptions
- stage-bound caches

정책:

- opened에서 attach
- closed에서 detach
- stage reload는 closed + opened처럼 취급

### 3. Feature task lifecycle

시점:

- upload 시작/완료/실패
- event processing 시작/완료/실패

대상:

- worker
- queue
- UI pending state
- status message

정책:

- task 시작 시 등록
- 완료/실패 시 queue에 결과 전달
- shutdown 시 drain 또는 ignore policy 명시

## 7.2 권장 객체

### `StageSessionManager`

역할:

- stage attach/detach의 단일 진입점
- stage session 시작/종료 관리

예시 메서드:

- `attach_stage(stage)`
- `detach_stage()`
- `has_stage()`
- `get_stage()`

### `SubscriptionRegistry`

역할:

- update/stage subscriptions 등록
- dispose 시 일괄 해제

### `Disposable` contract

모든 stage-bound 객체는 아래 규칙을 가지는 것이 좋다.

- `initialize()`
- `shutdown()` 또는 `dispose()`

즉, 어떤 객체가 "열릴 때 준비되고 닫힐 때 해제되는 객체"인지 코드 차원에서 드러나야 한다.

## 7.3 feature별 개선 구조

### Time Travel

현재:

- `TimeTravelCore`가 lifecycle-aware하지 않음

개선:

- `PlaybackController`는 stage를 모름
- `TrajectoryRepository`는 stage를 모름
- `StageObjectController`는 stage attach 시 prim 관련 준비
- `SummarizationCameraController`는 stage attach 시 camera 확인/생성
- `AppController`가 stage opened 때 둘을 호출

이유:

- 재생 상태는 stage와 독립적으로 유지할 수 있어야 한다.
- stage가 없어도 현재 시간, progress, event index는 살아 있을 수 있다.
- stage가 다시 열리면 그 상태를 stage에 재적용하면 된다.

### Overlay

현재:

- `ViewOverlay`가 build/update/cleanup/tracking을 모두 담당

개선:

- `OverlayRegistry`: 어떤 prim을 추적할지 관리
- `ObjectLabelOverlay`: label scene view 렌더링
- `TimeHudOverlay`: time HUD 렌더링
- `OverlayController`: lifecycle orchestration

이유:

- tracked 대상이 바뀌는 경우와, 그리는 방식이 바뀌는 경우를 분리할 수 있다.
- 향후 filtering, selection, event-only view 같은 요구사항에 대응하기 쉽다.

### Event Processing

현재:

- window가 `core.process_event_json()` 직접 호출

개선:

- `EventSummaryService`가 후처리 orchestration 담당
- `PositionLookupAdapter`가 trajectory lookup만 담당
- window는 service 실행 요청만 함

이유:

- event 처리와 TimeTravel main core 결합도를 낮출 수 있다.
- data loaded 여부를 명시적으로 검증하기 쉬워진다.

### VLM Client

현재:

- window가 thread 생성 및 UI 갱신까지 담당

개선:

- `VLMClientCore`: 서버 작업만 담당
- `BackgroundTaskService`: worker 실행
- `VLMWindowPresenter`: UI 상태 계산

이유:

- thread-safe 문제를 없애고, task 취소/완료/실패 상태를 일관되게 다룰 수 있다.

## 8. 왜 이런 구조가 되어야 하는가

### 1. stage는 영속 객체가 아니기 때문이다

stage는 열리고 닫히고 다시 로드된다.  
따라서 stage에 붙는 객체는 언제든 재초기화될 수 있어야 한다.

### 2. playback state와 stage state는 같은 것이 아니기 때문이다

예:

- 현재 시간
- 재생 속도
- event index

이 값들은 stage가 없어도 유지 가능한 application state다.  
반면 prim handle, camera prim, scene view는 stage가 닫히면 버려야 하는 state다.

이 둘을 섞어두면 stage close 시 application state까지 불필요하게 흔들리거나, 반대로 stale stage handle이 남는다.

### 3. Omniverse 의존 로직은 변동성이 크기 때문이다

viewport, stage event, prim validity, UI thread 규칙은 pure logic보다 환경 변화에 더 민감하다.  
그래서 이 부분을 따로 격리해야 전체 시스템 안정성이 올라간다.

### 4. 기능 추가 방향이 이미 현재 구조를 넘어서고 있기 때문이다

앞으로 요구될 가능성이 높은 기능:

- 특정 객체만 표시
- event 관련 객체 강조
- 다른 asset type 자동 생성
- 여러 dataset 전환
- richer event summary playback

이런 기능은 controller, registry, presenter 계층 없이 `core/window`만으로 감당하기 어렵다.

## 9. 실제 권장 재편 순서

### 1단계

- `ExtensionConfig` 도입
- `TrajectoryRepository` 분리
- `PlaybackController` 분리

### 2단계

- `StageObjectController`
- `SummarizationCameraController`
- `StageSessionManager`

### 3단계

- `AppController` 도입
- window가 core 대신 controller 인터페이스만 사용하도록 변경

### 4단계

- `ViewOverlay` 분해
- `BackgroundTaskService` 도입
- VLM/Event Processing presenter화

## 최종 판단

현재 구조는 "기능별 core와 window를 나눈 프로토타입 구조"로는 이해할 수 있다.  
하지만 stage 접근, lifecycle, orchestration, background task를 고려하면 지금 구조는 한 단계 더 세분화되어야 한다.

따라서 질문에 대한 직접적인 답은 다음과 같다.

- 지금도 `_core.py`와 `_window.py` 분리는 있다.
- 하지만 그것만으로는 충분하지 않다.
- 특히 `TimeTravelCore`와 `ViewOverlay`는 더 분해해야 한다.
- 분해 방향은 "기능별"이 아니라 "책임별"이어야 한다.
- 핵심 기준은 다음 세 가지다.
  - stage를 직접 만지는가
  - pure logic 인가
  - lifecycle에 묶이는 객체인가

이 기준으로 재편해야 stage reload, extension reload, UI 변경, 기능 확장에 모두 견딜 수 있는 구조가 된다.
