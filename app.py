import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from streamlit_option_menu import option_menu  # <-- Thư viện mới tạo menu xịn

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Financial Risk & Fraud Analysis",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS FOR "PRO" LOOK & ANIMATIONS ---
st.markdown("""
    <style>
    /* Tổng quan màu nền app */
    .stApp {
        background-color: #F0F2F6;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* ĐÃ XÓA CODE ẨN HEADER ĐỂ HIỆN LẠI THANH CÔNG CỤ (DEPLOY / SETTINGS) CỦA STREAMLIT */

    /* Tùy chỉnh Sidebar */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #E2E8F0;
    }
    
    /* Thiết kế lại các KPI Metrics (Thẻ số liệu) */
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #E2E8F0;
        border-top: 4px solid #2563EB; /* Viền nhấn màu xanh biển chuẩn Pro */
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    
    /* Định dạng Text trong KPI */
    div[data-testid="metric-container"] label {
        color: #64748B !important;
        font-weight: 500 !important;
        font-size: 0.95rem !important;
    }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        color: #0F172A !important;
        font-weight: 700 !important;
    }

    /* Tiêu đề */
    h1, h2, h3 {
        color: #0F172A;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    /* Các đường kẻ ngang */
    hr {
        border-top: 1px solid #CBD5E1;
        margin: 1.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# --- TẠO HÀM CHUẨN HÓA GIAO DIỆN BIỂU ĐỒ PLOTLY ---
def apply_pro_theme(fig):
    """Hàm này giúp mọi biểu đồ đều có chung 1 phong cách màu sắc, font chữ cao cấp"""
    fig.update_layout(
        template="plotly_white",
        font=dict(family="Inter, sans-serif", size=12, color="#475569"),
        margin=dict(l=20, r=20, t=50, b=20),
        hovermode="x unified",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        title_font=dict(size=16, color="#1E293B", family="Inter, sans-serif"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor="#CBD5E1")
    fig.update_yaxes(gridcolor="#E2E8F0", zeroline=False, linecolor="#CBD5E1")
    return fig

# --- 2. LOAD DATA ---
@st.cache_data
def load_data():
    file_path = 'final_merged_dataset.csv'
    if not os.path.exists(file_path):
        st.error(f"Data file not found: {file_path}")
        return pd.DataFrame()
        
    df = pd.read_csv(file_path)
    if 'Year' in df.columns:
        df['Year'] = df['Year'].astype(int)
    
    num_cols = df.select_dtypes(include=['float64', 'int64']).columns
    df[num_cols] = df[num_cols].fillna(0)
            
    return df

df = load_data()

if not df.empty:
    # --- 3. SIDEBAR NAVIGATION & CONTROLS ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135673.png", width=60)
        st.markdown("<h2 style='font-size: 1.2rem;'>RISK PORTAL</h2>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- THANH CÔNG CỤ MENU BÊN TRÁI HIỆN ĐẠI ---
        page = option_menu(
            menu_title="MAIN MENU", 
            options=["Industry Overview", "Red Flag Identification", "Company Lookup", "Competitor Comparison", "In-depth Analysis", "Multi-dimensional View"],
            icons=["bar-chart", "exclamation-triangle", "building", "scales", "microscope", "globe"], 
            menu_icon="cast", 
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "#ffffff", "border": "none"},
                "icon": {"color": "#64748b", "font-size": "16px"}, 
                "nav-link": {"font-size": "14px", "text-align": "left", "margin":"5px", "color": "#0f172a", "font-weight": "500"},
                "nav-link-selected": {"background-color": "#2563EB", "color": "white", "font-weight": "600"},
            }
        )
        
        st.markdown("---")
        st.markdown("<p style='color: #64748B; font-size: 0.8rem; font-weight: 700; margin-bottom: 5px;'>FILTERS & CONTROLS</p>", unsafe_allow_html=True)
        
        min_year, max_year = int(df['Year'].min()), int(df['Year'].max())
        selected_years = st.slider("Period (Years):", min_year, max_year, (min_year, max_year))
        
        risk_levels = sorted(df['risk_level'].dropna().unique().tolist())
        selected_risks = st.multiselect("Risk Levels:", options=risk_levels, default=risk_levels)

        fraud_threshold = st.slider("Fraud Score Threshold:", 0.0, 5.0, 1.5, 0.1)

    # Filter Data
    mask = (df['Year'] >= selected_years[0]) & (df['Year'] <= selected_years[1]) & (df['risk_level'].isin(selected_risks))
    df_filtered = df.loc[mask]
    all_symbols = sorted(df_filtered['Symbol'].dropna().unique().tolist())
    
    # Bảng màu Pro: Muted & Professional
    COLOR_MAP = {'HighRisk': '#E11D48', 'MediumRisk': '#F59E0B', 'LowRisk': '#10B981', 'Safe': '#3B82F6'}

    # Cảnh báo chung (Nằm trên cùng)
    high_risk_df = df_filtered[df_filtered['fraud_score'] >= fraud_threshold]
    if not high_risk_df.empty:
        st.warning(f"SYSTEM ALERT: {high_risk_df['Symbol'].nunique()} companies exceeded the fraud threshold of {fraud_threshold}.", icon="🚨")

    st.title(f"{page}")
    st.caption(f"Showing analytical data from **{selected_years[0]}** to **{selected_years[1]}**")
    st.markdown("<br>", unsafe_allow_html=True)

    # ====================================================
    # PAGE 1: INDUSTRY OVERVIEW
    # ====================================================
    if page == "Industry Overview":
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Companies", f"{df_filtered['Symbol'].nunique()}")
        c2.metric("Avg Fraud Score", f"{df_filtered['fraud_score'].mean():.2f}")
        c3.metric("Flagged Cases", f"{df_filtered['Target_Fraud'].sum()}")
        avg_rev = df_filtered['Rev'].mean() / 1e9 if 'Rev' in df_filtered.columns else 0
        c4.metric("Avg Revenue", f"{avg_rev:,.0f} B")
        st.markdown("<br><br>", unsafe_allow_html=True)

        r1_c1, r1_c2 = st.columns([2, 1])
        with r1_c1:
            yearly_stats = df_filtered.groupby('Year')['fraud_score'].mean().reset_index()
            fig1 = px.line(yearly_stats, x='Year', y='fraud_score', markers=True, title="Average Industry Fraud Score Trend", color_discrete_sequence=['#E11D48'])
            fig1.add_hline(y=fraud_threshold, line_dash="dash", line_color="#F59E0B")
            fig1.update_xaxes(dtick=1)
            st.plotly_chart(apply_pro_theme(fig1), use_container_width=True)
            
        with r1_c2:
            risk_counts = df_filtered['risk_level'].value_counts().reset_index()
            fig2 = px.pie(risk_counts, values='count', names='risk_level', hole=0.5, title="Proportion of Risk Groups", color='risk_level', color_discrete_map=COLOR_MAP)
            st.plotly_chart(apply_pro_theme(fig2), use_container_width=True)

        r2_c1, r2_c2 = st.columns(2)
        with r2_c1:
            rev_prof = df_filtered.groupby('Year')[['Rev', 'Net_Profit']].sum().reset_index()
            fig3 = go.Figure(data=[
                go.Bar(name='Total Revenue', x=rev_prof['Year'], y=rev_prof['Rev'], marker_color='#3B82F6'),
                go.Bar(name='Total Profit', x=rev_prof['Year'], y=rev_prof['Net_Profit'], marker_color='#10B981')
            ])
            fig3.update_layout(title="Total Industry Revenue & Profit", barmode='group', xaxis=dict(dtick=1))
            st.plotly_chart(apply_pro_theme(fig3), use_container_width=True)
            
        with r2_c2:
            top_10 = df_filtered.sort_values(by='fraud_score', ascending=False).drop_duplicates(subset=['Symbol']).head(10)
            fig4 = px.bar(top_10, x='Symbol', y='fraud_score', color='fraud_score', color_continuous_scale='Reds', title="Top 10 High-Risk Companies")
            st.plotly_chart(apply_pro_theme(fig4), use_container_width=True)

        fig5 = px.histogram(df_filtered, x='fraud_score', color='risk_level', nbins=50, title="Fraud Score Frequency Distribution", color_discrete_map=COLOR_MAP)
        st.plotly_chart(apply_pro_theme(fig5), use_container_width=True)

    # ====================================================
    # PAGE 2: RED FLAG IDENTIFICATION
    # ====================================================
    elif page == "Red Flag Identification":
        r3_c1, r3_c2 = st.columns(2)
        flag_cols = [c for c in df.columns if c.startswith('f_') and c not in ['f_score']]
        
        with r3_c1:
            flag_sums = df_filtered[flag_cols].sum().sort_values(ascending=True).reset_index()
            flag_sums.columns = ['Red Flag Type', 'Count']
            fig6 = px.bar(flag_sums, x='Count', y='Red Flag Type', orientation='h', title="Most Common Fraud Types", color='Count', color_continuous_scale='Sunsetdark')
            st.plotly_chart(apply_pro_theme(fig6), use_container_width=True)

        with r3_c2:
            fig7 = px.scatter(df_filtered, x='Delta_Rev', y='Delta_Inv', color='risk_level', size='fraud_score', title="Revenue Growth vs Inventory Growth", hover_name='Symbol', color_discrete_map=COLOR_MAP)
            fig7.add_hline(y=0, line_dash="dot", line_color="#94A3B8")
            fig7.add_vline(x=0, line_dash="dot", line_color="#94A3B8")
            st.plotly_chart(apply_pro_theme(fig7), use_container_width=True)

        r4_c1, r4_c2 = st.columns(2)
        with r4_c1:
            fig8 = px.box(df_filtered, x='risk_level', y='Leverage', color='risk_level', title="Leverage Level by Risk", color_discrete_map=COLOR_MAP)
            st.plotly_chart(apply_pro_theme(fig8), use_container_width=True)

        with r4_c2:
            if 'accrual_ratio' in df_filtered.columns:
                fig9 = px.box(df_filtered, x='risk_level', y='accrual_ratio', color='risk_level', title="Accrual Ratio by Risk", color_discrete_map=COLOR_MAP)
                st.plotly_chart(apply_pro_theme(fig9), use_container_width=True)

    # ====================================================
    # PAGE 3: COMPANY LOOKUP
    # ====================================================
    elif page == "Company Lookup":
        selected_symbol = st.selectbox("Search or Select Company Symbol:", all_symbols)
        df_company = df[df['Symbol'] == selected_symbol].sort_values(by='Year')
        
        if not df_company.empty:
            r5_c1, r5_c2 = st.columns(2)
            with r5_c1:
                fig10 = go.Figure()
                fig10.add_trace(go.Bar(x=df_company['Year'], y=df_company['Net_Profit'], name='Profit', marker_color='#3B82F6', yaxis='y1'))
                fig10.add_trace(go.Scatter(x=df_company['Year'], y=df_company['fraud_score'], name='Fraud Score', mode='lines+markers', marker=dict(color='#E11D48'), yaxis='y2'))
                fig10.update_layout(title="Profit & Risk Score Over Years", xaxis=dict(dtick=1), yaxis2=dict(overlaying='y', side='right', showgrid=False))
                st.plotly_chart(apply_pro_theme(fig10), use_container_width=True)
            
            with r5_c2:
                fig11 = go.Figure(data=[
                    go.Bar(name='Revenue', x=df_company['Year'], y=df_company['Rev'], marker_color='#10B981'),
                    go.Bar(name='COGS', x=df_company['Year'], y=df_company['COGS'], marker_color='#F59E0B')
                ])
                fig11.update_layout(title="Revenue & COGS Structure", barmode='group', xaxis=dict(dtick=1))
                st.plotly_chart(apply_pro_theme(fig11), use_container_width=True)

            r6_c1, r6_c2 = st.columns(2)
            with r6_c1:
                fig12 = go.Figure()
                fig12.add_trace(go.Scatter(x=df_company['Year'], y=df_company['Net_Profit'], name='Net Profit', mode='lines+markers', line=dict(color='#3B82F6')))
                fig12.add_trace(go.Scatter(x=df_company['Year'], y=df_company['Operating_Cash_Flow'], name='Operating Cash Flow', mode='lines+markers', line=dict(color='#8B5CF6')))
                fig12.update_layout(title="Profit Quality (Profit vs Cash Flow)", xaxis=dict(dtick=1))
                st.plotly_chart(apply_pro_theme(fig12), use_container_width=True)

            with r6_c2:
                fig13 = go.Figure(data=[
                    go.Bar(name='Assets', x=df_company['Year'], y=df_company['Total_Assets'], marker_color='#06B6D4'),
                    go.Bar(name='Liabilities', x=df_company['Year'], y=df_company['Total_Liabilities'], marker_color='#EC4899')
                ])
                fig13.update_layout(title="Assets & Liabilities Structure", barmode='group', xaxis=dict(dtick=1))
                st.plotly_chart(apply_pro_theme(fig13), use_container_width=True)
            
            st.markdown(f"**Red Flag Violation History of {selected_symbol}**")
            flag_cols = [c for c in df.columns if c.startswith('f_') and c not in ['f_score']]
            flag_df = df_company[['Year'] + flag_cols]
            st.dataframe(flag_df.set_index('Year').T, use_container_width=True)

    # ====================================================
    # PAGE 4: COMPETITOR COMPARISON
    # ====================================================
    elif page == "Competitor Comparison":
        selected_comp = st.multiselect("Select Companies for Comparison:", all_symbols, default=all_symbols[:3] if len(all_symbols)>=3 else all_symbols)
        if selected_comp:
            df_comp = df_filtered[df_filtered['Symbol'].isin(selected_comp)].sort_values(by='Year')
            
            r7_c1, r7_c2 = st.columns(2)
            with r7_c1:
                fig14 = px.line(df_comp, x='Year', y='fraud_score', color='Symbol', markers=True, title="Fraud Score Fluctuation")
                fig14.update_xaxes(dtick=1)
                st.plotly_chart(apply_pro_theme(fig14), use_container_width=True)
                
            with r7_c2:
                fig15 = px.scatter(df_comp, x='fraud_score', y='Net_Profit', size='Total_Assets', color='Symbol', hover_name='Year', title="Profit vs Risk Trade-off (Bubble = Assets)")
                st.plotly_chart(apply_pro_theme(fig15), use_container_width=True)

            r8_c1, r8_c2 = st.columns(2)
            with r8_c1:
                fig16 = px.bar(df_comp, x='Year', y='Rev', color='Symbol', barmode='group', title="Revenue Scale Comparison")
                fig16.update_xaxes(dtick=1)
                st.plotly_chart(apply_pro_theme(fig16), use_container_width=True)

            with r8_c2:
                latest_year = df_comp['Year'].max()
                df_radar = df_comp[df_comp['Year'] == latest_year]
                radar_cols = ['leverage_ratio', 'accrual_ratio', 'noncore_ratio', 'rec_manip_ratio', 'cash_crunch_ratio']
                
                fig17 = go.Figure()
                for sym in selected_comp:
                    sym_data = df_radar[df_radar['Symbol'] == sym]
                    if not sym_data.empty:
                        values = sym_data[radar_cols].iloc[0].tolist()
                        values += [values[0]]
                        plot_cols = radar_cols + [radar_cols[0]]
                        fig17.add_trace(go.Scatterpolar(r=values, theta=plot_cols, fill='toself', name=sym))
                
                fig17.update_layout(polar=dict(radialaxis=dict(visible=True)), title=f"Financial Index Risk Profile (Year {latest_year})")
                st.plotly_chart(apply_pro_theme(fig17), use_container_width=True)
                
            fig18 = px.line(df_comp, x='Year', y='Delta_Gross_Margin', color='Symbol', markers=True, title="Gross Margin Fluctuation (Delta Gross Margin)")
            fig18.update_xaxes(dtick=1)
            st.plotly_chart(apply_pro_theme(fig18), use_container_width=True)

    # ====================================================
    # PAGE 5: IN-DEPTH ANALYSIS
    # ====================================================
    elif page == "In-depth Analysis":
        r9_c1, r9_c2 = st.columns(2)
        with r9_c1:
            corr_cols = ['fraud_score', 'Rev', 'Net_Profit', 'Total_Assets', 'Leverage', 'Operating_Cash_Flow', 'accrual_ratio']
            corr_matrix = df_filtered[[c for c in corr_cols if c in df_filtered.columns]].corr().round(2)
            fig19 = px.imshow(corr_matrix, text_auto=True, color_continuous_scale='RdBu_r', title="Correlation Matrix of Variables")
            st.plotly_chart(apply_pro_theme(fig19), use_container_width=True)

        with r9_c2:
            fig20 = px.scatter_3d(df_filtered, x='Total_Assets', y='Total_Liabilities', z='Operating_Cash_Flow', color='risk_level', size='fraud_score', title="3D Space: Assets - Liabilities - Cash Flow", color_discrete_map=COLOR_MAP, opacity=0.7)
            fig20.update_layout(scene=dict(xaxis_title='Assets', yaxis_title='Liabilities', zaxis_title='Cash Flow'))
            st.plotly_chart(apply_pro_theme(fig20), use_container_width=True)

        r10_c1, r10_c2 = st.columns(2)
        with r10_c1:
            fig21 = px.box(df_filtered, x='risk_level', y='rec_manip_ratio', color='risk_level', title="Receivables Pressure (Receivables Manip)", color_discrete_map=COLOR_MAP)
            st.plotly_chart(apply_pro_theme(fig21), use_container_width=True)

        with r10_c2:
            fig22 = px.box(df_filtered, x='risk_level', y='cash_crunch_ratio', color='risk_level', title="Cash Crunch Indicator", color_discrete_map=COLOR_MAP)
            st.plotly_chart(apply_pro_theme(fig22), use_container_width=True)
            
        fig23 = px.histogram(df_filtered, x='noncore_ratio', color='Target_Fraud', barmode='overlay', title="Noncore Income Ratio Between Fraud (1) vs Normal (0) Companies")
        st.plotly_chart(apply_pro_theme(fig23), use_container_width=True)

    # ====================================================
    # PAGE 6: MULTI-DIMENSIONAL VIEW
    # ====================================================
    elif page == "Multi-dimensional View":
        r11_c1, r11_c2 = st.columns(2)
        with r11_c1:
            top_rev = df_filtered.groupby('Symbol')[['Rev', 'fraud_score']].mean().reset_index().sort_values('Rev', ascending=False).head(50)
            top_rev['Rev_Plot'] = top_rev['Rev'].clip(lower=0)
            fig24 = px.treemap(top_rev, path=[px.Constant("Market"), 'Symbol'], values='Rev_Plot', color='fraud_score', color_continuous_scale='RdYlGn_r', title="Top 50 Companies Heatmap (Size = Rev, Color = Risk)")
            st.plotly_chart(apply_pro_theme(fig24), use_container_width=True)

        with r11_c2:
            risk_trend = df_filtered.groupby(['Year', 'risk_level']).size().reset_index(name='Count')
            fig25 = px.bar(risk_trend, x='Year', y='Count', color='risk_level', title="Risk Spread Rate Over Years", barmode='stack', color_discrete_map=COLOR_MAP)
            fig25.update_xaxes(dtick=1)
            st.plotly_chart(apply_pro_theme(fig25), use_container_width=True)

        r12_c1, r12_c2 = st.columns(2)
        with r12_c1:
            cap_struct = df_filtered.groupby('Year')[['Owners_Equity', 'LT_Debt']].sum().reset_index()
            fig26 = go.Figure(data=[
                go.Bar(name='Owners Equity', x=cap_struct['Year'], y=cap_struct['Owners_Equity'], marker_color='#8B5CF6'),
                go.Bar(name='Long-Term Debt', x=cap_struct['Year'], y=cap_struct['LT_Debt'], marker_color='#F43F5E')
            ])
            fig26.update_layout(title="Industry Owners Equity & Long-Term Debt Structure", barmode='stack', xaxis=dict(dtick=1))
            st.plotly_chart(apply_pro_theme(fig26), use_container_width=True)

        with r12_c2:
            fig27 = px.scatter(df_filtered, x='Rev', y='depreciation_of_fixed_assets_and_properties_investment', color='risk_level', marginal_x="histogram", marginal_y="box", hover_name="Symbol", title="Revenue vs Fixed Assets Depreciation", color_discrete_map=COLOR_MAP)
            st.plotly_chart(apply_pro_theme(fig27), use_container_width=True)
