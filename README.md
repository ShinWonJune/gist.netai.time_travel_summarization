# Time Travel Summarization

> 디지털 트윈과 시각 언어 모델(VLM)을 연계해 **사건 중심으로 과거 시공간을 재구성**하는 NVIDIA Omniverse Kit 익스텐션.

GIST NetAI Lab의 연구 결과물 레포지토리이다.

---

## 연구 요약

- **목표** — 관리자가 긴 로그 영상을 수동으로 훑지 않아도 사건 발생 시점·위치 중심으로 디지털 트윈을 즉시 재구성할 수 있도록 한다.
- **접근** — 디지털 트윈(시공간 재현) ↔ Omniverse Extension(재구성 로직) ↔ VLM(이벤트 탐지) 세 모듈을 인터페이스 기반으로 연결한 폐루프 프레임워크.
- **검증 결과** — 시각적 추상화 환경에서 Qwen3-VL-8B의 F1 약 0.2 개선, 3배속 가속 시 추론 시간 50% 이상 단축(최대 12시간 로그까지 적용 가능 확인).


---

## 시스템 구성

```
 ┌─────────────────────┐    overlay+playback    ┌──────────────────┐
 │  Digital Twin (USD) │ ─────────────────────▶ │ Omniverse        │
 │  + trajectory CSV   │                        │ Extension (this) │
 └─────────────────────┘  ◀──── event feedback ─└────────┬─────────┘
                                                         │ video chunks
                                                         ▼
                                                ┌──────────────────┐
                                                │ VLM Server       │
                                                │ (NVIDIA VSS +    │
                                                │  open VLM / API) │
                                                └──────────────────┘
```

---

## 디렉토리 구조

```
gist/netai/time_travel_summarization/
├── extension.py                # Kit 진입점
├── config.json                 # 사용자 환경 설정 (env 치환 지원)
├── config.example.json         # 설정 샘플
├── README.md                   # 사용자 워크플로 가이드 (정본)
│
├── app/                        # 익스텐션 컴포지션
│   ├── facade.py               # TimeTravelCore (외부 API)
│   ├── config.py               # ExtensionConfig
│   └── paths.py                # ExtensionPaths (artifacts 정책)
│
├── playback/                   # Time Travel 재생 도메인
│   ├── controller.py
│   ├── trajectory_repository.py
│   └── stage_object_controller.py
│
├── overlay/                    # Viewport overlay
│   ├── core.py
│   ├── components.py
│   └── window.py
│
├── vlm_client/                 # VLM 서버 통신
│   ├── core.py
│   └── window.py
│
├── event_processing/           # VLM 결과 후처리
│   ├── core.py
│   ├── summary_service.py
│   └── window.py
│
├── ui/                         # UI 인프라
│   ├── main_window.py
│   └── task_dispatcher.py      # main thread dispatcher
│
├── utils/                      # 운영 스크립트 (런타임 비의존)
├── tests/                      # smoke test
├── data/                       # 입력 trajectory CSV
├── VLM_server/                 # VLM 서버 운영 가이드
└── artifacts/                  # 런타임 산출물 (gitignored)
    ├── video/
    ├── vlm_outputs/
    ├── intermediate_results/
    └── event_list/
```

---

## 빠른 시작

1. **VLM 서버 준비** — [`gist/netai/time_travel_summarization/VLM_server/README.md`](gist/netai/time_travel_summarization/VLM_server/README.md)
2. **환경 변수 설정**
   ```bash
   export VIA_BACKEND="http://<vlm-server-host>:8100"
   export ASTRONAUT_USD_PATH="omniverse://<your-nucleus-host>/.../Astronaut.usd"
   ```
3. **익스텐션 로드** — USD Composer → Extensions → Local Path 추가 후 활성화.
4. **사용자 워크플로** — [`gist/netai/time_travel_summarization/README.md`](gist/netai/time_travel_summarization/README.md) (궤적 데이터 생성 → Time Travel → View Overlay → 동영상 추출 → VLM 추론 → Event 기반 요약 재생까지 단계별).

---

## 환경 변수

| 변수 | 용도 | 예 |
|------|------|----|
| `VIA_BACKEND` | VSS 서버 base URL | `http://10.0.0.10:8100` |
| `ASTRONAUT_USD_PATH` | Time Travel 객체로 사용할 USD 경로 (`config.json`의 `${ASTRONAUT_USD_PATH}`로 치환) | `omniverse://host/.../Astronaut.usd` |

설정값을 직접 `config.json`에 적어 두는 것도 가능하다. 샘플은 [`config.example.json`](gist/netai/time_travel_summarization/config.example.json) 참조.

---

