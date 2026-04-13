import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Hệ Thống Phân Tích Rủi Ro & Gian Lận Tài Chính",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS CHO ĐẸP HƠN ---
st.markdown("""
    <style>
    .main {background-color: #f8f9fa;}
    h1, h2, h3 {color: #1f2937;}
    .stAlert {border-radius: 8px;}
    .stTabs [data-baseweb="tab-list"] {gap: 8px;}
    .stTabs [data-baseweb="tab"] {padding-top: 10px; padding-bottom: 10px;}
    </style>
""", unsafe_allow_html=True)

# --- 2. LOAD DATA ---
@st.cache_data
def load_data():
    file_path = 'final_merged_dataset.csv'
    
    if not os.path.exists(file_path):
        st.error(f"❌ Không tìm thấy file dữ liệu: {file_path}. Vui lòng kiểm tra lại!")
        return pd.DataFrame()
        
    df = pd.read_csv(file_path)
    
    if 'Year' in df.columns:
        df['Year'] = df['Year'].astype(int)
    
    # Fill NA cho các cột tài chính cơ bản
    cols_to_fill = ['Rev', 'COGS', 'Gross_Profit', 'Net_Profit', 'Leverage', 'fraud_score', 'Total_Assets', 'Total_Liabilities', 'Operating_Cash_Flow']
    for col in cols_to_fill:
        if col in df.columns:
            df[col] = df[col].fillna(0)
            
    return df

df = load_data()

