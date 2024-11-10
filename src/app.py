# First imports
import sys
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import os
import plotly.express as px
import plotly.graph_objects as go

# Debug prints
print("Starting app initialization...")
print("Python version:", sys.version)

init_db()

# First Streamlit command
st.set_page_config(page_title="Recruitment Analytics", layout="wide")

# Custom CSS for styling
st.markdown("""
    <style>
    .stApp {
        background-color: #f8f9fa;
    }
    div[data-testid="stMetricValue"] {
        font-size: 24px;
        color: #0066cc;
    }
    div[data-testid="stMetricDelta"] {
        font-size: 14px;
    }
    div[data-testid="metric-container"] {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin: 10px 0;
    }
    .chart-container {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin: 10px 0;
    }
    .header-container {
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 10px;
        background: linear-gradient(90deg, #0066cc 0%, #0099ff 100%);
        color: white;
    }
    .metric-row {
        display: flex;
        justify-content: space-between;
        margin: 1rem 0;
    }
    /* Upload History styling */
    .file-record {
        background-color: white;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
        border-left: 3px solid #0066cc;
    }
    
    /* Success messages styling */
    div.stSuccess {
        padding: 1rem;
        border-radius: 0.5rem;
    }
    
    /* Enhanced section headers */
    h2 {
        padding: 0.5rem 0;
        border-bottom: 2px solid #0066cc;
        margin-bottom: 1.5rem;
    }
    
    /* Card-like styling for metric containers */
    div[data-testid="metric-container"] {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-top: 3px solid #0066cc;
    }
    
    /* Chart container styling */
    .plot-container {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin: 1rem 0;
    }
    
    /* Table styling */
    div[data-testid="stDataFrame"] {
        background-color: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# Custom header
st.markdown("""
    <div class="header-container">
        <h1 style='color: white;'>Ryz Labs Recruitment Analytics Dashboard</h1>
    </div>
    """, unsafe_allow_html=True)

# Database functions (keep your existing ones)
def get_db_path():
    # For local development, use file-based database
    if os.getenv('STREAMLIT_SHARING') != 'true':
        return os.path.abspath('recruitment_data.db')
    # For Streamlit Cloud, use in-memory database
    return ':memory:'

def init_db():
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    
    # Create recruitment_data table if it doesn't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS recruitment_data (
            candidate_name TEXT,
            interview_date TEXT,
            interviewer TEXT,
            feedback_form TEXT,
            overall_score TEXT,
            candidate_origin TEXT,
            candidate_owner_name TEXT,
            posting_title TEXT
        )
    ''')
    
    # Create file_uploads table if it doesn't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS file_uploads (
            filename TEXT PRIMARY KEY,
            upload_timestamp DATETIME,
            record_count INTEGER
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_count():
    conn = sqlite3.connect(get_db_path())  # NEW VERSION using get_db_path()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM recruitment_data")
        count = cursor.fetchone()[0]
        return count
    finally:
        conn.close()

def reset_database():
    try:
        db_path = get_db_path()
        if db_path != ':memory:' and os.path.exists(db_path):
            os.remove(db_path)
        init_db()
        st.session_state.clear()
        return True, "Database completely reset"
    except Exception as e:
        return False, f"Error resetting database: {str(e)}"

def save_to_db(df):
    df_to_save = df.rename(columns={
        'Candidate Name': 'candidate_name',
        'Interview Date TZ': 'interview_date',
        'Interviewer': 'interviewer',
        'Feedback Form': 'feedback_form',
        'Overall Score': 'overall_score',
        'Candidate Origin': 'candidate_origin',
        'Candidate Owner Name': 'candidate_owner_name',
        'Posting Title': 'posting_title'
    })
    
    conn = sqlite3.connect(get_db_path())  # NEW VERSION using get_db_path()
    df_to_save.to_sql('recruitment_data', conn, if_exists='append', index=False)
    conn.close()
    
    count = get_db_count()
    return True, f"Data saved successfully. Total records: {count}"

def load_from_db():
    conn = sqlite3.connect(get_db_path())  # NEW VERSION using get_db_path()
    try:
        df = pd.read_sql_query("SELECT * FROM recruitment_data", conn)
        df = df.rename(columns={
            'candidate_name': 'Candidate Name',
            'interview_date': 'Interview Date TZ',
            'interviewer': 'Interviewer',
            'feedback_form': 'Feedback Form',
            'overall_score': 'Overall Score',
            'candidate_origin': 'Candidate Origin',
            'candidate_owner_name': 'Candidate Owner Name',
            'posting_title': 'Posting Title'
        })
        return df
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        return pd.DataFrame()
    finally:
        conn.close()

def save_file_record(filename, record_count):
    conn = sqlite3.connect(get_db_path())
    try:
        c = conn.cursor()
        # Use REPLACE to handle duplicates
        c.execute('''
            INSERT OR REPLACE INTO file_uploads (filename, upload_timestamp, record_count)
            VALUES (?, datetime('now', 'localtime'), ?)
        ''', (filename, record_count))
        conn.commit()
    except Exception as e:
        print(f"Error saving file record: {str(e)}")
    finally:
        conn.close()

def get_uploaded_files():
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    c.execute('SELECT filename, upload_timestamp, record_count FROM file_uploads ORDER BY upload_timestamp DESC')
    files = c.fetchall()
    conn.close()
    return files

def remove_file_record(filename):
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    c.execute('DELETE FROM file_uploads WHERE filename = ?', (filename,))
    conn.commit()
    conn.close()

# Metrics calculation functions
def get_recruiter_screen_metrics(df, weeks_to_show=4):
    """Calculate recruiter screen metrics for the last n weeks"""
    df['Interview Date TZ'] = pd.to_datetime(df['Interview Date TZ'])
    df['Week'] = df['Interview Date TZ'].dt.strftime('%Y-W%V')
    
    recruiter_screens = df[
        df['Feedback Form'].str.contains('Recruiter Screen', case=False, na=False) &
        ~df['Interviewer'].isin(['Sam Nadler', 'Jordan Metzner'])
    ].copy()
    
    latest_weeks = sorted(recruiter_screens['Week'].unique())[-weeks_to_show:]
    
    weekly_metrics = recruiter_screens[recruiter_screens['Week'].isin(latest_weeks)].groupby(
        ['Week', 'Interviewer']
    ).agg({
        'Candidate Name': 'count',
        'Overall Score': lambda x: sum(pd.to_numeric(x, errors='coerce') >= 3)
    }).reset_index()
    
    weekly_metrics.columns = ['Week', 'Recruiter', 'Total Screens', 'Passes']
    weekly_metrics['Pass Rate'] = (weekly_metrics['Passes'] / weekly_metrics['Total Screens'] * 100).round(1)
    
    return weekly_metrics

def get_onsite_conversion_metrics(df, weeks_to_show=4):
    """Calculate onsite interview conversion rates per recruiter"""
    df['Interview Date TZ'] = pd.to_datetime(df['Interview Date TZ'])
    df['Week'] = df['Interview Date TZ'].dt.strftime('%Y-W%V')
    
    recruiter_screens = df[df['Feedback Form'].str.contains('Recruiter Screen', case=False, na=False)].copy()
    onsite_interviews = df[df['Interviewer'].isin(['Sam Nadler', 'Jordan Metzner'])].copy()
    
    latest_weeks = sorted(df['Week'].unique())[-weeks_to_show:]
    
    metrics = []
    for week in latest_weeks:
        for recruiter in recruiter_screens['Interviewer'].unique():
            if recruiter not in ['Sam Nadler', 'Jordan Metzner']:
                week_screens = len(recruiter_screens[
                    (recruiter_screens['Week'] == week) & 
                    (recruiter_screens['Interviewer'] == recruiter)
                ])
                week_onsites = len(onsite_interviews[
                    (onsite_interviews['Week'] == week) & 
                    (onsite_interviews['Candidate Name'].isin(
                        recruiter_screens[recruiter_screens['Interviewer'] == recruiter]['Candidate Name']
                    ))
                ])
                metrics.append({
                    'Week': week,
                    'Recruiter': recruiter,
                    'Screens': week_screens,
                    'Onsites': week_onsites,
                    'Conversion': round(week_onsites/week_screens*100 if week_screens > 0 else 0, 1)
                })
    
    return pd.DataFrame(metrics)

def get_source_metrics(df, weeks_to_show=4):
    """Calculate applied vs sourced ratios"""
    df['Interview Date TZ'] = pd.to_datetime(df['Interview Date TZ'])
    df['Week'] = df['Interview Date TZ'].dt.strftime('%Y-W%V')
    
    latest_weeks = sorted(df['Week'].unique())[-weeks_to_show:]
    
    source_metrics = df[df['Week'].isin(latest_weeks)].groupby(['Week', 'Candidate Origin']).size().reset_index()
    source_metrics.columns = ['Week', 'Source', 'Count']
    
    return source_metrics

def get_time_to_hire_metrics(df, weeks_to_show=4):
    """Calculate time between recruiter screen and onsite"""
    df['Interview Date TZ'] = pd.to_datetime(df['Interview Date TZ'])
    df['Week'] = df['Interview Date TZ'].dt.strftime('%Y-W%V')
    
    recruiter_screens = df[df['Feedback Form'].str.contains('Recruiter Screen', case=False, na=False)]
    onsites = df[df['Interviewer'].isin(['Sam Nadler', 'Jordan Metzner'])]
    
    metrics = []
    for _, screen in recruiter_screens.iterrows():
        candidate_onsite = onsites[onsites['Candidate Name'] == screen['Candidate Name']]
        if not candidate_onsite.empty:
            time_to_onsite = (candidate_onsite['Interview Date TZ'].iloc[0] - screen['Interview Date TZ']).days
            metrics.append({
                'Week': screen['Week'],
                'Recruiter': screen['Interviewer'],
                'Time to Onsite': time_to_onsite
            })
    
    return pd.DataFrame(metrics)

def get_quality_metrics(df, weeks_to_show=4):
    """Calculate quality metrics for recruiters"""
    df['Interview Date TZ'] = pd.to_datetime(df['Interview Date TZ'])
    df['Week'] = df['Interview Date TZ'].dt.strftime('%Y-W%V')
    
    latest_weeks = sorted(df['Week'].unique())[-weeks_to_show:]
    
    recruiter_screens = df[
        df['Feedback Form'].str.contains('Recruiter Screen', case=False, na=False) &
        df['Week'].isin(latest_weeks)
    ]
    
    metrics = recruiter_screens.groupby('Interviewer').agg({
        'Overall Score': lambda x: sum(pd.to_numeric(x, errors='coerce') >= 4) / len(x) * 100  # % of high scores (4+)
    }).round(1)
    
    return metrics

# Add this function to get the Monday date for a week
def get_monday_date(df):
    """Get the Monday date for the latest week"""
    latest_date = pd.to_datetime(df['Interview Date TZ']).max()
    monday = latest_date - pd.Timedelta(days=latest_date.weekday())
    return monday.strftime('%B %d, %Y')

# Add function for onsite interview metrics
def get_onsite_interview_metrics(df, weeks_to_show=4):
    """Calculate onsite interview metrics for Sam and Jordan"""
    df = df.copy()
    
    # Ensure we have Week column
    if 'Week' not in df.columns:
        df['Interview Date TZ'] = pd.to_datetime(df['Interview Date TZ'])
        df['Week'] = df['Interview Date TZ'].dt.strftime('%Y-W%V')
    
    # Get only onsite interviews by Sam and Jordan
    onsite_interviews = df[
        (df['Interviewer'].isin(['Sam Nadler', 'Jordan Metzner'])) &
        (~df['Feedback Form'].str.contains('Recruiter Screen', case=False, na=False))  # Exclude recruiter screens
    ].copy()
    
    # Get the latest weeks
    latest_weeks = sorted(df['Week'].unique())[-weeks_to_show:]
    
    # Group by week and interviewer
    weekly_metrics = onsite_interviews[
        onsite_interviews['Week'].isin(latest_weeks)
    ].groupby(['Week', 'Interviewer']).agg({
        'Candidate Name': 'count'  # Count unique interviews
    }).reset_index()
    
    weekly_metrics.columns = ['Week', 'Interviewer', 'Total Onsites']
    
    return weekly_metrics

# Add this function to determine the star recruiter
def get_star_recruiter(metrics_df):
    """Returns the recruiter with the most screens"""
    if metrics_df.empty:
        return None
    return metrics_df.loc[metrics_df['Total Screens'].idxmax(), 'Recruiter']

# Update emoji mapping to be dynamic
def get_recruiter_emoji(recruiter, star_recruiter):
    """Returns appropriate emoji for each recruiter"""
    if recruiter == star_recruiter:
        return '⭐'  # Star for the leader
    emoji_map = {
        'Recruiter1': '🚀',
        'Recruiter2': '🌟',
        'Recruiter3': '💫',
        'Recruiter4': '✨',
        'Default': '👩‍💼'
    }
    return emoji_map.get(recruiter, emoji_map['Default'])

# Initialize database
init_db()

# Near the top of your file, after imports
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame()

# Sidebar for data management
with st.sidebar:
    st.header("Data Management")
    
    # Show current database status
    db_count = get_db_count()
    st.write(f"Current records in database: {db_count}")
    
    # File uploader
    uploaded_file = st.file_uploader("Upload Data", type=['csv'], key="data_upload")
    if uploaded_file is not None:
        # Load new data
        new_df = pd.read_csv(uploaded_file)
        
        # Convert dates to datetime for comparison
        new_df['Interview Date TZ'] = pd.to_datetime(new_df['Interview Date TZ'])
        
        # Load existing data
        existing_df = load_from_db()
        if not existing_df.empty:
            existing_df['Interview Date TZ'] = pd.to_datetime(existing_df['Interview Date TZ'])
        
        if existing_df.empty:
            # First upload (historical data)
            df_to_save = new_df
            success, message = save_to_db(df_to_save)
            if success:
                # Save file record
                save_file_record(uploaded_file.name, len(df_to_save))
        else:
            # Get the latest date in existing data
            latest_date = existing_df['Interview Date TZ'].max()
            
            # Only add records that are newer than existing data
            new_records = new_df[new_df['Interview Date TZ'] > latest_date]
            
            if len(new_records) > 0:
                success, message = save_to_db(new_records)
                if success:
                    # Save file record
                    save_file_record(uploaded_file.name, len(new_records))
                st.write(f"Added {len(new_records)} new records")
            else:
                st.warning("No new records to add")
                success = True
                message = "No new records to add"
        
        if success:
            st.success(message)
    
    # Database management - only one reset button
    st.subheader("Database Management")
    if st.button("Reset Database", type="primary"):
        success, message = reset_database()
        if success:
            st.success(message)
            st.rerun()
        else:
            st.error(message)

    # Upload History
    st.subheader("Upload History")
    uploaded_files = get_uploaded_files()
    
    if uploaded_files:
        for filename, timestamp, record_count in uploaded_files:
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"""
                        <div class='file-record'>
                        📄 <b>{filename}</b><br>
                        🕒 {timestamp}<br>
                        📊 {record_count} records
                        </div>
                    """, unsafe_allow_html=True)
                with col2:
                    if st.button("🗑️", key=f"delete_{filename}"):
                        remove_file_record(filename)
                        st.rerun()
    else:
        st.text("No files uploaded yet")

# Load and display data
df = load_from_db()
if not df.empty:
    # Prepare the data - add Week column
    df['Interview Date TZ'] = pd.to_datetime(df['Interview Date TZ'])
    df['Week'] = df['Interview Date TZ'].dt.strftime('%Y-W%V')

    # Calculate all metrics first
    latest_metrics = get_recruiter_screen_metrics(df, weeks_to_show=1)
    prev_metrics = get_recruiter_screen_metrics(df, weeks_to_show=2)
    onsite_metrics = get_onsite_conversion_metrics(df, weeks_to_show=1)
    onsite_interview_metrics = get_onsite_interview_metrics(df, weeks_to_show=1)
    
    # Calculate current week totals
    total_screens = latest_metrics['Total Screens'].sum()
    avg_pass_rate = latest_metrics['Pass Rate'].mean()
    total_onsites = onsite_interview_metrics['Total Onsites'].sum()
    conversion_rate = onsite_metrics['Conversion'].mean()
    
    # Calculate previous week totals
    prev_week_metrics = prev_metrics[prev_metrics['Week'] != latest_metrics['Week'].iloc[0]]
    prev_week_screens = prev_week_metrics['Total Screens'].sum()
    prev_week_pass_rate = prev_week_metrics['Pass Rate'].mean()
    
    prev_week_onsites = get_onsite_interview_metrics(df, weeks_to_show=2)
    prev_week_onsites = prev_week_onsites[prev_week_onsites['Week'] != latest_metrics['Week'].iloc[0]]['Total Onsites'].sum()
    
    prev_week_conversion = get_onsite_conversion_metrics(df, weeks_to_show=2)
    prev_week_conversion = prev_week_conversion[prev_week_conversion['Week'] != latest_metrics['Week'].iloc[0]]['Conversion'].mean()

    # Get the Monday date for the latest week
    latest_week = sorted(df['Week'].unique())[-1]
    latest_date = pd.to_datetime(df['Interview Date TZ']).max()
    monday_date = latest_date - pd.Timedelta(days=latest_date.weekday())
    monday_str = monday_date.strftime('%B %d, %Y')

    # Source Distribution with Monday date
    st.markdown(f"<h2 style='color: #0066cc;'>Source Distribution (Week of {monday_str})</h2>", unsafe_allow_html=True)
    source_by_week = df.groupby(['Week', 'Candidate Origin']).size().reset_index(name='Count')
    
    # Calculate total by week for trend line
    total_by_week = source_by_week.groupby('Week')['Count'].sum().reset_index()
    
    # Create stacked bar chart with trend line
    fig_source = go.Figure()
    
    # Add stacked bars
    for source in source_by_week['Candidate Origin'].unique():
        source_data = source_by_week[source_by_week['Candidate Origin'] == source]
        fig_source.add_trace(go.Bar(
            x=source_data['Week'],
            y=source_data['Count'],
            name=source,
            text=source_data['Count'],
            textposition='auto',
        ))
    
    # Add trend line
    fig_source.add_trace(go.Scatter(
        x=total_by_week['Week'],
        y=total_by_week['Count'],
        name='Total Trend',
        line=dict(color='red', width=2),
        mode='lines+markers'
    ))
    
    fig_source.update_layout(
        height=300,
        barmode='stack',
        xaxis_title="Week",
        yaxis_title="Number of Candidates",
        title='Weekly Candidate Source Distribution',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    st.plotly_chart(fig_source, use_container_width=True, key="source_dist")

    # Recruiter Performance with Monday date
    st.markdown(f"<h2 style='color: #0066cc;'>Recruiter Performance (Week of {monday_str})</h2>", unsafe_allow_html=True)
    
    # Overall metrics first (previously Weekly Summary)
    st.markdown("<h3>Overall Performance</h3>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "Total Screens This Week",
            f"{total_screens}",
            f"{total_screens - prev_week_screens:+d} vs prev week"
        )
    with col2:
        st.metric(
            "Average Pass Rate",
            f"{avg_pass_rate:.1f}%",
            f"{avg_pass_rate - prev_week_pass_rate:+.1f}% vs prev week"
        )
    with col3:
        st.metric(
            "Total Onsite Interviews",
            f"{total_onsites}",
            f"{total_onsites - prev_week_onsites:+d} vs prev week"
        )
    with col4:
        st.metric(
            "Avg Onsite Conversion",
            f"{conversion_rate:.1f}%",
            f"{conversion_rate - prev_week_conversion:+.1f}% vs prev week"
        )

    # Individual recruiter metrics
    st.markdown("<h3>Individual Performance</h3>", unsafe_allow_html=True)
    
    # Get star recruiter (most screens)
    star_recruiter = get_star_recruiter(latest_metrics)
    
    for recruiter in latest_metrics['Recruiter'].unique():
        # Get emoji for recruiter (star for leader, different emoji for others)
        emoji = get_recruiter_emoji(recruiter, star_recruiter)
        st.markdown(f"<h3>{emoji} {recruiter}</h3>", unsafe_allow_html=True)
        
        # Get current and previous week data for this recruiter
        current_data = latest_metrics[latest_metrics['Recruiter'] == recruiter]
        prev_data = prev_metrics[
            (prev_metrics['Recruiter'] == recruiter) & 
            (prev_metrics['Week'] != latest_metrics['Week'].iloc[0])
        ]
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            current_screens = current_data['Total Screens'].iloc[0]
            prev_screens = prev_data['Total Screens'].iloc[0] if not prev_data.empty else 0
            st.metric(
                "Screens",
                current_screens,
                f"{current_screens - prev_screens:+d} vs prev week"
            )
        with col2:
            current_pass = current_data['Pass Rate'].iloc[0]
            prev_pass = prev_data['Pass Rate'].iloc[0] if not prev_data.empty else 0
            st.metric(
                "Pass Rate",
                f"{current_pass:.1f}%",
                f"{current_pass - prev_pass:+.1f}% vs prev week"
            )
        with col3:
            current_onsite = onsite_metrics[onsite_metrics['Recruiter'] == recruiter]['Onsites'].sum()
            prev_onsite = get_onsite_conversion_metrics(df, weeks_to_show=2)
            prev_onsite = prev_onsite[
                (prev_onsite['Recruiter'] == recruiter) & 
                (prev_onsite['Week'] != latest_metrics['Week'].iloc[0])
            ]['Onsites'].sum()
            st.metric(
                "Onsite Interviews",
                current_onsite,
                f"{current_onsite - prev_onsite:+d} vs prev week"
            )
        with col4:
            current_conv = onsite_metrics[onsite_metrics['Recruiter'] == recruiter]['Conversion'].mean()
            prev_conv = get_onsite_conversion_metrics(df, weeks_to_show=2)
            prev_conv = prev_conv[
                (prev_conv['Recruiter'] == recruiter) & 
                (prev_conv['Week'] != latest_metrics['Week'].iloc[0])
            ]['Conversion'].mean()
            st.metric(
                "Onsite Conversion",
                f"{current_conv:.1f}%",
                f"{current_conv - prev_conv:+.1f}% vs prev week"
            )

    # Trend Analysis with proper charts and time periods
    st.markdown("<h2 style='color: #0066cc;'>Trend Analysis</h2>", unsafe_allow_html=True)
    weeks_to_show = st.selectbox(
        "Select Time Period",
        options=[4, 8, 12],
        format_func=lambda x: f"Last {x} Weeks",
        key="trend_weeks"
    )

    # Weekly Screens by Recruiter
    trend_metrics = get_recruiter_screen_metrics(df, weeks_to_show=weeks_to_show)
    fig_screens = px.line(
        trend_metrics,
        x='Week',
        y='Total Screens',
        color='Recruiter',
        title='Weekly Screens by Recruiter',
        markers=True
    )
    st.plotly_chart(fig_screens, use_container_width=True, key="screens_trend")

    # Weekly Onsite Interviews by Recruiter (using selected time period)
    all_weeks = sorted(df['Week'].unique())
    latest_n_weeks = all_weeks[-weeks_to_show:]  # Use the selected time period
    
    # Create a base dataframe with all recruiter/week combinations
    recruiters = df[
        (df['Feedback Form'].str.contains('Recruiter Screen', case=False, na=False)) & 
        (~df['Interviewer'].isin(['Sam Nadler', 'Jordan Metzner']))
    ]['Interviewer'].unique()
    
    week_recruiter_combos = pd.MultiIndex.from_product(
        [latest_n_weeks, recruiters],  # Use latest_n_weeks instead of latest_four_weeks
        names=['Week', 'Recruiter']
    ).to_frame(index=False)
    
    # Get onsite interviews for the selected period
    onsite_data = df[
        (df['Week'].isin(latest_n_weeks)) &  # Use latest_n_weeks
        (df['Interviewer'].isin(['Sam Nadler', 'Jordan Metzner']))
    ].copy()
    
    # Count onsites by week and original recruiter
    weekly_onsites = []
    for week in latest_n_weeks:  # Use latest_n_weeks
        week_onsites = onsite_data[onsite_data['Week'] == week]
        for recruiter in recruiters:
            recruiter_candidates = df[
                (df['Interviewer'] == recruiter) &
                (df['Feedback Form'].str.contains('Recruiter Screen', case=False, na=False))
            ]['Candidate Name'].unique()
            
            onsite_count = len(week_onsites[
                week_onsites['Candidate Name'].isin(recruiter_candidates)
            ])
            
            weekly_onsites.append({
                'Week': week,
                'Recruiter': recruiter,
                'Onsites': onsite_count
            })
    
    onsite_df = pd.DataFrame(weekly_onsites)
    full_onsite_data = week_recruiter_combos.merge(
        onsite_df,
        on=['Week', 'Recruiter'],
        how='left'
    ).fillna(0)
    
    # Create the visualization with legend on the right
    fig_recruiter_onsites = px.line(
        full_onsite_data,
        x='Week',
        y='Onsites',
        color='Recruiter',
        title=f'Weekly Onsite Interviews by Recruiter (Last {weeks_to_show} Weeks)',
        markers=True
    )
    
    fig_recruiter_onsites.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(
            orientation="v",  # Changed to vertical
            yanchor="top",   # Anchor to top
            y=1,            # Position at top
            xanchor="right", # Anchor to right
            x=1.15          # Move slightly outside the plot
        ),
        xaxis=dict(
            tickmode='array',
            ticktext=latest_n_weeks,
            tickvals=latest_n_weeks
        )
    )
    st.plotly_chart(fig_recruiter_onsites, use_container_width=True, key="recruiter_onsites_trend")

    # Weekly Onsite Interviews (Sam & Jordan)
    onsite_trend = get_onsite_interview_metrics(df, weeks_to_show=weeks_to_show)
    fig_onsites = px.line(
        onsite_trend,
        x='Week',
        y='Total Onsites',
        color='Interviewer',
        title='Weekly Onsite Interviews (Sam & Jordan)',
        markers=True
    )
    st.plotly_chart(fig_onsites, use_container_width=True, key="sam_jordan_trend")

    # Detailed Metrics Table
    st.markdown("<h2 style='color: #0066cc;'>Detailed Metrics</h2>", unsafe_allow_html=True)
    
    # Get all recruiter screen metrics
    all_screen_metrics = get_recruiter_screen_metrics(df, weeks_to_show=weeks_to_show)
    
    # Get all onsite conversion metrics
    all_onsite_metrics = get_onsite_conversion_metrics(df, weeks_to_show=weeks_to_show)
    
    # Merge the metrics
    detailed_metrics = pd.merge(
        all_screen_metrics,
        all_onsite_metrics[['Week', 'Recruiter', 'Onsites', 'Conversion']],
        on=['Week', 'Recruiter'],
        how='left'
    )
    
    # Fill NaN values with 0 for Onsites and format properly
    detailed_metrics['Onsites'] = detailed_metrics['Onsites'].fillna(0).astype(int)
    detailed_metrics['Conversion'] = detailed_metrics['Conversion'].fillna(0).round(1)
    
    # Sort by Week (descending) and Recruiter
    detailed_metrics_sorted = detailed_metrics.sort_values(
        ['Week', 'Recruiter'], 
        ascending=[False, True]
    )
    
    # Display the table
    st.dataframe(
        detailed_metrics_sorted[[
            'Week', 'Recruiter', 'Total Screens', 'Passes', 
            'Pass Rate', 'Onsites', 'Conversion'
        ]],
        hide_index=True
    )
else:
    st.warning("No data available. Please upload some data to get started.")