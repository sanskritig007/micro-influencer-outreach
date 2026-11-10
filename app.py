"""Enterprise Influencer Outreach & Qualification System.
Modern minimal SaaS UI inspired by high-end influencer marketing platforms.
Natural full-page scrolling without nested box containers.
"""

import json
from pathlib import Path
import pandas as pd
import streamlit as st

from src.config import (
    DATA_DIR,
    FILTERED_DATA_PATH,
    GEMINI_API_KEY,
    MAX_FOLLOWERS,
    MIN_FOLLOWERS,
    OUTREACH_TRACKER_PATH,
    RAW_DATA_PATH,
    TARGET_NICHE,
    YOUTUBE_API_KEY,
)
from src.personalization.generator import count_words, generate_pitch_for_influencer
from src.sending.dispatcher import dispatch_all_pitches, prepare_instagram_dm_workflow
from src.sending.tracker import get_tracker_stats

# Page Configuration
st.set_page_config(
    page_title="Influencer Marketing Platform | EDXSO",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom High-End SaaS Styling (Dribbble Linur inspired, zero nested scrollbars)
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Hide Streamlit Clutter while KEEPING sidebar toggle visible */
    #MainMenu {display: none !important;}
    footer {display: none !important;}
    [data-testid="stToolbar"] {display: none !important;}
    [data-testid="stDecoration"] {display: none !important;}
    .stDeployButton {display: none !important;}

    header {
        background: transparent !important;
        height: 2.5rem !important;
    }

    /* Keep Sidebar Toggle Arrow Button Visible and Accessible */
    [data-testid="collapsedControl"] {
        display: flex !important;
        visibility: visible !important;
        background: #1E293B !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 6px !important;
        color: #FFFFFF !important;
        z-index: 999999 !important;
    }

    /* Main background */
    .stApp {
        background-color: #0B0F17;
        color: #E2E8F0;
    }

    /* Remove Top Header Padding Gap */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
    }

    /* Top Navigation Banner */
    .top-navbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1.2rem 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.07);
        margin-bottom: 1.8rem;
    }
    .brand-title {
        font-size: 1.4rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: #FFFFFF;
    }
    .brand-subtitle {
        font-size: 0.85rem;
        color: #94A3B8;
        margin-top: 2px;
    }

    /* Metric Cards */
    .kpi-card {
        background: #131B2E;
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 10px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 1.2rem;
    }
    .kpi-label {
        font-size: 0.76rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748B;
        font-weight: 600;
        margin-bottom: 0.4rem;
    }
    .kpi-value {
        font-size: 1.7rem;
        font-weight: 700;
        color: #F8FAFC;
        letter-spacing: -0.02em;
    }
    .kpi-subtext {
        font-size: 0.8rem;
        color: #10B981;
        margin-top: 0.3rem;
        font-weight: 500;
    }

    /* Custom Full-Width HTML Table (Zero nested scrolling) */
    .saas-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        margin-top: 1rem;
        margin-bottom: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 8px;
        overflow: hidden;
        background: #0E1526;
    }
    .saas-table th {
        background: #162036;
        color: #94A3B8;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        padding: 12px 16px;
        text-align: left;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }
    .saas-table td {
        padding: 13px 16px;
        font-size: 0.86rem;
        color: #E2E8F0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.04);
        vertical-align: middle;
    }
    .saas-table tr:last-child td {
        border-bottom: none;
    }
    .saas-table tr:hover td {
        background: #151F33;
    }

    /* Status Badges */
    .badge-pill {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.74rem;
        font-weight: 600;
    }
    .badge-pass {
        background: rgba(16, 185, 129, 0.12);
        color: #34D399;
        border: 1px solid rgba(16, 185, 129, 0.25);
    }
    .badge-fail {
        background: rgba(239, 68, 68, 0.12);
        color: #F87171;
        border: 1px solid rgba(239, 68, 68, 0.25);
    }
    .badge-info {
        background: rgba(99, 102, 241, 0.12);
        color: #818CF8;
        border: 1px solid rgba(99, 102, 241, 0.25);
    }

    /* Sidebar Diagnostics */
    section[data-testid="stSidebar"] {
        background-color: #0E1424 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
    }
    .status-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.6rem 0.8rem;
        background: #141D32;
        border-radius: 6px;
        margin-bottom: 0.5rem;
        font-size: 0.82rem;
        border: 1px solid rgba(255, 255, 255, 0.04);
    }
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #10B981;
        display: inline-block;
        margin-right: 6px;
    }

    /* Tab bar minimal */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding-bottom: 0.4rem;
        margin-bottom: 1.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        border: none !important;
        color: #94A3B8 !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
        padding: 0.6rem 1rem !important;
    }
    .stTabs [aria-selected="true"] {
        color: #FFFFFF !important;
        border-bottom: 2px solid #6366F1 !important;
        font-weight: 600 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Sidebar
st.sidebar.markdown("### System Architecture")
st.sidebar.markdown(
    """
    <div style="margin-bottom: 1.2rem;">
        <div class="status-item">
            <span><span class="status-dot"></span>YouTube Data API v3</span>
            <span style="color: #10B981; font-weight: 600;">Connected</span>
        </div>
        <div class="status-item">
            <span><span class="status-dot"></span>Gemini 2.5 Flash</span>
            <span style="color: #10B981; font-weight: 600;">Active</span>
        </div>
        <div class="status-item">
            <span><span class="status-dot"></span>Audit Classification</span>
            <span style="color: #818CF8; font-weight: 600;">Enforced</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown("### Qualification Parameters")
st.sidebar.markdown(f"**Target Vertical:** `{TARGET_NICHE}`")
st.sidebar.markdown(f"**Follower Threshold:** `{MIN_FOLLOWERS:,}` – `{MAX_FOLLOWERS:,}`")
st.sidebar.markdown("**Engagement Benchmark:** `0.05%` (Micro-Tier)")

st.sidebar.divider()
st.sidebar.markdown("### Safe Dispatch Mode")
simulate_toggle = st.sidebar.toggle(
    "Simulation Mode",
    value=True,
    help="Guarantees zero unsolicited external emails during system evaluation.",
)

# Top Brand Header
st.markdown(
    """
    <div class="top-navbar">
        <div>
            <div class="brand-title">EDXSO Influencer Outreach Platform</div>
            <div class="brand-subtitle">Automated discovery, multi-criteria audit qualification, and LLM message synthesis</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Navigation Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "Influencer Discovery",
    "Filtering & Classification",
    "Personalization Studio",
    "Outreach Dispatcher & Log",
])


