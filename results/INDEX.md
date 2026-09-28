# results/ 폴더 인덱스

보고서 작성용 참조 인덱스. 재생성 방법은 각 행의 "생성 스크립트" 참고.

## 01_main_comparison — 3종 알고리즘 핵심 비교

대표 조합(cell_size=1.0, speed=0.3, num_nodes=30, mean ± std, n=10시드) 기준 막대그래프.

| 파일명 | 무엇을 보여주는지 | 생성 단계 / 스크립트 |
|---|---|---|
| bar_signaling_overhead.png | baseline/improved/ai의 signaling_overhead 평균±표준편차 막대비교 | bar_chart_snapshot.py 도입 시점, 정리 작업에서 대표 조합 필터링 방식으로 재작성 |
| bar_ping_pong_ratio.png | 3알고리즘 ping_pong_ratio 비교 | 〃 |
| bar_call_drop_approx.png | 3알고리즘 call_drop_approx 비교 | 〃 |
| bar_session_reset_count.png | 3알고리즘 session_reset_count 비교 | 〃 |
| bar_session_continuity_rate.png | 3알고리즘 session_continuity_rate 비교 | 〃 |

## 02_sensitivity — 파라미터 민감도 분석 (3알고리즘 공통 5개 지표)

한 번에 파라미터 1개만 변화시키고 나머지는 기준값 고정(one-at-a-time), mean ± std(n=10시드) 에러바 포함.

| 파일명 | 무엇을 보여주는지 | 생성 단계 / 스크립트 |
|---|---|---|
| signaling_overhead_vs_cell_size.png | cell_size 변화에 따른 signaling_overhead | 7-2단계(파라미터 스윕) 도입, 확장 1단계(반복실험)에서 에러바 추가 |
| signaling_overhead_vs_speed.png | speed 변화에 따른 signaling_overhead | 〃 |
| signaling_overhead_vs_num_nodes.png | num_nodes 변화에 따른 signaling_overhead | 〃 |
| ping_pong_ratio_vs_cell_size.png | cell_size 변화에 따른 ping_pong_ratio | 〃 |
| ping_pong_ratio_vs_speed.png | speed 변화에 따른 ping_pong_ratio (FINDINGS [확장 1단계] 근거 그래프) | 〃 |
| ping_pong_ratio_vs_num_nodes.png | num_nodes 변화에 따른 ping_pong_ratio | 〃 |
| call_drop_approx_vs_cell_size.png | cell_size 변화에 따른 call_drop_approx | 〃 |
| call_drop_approx_vs_speed.png | speed 변화에 따른 call_drop_approx | 〃 |
| call_drop_approx_vs_num_nodes.png | num_nodes 변화에 따른 call_drop_approx | 〃 |
| session_reset_count_vs_cell_size.png | cell_size 변화에 따른 session_reset_count | 〃 |
| session_reset_count_vs_speed.png | speed 변화에 따른 session_reset_count | 〃 |
| session_reset_count_vs_num_nodes.png | num_nodes 변화에 따른 session_reset_count | 〃 |
| session_continuity_rate_vs_cell_size.png | cell_size 변화에 따른 session_continuity_rate | 〃 |
| session_continuity_rate_vs_speed.png | speed 변화에 따른 session_continuity_rate | 〃 |
| session_continuity_rate_vs_num_nodes.png | num_nodes 변화에 따른 session_continuity_rate | 〃 |

## 03_special_analysis — AI 예측기 관련 특수 분석 + 토폴로지 시각화

| 파일명 | 무엇을 보여주는지 | 생성 단계 / 스크립트 |
|---|---|---|
| heatmap_signaling_overhead.png | ai 알고리즘의 cell_size×speed 조합별 signaling_overhead 히트맵 (num_nodes=10 고정) | 확장 2단계 (run_experiment.py의 plot_heatmap) |
| prediction_accuracy_vs_cell_size.png | ai 예측정확도가 cell_size에 따라 어떻게 변하는지 | 7-2단계 도입, 확장 1단계에서 에러바 추가 |
| prediction_accuracy_vs_speed.png | ai 예측정확도가 speed에 따라 어떻게 변하는지 | 〃 |
| prediction_accuracy_vs_num_nodes.png | ai 예측정확도가 num_nodes에 따라 어떻게 변하는지 | 〃 |
| mobility_ai_comparison.csv | random_walk/random_waypoint/manhattan_grid 3종 이동모델별 ai(0차 마르코프) 예측정확도·HO횟수·오버헤드 원본 데이터 | 7-1단계 |
| predictor_order_comparison.csv | 0차 vs 1차(방향성 포함) 마르코프 예측기의 이동모델별 예측정확도 비교(5시드 평균) | 확장 3단계 (ai_predictor.py의 FirstOrderMarkovPredictor 추가) |
| topology_visualization.png | 5x5 육각 셀 격자 + Domain 경계선 + 단말기 2개 이동 경로 + HO 발생 지점 다이어그램 | 토폴로지 시각화 요청 (visualize_topology.py) |

## 04_validation — 통계적 검증

| 파일명 | 무엇을 보여주는지 | 생성 단계 / 스크립트 |
|---|---|---|
| statistical_test_results.csv | baseline/improved/ai 쌍체(paired) t-검정 15건 (대표 조합, n=10시드): 지표별 평균/t통계량/p값/유의여부 | 확장 4단계 (statistical_test.py) |
| scalability_benchmark.png | num_nodes 100/500/1000에서 3알고리즘 실행 시간(wall-clock) 벤치마크, 3회 평균 | 확장성 벤치마크 요청 (scalability_benchmark.py) |

## 05_raw_data — 원본/집계 데이터

| 파일명 | 무엇을 보여주는지 | 생성 단계 / 스크립트 |
|---|---|---|
| results.csv | 27개 파라미터 조합(cell_size×speed×num_nodes) × 3알고리즘 = 81행, 지표별 mean/std 집계 (n=10시드) | 확장 1단계 (run_experiment.py aggregate_repeats) |
| results_raw.csv | 위 81개 조합 × 10시드 = 810행, 시드별 개별 실행 원본 결과 (집계 전) | 〃 |

## 참고

- 전체 재생성 순서: `run_experiment.py` → `bar_chart_snapshot.py` / `statistical_test.py` / `scalability_benchmark.py` / `visualize_topology.py` (뒤 4개는 순서 무관, 단 `results/05_raw_data/results.csv`가 먼저 있어야 함)
- 실시간으로 훑어보려면 `streamlit run dashboard.py` — 이 인덱스와 동일한 5개 구획(01~05)을 탭으로 그대로 매핑해뒀다.
- 예상과 다르거나 보고서에 쓸 만한 발견은 프로젝트 루트의 `FINDINGS.md`에 별도 기록되어 있다.
