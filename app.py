import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Financial Risk Analysis",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS FOR "PRO" LOOK & ANIMATIONS ---
st.markdown("""
    <style>
    /* Tổng quan màu nền app */
    .stApp {
        background-color: #f4f6f9;
        font-family: 'Inter', sans-serif;
    }
    
    /* Ẩn header và footer mặc định của Streamlit cho pro */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Tùy chỉnh Sidebar */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
        box-shadow: 2px 0 5px rgba(0,0,0,0.02);
    }
    
    /* Tùy chỉnh Menu Navigation trong Sidebar (Radio buttons) */
    div.row-widget.stRadio > div {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    div.row-widget.stRadio > div > label {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 10px 15px;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    div.row-widget.stRadio > div > label:hover {
        background-color: #e2e8f0;
        transform: translateX(4px);
    }
    
    /* Hiệu ứng nổi (Hover Effect) cho KPI Cards */
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        border-color: #cbd5e1;
    }

    /* Tiêu đề chính */
    h1, h2, h3 {
        color: #0f172a;
        font-weight: 600;
        padding-bottom: 10px;
    }
    
    /* Căn chỉnh đường gạch ngang */
    hr {
        margin-top: 1.5rem;
        margin-bottom: 1.5rem;
        border: 0;
        border-top: 1px solid #e2e8f0;
    }
    </style>
""", unsafe_allow_html=True)

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
        st.markdown("### NAVIGATION")
        menu_options = [
            "Industry Overview", 
            "Red Flag Identification", 
            "Company Lookup",
            "Competitor Comparison",
            "In-depth Analysis",
            "Multi-dimensional View"
        ]
        # Sử dụng radio làm menu điều hướng chính
        selected_page = st.radio("Go to", menu_options, label_visibility="collapsed")
        
        st.markdown("---")
        st.markdown("### FILTERS & CONTROLS")
        min_year, max_year = int(df['Year'].min()), int(df['Year'].max())
        selected_years = st.slider("Period (Years):", min_year, max_year, (min_year, max_year))
        
        risk_levels = sorted(df['risk_level'].dropna().unique().tolist())
        selected_risks = st.multiselect("Risk Levels:", options=risk_levels, default=risk_levels)

        fraud_threshold = st.slider("Fraud Score Threshold:", 0.0, 5.0, 1.5, 0.1)

    # Lọc dữ liệu dùng chung
    mask = (df['Year'] >= selected_years[0]) & (df['Year'] <= selected_years[1]) & (df['risk_level'].isin(selected_risks))
    df_filtered = df.loc[mask]
    all_symbols = sorted(df_filtered['Symbol'].dropna().unique().tolist())
    
    COLOR_MAP = {'HighRisk': '#ef4444', 'MediumRisk': '#f59e0b', 'LowRisk': '#10b981', 'Safe': '#3b82f6'}

    # Cảnh báo chung (Nằm trên cùng)
    high_risk_df = df_filtered[df_filtered['fraud_score'] >= fraud_threshold]
    if not high_risk_df.empty:
        st.warning(f"SYSTEM ALERT: {high_risk_df['Symbol'].nunique()} companies exceeded the fraud threshold of {fraud_threshold}.")

    st.markdown(f"## {selected_page}")
    st.caption(f"Analyzing data from {selected_years[0]} to {selected_years[1]}")
    st.markdown("<br>", unsafe_allow_html=True)

    # ====================================================
    # PAGE 1: INDUSTRY OVERVIEW
    # ====================================================
    if selected_page == "Industry Overview":
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Companies", f"{df_filtered['Symbol'].nunique()}")
        c2.metric("Avg Fraud Score", f"{df_filtered['fraud_score'].mean():.2f}")
        c3.metric("Flagged Cases", f"{df_filtered['Target_Fraud'].sum()}")
        avg_rev = df_filtered['Rev'].mean() / 1e9 if 'Rev' in df_filtered.columns else 0
        c4.metric("Avg Revenue", f"{avg_rev:,.0f} B")
        st.markdown("<br>", unsafe_allow_html=True)

        r1_c1, r1_c2 = st.columns(2)
        with r1_c1:
            yearly_stats = df_filtered.groupby('Year')['fraud_score'].mean().reset_index()
            fig1 = px.line(yearly_stats, x='Year', y='fraud_score', markers=True, title="Average Industry Fraud Score Trend", color_discrete_sequence=['#ef4444'], template="plotly_white")
            fig1.add_hline(y=fraud_threshold, line_dash="dash", line_color="orange")
            fig1.update_xaxes(dtick=1)
            st.plotly_chart(fig1, use_container_width=True)
            
        with r1_c2:
            risk_counts = df_filtered['risk_level'].value_counts().reset_index()
            fig2 = px.pie(risk_counts, values='count', names='risk_level', hole=0.4, title="Proportion of Risk Groups", color='risk_level', color_discrete_map=COLOR_MAP, template="plotly_white")
            st.plotly_chart(fig2, use_container_width=True)

        r2_c1, r2_c2 = st.columns(2)
        with r2_c1:
            rev_prof = df_filtered.groupby('Year')[['Rev', 'Net_Profit']].sum().reset_index()
            fig3 = go.Figure(data=[
                go.Bar(name='Total Revenue', x=rev_prof['Year'], y=rev_prof['Rev'], marker_color='#3b82f6'),
                go.Bar(name='Total Profit', x=rev_prof['Year'], y=rev_prof['Net_Profit'], marker_color='#10b981')
            ])
            fig3.update_layout(title="Total Industry Revenue & Profit", barmode='group', xaxis=dict(dtick=1), template="plotly_white")
            st.plotly_chart(fig3, use_container_width=True)
            
        with r2_c2:
            top_10 = df_filtered.sort_values(by='fraud_score', ascending=False).drop_duplicates(subset=['Symbol']).head(10)
            fig4 = px.bar(top_10, x='Symbol', y='fraud_score', color='fraud_score', color_continuous_scale='Reds', title="Top 10 High-Risk Companies", template="plotly_white")
            st.plotly_chart(fig4, use_container_width=True)

        fig5 = px.histogram(df_filtered, x='fraud_score', color='risk_level', nbins=50, title="Fraud Score Frequency Distribution", color_discrete_map=COLOR_MAP, template="plotly_white")
        st.plotly_chart(fig5, use_container_width=True)

    # ====================================================
    # PAGE 2: RED FLAG IDENTIFICATION
    # ====================================================
    elif selected_page == "Red Flag Identification":
        r3_c1, r3_c2 = st.columns(2)
        flag_cols = [c for c in df.columns if c.startswith('f_') and c not in ['f_score']]
        
        with r3_c1:
            flag_sums = df_filtered[flag_cols].sum().sort_values(ascending=True).reset_index()
            flag_sums.columns = ['Red Flag Type', 'Count']
            fig6 = px.bar(flag_sums, x='Count', y='Red Flag Type', orientation='h', title="Most Common Fraud Types", color='Count', color_continuous_scale='Sunsetdark', template="plotly_white")
            st.plotly_chart(fig6, use_container_width=True)

        with r3_c2:
            fig7 = px.scatter(df_filtered, x='Delta_Rev', y='Delta_Inv', color='risk_level', size='fraud_score', title="Revenue Growth vs Inventory Growth", hover_name='Symbol', color_discrete_map=COLOR_MAP, template="plotly_white")
            fig7.add_hline(y=0, line_dash="dot", line_color="gray")
            fig7.add_vline(x=0, line_dash="dot", line_color="gray")
            st.plotly_chart(fig7, use_container_width=True)

        r4_c1, r4_c2 = st.columns(2)
        with r4_c1:
            fig8 = px.box(df_filtered, x='risk_level', y='Leverage', color='risk_level', title="Leverage Level by Risk", color_discrete_map=COLOR_MAP, template="plotly_white")
            st.plotly_chart(fig8, use_container_width=True)

        with r4_c2:
            if 'accrual_ratio' in df_filtered.columns:
                fig9 = px.box(df_filtered, x='risk_level', y='accrual_ratio', color='risk_level', title="Accrual Ratio by Risk", color_discrete_map=COLOR_MAP, template="plotly_white")
                st.plotly_chart(fig9, use_container_width=True)

    # ====================================================
    # PAGE 3: COMPANY LOOKUP
    # ====================================================
    elif selected_page == "Company Lookup":
        selected_symbol = st.selectbox("Search or Select Company Symbol:", all_symbols)
        df_company = df[df['Symbol'] == selected_symbol].sort_values(by='Year')
        
        if not df_company.empty:
            r5_c1, r5_c2 = st.columns(2)
            with r5_c1:
                fig10 = go.Figure()
                fig10.add_trace(go.Bar(x=df_company['Year'], y=df_company['Net_Profit'], name='Profit', marker_color='#3b82f6', yaxis='y1'))
                fig10.add_trace(go.Scatter(x=df_company['Year'], y=df_company['fraud_score'], name='Fraud Score', mode='lines+markers', marker=dict(color='#ef4444'), yaxis='y2'))
                fig10.update_layout(title="Profit & Risk Score Over Years", xaxis=dict(dtick=1), yaxis2=dict(overlaying='y', side='right'), template="plotly_white")
                st.plotly_chart(fig10, use_container_width=True)
            
            with r5_c2:
                fig11 = go.Figure(data=[
                    go.Bar(name='Revenue', x=df_company['Year'], y=df_company['Rev'], marker_color='#10b981'),
                    go.Bar(name='COGS', x=df_company['Year'], y=df_company['COGS'], marker_color='#f59e0b')
                ])
                fig11.update_layout(title="Revenue & COGS Structure", barmode='group', xaxis=dict(dtick=1), template="plotly_white")
                st.plotly_chart(fig11, use_container_width=True)

            r6_c1, r6_c2 = st.columns(2)
            with r6_c1:
                fig12 = go.Figure()
                fig12.add_trace(go.Scatter(x=df_company['Year'], y=df_company['Net_Profit'], name='Net Profit', mode='lines+markers', line=dict(color='#3b82f6')))
                fig12.add_trace(go.Scatter(x=df_company['Year'], y=df_company['Operating_Cash_Flow'], name='Operating Cash Flow', mode='lines+markers', line=dict(color='#8b5cf6')))
                fig12.update_layout(title="Profit Quality (Profit vs Cash Flow)", xaxis=dict(dtick=1), template="plotly_white")
                st.plotly_chart(fig12, use_container_width=True)

            with r6_c2:
                fig13 = go.Figure(data=[
                    go.Bar(name='Assets', x=df_company['Year'], y=df_company['Total_Assets'], marker_color='#06b6d4'),
                    go.Bar(name='Liabilities', x=df_company['Year'], y=df_company['Total_Liabilities'], marker_color='#ec4899')
                ])
                fig13.update_layout(title="Assets & Liabilities Structure", barmode='group', xaxis=dict(dtick=1), template="plotly_white")
                st.plotly_chart(fig13, use_container_width=True)
            
            st.markdown(f"**Red Flag Violation History of {selected_symbol}**")
            flag_cols = [c for c in df.columns if c.startswith('f_') and c not in ['f_score']]
            flag_df = df_company[['Year'] + flag_cols]
            st.dataframe(flag_df.set_index('Year').T, use_container_width=True)

    # ====================================================
    # PAGE 4: COMPETITOR COMPARISON
    # ====================================================
    elif selected_page == "Competitor Comparison":
        selected_comp = st.multiselect("Select Companies for Comparison:", all_symbols, default=all_symbols[:3] if len(all_symbols)>=3 else all_symbols)
        if selected_comp:
            df_comp = df_filtered[df_filtered['Symbol'].isin(selected_comp)].sort_values(by='Year')
            
            r7_c1, r7_c2 = st.columns(2)
            with r7_c1:
                fig14 = px.line(df_comp, x='Year', y='fraud_score', color='Symbol', markers=True, title="Fraud Score Fluctuation", template="plotly_white")
                fig14.update_xaxes(dtick=1)
                st.plotly_chart(fig14, use_container_width=True)
                
            with r7_c2:
                fig15 = px.scatter(df_comp, x='fraud_score', y='Net_Profit', size='Total_Assets', color='Symbol', hover_name='Year', title="Profit vs Risk Trade-off (Bubble = Assets)", template="plotly_white")
                st.plotly_chart(fig15, use_container_width=True)

            r8_c1, r8_c2 = st.columns(2)
            with r8_c1:
                fig16 = px.bar(df_comp, x='Year', y='Rev', color='Symbol', barmode='group', title="Revenue Scale Comparison", template="plotly_white")
                fig16.update_xaxes(dtick=1)
                st.plotly_chart(fig16, use_container_width=True)

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
                
                fig17.update_layout(polar=dict(radialaxis=dict(visible=True)), title=f"Financial Index Risk Profile (Year {latest_year})", template="plotly_white")
                st.plotly_chart(fig17, use_container_width=True)
                
            fig18 = px.line(df_comp, x='Year', y='Delta_Gross_Margin', color='Symbol', markers=True, title="Gross Margin Fluctuation (Delta Gross Margin)", template="plotly_white")
            fig18.update_xaxes(dtick=1)
            st.plotly_chart(fig18, use_container_width=True)

    # ====================================================
    # PAGE 5: IN-DEPTH ANALYSIS
    # ====================================================
    elif selected_page == "In-depth Analysis":
        r9_c1, r9_c2 = st.columns(2)
        with r9_c1:
            corr_cols = ['fraud_score', 'Rev', 'Net_Profit', 'Total_Assets', 'Leverage', 'Operating_Cash_Flow', 'accrual_ratio']
            corr_matrix = df_filtered[[c for c in corr_cols if c in df_filtered.columns]].corr().round(2)
            fig19 = px.imshow(corr_matrix, text_auto=True, color_continuous_scale='RdBu_r', title="Correlation Matrix of Variables", template="plotly_white")
            st.plotly_chart(fig19, use_container_width=True)

        with r9_c2:
            fig20 = px.scatter_3d(df_filtered, x='Total_Assets', y='Total_Liabilities', z='Operating_Cash_Flow', color='risk_level', size='fraud_score', title="3D Space: Assets - Liabilities - Cash Flow", color_discrete_map=COLOR_MAP, opacity=0.7)
            fig20.update_layout(scene=dict(xaxis_title='Assets', yaxis_title='Liabilities', zaxis_title='Cash Flow'), template="plotly_white")
            st.plotly_chart(fig20, use_container_width=True)

        r10_c1, r10_c2 = st.columns(2)
        with r10_c1:
            fig21 = px.box(df_filtered, x='risk_level', y='rec_manip_ratio', color='risk_level', title="Receivables Pressure (Receivables Manip)", color_discrete_map=COLOR_MAP, template="plotly_white")
            st.plotly_chart(fig21, use_container_width=True)

        with r10_c2:
            fig22 = px.box(df_filtered, x='risk_level', y='cash_crunch_ratio', color='risk_level', title="Cash Crunch Indicator", color_discrete_map=COLOR_MAP, template="plotly_white")
            st.plotly_chart(fig22, use_container_width=True)
            
        fig23 = px.histogram(df_filtered, x='noncore_ratio', color='Target_Fraud', barmode='overlay', title="Noncore Income Ratio Between Fraud (1) vs Normal (0) Companies", template="plotly_white")
        st.plotly_chart(fig23, use_container_width=True)

    # ====================================================
    # PAGE 6: MULTI-DIMENSIONAL VIEW
    # ====================================================
    elif selected_page == "Multi-dimensional View":
        r11_c1, r11_c2 = st.columns(2)
        with r11_c1:
            top_rev = df_filtered.groupby('Symbol')[['Rev', 'fraud_score']].mean().reset_index().sort_values('Rev', ascending=False).head(50)
            top_rev['Rev_Plot'] = top_rev['Rev'].clip(lower=0)
            fig24 = px.treemap(top_rev, path=[px.Constant("Market"), 'Symbol'], values='Rev_Plot', color='fraud_score', color_continuous_scale='RdYlGn_r', title="Top 50 Companies Heatmap (Size = Rev, Color = Risk)")
            st.plotly_chart(fig24, use_container_width=True)

        with r11_c2:
            risk_trend = df_filtered.groupby(['Year', 'risk_level']).size().reset_index(name='Count')
            fig25 = px.bar(risk_trend, x='Year', y='Count', color='risk_level', title="Risk Spread Rate Over Years", barmode='stack', color_discrete_map=COLOR_MAP, template="plotly_white")
            fig25.update_xaxes(dtick=1)
            st.plotly_chart(fig25, use_container_width=True)

        r12_c1, r12_c2 = st.columns(2)
        with r12_c1:
            cap_struct = df_filtered.groupby('Year')[['Owners_Equity', 'LT_Debt']].sum().reset_index()
            fig26 = go.Figure(data=[
                go.Bar(name='Owners Equity', x=cap_struct['Year'], y=cap_struct['Owners_Equity'], marker_color='#8b5cf6'),
                go.Bar(name='Long-Term Debt', x=cap_struct['Year'], y=cap_struct['LT_Debt'], marker_color='#f43f5e')
            ])
            fig26.update_layout(title="Industry Owners Equity & Long-Term Debt Structure", barmode='stack', xaxis=dict(dtick=1), template="plotly_white")
            st.plotly_chart(fig26, use_container_width=True)

        with r12_c2:
            fig27 = px.scatter(df_filtered, x='Rev', y='depreciation_of_fixed_assets_and_properties_investment', color='risk_level', marginal_x="histogram", marginal_y="box", hover_name="Symbol", title="Revenue vs Fixed Assets Depreciation", color_discrete_map=COLOR_MAP, template="plotly_white")
            st.plotly_chart(fig27, use_container_width=True)