# ==========================================
# TAB 1: Discovery & Profiles
# ==========================================
with tab1:
    if RAW_DATA_PATH.exists():
        with open(RAW_DATA_PATH, "r", encoding="utf-8") as f:
            raw_profiles = json.load(f)

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(
                f"""<div class="kpi-card"><div class="kpi-label">Discovered Creators</div><div class="kpi-value">{len(raw_profiles)}</div><div class="kpi-subtext">Verified Channels</div></div>""",
                unsafe_allow_html=True,
            )
        with c2:
            avg_subs = int(sum(p["follower_count"] for p in raw_profiles) / max(len(raw_profiles), 1))
            st.markdown(
                f"""<div class="kpi-card"><div class="kpi-label">Average Subscribers</div><div class="kpi-value">{avg_subs:,}</div><div class="kpi-subtext">Discovered Pool</div></div>""",
                unsafe_allow_html=True,
            )
        with c3:
            avg_er = sum(p["engagement_rate"] for p in raw_profiles) / max(len(raw_profiles), 1)
            st.markdown(
                f"""<div class="kpi-card"><div class="kpi-label">Avg Engagement Rate</div><div class="kpi-value">{avg_er:.2f}%</div><div class="kpi-subtext">Recent Video Average</div></div>""",
                unsafe_allow_html=True,
            )
        with c4:
            valid_emails = sum(1 for p in raw_profiles if p["contact_email"] != "Not Found")
            st.markdown(
                f"""<div class="kpi-card"><div class="kpi-label">Business Emails</div><div class="kpi-value">{valid_emails} <span style="font-size: 1rem; color: #64748B;">/ {len(raw_profiles)}</span></div><div class="kpi-subtext">Explicitly Extracted</div></div>""",
                unsafe_allow_html=True,
            )

        # Full-Page Natural Flowing Table (Zero Inner Scroll)
        rows_html = []
        for p in raw_profiles:
            email_val = p["contact_email"]
            email_badge = '<span style="color: #64748B;">Not Found</span>' if email_val == "Not Found" else f'<span style="color: #38BDF8;">{email_val}</span>'
            video_topic = p.get("recent_video_title") or "N/A"
            rows_html.append(f"""<tr>
<td><strong>{p['name']}</strong></td>
<td>{p['follower_count']:,}</td>
<td><span class="badge-pill badge-info">{p['engagement_rate']:.2f}%</span></td>
<td>{email_badge}</td>
<td><span style="color: #94A3B8;">{video_topic[:45]}...</span></td>
<td><a href="{p['profile_url']}" target="_blank" style="color: #818CF8; text-decoration: none; font-weight: 500;">View ↗</a></td>
</tr>""")

        table_html = f"""<table class="saas-table">
<thead>
<tr>
<th style="width: 22%;">Creator / Channel</th>
<th style="width: 14%;">Subscribers</th>
<th style="width: 14%;">Engagement Rate</th>
<th style="width: 20%;">Business Email</th>
<th style="width: 22%;">Latest Video Content</th>
<th style="width: 8%;">Link</th>
</tr>
</thead>
<tbody>
{''.join(rows_html)}
</tbody>
</table>"""
        st.html(table_html)
    else:
        st.warning("Discovery dataset not found.")


