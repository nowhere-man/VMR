"""
指标对比页面

对比多个报告的质量指标
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from pathlib import Path
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.report_scanner import report_scanner

# 页面配置
st.set_page_config(
    page_title="指标对比 - VQMR",
    page_icon="📉",
    layout="wide",
)

st.title("📉 质量指标对比")

# 获取所有报告
all_reports = report_scanner.scan_all_reports()

if not all_reports or len(all_reports) < 2:
    st.warning("至少需要2个报告才能进行对比")
    st.info("请先执行转码模板生成更多质量分析报告")
    st.stop()

# 报告选择
st.header("选择要对比的报告")

col1, col2 = st.columns(2)

with col1:
    st.subheader("报告 A")
    report_options_a = [
        f"{r['template_name']} - {r['file_name']} ({r['created_at']})"
        for r in all_reports
    ]
    selected_a = st.selectbox("选择报告A", report_options_a, key="report_a")
    report_a_idx = report_options_a.index(selected_a)
    report_a = all_reports[report_a_idx]

with col2:
    st.subheader("报告 B")
    report_options_b = [
        f"{r['template_name']} - {r['file_name']} ({r['created_at']})"
        for r in all_reports
    ]
    # 默认选择第二个报告
    default_b_idx = 1 if len(all_reports) > 1 else 0
    selected_b = st.selectbox("选择报告B", report_options_b, index=default_b_idx, key="report_b")
    report_b_idx = report_options_b.index(selected_b)
    report_b = all_reports[report_b_idx]

if report_a['report_id'] == report_b['report_id']:
    st.error("请选择不同的报告进行对比")
    st.stop()

st.divider()

# 对比分析
st.header("📊 对比分析")

metrics_a = report_a.get('metrics', {})
metrics_b = report_b.get('metrics', {})

# 创建对比表格
st.subheader("指标对比表")

comparison_data = {
    '指标': [],
    '报告 A': [],
    '报告 B': [],
    '差值 (B - A)': [],
    '差值百分比': []
}

# PSNR对比
if 'psnr_avg' in metrics_a and 'psnr_avg' in metrics_b:
    psnr_a = metrics_a['psnr_avg']
    psnr_b = metrics_b['psnr_avg']
    diff = psnr_b - psnr_a
    diff_pct = (diff / psnr_a * 100) if psnr_a > 0 else 0

    comparison_data['指标'].append('PSNR (dB)')
    comparison_data['报告 A'].append(f"{psnr_a:.2f}")
    comparison_data['报告 B'].append(f"{psnr_b:.2f}")
    comparison_data['差值 (B - A)'].append(f"{diff:+.2f}")
    comparison_data['差值百分比'].append(f"{diff_pct:+.2f}%")

# VMAF对比
if 'vmaf_mean' in metrics_a and 'vmaf_mean' in metrics_b:
    vmaf_a = metrics_a['vmaf_mean']
    vmaf_b = metrics_b['vmaf_mean']
    diff = vmaf_b - vmaf_a
    diff_pct = (diff / vmaf_a * 100) if vmaf_a > 0 else 0

    comparison_data['指标'].append('VMAF')
    comparison_data['报告 A'].append(f"{vmaf_a:.2f}")
    comparison_data['报告 B'].append(f"{vmaf_b:.2f}")
    comparison_data['差值 (B - A)'].append(f"{diff:+.2f}")
    comparison_data['差值百分比'].append(f"{diff_pct:+.2f}%")

# SSIM对比
if 'ssim_avg' in metrics_a and 'ssim_avg' in metrics_b:
    ssim_a = metrics_a['ssim_avg']
    ssim_b = metrics_b['ssim_avg']
    diff = ssim_b - ssim_a
    diff_pct = (diff / ssim_a * 100) if ssim_a > 0 else 0

    comparison_data['指标'].append('SSIM')
    comparison_data['报告 A'].append(f"{ssim_a:.4f}")
    comparison_data['报告 B'].append(f"{ssim_b:.4f}")
    comparison_data['差值 (B - A)'].append(f"{diff:+.4f}")
    comparison_data['差值百分比'].append(f"{diff_pct:+.2f}%")

if comparison_data['指标']:
    df = pd.DataFrame(comparison_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.warning("这两个报告没有可对比的指标")

st.divider()

# 可视化对比
st.subheader("可视化对比")

# 并排条形图
fig = go.Figure()

metrics_names = []
values_a = []
values_b = []

if 'psnr_avg' in metrics_a and 'psnr_avg' in metrics_b:
    metrics_names.append('PSNR (dB)')
    values_a.append(metrics_a['psnr_avg'])
    values_b.append(metrics_b['psnr_avg'])

if 'vmaf_mean' in metrics_a and 'vmaf_mean' in metrics_b:
    metrics_names.append('VMAF')
    values_a.append(metrics_a['vmaf_mean'])
    values_b.append(metrics_b['vmaf_mean'])

if 'ssim_avg' in metrics_a and 'ssim_avg' in metrics_b:
    metrics_names.append('SSIM (×100)')
    values_a.append(metrics_a['ssim_avg'] * 100)
    values_b.append(metrics_b['ssim_avg'] * 100)

if metrics_names:
    fig.add_trace(go.Bar(
        name='报告 A',
        x=metrics_names,
        y=values_a,
        marker_color='rgb(31, 119, 180)'
    ))

    fig.add_trace(go.Bar(
        name='报告 B',
        x=metrics_names,
        y=values_b,
        marker_color='rgb(255, 127, 14)'
    ))

    fig.update_layout(
        title='质量指标并排对比',
        barmode='group',
        yaxis_title='指标值',
        xaxis_title='指标类型'
    )

    st.plotly_chart(fig, use_container_width=True)

# YUV分量对比
st.subheader("YUV分量对比")

col1, col2 = st.columns(2)

with col1:
    st.write("**PSNR YUV分量对比**")
    if all(k in metrics_a for k in ['psnr_y', 'psnr_u', 'psnr_v']) and \
       all(k in metrics_b for k in ['psnr_y', 'psnr_u', 'psnr_v']):

        fig_psnr = go.Figure()
        fig_psnr.add_trace(go.Bar(
            name='报告 A',
            x=['Y', 'U', 'V'],
            y=[metrics_a['psnr_y'], metrics_a['psnr_u'], metrics_a['psnr_v']],
            marker_color='rgb(31, 119, 180)'
        ))
        fig_psnr.add_trace(go.Bar(
            name='报告 B',
            x=['Y', 'U', 'V'],
            y=[metrics_b['psnr_y'], metrics_b['psnr_u'], metrics_b['psnr_v']],
            marker_color='rgb(255, 127, 14)'
        ))
        fig_psnr.update_layout(
            barmode='group',
            yaxis_title='PSNR (dB)',
            xaxis_title='分量'
        )
        st.plotly_chart(fig_psnr, use_container_width=True)
    else:
        st.info("部分报告缺少PSNR YUV分量数据")

with col2:
    st.write("**SSIM YUV分量对比**")
    if all(k in metrics_a for k in ['ssim_y', 'ssim_u', 'ssim_v']) and \
       all(k in metrics_b for k in ['ssim_y', 'ssim_u', 'ssim_v']):

        fig_ssim = go.Figure()
        fig_ssim.add_trace(go.Bar(
            name='报告 A',
            x=['Y', 'U', 'V'],
            y=[metrics_a['ssim_y'], metrics_a['ssim_u'], metrics_a['ssim_v']],
            marker_color='rgb(31, 119, 180)'
        ))
        fig_ssim.add_trace(go.Bar(
            name='报告 B',
            x=['Y', 'U', 'V'],
            y=[metrics_b['ssim_y'], metrics_b['ssim_u'], metrics_b['ssim_v']],
            marker_color='rgb(255, 127, 14)'
        ))
        fig_ssim.update_layout(
            barmode='group',
            yaxis_title='SSIM',
            xaxis_title='分量'
        )
        st.plotly_chart(fig_ssim, use_container_width=True)
    else:
        st.info("部分报告缺少SSIM YUV分量数据")

# 模板参数对比
st.divider()
st.subheader("📝 模板参数对比")

col1, col2 = st.columns(2)

with col1:
    st.write("**报告 A - 模板参数**")
    st.write(f"- 模板: {report_a['template_name']}")
    st.write(f"- 编码器: {report_a.get('encoder_type', 'N/A')}")
    st.write(f"- 模式: {report_a.get('mode', 'N/A')}")
    if report_a.get('encoder_params'):
        st.code(report_a['encoder_params'], language='bash')

with col2:
    st.write("**报告 B - 模板参数**")
    st.write(f"- 模板: {report_b['template_name']}")
    st.write(f"- 编码器: {report_b.get('encoder_type', 'N/A')}")
    st.write(f"- 模式: {report_b.get('mode', 'N/A')}")
    if report_b.get('encoder_params'):
        st.code(report_b['encoder_params'], language='bash')

# 页脚
st.markdown("---")
st.caption("VQMR - Video Quality Metrics Report | Powered by Streamlit")
