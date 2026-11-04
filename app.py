import datetime
import io
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="FabTech Project Management System", layout="wide"
)

# Initialize Session State Data if not present
if "order_backlog" not in st.session_state:
  st.session_state.order_backlog = pd.DataFrame([
      {
          "Sl No": 1,
          "Job Number": 201,
          "Customer Name": "Adani Pirapanti",
          "Type of Project": "Power Plant",
          "Place": "Bhagalpur",
          "State": "Bihar",
          "Country": "India",
          "PO Number": "2002323",
          "PO Line Item": 10,
          "Po Qty": 1000,
          "PO Rate": 105000,
          "End Delivery Date": "2027-12-31",
      },
      {
          "Sl No": 2,
          "Job Number": 202,
          "Customer Name": "Adani Pirapanti",
          "Type of Project": "Power Plant",
          "Place": "Bhagalpur",
          "State": "Bihar",
          "Country": "India",
          "PO Number": "2002323",
          "PO Line Item": 20,
          "Po Qty": 500,
          "PO Rate": 110000,
          "End Delivery Date": "2027-01-31",
      },
  ])

if "master_sheet" not in st.session_state:
  st.session_state.master_sheet = pd.DataFrame([
      {
          "SR NO.": 1,
          "Project No": 201,
          "DESCRIPTION": "CT-T1",
          "Mark No": "MB-1",
          "QTY": 1,
          "STATUS": "WIP",
          "WIP Date": "2026-02-25",
          "RFD Date": pd.NaT,
      },
      {
          "SR NO.": 2,
          "Project No": 201,
          "DESCRIPTION": "CT-T1",
          "Mark No": "MB-2",
          "QTY": 1,
          "STATUS": "RFD",
          "WIP Date": "2026-01-10",
          "RFD Date": "2026-02-15",
      },
      {
          "SR NO.": 3,
          "Project No": 202,
          "DESCRIPTION": "BLR-01",
          "Mark No": "COL-1",
          "QTY": 2,
          "STATUS": "WIP",
          "WIP Date": "2026-10-15",
          "RFD Date": pd.NaT,
      },
  ])

st.title("⚙️ FabTech Project Management & Tracking Portal")
st.markdown(
    "Manage Order Backlogs, Shop-Floor Mark Numbers, and Automated Ageing"
    " Buckets."
)

tab1, tab2, tab3, tab4 = st.tabs([
    "1. Order Backlog",
    "2. Project Master Sheet",
    "3. WIP Ageing Report",
    "4. RFD Ageing Report",
])

# --- TAB 1: ORDER BACKLOG ---
with tab1:
  st.subheader("Order Backlog Management")
  st.markdown(
      "Edit orders online or download the master template for bulk upload."
  )

  # Download template
  buffer = io.BytesIO()
  with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
    st.session_state.order_backlog.to_excel(
        writer, index=False, sheet_name="Order Backlog"
    )
  st.download_button(
      label="📥 Download Order Backlog Template",
      data=buffer.getvalue(),
      file_name="Order_Backlog_Template.xlsx",
      mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  )

  # Upload master data
  uploaded_file = st.file_uploader(
      "Upload Master Excel (Order Backlog)", type=["xlsx", "csv"], key="order_up"
  )
  if uploaded_file is not None:
    if uploaded_file.name.endswith(".csv"):
      st.session_state.order_backlog = pd.read_csv(uploaded_file)
    else:
      st.session_state.order_backlog = pd.read_excel(uploaded_file)
    st.success("Order backlog updated successfully from file!")

  # Interactive online editor
  st.markdown("### Online Order Table Editor")
  edited_orders = st.data_editor(
      st.session_state.order_backlog, num_rows="dynamic", key="order_editor"
  )
  st.session_state.order_backlog = edited_orders

# --- TAB 2: PROJECT MASTER SHEET ---
with tab2:
  st.subheader("Project Master Sheet (Mark Numbers & Status)")
  st.markdown(
      "Track individual mark numbers, production status, WIP dates, and RFD"
      " dates."
  )

  # Filter by project
  proj_list = st.session_state.master_sheet["Project No"].unique()
  selected_proj = st.selectbox(
      "Select Project Number to Filter", options=["All"] + list(proj_list)
  )

  display_df = st.session_state.master_sheet
  if selected_proj != "All":
    display_df = display_df[display_df["Project No"] == selected_proj]

  edited_master = st.data_editor(
      display_df, num_rows="dynamic", key="master_editor"
  )
  # Update back session state
  if selected_proj == "All":
    st.session_state.master_sheet = edited_master
  else:
    st.session_state.master_sheet.update(edited_master)

# --- HELPER FUNCTION FOR AGEING BUCKETS ---
def calculate_ageing_report(df, status_filter, date_col):
  if df.empty:
    return pd.DataFrame()

  working_df = df[df["STATUS"] == status_filter].copy()
  if working_df.empty:
    return pd.DataFrame(
        columns=[
            "ProjectNo",
            "0-7 Days",
            "8-15 Days",
            "16-30 Days",
            "30-60 Days",
            ">60 Days",
        ]
    )

  today = pd.Timestamp.today().normalize()
  working_df[date_col] = pd.to_datetime(working_df[date_col], errors="coerce")
  working_df["Age"] = (today - working_df[date_col]).dt.days

  def get_bucket(age):
    if pd.isna(age) or age < 0:
      return "Unknown"
    elif age <= 7:
      return "0-7 Days"
    elif age <= 15:
      return "8-15 Days"
    elif age <= 30:
      return "16-30 Days"
    elif age <= 60:
      return "30-60 Days"
    else:
      return ">60 Days"

  working_df["Bucket"] = working_df["Age"].apply(get_bucket)

  pivot = (
      working_df.pivot_table(
          index="Project No",
          columns="Bucket",
          values="Mark No",
          aggfunc="count",
          fill_value=0,
      )
      .reset_index()
      .rename(columns={"Project No": "ProjectNo"})
  )

  # Ensure all columns exist
  expected_cols = [
      "ProjectNo",
      "0-7 Days",
      "8-15 Days",
      "16-30 Days",
      "30-60 Days",
      ">60 Days",
  ]
  for col in expected_cols:
    if col not in pivot.columns:
      pivot[col] = 0

  return pivot[expected_cols]

# --- TAB 3: WIP AGEING REPORT ---
with tab3:
  st.subheader("WIP Ageing Bucket Report")
  st.markdown(
      "Calculated automatically based on **Today's Date - WIP Date** for items"
      " with status **WIP**."
  )

  wip_report = calculate_ageing_report(
      st.session_state.master_sheet, "WIP", "WIP Date"
  )
  if wip_report.empty:
    st.info("No items currently in WIP status.")
  else:
    st.dataframe(wip_report, use_container_width=True)

# --- TAB 4: RFD AGEING REPORT ---
with tab4:
  st.subheader("RFD Ageing Bucket Report")
  st.markdown(
      "Calculated automatically based on **Today's Date - RFD Date** for items"
      " with status **RFD** (Ready for Dispatch)."
  )

  rfd_report = calculate_ageing_report(
      st.session_state.master_sheet, "RFD", "RFD Date"
  )
  if rfd_report.empty:
    st.info("No items currently in RFD status.")
  else:
    st.dataframe(rfd_report, use_container_width=True)