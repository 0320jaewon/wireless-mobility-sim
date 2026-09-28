# CLAUDE.md

이 파일은 Claude Code가 이 프로젝트를 다시 열었을 때 맥락을 빠르게 파악하기 위한 요약이다. 실험 결과·발견은 여기 복사하지 않고 [FINDINGS.md](FINDINGS.md)와 [results/INDEX.md](results/INDEX.md)를 참조한다.

## 1. 프로젝트 개요

무선통신망의 위치관리(LM)와 핸드오버(HO) 과정에서 발생하는 시그널링 오버헤드를 Baseline(즉시 전환+주기적 LU) / 개선된 전통기법(히스테리시스+타이머) / AI(마르코프 체인 예측) 3종으로 비교하고, 여기에 더해 Domain(Access Network) 전환 시 발생하는 세션 커넥티비티(IP 변경) 문제를 같은 시뮬레이터 안에서 함께 측정하는 Python 시뮬레이터다. 5x5 육각 셀 격자를 2개 Domain으로 나눈 환경에서 단말기 여러 개를 이동시키며, 알고리즘별로 시그널링 오버헤드/핑퐁 HO 비율/예측 정확도/콜 드랍 근사치/세션 연속성 지표를 CSV와 그래프로 비교한다.

## 2. 핵심 개념

**LM(위치관리)/HO(핸드오버)**: 세 알고리즘 각각 `step_handover()`(HO 결정)와 `step_lm()`(주기적 위치갱신)을 구현한다. Baseline은 즉시 전환 + 고정 주기 LU, improved는 히스테리시스+타이머로 핑퐁 억제, ai는 마르코프 예측 방향으로 히스테리시스를 낮춰 더 빠르게 전환하고 페이징 범위도 예측 셀 중심으로 축소한다.

**세션 커넥티비티 (Triple Tuple)**: `session.py`의 `Session` 클래스가 `(application_id, port, ip_address)` 튜플로 세션을 모델링한다. `SessionManager`가 단말기의 `domain_id`가 바뀔 때만 `ip_address`를 재할당하고, 이를 "세션 재설정" 이벤트로 카운트한다(`session_reset_count`, `session_continuity_rate` 지표로 집계).

**CBN/PBN (배경 개념, 코드에 직접 구현되지 않음)**: CBN(Circuit-Based Network, 2G~3G 회선교환, 통화 전 SS7 시그널링으로 경로를 미리 고정)과 PBN(Packet-Based Network, 4G~5G 패킷교환, IP 패킷 단위로 데이터 송수신)은 이 프로젝트가 전제하는 배경 지식이다. 4G부터 데이터 인프라가 IP 기반으로 전환되면서 CBN → PBN으로 넘어갔고, **본 시뮬레이터는 PBN(IP 기반) 환경을 가정한다** — `session.py`의 `ip_address` 필드 기반 세션 모델링이 바로 이 PBN 전제 위에서 설계된 것이다. CBN 자체(회선교환, SS7 시그널링)는 코드로 구현되어 있지 않다.

## 3. 진행 현황

스펙 1~7단계(topology/mobility → baseline+metrics → session 연동 → run_experiment 단일 실행 → improved 3종 비교 → ai_predictor(마르코프) → 이동모델 2종 추가+파라미터 스윕)와 확장 작업(반복실험+신뢰구간, cell_size×speed 히트맵, 1차 마르코프 예측기, Streamlit 대시보드, baseline/improved/ai 쌍체 t-검정, num_nodes 100/500/1000 확장성 벤치마크, pytest 핵심 함수 테스트, 토폴로지+이동경로+HO 시각화, results/ 폴더 정리) **전부 완료** 상태다.

## 4. 파일 구조 — `simulator/`

| 파일 | 역할 |
|---|---|
| `topology.py` | 육각 셀 격자 생성, 셀 인접관계, Domain 분할 |
| `mobility.py` | MobileNode 상태, 이동모델 3종(random_walk/random_waypoint/manhattan_grid), 신호세기 함수 |
| `baseline.py` | Baseline 알고리즘: 즉시 전환 HO + 고정 주기 LU + 전체 셀 페이징 |
| `improved.py` | 개선된 전통기법: 히스테리시스+타이머 HO + 독립 주기 LU |
| `ai_predictor.py` | 마르코프 예측(0차/1차) + AI LM/HO (예측 방향 히스테리시스 완화, 페이징 범위 축소) |
| `session.py` | 세션 커넥티비티: (application_id, port, ip_address) 튜플, domain 변경 시 IP 재할당 및 재설정 카운트 |
| `metrics.py` | 시그널링 오버헤드/핑퐁 비율/콜 드랍 근사치/예측 정확도/세션 지표 계산 |

**루트 스크립트**: `run_experiment.py`(파라미터 스윕+반복실험+CSV+그래프 메인 파이프라인), `bar_chart_snapshot.py`, `statistical_test.py`, `scalability_benchmark.py`, `visualize_topology.py`, `dashboard.py`(Streamlit), `tests/`(pytest).

## 5. results/ 폴더 구조

`results/`는 5개 하위 폴더(01_main_comparison ~ 05_raw_data)로 정리되어 있다. 파일별 설명과 생성 단계는 **[results/INDEX.md](results/INDEX.md)** 참고.

## 6. 보고서 진행 상황

- **기획서**: 제출 완료
- **중간보고서**: 작성 중. 범위는 Baseline + Improved + 세션 기본(IP 재할당/재설정 카운트)까지만 — AI(마르코프 예측), 파라미터 스윕, 통계 검증(t-test)은 **최종보고서용으로 남겨둠**
- **최종보고서**: 미착수. AI 기법, 파라미터 스윕/히트맵, t-검정, 확장성 벤치마크, 1차 마르코프 비교 등 확장 작업 결과를 여기서 다룰 예정

## 7. 세션을 다시 열면 가장 먼저 확인할 것

1. **[FINDINGS.md](FINDINGS.md)** — 예상과 다르거나 보고서에 쓸 만한 발견 전부 기록됨 (단계별로 계속 추가 중)
2. **[results/INDEX.md](results/INDEX.md)** — 어느 파일이 뭘 보여주는지, 어느 단계에서 만들어졌는지
