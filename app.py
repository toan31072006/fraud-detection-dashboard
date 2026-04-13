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
    
    # Xử lý các cột dữ liệu
    if 'Year' in df.columns:
        df['Year'] = df['Year'].astype(int)
    
    # Fill NA cho các cột tài chính cơ bản để tránh lỗi biểu đồ
    cols_to_fill = ['Rev', 'Net_Profit', 'Leverage', 'fraud_score']
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
        # Lọc theo Năm
        min_year, max_year = int(df['Year'].min()), int(df['Year'].max())
        selected_years = st.slider("Giai Đoạn (Năm):", min_year, max_year, (min_year, max_year))
        
        # Lọc theo Mức Độ Rủi Ro
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

    # --- 4. MAIN DASHBOARD ---
    st.title("🛡️ Dashboard Phân Tích Rủi Ro & Gian Lận BCTC")
    st.markdown(f"*Dữ liệu phân tích từ năm **{selected_years[0]}** đến **{selected_years[1]}***")

    # --- ALERT BOX ---
    high_risk_df = df_filtered[df_filtered['fraud_score'] >= fraud_threshold]
    if not high_risk_df.empty:
        st.error(f"🚨 **PHÁT HIỆN RỦI RO:** Có **{high_risk_df['Symbol'].nunique()}** công ty vượt ngưỡng gian lận ({fraud_threshold}).")
    else:
        st.success(f"✅ **AN TOÀN:** Hiện tại không có công ty nào vượt ngưỡng rủi ro đã chọn.")

    # --- TẠO TABS ĐỂ GIAO DIỆN GỌN GÀNG HƠN ---
    tab1, tab2, tab3 = st.tabs(["📊 Tổng Quan Ngành", "🚩 Nhận Diện Cảnh Báo", "🏢 Tra Cứu Doanh Nghiệp"])

    # ====================================================
    # TAB 1: TỔNG QUAN NGÀNH
    # ====================================================
    with tab1:
        # KPI METRICS
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Tổng Số Doanh Nghiệp", f"{df_filtered['Symbol'].nunique()} cty")
        c2.metric("Điểm Gian Lận TB", f"{df_filtered['fraud_score'].mean():.2f}")
        c3.metric("Số Lần Bị Đánh Dấu (Target=1)", f"{df_filtered['Target_Fraud'].sum()} vụ")
        
        avg_rev = df_filtered['Rev'].mean() / 1e9 if 'Rev' in df_filtered.columns else 0
        c4.metric("Doanh Thu TB (Tỷ VNĐ)", f"{avg_rev:,.0f}")

        st.markdown("<br>", unsafe_allow_html=True)

        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("📈 Xu Hướng Điểm Rủi Ro Theo Thời Gian")
            yearly_stats = df_filtered.groupby('Year')['fraud_score'].mean().reset_index()
            fig_trend = px.line(yearly_stats, x='Year', y='fraud_score', markers=True, 
                                line_shape='spline', color_discrete_sequence=['#ef4444'])
            fig_trend.add_hline(y=fraud_threshold, line_dash="dash", line_color="orange", annotation_text=f"Ngưỡng Cảnh Báo ({fraud_threshold})")
            fig_trend.update_layout(xaxis_title="Năm", yaxis_title="Điểm Gian Lận TB", height=350, margin=dict(l=0, r=0, t=30, b=0))
            # Ép trục X hiển thị số nguyên
            fig_trend.update_xaxes(dtick=1)
            st.plotly_chart(fig_trend, use_container_width=True)

        with col2:
            st.subheader("Trọng Số Mức Độ Rủi Ro")
            risk_counts = df_filtered['risk_level'].value_counts().reset_index()
            risk_counts.columns = ['risk_level', 'count']
            
            # Đổi màu tùy theo mức độ rủi ro (Giả định Low/Medium/High)
            color_map = {'HighRisk': '#ef4444', 'MediumRisk': '#f59e0b', 'LowRisk': '#10b981', 'Safe': '#3b82f6'}
            fig_pie = px.pie(risk_counts, values='count', names='risk_level', hole=0.4, 
                             color='risk_level', color_discrete_map=color_map)
            fig_pie.update_layout(height=350, margin=dict(l=0, r=0, t=30, b=0), showlegend=True)
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)

        st.subheader("🔥 Top 10 Doanh Nghiệp Rủi Ro Nhất")
        top_10 = df_filtered.sort_values(by='fraud_score', ascending=False).drop_duplicates(subset=['Symbol']).head(10)
        fig_bar = px.bar(top_10, x='Symbol', y='fraud_score', color='fraud_score', 
                         color_continuous_scale='Reds', text_auto='.2f')
        fig_bar.update_layout(xaxis_title="Mã Công Ty", yaxis_title="Điểm Gian Lận", height=350, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_bar, use_container_width=True)

    # ====================================================
    # TAB 2: DẤU HIỆU CẢNH BÁO (RED FLAGS)
    # ====================================================
    with tab2:
        st.markdown("Phân tích chuyên sâu về các cờ báo hiệu (Red Flags) và mối tương quan với sức khỏe tài chính.")
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.subheader("🚩 Mức Độ Phổ Biến Của Các Loại Gian Lận")
            # Lấy các cột bắt đầu bằng f_ (ngoại trừ f_score nếu có)
            flag_cols = [col for col in df.columns if col.startswith('f_') and col not in ['f_score']]
            if flag_cols:
                flag_sums = df_filtered[flag_cols].sum().sort_values(ascending=True).reset_index()
                flag_sums.columns = ['Loại Cảnh Báo', 'Số Lần Xuất Hiện']
                
                fig_flags = px.bar(flag_sums, x='Số Lần Xuất Hiện', y='Loại Cảnh Báo', orientation='h',
                                   color='Số Lần Xuất Hiện', color_continuous_scale='Sunsetdark')
                fig_flags.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig_flags, use_container_width=True)
            else:
                st.info("Không tìm thấy các cột 'f_' trong bộ dữ liệu.")

        with col4:
            st.subheader("⚖️ Chỉ Số Đòn Bẩy (Leverage) vs Rủi Ro")
            fig_box = px.box(df_filtered, x='Target_Fraud', y='Leverage', color='Target_Fraud', 
                             color_discrete_sequence=['#10b981', '#ef4444'])
            fig_box.update_layout(xaxis_title="Có Gian Lận (0 = Không, 1 = Có)", yaxis_title="Đòn Bẩy Tài Chính", height=400, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig_box, use_container_width=True)

        st.subheader("💰 Tương Quan Doanh Thu & Lợi Nhuận (Theo Fraud Score)")
        fig_scatter = px.scatter(df_filtered, x='Rev', y='Net_Profit', color='fraud_score', 
                                 size='Total_Assets' if 'Total_Assets' in df_filtered.columns else None,
                                 hover_name='Symbol', hover_data=['Year', 'risk_level'],
                                 color_continuous_scale='RdYlBu_r')
        fig_scatter.update_layout(xaxis_title="Doanh Thu (VND)", yaxis_title="Lợi Nhuận Thuần (VND)", height=450)
        st.plotly_chart(fig_scatter, use_container_width=True)


    # ====================================================
    # TAB 3: TRA CỨU DOANH NGHIỆP CỤ THỂ
    # ====================================================
    with tab3:
        st.markdown("Chọn một mã công ty để xem chi tiết sức khỏe tài chính và lịch sử điểm gian lận qua các năm.")
        
        all_symbols = sorted(df['Symbol'].dropna().unique().tolist())
        selected_symbol = st.selectbox("🔍 Nhập hoặc Chọn Mã Công Ty (Symbol):", all_symbols)
        
        df_company = df[df['Symbol'] == selected_symbol].sort_values(by='Year')
        
        if not df_company.empty:
            c1, c2, c3 = st.columns(3)
            latest_year = df_company['Year'].max()
            latest_data = df_company[df_company['Year'] == latest_year].iloc[0]
            
            c1.info(f"**Năm cập nhật gần nhất:** {latest_year}")
            c2.warning(f"**Mức độ rủi ro hiện tại:** {latest_data['risk_level']}")
            c3.error(f"**Điểm gian lận hiện tại:** {latest_data['fraud_score']:.2f}")
            
            st.markdown("---")
            
            # Biểu đồ kết hợp: Cột (Lợi nhuận) và Đường (Điểm rủi ro)
            fig_combo = go.Figure()
            
            # Thêm cột Lợi Nhuận
            fig_combo.add_trace(go.Bar(
                x=df_company['Year'], y=df_company['Net_Profit'], 
                name='Lợi Nhuận Thuần', marker_color='#3b82f6', yaxis='y1'
            ))
            
            # Thêm đường Fraud Score
            fig_combo.add_trace(go.Scatter(
                x=df_company['Year'], y=df_company['fraud_score'], 
                name='Fraud Score', mode='lines+markers', marker=dict(color='#ef4444', size=10), yaxis='y2'
            ))
            
            # Setup 2 trục Y
            fig_combo.update_layout(
                title=f"Sức Khỏe Tài Chính Của {selected_symbol}",
                xaxis=dict(title="Năm", dtick=1),
                yaxis=dict(title="Lợi Nhuận (VND)", side='left', showgrid=False),
                yaxis2=dict(title="Điểm Gian Lận", side='right', overlaying='y', range=[0, max(5, df_company['fraud_score'].max() + 1)]),
                height=400,
                legend=dict(x=0.01, y=0.99),
                margin=dict(l=0, r=0, t=40, b=0)
            )
            st.plotly_chart(fig_combo, use_container_width=True)
            
            # Bảng dữ liệu thô của công ty
            st.subheader(f"📄 Bảng Số Liệu Chi Tiết Của {selected_symbol}")
            cols_to_show = ['Year', 'Rev', 'Gross_Profit', 'Net_Profit', 'Leverage', 'fraud_score', 'risk_level']
            # Lọc chỉ những cột tồn tại trong data
            cols_to_show = [c for c in cols_to_show if c in df_company.columns]
            st.dataframe(df_company[cols_to_show].style.format({"Rev": "{:,.0f}", "Gross_Profit": "{:,.0f}", "Net_Profit": "{:,.0f}", "fraud_score": "{:.2f}"}), use_container_width=True, hide_index=True)
