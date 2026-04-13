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

# --- CUSTOM CSS ---
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
        st.error(f"❌ Không tìm thấy file dữ liệu: {file_path}")
        return pd.DataFrame()
        
    df = pd.read_csv(file_path)
    if 'Year' in df.columns:
        df['Year'] = df['Year'].astype(int)
    
    # Lấp đầy NaN cho toàn bộ các cột số
    num_cols = df.select_dtypes(include=['float64', 'int64']).columns
    df[num_cols] = df[num_cols].fillna(0)
            
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
        fraud_threshold = st.slider("Ngưỡng Fraud Score:", 0.0, 5.0, 1.5, 0.1)

    # Filter Data
    mask = (df['Year'] >= selected_years[0]) & (df['Year'] <= selected_years[1]) & (df['risk_level'].isin(selected_risks))
    df_filtered = df.loc[mask]
    all_symbols = sorted(df_filtered['Symbol'].dropna().unique().tolist())
    
    # Bảng màu chung chuẩn hóa
    COLOR_MAP = {'HighRisk': '#ef4444', 'MediumRisk': '#f59e0b', 'LowRisk': '#10b981', 'Safe': '#3b82f6'}

    # --- 4. MAIN DASHBOARD ---
    st.title("🛡️ Dashboard Phân Tích Rủi Ro & Gian Lận BCTC")
    st.markdown(f"*Dữ liệu phân tích từ năm **{selected_years[0]}** đến **{selected_years[1]}***")

    # --- TẠO TABS ---
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Tổng Quan Ngành", 
        "🚩 Nhận Diện Cảnh Báo", 
        "🏢 Tra Cứu Doanh Nghiệp",
        "⚖️ So Sánh Đối Thủ",
        "🧠 Phân Tích Chuyên Sâu",
        "🌌 Bức Tranh Đa Chiều"
    ])

    # ====================================================
    # TAB 1: TỔNG QUAN NGÀNH (5 BIỂU ĐỒ)
    # ====================================================
    with tab1:
        st.markdown("### 📊 Tổng Quan Tình Hình Toàn Ngành")
        
        r1_c1, r1_c2 = st.columns(2)
        with r1_c1:
            # 1.1 Line Chart: Xu hướng điểm rủi ro
            yearly_stats = df_filtered.groupby('Year')['fraud_score'].mean().reset_index()
            fig1 = px.line(yearly_stats, x='Year', y='fraud_score', markers=True, title="1. Xu Hướng Điểm Gian Lận TB Toàn Ngành", color_discrete_sequence=['#ef4444'])
            fig1.add_hline(y=fraud_threshold, line_dash="dash", line_color="orange")
            fig1.update_xaxes(dtick=1)
            st.plotly_chart(fig1, use_container_width=True)
            
        with r1_c2:
            # 1.2 Donut Chart: Tỷ trọng mức độ rủi ro
            risk_counts = df_filtered['risk_level'].value_counts().reset_index()
            fig2 = px.pie(risk_counts, values='count', names='risk_level', hole=0.4, title="2. Tỷ Trọng Các Nhóm Rủi Ro", color='risk_level', color_discrete_map=COLOR_MAP)
            st.plotly_chart(fig2, use_container_width=True)

        r2_c1, r2_c2 = st.columns(2)
        with r2_c1:
            # 1.3 Bar Chart: Doanh thu & Lợi nhuận ngành
            rev_prof = df_filtered.groupby('Year')[['Rev', 'Net_Profit']].sum().reset_index()
            fig3 = go.Figure(data=[
                go.Bar(name='Tổng Doanh Thu', x=rev_prof['Year'], y=rev_prof['Rev'], marker_color='#3b82f6'),
                go.Bar(name='Tổng Lợi Nhuận', x=rev_prof['Year'], y=rev_prof['Net_Profit'], marker_color='#10b981')
            ])
            fig3.update_layout(title="3. Tổng Doanh Thu & Lợi Nhuận Toàn Ngành", barmode='group', xaxis=dict(dtick=1))
            st.plotly_chart(fig3, use_container_width=True)
            
        with r2_c2:
            # 1.4 Bar Chart: Top 10 Cty rủi ro
            top_10 = df_filtered.sort_values(by='fraud_score', ascending=False).drop_duplicates(subset=['Symbol']).head(10)
            fig4 = px.bar(top_10, x='Symbol', y='fraud_score', color='fraud_score', color_continuous_scale='Reds', title="4. Top 10 Cty Có Điểm Rủi Ro Cao Nhất")
            st.plotly_chart(fig4, use_container_width=True)

        # 1.5 Histogram phân phối điểm toàn ngành
        fig5 = px.histogram(df_filtered, x='fraud_score', color='risk_level', nbins=50, title="5. Phân Phối Tần Suất Điểm Gian Lận", color_discrete_map=COLOR_MAP)
        st.plotly_chart(fig5, use_container_width=True)

    # ====================================================
    # TAB 2: NHẬN DIỆN CẢNH BÁO / RED FLAGS (4 BIỂU ĐỒ)
    # ====================================================
    with tab2:
        st.markdown("### 🚩 Phân Tích Cờ Báo Hiệu (Red Flags)")
        
        r3_c1, r3_c2 = st.columns(2)
        with r3_c1:
            # 2.1 Horizontal Bar: Tần suất xuất hiện các Red Flags
            flag_cols = [c for c in df.columns if c.startswith('f_') and c not in ['f_score']]
            flag_sums = df_filtered[flag_cols].sum().sort_values(ascending=True).reset_index()
            flag_sums.columns = ['Loại Cờ Cảnh Báo', 'Số Lần']
            fig6 = px.bar(flag_sums, x='Số Lần', y='Loại Cờ Cảnh Báo', orientation='h', title="1. Các Loại Gian Lận Phổ Biến Nhất", color='Số Lần', color_continuous_scale='Sunsetdark')
            st.plotly_chart(fig6, use_container_width=True)

        with r3_c2:
            # 2.2 Scatter: Tăng trưởng doanh thu vs Hàng tồn kho (Dấu hiệu nhồi nhét doanh thu)
            fig7 = px.scatter(df_filtered, x='Delta_Rev', y='Delta_Inv', color='risk_level', size='fraud_score', title="2. Tăng Trưởng Doanh Thu vs Tồn Kho", hover_name='Symbol', color_discrete_map=COLOR_MAP)
            fig7.add_hline(y=0, line_dash="dot", line_color="gray")
            fig7.add_vline(x=0, line_dash="dot", line_color="gray")
            st.plotly_chart(fig7, use_container_width=True)

        r4_c1, r4_c2 = st.columns(2)
        with r4_c1:
            # 2.3 Boxplot: Đòn bẩy tài chính theo rủi ro
            fig8 = px.box(df_filtered, x='risk_level', y='Leverage', color='risk_level', title="3. Mức Độ Đòn Bẩy (Leverage) Theo Rủi Ro", color_discrete_map=COLOR_MAP)
            st.plotly_chart(fig8, use_container_width=True)

        with r4_c2:
            # 2.4 Boxplot: Tỷ lệ dồn tích (Accrual Ratio - Nhận diện thủ thuật kế toán)
            if 'accrual_ratio' in df_filtered.columns:
                fig9 = px.box(df_filtered, x='risk_level', y='accrual_ratio', color='risk_level', title="4. Tỷ Lệ Dồn Tích (Accrual Ratio) Theo Rủi Ro", color_discrete_map=COLOR_MAP)
                st.plotly_chart(fig9, use_container_width=True)

    # ====================================================
    # TAB 3: TRA CỨU DOANH NGHIỆP CỤ THỂ (5 BIỂU ĐỒ)
    # ====================================================
    with tab3:
        st.markdown("### 🏢 Bóc Tách Sức Khỏe Một Doanh Nghiệp")
        selected_symbol = st.selectbox("🔍 Chọn Mã Công Ty (Symbol):", all_symbols, key='tab3_search')
        df_company = df[df['Symbol'] == selected_symbol].sort_values(by='Year')
        
        if not df_company.empty:
            r5_c1, r5_c2 = st.columns(2)
            with r5_c1:
                # 3.1 Combo: Lợi nhuận vs Điểm rủi ro
                fig10 = go.Figure()
                fig10.add_trace(go.Bar(x=df_company['Year'], y=df_company['Net_Profit'], name='Lợi Nhuận', marker_color='#3b82f6', yaxis='y1'))
                fig10.add_trace(go.Scatter(x=df_company['Year'], y=df_company['fraud_score'], name='Fraud Score', mode='lines+markers', marker=dict(color='#ef4444'), yaxis='y2'))
                fig10.update_layout(title="1. Lợi Nhuận & Điểm Rủi Ro Qua Các Năm", xaxis=dict(dtick=1), yaxis2=dict(overlaying='y', side='right'))
                st.plotly_chart(fig10, use_container_width=True)
            
            with r5_c2:
                # 3.2 Grouped Bar: Cấu trúc Doanh Thu & Giá Vốn
                fig11 = go.Figure(data=[
                    go.Bar(name='Doanh Thu', x=df_company['Year'], y=df_company['Rev'], marker_color='#10b981'),
                    go.Bar(name='Giá Vốn (COGS)', x=df_company['Year'], y=df_company['COGS'], marker_color='#f59e0b')
                ])
                fig11.update_layout(title="2. Cấu Trúc Doanh Thu & Giá Vốn", barmode='group', xaxis=dict(dtick=1))
                st.plotly_chart(fig11, use_container_width=True)

            r6_c1, r6_c2 = st.columns(2)
            with r6_c1:
                # 3.3 Line: Phân tích dòng tiền (Lợi nhuận vs Dòng tiền HĐKD)
                fig12 = go.Figure()
                fig12.add_trace(go.Scatter(x=df_company['Year'], y=df_company['Net_Profit'], name='Net Profit', mode='lines+markers', line=dict(color='#3b82f6')))
                fig12.add_trace(go.Scatter(x=df_company['Year'], y=df_company['Operating_Cash_Flow'], name='Operating Cash Flow', mode='lines+markers', line=dict(color='#8b5cf6')))
                fig12.update_layout(title="3. Chất Lượng Lợi Nhuận (Lợi nhuận vs Dòng tiền)", xaxis=dict(dtick=1))
                st.plotly_chart(fig12, use_container_width=True)

            with r6_c2:
                # 3.4 Grouped Bar: Tổng Tài Sản vs Nợ
                fig13 = go.Figure(data=[
                    go.Bar(name='Tài Sản (Assets)', x=df_company['Year'], y=df_company['Total_Assets'], marker_color='#06b6d4'),
                    go.Bar(name='Nợ Phải Trả (Liabilities)', x=df_company['Year'], y=df_company['Total_Liabilities'], marker_color='#ec4899')
                ])
                fig13.update_layout(title="4. Cấu Trúc Tài Sản & Nợ Phải Trả", barmode='group', xaxis=dict(dtick=1))
                st.plotly_chart(fig13, use_container_width=True)
            
            # 3.5 Bảng tóm tắt các Red Flag doanh nghiệp đã vi phạm
            st.markdown(f"**5. Lịch Sử Vi Phạm Red Flags Của {selected_symbol}**")
            flag_df = df_company[['Year'] + flag_cols]
            st.dataframe(flag_df.set_index('Year').T, use_container_width=True)

    # ====================================================
    # TAB 4: SO SÁNH ĐỐI THỦ (5 BIỂU ĐỒ)
    # ====================================================
    with tab4:
        st.markdown("### ⚖️ So Sánh Trực Tiếp Các Doanh Nghiệp")
        selected_comp = st.multiselect("🤝 Chọn 2-5 mã công ty:", all_symbols, default=all_symbols[:3] if len(all_symbols)>=3 else all_symbols)
        if selected_comp:
            df_comp = df_filtered[df_filtered['Symbol'].isin(selected_comp)].sort_values(by='Year')
            
            r7_c1, r7_c2 = st.columns(2)
            with r7_c1:
                # 4.1 Line: Chạy đua Fraud Score
                fig14 = px.line(df_comp, x='Year', y='fraud_score', color='Symbol', markers=True, title="1. Biến Động Fraud Score")
                fig14.update_xaxes(dtick=1)
                st.plotly_chart(fig14, use_container_width=True)
                
            with r7_c2:
                # 4.2 Scatter Bubble: Ma trận Rủi ro vs Lợi nhuận
                fig15 = px.scatter(df_comp, x='fraud_score', y='Net_Profit', size='Total_Assets', color='Symbol', hover_name='Year', title="2. Đánh Đổi Lợi Nhuận vs Rủi Ro (Bóng = Tài sản)")
                st.plotly_chart(fig15, use_container_width=True)

            r8_c1, r8_c2 = st.columns(2)
            with r8_c1:
                # 4.3 Bar: So sánh Doanh thu (Grouped)
                fig16 = px.bar(df_comp, x='Year', y='Rev', color='Symbol', barmode='group', title="3. So Sánh Quy Mô Doanh Thu")
                fig16.update_xaxes(dtick=1)
                st.plotly_chart(fig16, use_container_width=True)

            with r8_c2:
                # 4.4 Radar Chart: So sánh sức khỏe tài chính (Năm mới nhất)
                latest_year = df_comp['Year'].max()
                df_radar = df_comp[df_comp['Year'] == latest_year]
                radar_cols = ['leverage_ratio', 'accrual_ratio', 'noncore_ratio', 'rec_manip_ratio', 'cash_crunch_ratio']
                
                fig17 = go.Figure()
                for sym in selected_comp:
                    sym_data = df_radar[df_radar['Symbol'] == sym]
                    if not sym_data.empty:
                        values = sym_data[radar_cols].iloc[0].tolist()
                        # Nối điểm cuối với điểm đầu để vòng khép kín
                        values += [values[0]]
                        plot_cols = radar_cols + [radar_cols[0]]
                        fig17.add_trace(go.Scatterpolar(r=values, theta=plot_cols, fill='toself', name=sym))
                
                fig17.update_layout(polar=dict(radialaxis=dict(visible=True)), title=f"4. Hồ Sơ Rủi Ro Chỉ Số Tài Chính (Năm {latest_year})")
                st.plotly_chart(fig17, use_container_width=True)
                
            # 4.5 So sánh Biên Lợi Nhuận Gộp (Delta Gross Margin)
            fig18 = px.line(df_comp, x='Year', y='Delta_Gross_Margin', color='Symbol', markers=True, title="5. Biến Động Biên Lợi Nhuận Gộp (Delta Gross Margin)")
            fig18.update_xaxes(dtick=1)
            st.plotly_chart(fig18, use_container_width=True)

    # ====================================================
    # TAB 5: PHÂN TÍCH CHUYÊN SÂU (5 BIỂU ĐỒ)
    # ====================================================
    with tab5:
        st.markdown("### 🧠 Không Gian Phân Tích Chuyên Gia")
        
        r9_c1, r9_c2 = st.columns(2)
        with r9_c1:
            # 5.1 Correlation Heatmap
            corr_cols = ['fraud_score', 'Rev', 'Net_Profit', 'Total_Assets', 'Leverage', 'Operating_Cash_Flow', 'accrual_ratio']
            corr_matrix = df_filtered[[c for c in corr_cols if c in df_filtered.columns]].corr().round(2)
            fig19 = px.imshow(corr_matrix, text_auto=True, color_continuous_scale='RdBu_r', title="1. Ma Trận Tương Quan Các Trọng Số")
            st.plotly_chart(fig19, use_container_width=True)

        with r9_c2:
            # 5.2 3D Scatter: Tài sản vs Nợ vs Dòng tiền
            fig20 = px.scatter_3d(df_filtered, x='Total_Assets', y='Total_Liabilities', z='Operating_Cash_Flow', color='risk_level', size='fraud_score', title="2. Không Gian 3D: Tài Sản - Nợ - Dòng Tiền", color_discrete_map=COLOR_MAP, opacity=0.7)
            fig20.update_layout(scene=dict(xaxis_title='Tài Sản', yaxis_title='Nợ', zaxis_title='Dòng Tiền'))
            st.plotly_chart(fig20, use_container_width=True)

        r10_c1, r10_c2 = st.columns(2)
        with r10_c1:
            # 5.3 Boxplot: Thao túng khoản phải thu (Receivables Manipulation)
            fig21 = px.box(df_filtered, x='risk_level', y='rec_manip_ratio', color='risk_level', title="3. Áp Lực Khoản Phải Thu (Receivables Manip)", color_discrete_map=COLOR_MAP)
            st.plotly_chart(fig21, use_container_width=True)

        with r10_c2:
            # 5.4 Boxplot: Cạn kiệt tiền mặt (Cash Crunch)
            fig22 = px.box(df_filtered, x='risk_level', y='cash_crunch_ratio', color='risk_level', title="4. Chỉ Báo Khát Tiền Mặt (Cash Crunch)", color_discrete_map=COLOR_MAP)
            st.plotly_chart(fig22, use_container_width=True)
            
        # 5.5 Histogram Phân phối lợi nhuận ngoài ngành cốt lõi
        fig23 = px.histogram(df_filtered, x='noncore_ratio', color='Target_Fraud', barmode='overlay', title="5. Tỷ Lệ Thu Nhập Bất Thường (Noncore) Giữa Công Ty Gian Lận (1) vs Bình Thường (0)")
        st.plotly_chart(fig23, use_container_width=True)

    # ====================================================
    # TAB 6: BỨC TRANH ĐA CHIỀU (MEGA DASHBOARD - 4 BIỂU ĐỒ TỔNG HỢP)
    # ====================================================
    with tab6:
        st.markdown("### 🌌 Lưới Giám Sát Đa Chiều Toàn Cảnh")
        
        r11_c1, r11_c2 = st.columns(2)
        with r11_c1:
            # 6.1 Treemap Doanh thu & Rủi ro
            top_rev = df_filtered.groupby('Symbol')[['Rev', 'fraud_score']].mean().reset_index().sort_values('Rev', ascending=False).head(50)
            top_rev['Rev_Plot'] = top_rev['Rev'].clip(lower=0)
            fig24 = px.treemap(top_rev, path=[px.Constant("Thị Trường"), 'Symbol'], values='Rev_Plot', color='fraud_score', color_continuous_scale='RdYlGn_r', title="1. Bản Đồ Nhiệt Top 50 Cty (Kích Thước = Rev, Màu = Risk)")
            st.plotly_chart(fig24, use_container_width=True)

        with r11_c2:
            # 6.2 Stacked Bar: Dịch chuyển mức rủi ro
            risk_trend = df_filtered.groupby(['Year', 'risk_level']).size().reset_index(name='Count')
            fig25 = px.bar(risk_trend, x='Year', y='Count', color='risk_level', title="2. Tốc Độ Lan Rộng Rủi Ro Qua Từng Năm", barmode='stack', color_discrete_map=COLOR_MAP)
            fig25.update_xaxes(dtick=1)
            st.plotly_chart(fig25, use_container_width=True)

        r12_c1, r12_c2 = st.columns(2)
        with r12_c1:
            # 6.3 Bar: Cơ cấu Vốn Cổ phần (Owners Equity) vs Nợ Dài Hạn
            cap_struct = df_filtered.groupby('Year')[['Owners_Equity', 'LT_Debt']].sum().reset_index()
            fig26 = go.Figure(data=[
                go.Bar(name='Vốn Chủ Sở Hữu', x=cap_struct['Year'], y=cap_struct['Owners_Equity'], marker_color='#8b5cf6'),
                go.Bar(name='Nợ Dài Hạn', x=cap_struct['Year'], y=cap_struct['LT_Debt'], marker_color='#f43f5e')
            ])
            fig26.update_layout(title="3. Cơ Cấu Vốn Chủ Sở Hữu & Nợ Dài Hạn Ngành", barmode='stack', xaxis=dict(dtick=1))
            st.plotly_chart(fig26, use_container_width=True)

        with r12_c2:
            # 6.4 Scatter Marginals: Doanh thu vs Khấu hao (Giấu lãi/Lỗ qua tài sản cố định)
            fig27 = px.scatter(df_filtered, x='Rev', y='depreciation_of_fixed_assets_and_properties_investment', color='risk_level', marginal_x="histogram", marginal_y="box", hover_name="Symbol", title="4. Doanh Thu vs Khấu Hao TS Cố Định", color_discrete_map=COLOR_MAP)
            st.plotly_chart(fig27, use_container_width=True)