if not df.empty:
    # --- 3. SIDEBAR CONTROLS ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135673.png", width=80)
        st.title("🎛️ Bảng Điều Khiển")
        st.markdown("---")
        
        st.header("1. Lọc Dữ Liệu Chung")
        min_year, max_year = int(df['Year'].min()), int(df['Year'].max())
        selected_years = st.slider("Giai Đoạn (Năm):", min_year, max_year, (min_year, max_year))
        
        risk_levels = sorted(df['risk_level'].dropna().unique().tolist())
        selected_risks = st.multiselect("Mức Độ Rủi Ro:", options=risk_levels, default=risk_levels)

        st.markdown("---")
        st.header("⚠️ Cài Đặt Cảnh Báo")
        fraud_threshold = st.slider(
            "Ngưỡng Fraud Score Nguy Hiểm:", 
            min_value=0.0, max_value=5.0, value=1.5, step=0.1,
            help="Các công ty có điểm cao hơn ngưỡng này sẽ bị đánh dấu đỏ."
        )

    # Lọc DataFrame chung
    mask = (df['Year'] >= selected_years[0]) & (df['Year'] <= selected_years[1]) & (df['risk_level'].isin(selected_risks))
    df_filtered = df.loc[mask]
    all_symbols = sorted(df_filtered['Symbol'].dropna().unique().tolist())

    # --- 4. MAIN DASHBOARD ---
    st.title("🛡️ Dashboard Phân Tích Rủi Ro & Gian Lận BCTC")
    st.markdown(f"*Dữ liệu phân tích từ năm **{selected_years[0]}** đến **{selected_years[1]}***")

    # --- ALERT BOX ---
    high_risk_df = df_filtered[df_filtered['fraud_score'] >= fraud_threshold]
    if not high_risk_df.empty:
        st.error(f"🚨 **PHÁT HIỆN RỦI RO:** Có **{high_risk_df['Symbol'].nunique()}** công ty vượt ngưỡng gian lận ({fraud_threshold}).")
    else:
        st.success(f"✅ **AN TOÀN:** Hiện tại không có công ty nào vượt ngưỡng rủi ro đã chọn.")

    # --- TẠO TABS ---
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Tổng Quan Ngành", 
        "🚩 Nhận Diện Cảnh Báo", 
        "🏢 Tra Cứu Doanh Nghiệp",
        "⚖️ So Sánh Đối Thủ",
        "🧠 Phân Tích Chuyên Sâu",
        "🌌 Bức Tranh Đa Chiều" # <- TAB MỚI Ở ĐÂY
    ])

    # ====================================================
    # TAB 1: TỔNG QUAN NGÀNH
    # ====================================================
    with tab1:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Tổng Số Doanh Nghiệp", f"{df_filtered['Symbol'].nunique()} cty")
        c2.metric("Điểm Gian Lận TB", f"{df_filtered['fraud_score'].mean():.2f}")
        c3.metric("Số Lần Bị Đánh Dấu", f"{df_filtered['Target_Fraud'].sum()} vụ")
        avg_rev = df_filtered['Rev'].mean() / 1e9 if 'Rev' in df_filtered.columns else 0
        c4.metric("Doanh Thu TB", f"{avg_rev:,.0f} Tỷ VNĐ")
        st.markdown("<br>", unsafe_allow_html=True)

        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("📈 Xu Hướng Điểm Rủi Ro Theo Thời Gian")
            yearly_stats = df_filtered.groupby('Year')['fraud_score'].mean().reset_index()
            fig_trend = px.line(yearly_stats, x='Year', y='fraud_score', markers=True, 
                                line_shape='spline', color_discrete_sequence=['#ef4444'])
            fig_trend.add_hline(y=fraud_threshold, line_dash="dash", line_color="orange")
            fig_trend.update_layout(xaxis_title="Năm", yaxis_title="Điểm Gian Lận TB", height=350, margin=dict(l=0, r=0, t=30, b=0))
            fig_trend.update_xaxes(dtick=1)
            st.plotly_chart(fig_trend, use_container_width=True)

        with col2:
            st.subheader("Trọng Số Mức Độ Rủi Ro")
            risk_counts = df_filtered['risk_level'].value_counts().reset_index()
            risk_counts.columns = ['risk_level', 'count']
            color_map = {'HighRisk': '#ef4444', 'MediumRisk': '#f59e0b', 'LowRisk': '#10b981', 'Safe': '#3b82f6'}
            fig_pie = px.pie(risk_counts, values='count', names='risk_level', hole=0.4, 
                             color='risk_level', color_discrete_map=color_map)
            fig_pie.update_layout(height=350, margin=dict(l=0, r=0, t=30, b=0), showlegend=True)
            st.plotly_chart(fig_pie, use_container_width=True)

        st.subheader("🔥 Top 10 Doanh Nghiệp Rủi Ro Nhất")
        top_10 = df_filtered.sort_values(by='fraud_score', ascending=False).drop_duplicates(subset=['Symbol']).head(10)
        fig_bar = px.bar(top_10, x='Symbol', y='fraud_score', color='fraud_score', color_continuous_scale='Reds', text_auto='.2f')
        fig_bar.update_layout(height=350, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_bar, use_container_width=True)

    # ====================================================
    # TAB 2: DẤU HIỆU CẢNH BÁO (RED FLAGS)
    # ====================================================
    with tab2:
        col3, col4 = st.columns(2)
        with col3:
            st.subheader("🚩 Mức Độ Phổ Biến Của Các Loại Gian Lận")
            flag_cols = [col for col in df.columns if col.startswith('f_') and col not in ['f_score']]
            if flag_cols:
                flag_sums = df_filtered[flag_cols].sum().sort_values(ascending=True).reset_index()
                flag_sums.columns = ['Loại Cảnh Báo', 'Số Lần Xuất Hiện']
                fig_flags = px.bar(flag_sums, x='Số Lần Xuất Hiện', y='Loại Cảnh Báo', orientation='h', color='Số Lần Xuất Hiện', color_continuous_scale='Sunsetdark')
                fig_flags.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig_flags, use_container_width=True)

        with col4:
            st.subheader("⚖️ Chỉ Số Đòn Bẩy (Leverage) vs Rủi Ro")
            fig_box = px.box(df_filtered, x='Target_Fraud', y='Leverage', color='Target_Fraud', color_discrete_sequence=['#10b981', '#ef4444'])
            fig_box.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig_box, use_container_width=True)

    # ====================================================
    # TAB 3: TRA CỨU DOANH NGHIỆP CỤ THỂ
    # ====================================================
    with tab3:
        selected_symbol = st.selectbox("🔍 Nhập hoặc Chọn Mã Công Ty (Symbol):", all_symbols, key='tab3_search')
        df_company = df[df['Symbol'] == selected_symbol].sort_values(by='Year')
        if not df_company.empty:
            st.dataframe(df_company.style.format(precision=2), use_container_width=True)

    # ====================================================
    # TAB 4: SO SÁNH ĐỐI THỦ
    # ====================================================
    with tab4:
        selected_compare = st.multiselect("🤝 Chọn các mã công ty để so sánh:", all_symbols, default=all_symbols[:2] if len(all_symbols) >= 2 else all_symbols)
        if selected_compare:
            df_comp = df_filtered[df_filtered['Symbol'].isin(selected_compare)].sort_values(by='Year')
            fig_comp_score = px.line(df_comp, x='Year', y='fraud_score', color='Symbol', markers=True)
            st.plotly_chart(fig_comp_score, use_container_width=True)

    # ====================================================
    # TAB 5: PHÂN TÍCH CHUYÊN Sâu
    # ====================================================
    with tab5:
        corr_cols = ['fraud_score', 'Target_Fraud', 'Rev', 'Net_Profit', 'Total_Assets', 'Total_Liabilities', 'Leverage', 'Operating_Cash_Flow']
        corr_cols_exist = [c for c in corr_cols if c in df_filtered.columns]
        if len(corr_cols_exist) > 1:
            corr_matrix = df_filtered[corr_cols_exist].corr().round(2)
            fig_corr = px.imshow(corr_matrix, text_auto=True, aspect="auto", color_continuous_scale='RdBu_r', zmin=-1, zmax=1)
            st.plotly_chart(fig_corr, use_container_width=True)

    # ====================================================
    # TAB 6: 🌌 BỨC TRANH ĐA CHIỀU (MEGA DASHBOARD)
    # ====================================================
    with tab6:
        st.markdown("### 🔭 Lưới Phân Tích Đa Dữ Liệu")
        st.markdown("Cung cấp một loạt các biểu đồ xếp san sát nhau để bạn có cái nhìn bao quát về cả doanh thu, dòng tiền, nợ và tỷ trọng rủi ro.")

        # --- HÀNG 1: Dịch chuyển rủi ro & Phân phối điểm ---
        r1_c1, r1_c2 = st.columns(2)
        with r1_c1:
            # Stacked Bar: Số lượng doanh nghiệp theo mức rủi ro qua từng năm
            risk_trend = df_filtered.groupby(['Year', 'risk_level']).size().reset_index(name='Count')
            color_map = {'HighRisk': '#ef4444', 'MediumRisk': '#f59e0b', 'LowRisk': '#10b981', 'Safe': '#3b82f6'}
            fig_stacked = px.bar(risk_trend, x='Year', y='Count', color='risk_level', 
                                 title='1. Dịch Chuyển Rủi Ro Qua Các Năm', barmode='stack', color_discrete_map=color_map)
            fig_stacked.update_xaxes(dtick=1)
            fig_stacked.update_layout(height=380, margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig_stacked, use_container_width=True)

        with r1_c2:
            # Histogram: Phổ điểm gian lận
            fig_hist = px.histogram(df_filtered, x='fraud_score', color='risk_level', nbins=40, 
                                    title='2. Phân Phối Điểm Gian Lận Toàn Ngành', marginal='box', color_discrete_map=color_map)
            fig_hist.update_layout(height=380, margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig_hist, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # --- HÀNG 2: Treemap Doanh Thu & Scatter Dòng tiền vs Lợi Nhuận ---
        r2_c1, r2_c2 = st.columns(2)
        with r2_c1:
            # Treemap: Bản đồ nhiệt Doanh thu và Điểm rủi ro (Top 50 cty)
            top_rev = df_filtered.groupby('Symbol')[['Rev', 'fraud_score']].mean().reset_index()
            top_rev = top_rev.sort_values('Rev', ascending=False).head(40)
            top_rev['Rev_Plot'] = top_rev['Rev'].apply(lambda x: x if x > 0 else 0) # Tránh số âm trong treemap
            fig_tree = px.treemap(top_rev, path=[px.Constant("Toàn Ngành"), 'Symbol'], values='Rev_Plot', color='fraud_score', 
                                  color_continuous_scale='RdYlGn_r', title='3. Top 40 Cty Có Doanh Thu Lớn Nhất (Màu: Điểm Rủi Ro)')
            fig_tree.update_layout(height=400, margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig_tree, use_container_width=True)

        with r2_c2:
            # Scatter: Chất lượng lợi nhuận (Net Profit vs Operating Cash Flow)
            fig_scatter_ocf = px.scatter(df_filtered, x='Net_Profit', y='Operating_Cash_Flow', color='risk_level', 
                                         hover_name='Symbol', size='Total_Assets', color_discrete_map=color_map,
                                         title='4. Chất Lượng Lợi Nhuận: Lợi Nhuận Thuần vs Dòng Tiền HĐKD')
            fig_scatter_ocf.add_shape(type="line", x0=df_filtered['Net_Profit'].min(), y0=df_filtered['Net_Profit'].min(), 
                                      x1=df_filtered['Net_Profit'].max(), y1=df_filtered['Net_Profit'].max(), 
                                      line=dict(color="Gray", dash="dash")) # Đường y=x để tham chiếu
            fig_scatter_ocf.update_layout(height=400, margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig_scatter_ocf, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # --- HÀNG 3: Doanh thu vs Giá vốn & Cấu trúc Tỷ lệ Kế toán ---
        r3_c1, r3_c2 = st.columns(2)
        with r3_c1:
            # So sánh Doanh thu và Giá vốn hàng bán (COGS) tổng hợp toàn ngành
            if 'COGS' in df_filtered.columns:
                rev_cogs = df_filtered.groupby('Year')[['Rev', 'COGS']].sum().reset_index()
                fig_rev_cogs = go.Figure()
                fig_rev_cogs.add_trace(go.Bar(x=rev_cogs['Year'], y=rev_cogs['Rev'], name='Tổng Doanh Thu', marker_color='#3b82f6'))
                fig_rev_cogs.add_trace(go.Bar(x=rev_cogs['Year'], y=rev_cogs['COGS'], name='Tổng Giá Vốn (COGS)', marker_color='#ef4444'))
                fig_rev_cogs.update_layout(title='5. Doanh Thu vs Giá Vốn (Toàn Ngành)', barmode='group', xaxis=dict(dtick=1), height=380, margin=dict(l=0, r=0, t=40, b=0))
                st.plotly_chart(fig_rev_cogs, use_container_width=True)
            else:
                st.info("Không có cột COGS (Giá vốn) để vẽ biểu đồ này.")

        with r3_c2:
            # Boxplot: Đánh giá tỷ lệ dồn tích (Accrual Ratio) - Một chỉ báo quan trọng của thao túng lợi nhuận
            if 'accrual_ratio' in df_filtered.columns:
                fig_accrual = px.box(df_filtered, x='risk_level', y='accrual_ratio', color='risk_level', 
                                     color_discrete_map=color_map, title='6. Accrual Ratio (Tỷ lệ dồn tích) Theo Nhóm Rủi Ro')
                fig_accrual.update_layout(height=380, margin=dict(l=0, r=0, t=40, b=0))
                st.plotly_chart(fig_accrual, use_container_width=True)
            else:
                st.info("Không có cột accrual_ratio để vẽ biểu đồ này.")