# ==========================================
# TAB 2: Filtering & Classification
# ==========================================
with tab2:
    if FILTERED_DATA_PATH.exists():
        with open(FILTERED_DATA_PATH, "r", encoding="utf-8") as f:
            fdata = json.load(f)

        passed = fdata.get("qualified_influencers", [])
        rejected = fdata.get("rejected_influencers", [])
        total_eval = fdata.get("total_evaluated", 0)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                f"""<div class="kpi-card"><div class="kpi-label">Total Evaluated</div><div class="kpi-value">{total_eval}</div><div class="kpi-subtext">Scanned Profiles</div></div>""",
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f"""<div class="kpi-card"><div class="kpi-label">Passed Qualification</div><div class="kpi-value">{len(passed)}</div><div class="kpi-subtext">{len(passed)/max(total_eval, 1)*100:.1f}% Conversion</div></div>""",
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                f"""<div class="kpi-card"><div class="kpi-label">Rejected Candidates</div><div class="kpi-value">{len(rejected)}</div><div class="kpi-subtext">With Audit Trail</div></div>""",
                unsafe_allow_html=True,
            )

        col_seg, col_btn = st.columns([2.5, 1.5])
        with col_seg:
            segment = st.segmented_control(
                "Filter Segment",
                options=[f"Qualified Micro-Influencers ({len(passed)})", f"Rejected Candidates ({len(rejected)})"],
                default=f"Qualified Micro-Influencers ({len(passed)})",
                label_visibility="collapsed",
            )

        with col_btn:
            if "Qualified" in segment:
                # Prepare CSV data for Qualified only
                q_rows = []
                for item in passed:
                    p = item["profile"]
                    q_rows.append({
                        "Name": p["name"], "Followers": p["follower_count"],
                        "Engagement Rate": f"{p['engagement_rate']}%", "Email": p["contact_email"],
                        "Profile URL": p["profile_url"], "Audit Reason": item["audit"]["reasons"][0]
                    })
                q_csv = pd.DataFrame(q_rows).to_csv(index=False).encode("utf-8")
                st.download_button(
                    label=f"Download Qualified Leads ({len(passed)}) CSV",
                    data=q_csv,
                    file_name="qualified_influencers.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            else:
                r_rows = []
                for item in rejected:
                    p = item["profile"]
                    r_rows.append({
                        "Name": p["name"], "Followers": p["follower_count"],
                        "Engagement Rate": f"{p['engagement_rate']}%", "Status": "FAILED",
                        "Audit Reason": item["audit"]["reasons"][0]
                    })
                r_csv = pd.DataFrame(r_rows).to_csv(index=False).encode("utf-8")
                st.download_button(
                    label=f"Download Rejection Audit Log ({len(rejected)}) CSV",
                    data=r_csv,
                    file_name="rejected_audit_log.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

        # Full-Page Natural Flowing Table
        if "Qualified" in segment:
            q_tbody = []
            for item in passed:
                p = item["profile"]
                reason = item["audit"]["reasons"][0]
                q_tbody.append(f"""<tr>
<td><strong>{p['name']}</strong></td>
<td>{p['follower_count']:,}</td>
<td><span class="badge-pill badge-info">{p['engagement_rate']:.2f}%</span></td>
<td>{p['contact_email']}</td>
<td><span class="badge-pill badge-pass">QUALIFIED</span> <span style="font-size: 0.78rem; color: #94A3B8; margin-left: 6px;">{reason}</span></td>
</tr>""")

            t_html = f"""<table class="saas-table">
<thead>
<tr>
<th style="width: 25%;">Creator Name</th>
<th style="width: 15%;">Subscribers</th>
<th style="width: 15%;">Engagement Rate</th>
<th style="width: 20%;">Business Email</th>
<th style="width: 25%;">Audit Verdict</th>
</tr>
</thead>
<tbody>
{''.join(q_tbody)}
</tbody>
</table>"""
            st.html(t_html)

        else:
            r_tbody = []
            for item in rejected:
                p = item["profile"]
                reason = item["audit"]["reasons"][0]
                r_tbody.append(f"""<tr>
<td><strong>{p['name']}</strong></td>
<td>{p['follower_count']:,}</td>
<td>{p['engagement_rate']:.2f}%</td>
<td><span class="badge-pill badge-fail">FAILED</span></td>
<td><span style="color: #F87171; font-size: 0.82rem;">{reason}</span></td>
</tr>""")

            t_html = f"""<table class="saas-table">
<thead>
<tr>
<th style="width: 25%;">Candidate Name</th>
<th style="width: 15%;">Subscribers</th>
<th style="width: 15%;">Engagement Rate</th>
<th style="width: 15%;">Status</th>
<th style="width: 30%;">Audit Explanation</th>
</tr>
</thead>
<tbody>
{''.join(r_tbody)}
</tbody>
</table>"""
            st.html(t_html)


# ==========================================
# TAB 3: Personalization Studio
# ==========================================
with tab3:
    messages_path = DATA_DIR / "personalized_messages.json"
    if messages_path.exists():
        with open(messages_path, "r", encoding="utf-8") as f:
            pitches = json.load(f)

        influencer_names = [p["influencer_name"] for p in pitches]
        selected_name = st.selectbox("Select Target Influencer:", influencer_names)

        current_pitch = next((p for p in pitches if p["influencer_name"] == selected_name), None)

        if current_pitch:
            st.markdown("<br>", unsafe_allow_html=True)
            col_email, col_dm = st.columns([1.2, 0.8])

            with col_email:
                email_body = current_pitch.get("email_pitch", "")
                email_wc = count_words(email_body)
                badge_class = "badge-pass" if 60 <= email_wc <= 90 else "badge-fail"

                st.markdown(
                    f"""
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem;">
                        <span style="font-weight: 600; font-size: 0.95rem;">Email Collaboration Pitch</span>
                        <div>
                            <span class="badge-pill {badge_class}">{email_wc} words (Target: 60-90)</span>
                            <span class="badge-pill badge-info" style="margin-left: 6px;">{current_pitch.get("collaboration_angle")}</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                edited_email = st.text_area("Email Body", value=email_body, height=220, label_visibility="collapsed")

            with col_dm:
                dm_body = current_pitch.get("instagram_dm", "")
                dm_wc = count_words(dm_body)
                dm_badge = "badge-pass" if 15 <= dm_wc <= 30 else "badge-fail"

                st.markdown(
                    f"""
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem;">
                        <span style="font-weight: 600; font-size: 0.95rem;">Instagram Direct Message</span>
                        <span class="badge-pill {dm_badge}">{dm_wc} words (Target: 15-30)</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                edited_dm = st.text_area("DM Text", value=dm_body, height=90, label_visibility="collapsed")

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("**Campaign Customization**")
                custom_notes = st.text_input(
                    "Inject specific promotion points / custom terms:",
                    placeholder="e.g. Early access sandbox invite + 30% affiliate rev-share",
                )

                if st.button("Regenerate Outreach with Gemini LLM", use_container_width=True):
                    with st.spinner("Synthesizing personalized outreach..."):
                        with open(FILTERED_DATA_PATH, "r") as f_f:
                            fdata = json.load(f_f)
                        matched = next(
                            (item["profile"] for item in fdata.get("qualified_influencers", []) if item["profile"]["name"] == selected_name),
                            None
                        )
                        if matched:
                            new_p = generate_pitch_for_influencer(matched, custom_campaign_notes=custom_notes)
                            if new_p:
                                current_pitch["email_pitch"] = new_p.email_pitch
                                current_pitch["email_word_count"] = new_p.email_word_count
                                current_pitch["instagram_dm"] = new_p.instagram_dm
                                current_pitch["dm_word_count"] = new_p.dm_word_count
                                with open(messages_path, "w", encoding="utf-8") as f_out:
                                    json.dump(pitches, f_out, indent=2)
                                st.success("Outreach successfully regenerated with custom terms!")
                                st.rerun()
                            else:
                                st.warning("Gemini rate limit or network busy. Please wait a moment and retry.")


# ==========================================
# TAB 4: Dispatcher & Tracking Log
# ==========================================
with tab4:
    stats = get_tracker_stats()
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""<div class="kpi-card"><div class="kpi-label">Logged Attempts</div><div class="kpi-value">{stats['total_records']}</div><div class="kpi-subtext">Audit History</div></div>""",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""<div class="kpi-card"><div class="kpi-label">Dispatched / Simulated</div><div class="kpi-value">{stats['total_simulated'] + stats['total_sent']}</div><div class="kpi-subtext">Delivered State</div></div>""",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""<div class="kpi-card"><div class="kpi-label">Duplicates Prevented</div><div class="kpi-value">{stats['total_skipped_duplicate']}</div><div class="kpi-subtext">Idempotent Checks</div></div>""",
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f"""<div class="kpi-card"><div class="kpi-label">Skipped (No Email)</div><div class="kpi-value">{stats['total_skipped_no_email']}</div><div class="kpi-subtext">Protected Queues</div></div>""",
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    col_act, col_dl = st.columns([2, 1])

    with col_act:
        mode_text = "Simulation Mode (Safe)" if simulate_toggle else "Live SMTP Delivery"
        st.markdown(f"**Dispatch Engine State:** `{mode_text}`")
        if st.button("Execute Qualified Outreach Batch", type="primary"):
            with st.spinner("Dispatching outreach queue..."):
                results = dispatch_all_pitches(simulate=simulate_toggle)
                st.rerun()

    with col_dl:
        if OUTREACH_TRACKER_PATH.exists():
            with open(OUTREACH_TRACKER_PATH, "rb") as f_t:
                st.download_button(
                    label="Download Outreach Tracker (CSV)",
                    data=f_t,
                    file_name="outreach_tracker.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Outreach Tracking Log (Deliverable D)")

    if OUTREACH_TRACKER_PATH.exists():
        tracker_df = pd.read_csv(OUTREACH_TRACKER_PATH)
        if not tracker_df.empty:
            # Full-Page Natural Flowing Table for Logs
            log_tbody = []
            for _, row in tracker_df.tail(20).iterrows():
                st_val = row["Status"]
                badge_st = "badge-pass" if st_val in ["SENT", "SIMULATED"] else ("badge-fail" if "SKIPPED" in st_val else "badge-info")
                log_tbody.append(f"""<tr>
<td><strong>{row['Influencer']}</strong></td>
<td>{row['Email']}</td>
<td><span class="badge-pill {badge_st}">{st_val}</span></td>
<td><span style="color: #94A3B8; font-size: 0.8rem;">{row['Date']}</span></td>
<td><span style="color: #CBD5E1; font-size: 0.82rem;">{str(row.get('Notes', ''))[:40]}</span></td>
</tr>""")

            t_log = f"""<table class="saas-table">
<thead>
<tr>
<th style="width: 25%;">Influencer</th>
<th style="width: 20%;">Email</th>
<th style="width: 15%;">Status</th>
<th style="width: 18%;">Timestamp</th>
<th style="width: 22%;">Execution Notes</th>
</tr>
</thead>
<tbody>
{''.join(log_tbody)}
</tbody>
</table>"""
            st.html(t_log)
        else:
            st.info("Outreach log is currently empty.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Instagram DM Manual Workflow Queue")
    st.markdown("Adhering to API compliance rules, Instagram direct messages are queued for assisted or manual dispatch:")

    if messages_path.exists():
        with open(messages_path, "r", encoding="utf-8") as f:
            all_pitches = json.load(f)

        # Load real handle mapping from filtered dataset
        handle_map = {}
        if FILTERED_DATA_PATH.exists():
            with open(FILTERED_DATA_PATH, "r", encoding="utf-8") as f_f:
                fdata = json.load(f_f)
                for item in fdata.get("qualified_influencers", []):
                    p = item["profile"]
                    handle_map[p["name"]] = p.get("secondary_handles")

        all_names = [p["influencer_name"] for p in all_pitches]
        dm_target = st.selectbox(
            "Select Influencer for DM Dispatch:",
            all_names,
            key="dm_dispatch_dropdown",
        )

        target_obj = next((p for p in all_pitches if p["influencer_name"] == dm_target), None)
        if target_obj:
            creator_handle = handle_map.get(dm_target) or dm_target.lower().replace(" ", "")
            dm_wf = prepare_instagram_dm_workflow(dm_target, creator_handle, target_obj.get("instagram_dm", ""))

            dm_col1, dm_col2 = st.columns([1.5, 0.5])
            with dm_col1:
                st.code(dm_wf["dm_text"], language="text")
            with dm_col2:
                st.markdown(f"**Target Handle:** `{dm_wf['instagram_handle']}`")
                st.link_button("Open Instagram Profile", dm_wf["profile_url"], use_container_width=True)
