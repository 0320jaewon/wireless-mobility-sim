import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

RESULTS_DIR = "results"
MAIN_DIR = "01_main_comparison"
SENSITIVITY_DIR = "02_sensitivity"
SPECIAL_DIR = "03_special_analysis"
VALIDATION_DIR = "04_validation"
RAW_DIR = "05_raw_data"

METRIC_NAMES = [
    "signaling_overhead",
    "ping_pong_ratio",
    "call_drop_approx",
    "session_reset_count",
    "session_continuity_rate",
]

SWEEP_PARAMS = ["cell_size", "speed", "num_nodes"]


def load_csv(subdir, filename):
    path = os.path.join(RESULTS_DIR, subdir, filename)
    if not os.path.exists(path):
        return None
    return pd.read_csv(path)


def show_image(subdir, filename, caption=None):
    path = os.path.join(RESULTS_DIR, subdir, filename)
    if os.path.exists(path):
        st.image(path, caption=caption, use_container_width=True)
    else:
        st.warning(f"{path} 파일이 없습니다. 해당 스크립트를 먼저 실행하세요.")


st.set_page_config(page_title="무선망 LM/HO 시뮬레이터 대시보드", layout="wide")

st.title("무선통신망 LM/HO 및 세션 커넥티비티 시뮬레이터")
st.caption("Baseline / 개선된 전통기법 / AI(마르코프 체인) 3종 비교 대시보드")

tab_main, tab_sensitivity, tab_special, tab_validation, tab_raw = st.tabs([
    "01 핵심 비교",
    "02 민감도 분석",
    "03 특수 분석",
    "04 검증",
    "05 원본 데이터",
])

with tab_main:
    st.subheader("3종 알고리즘 핵심 비교 (cell_size=1.0, speed=0.3, num_nodes=30, mean ± std)")
    cols = st.columns(2)
    for i, metric in enumerate(METRIC_NAMES):
        with cols[i % 2]:
            show_image(MAIN_DIR, f"bar_{metric}.png", caption=metric)

with tab_sensitivity:
    st.subheader("파라미터 스윕: 평균 ± 표준편차 (n=10 시드)")
    col1, col2 = st.columns(2)
    with col1:
        metric = st.selectbox("지표 선택", METRIC_NAMES)
    with col2:
        sweep_param = st.selectbox("스윕 파라미터 선택", SWEEP_PARAMS)

    show_image(SENSITIVITY_DIR, f"{metric}_vs_{sweep_param}.png")

    results_df = load_csv(RAW_DIR, "results.csv")
    if results_df is not None:
        st.markdown("**집계 데이터 미리보기**")
        mean_col = f"{metric}_mean"
        std_col = f"{metric}_std"
        cols_to_show = ["algorithm"] + SWEEP_PARAMS + [c for c in [mean_col, std_col] if c in results_df.columns]
        st.dataframe(results_df[cols_to_show].sort_values(["algorithm"] + SWEEP_PARAMS), use_container_width=True)

with tab_special:
    st.subheader("cell_size × speed 히트맵 (ai 알고리즘, signaling_overhead)")
    show_image(SPECIAL_DIR, "heatmap_signaling_overhead.png")

    st.subheader("5x5 토폴로지 + Domain 경계 + 이동 경로 + HO 지점")
    show_image(SPECIAL_DIR, "topology_visualization.png")

    st.subheader("이동모델별 AI 예측 정확도 (0차 마르코프)")
    mobility_df = load_csv(SPECIAL_DIR, "mobility_ai_comparison.csv")
    if mobility_df is not None:
        st.dataframe(mobility_df, use_container_width=True)
        if "mobility_model" in mobility_df.columns and "prediction_accuracy" in mobility_df.columns:
            fig, ax = plt.subplots()
            ax.bar(mobility_df["mobility_model"], mobility_df["prediction_accuracy"])
            ax.set_xlabel("mobility_model")
            ax.set_ylabel("prediction_accuracy")
            ax.set_title("이동모델별 AI 예측 정확도")
            st.pyplot(fig)
    else:
        st.warning(f"{RESULTS_DIR}/{SPECIAL_DIR}/mobility_ai_comparison.csv가 없습니다.")

    st.subheader("0차 vs 1차(방향성 포함) 마르코프 예측기 비교")
    predictor_df = load_csv(SPECIAL_DIR, "predictor_order_comparison.csv")
    if predictor_df is not None:
        st.dataframe(predictor_df, use_container_width=True)

        pivot = predictor_df.pivot(
            index="mobility_model", columns="predictor_order", values="prediction_accuracy_mean"
        )
        fig, ax = plt.subplots()
        pivot.plot(kind="bar", ax=ax)
        ax.set_ylabel("prediction_accuracy_mean")
        ax.set_title("이동모델별 0차 vs 1차 마르코프 예측 정확도")
        ax.legend(title="predictor_order")
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.warning(f"{RESULTS_DIR}/{SPECIAL_DIR}/predictor_order_comparison.csv가 없습니다.")

with tab_validation:
    st.subheader("쌍체 t-검정 (cell_size=1.0, speed=0.3, num_nodes=30, n=10)")
    stats_df = load_csv(VALIDATION_DIR, "statistical_test_results.csv")
    if stats_df is not None:
        st.dataframe(stats_df, use_container_width=True)
    else:
        st.warning(f"{RESULTS_DIR}/{VALIDATION_DIR}/statistical_test_results.csv가 없습니다.")

    st.subheader("확장성 벤치마크 (num_nodes 100/500/1000)")
    show_image(VALIDATION_DIR, "scalability_benchmark.png")

with tab_raw:
    st.subheader("집계 결과 (results.csv)")
    results_df = load_csv(RAW_DIR, "results.csv")
    if results_df is not None:
        st.dataframe(results_df, use_container_width=True)
        st.download_button(
            "results.csv 다운로드",
            results_df.to_csv(index=False).encode("utf-8"),
            file_name="results.csv",
            mime="text/csv",
        )

    st.subheader("원본 반복실험 결과 (results_raw.csv)")
    raw_df = load_csv(RAW_DIR, "results_raw.csv")
    if raw_df is not None:
        st.dataframe(raw_df, use_container_width=True)
