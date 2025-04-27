import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from def_func.title_name import Title_Name
import matplotlib.pyplot as plt
import seaborn as sns
from streamlit_plotly_events import plotly_events

# cache management
if 'selected_league' not in st.session_state:
    st.session_state.selected_league = None

# tabs management
tab1, tab2 = st.tabs(["Main", "Club Details"])

# into different tabs
with tab1:
    st.title("⚽ Football Stats Explorer ")
    st.info("Note: Top 5 League only.")

    main = pd.read_parquet('cleaned_data/t5_league_clubs.parquet', engine='pyarrow')
    main = main[main['last_season']>=2024]
    # st.write(main.head())

    league_summary = main.groupby('competition_code').agg({
        'total_market_value': 'sum',
        'net_transfer_Mil': 'sum',
        'squad_size': 'mean',
        'foreigners_percentage': 'mean',
        'average_age': 'mean'
    }).reset_index()


    bar_colors = ['#3D195B', '#ff4b44', '#00A346', '#D3010C', '#CDFB0A']

    league_summary = league_summary.sort_values(by=['total_market_value'], ascending=[False])

    col1, col2, col3 = st.columns([2, 1, 2])
    # Calculate highest market value league
    high_mv_league = league_summary.iloc[0]['competition_code']
    high_mv = league_summary.iloc[0]['total_market_value'] - league_summary.iloc[1]['total_market_value']

    # Calculate youngest league (lowest avg age)
    youngest_league = league_summary.loc[league_summary['average_age'].idxmin(), 'competition_code']
    youngest_age = league_summary['average_age'].min()

    # locality of each league
    local_league = league_summary.loc[league_summary['foreigners_percentage'].idxmin(), 'competition_code']
    highest_locality = 100 - league_summary['foreigners_percentage'].min()

    title_obj = Title_Name()
    with col1:
        st.metric(
            label="🏆 Highest Market Value League",
            value=title_obj.title_word(high_mv_league),
            delta=f"{high_mv / 1000000:,.0f} M€ ahead"
        )

    with col2:
        st.metric(
            label="🧒 Youngest League",
            value=title_obj.title_word(youngest_league),
            delta=f"{youngest_age:.1f} yrs",
        )

    with col3:
        st.metric(
            label="⚓ Most Localised League (%)",
            value=title_obj.title_word(local_league),
            delta=f"{highest_locality:.1f}%"
        )

    col1, col2 = st.columns([1, 1])
    best_net_transfer = league_summary.loc[league_summary['net_transfer_Mil'].idxmax(), 'competition_code']
    high_net_transfer = league_summary['net_transfer_Mil'].max()

    worst_net_transfer = league_summary.loc[league_summary['net_transfer_Mil'].idxmin(), 'competition_code']
    low_net_transfer = league_summary['net_transfer_Mil'].min()

    with col1:
        st.metric(
            label="🤑 Best Net Transfer",
            value=title_obj.title_word(best_net_transfer),
            delta=f"{high_net_transfer:,.0f} M€"
        )
    
    with col2:
        st.metric(
            label="💸 Worst Net Transfer",
            value=title_obj.title_word(worst_net_transfer),
            delta=f"{low_net_transfer:,.0f} M€"
        )

    fig = go.Figure()

    # Bar for Market Value
    fig.add_trace(
        go.Bar(
            x=league_summary['competition_code'],
            y=league_summary['total_market_value'],
            name='Total Market Value (Bil€)',
            yaxis='y1',
            marker_color=bar_colors,
            # hover_data=['squad_size', 'average_age'],
        )
    )

    # Line for Foreign Players %
    fig.add_trace(
        go.Scatter(
            x=league_summary['competition_code'],
            y=league_summary['foreigners_percentage'],
            name='Foreign Player %',
            yaxis='y2',
            mode='lines+markers',
            line=dict(color='white')
        )
    )

    fig.update_layout(
        title='League Market Value vs Foreign Player Percentage',
        xaxis=dict(title='League'),
        yaxis=dict(
            title='Total Market Value (Bil€)',
            side='left'
        ),
        yaxis2=dict(
            title='Foreign Player %',
            overlaying='y',
            side='right',
            range=[0, 100],
            showgrid=False
        ),
        legend=dict(x=0.5, y=1.1, orientation='h'),
        height=600
    )

    st.plotly_chart(fig)

    # Part 2 of first page
    st.subheader("🔎 League Market Value Distribution")

    selected_league = st.selectbox(
        "Select a League",
        options=main['competition_code'].unique()
    )

    with open('cleaned_data/competitions.json') as f:
        league_logos = json.load(f)
    
    league_club_data = main[main['competition_code'] == selected_league]
    league_club_data = league_club_data.sort_values(by='total_market_value', ascending=False)
    league_club_data['value_pct'] = league_club_data['total_market_value'] / league_club_data['total_market_value'].sum()

    league_club_data.loc[:, 'club_code'] = league_club_data['club_code'].apply(title_obj.title_word)

    selected_logo_url = league_logos.get(selected_league, None)

    fig_pie = px.pie(
        league_club_data,
        names='club_code',
        values='total_market_value',
        title=f"Market Value Distribution - {title_obj.title_word(selected_league)}",
        hole=0.4
    )

    fig_pie.update_traces(
        textinfo='none',
        hovertemplate='%{label}: %{percent}',  # Still show on hover
        texttemplate=[
            f'{label}<br>{percent:.1%}' if pct >= 0.05 else ''
            for label, percent, pct in zip(
                league_club_data['club_code'],
                league_club_data['value_pct'],
                league_club_data['value_pct']
            )
        ],
        insidetextorientation='auto'
    )

    fig_pie.update_layout(
        xaxis=dict(scaleanchor="y", scaleratio=1),
        yaxis=dict(scaleanchor="x", scaleratio=1)
    )

    fig_pie.add_shape(
        type="circle",
        xref="paper", yref="paper",
        x0=0.3, y0=0.3, x1=0.7, y1=0.7,
        fillcolor="white",
        line_color="white",
        layer="below"
    )

    if selected_logo_url:
        fig_pie.add_layout_image(
            dict(
                source=selected_logo_url,
                xref="paper", yref="paper",
                x=0.5, y=0.5,  # center of the pie
                sizex=0.3, sizey=0.3,  # size of the logo
                xanchor="center",
                yanchor="middle",
                layer="above"  # on top
            )
        )

    st.plotly_chart(fig_pie)


    # Part 3: Spending
    st.subheader("💰 Net Transfers by League")

    keep = [
        'club_code', 'name', 'competition_code', 'net_transfer_sign', 'net_transfer_value', 'net_transfer_Mil'
    ]
    league_net_tx = main[main['competition_code'] == selected_league][keep]
    spenders = league_net_tx[league_net_tx.net_transfer_Mil < 0].sort_values(by='net_transfer_Mil', ascending=False) \
        .head(5)
    earners = league_net_tx[league_net_tx.net_transfer_Mil > 0].sort_values(by='net_transfer_Mil', ascending=False) \
        .head(5)
    
    top10 = pd.concat([spenders, earners])
    top10['type'] = top10.net_transfer_Mil.apply(lambda x: 'Spender' if x < 0 else 'Earner')
    top10.loc[:, 'club_code'] = top10['club_code'].apply(title_obj.title_word)

    fig_net = px.bar(
        top10,
        x='net_transfer_Mil',
        y='club_code',
        orientation='h',
        color='type',
        color_discrete_map={'Spender':'crimson', 'Earner':'seagreen'},
        title=f"Top 5 Spenders vs Top 5 Earners (Net Transfer) in {title_obj.title_word(selected_league)}",
        labels={'net_transfer_Mil':'Net Transfer (M€)', 'club_code': 'Club'}
    )

    fig_net.update_layout(
        yaxis={'categoryorder': 'total ascending'},
        xaxis_tickformat=',.0f'
    )

    st.plotly_chart(fig_net)





with tab2:
    st.subheader("Club Details")

    st.info("Still under maintenance.")

# fig = px.bar(
#     league_summary,
#     x='competition_code',
#     y='total_market_value',
#     hover_data=['squad_size', 'foreigners_percentage', 'average_age'],
#     color='competition_code',
#     labels={'competition_code': 'League', 'total_market_value': 'Total Market Value (Bil€)'},
#     title='Total Market Value by League'
# )

# px.bar(league_counts, x='League', y='Number of Clubs')
# Create interactive Plotly chart
# fig = px.bar(
#     league_counts,
#     x='League',
#     y='Number of Clubs',
#     color='League',
#     title='Clubs per League',
#     labels={'Number of Clubs': 'Clubs'},
#     # hover_data={'League': True, 'Number of Clubs': True}
# )
