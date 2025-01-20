import io
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import os

# Default values for the new DataFrame
default_data = {
    'Vol. [ml]': [3000, 3000.2, 3000.4, 3000.6, 3000.8, 3001],
    'Vol. salt solution added [ml]': [0, 0.2, 0.4, 0.6, 0.8, 1],
    'EC [uS/cm]': [None] * 6  # Placeholder for EC values to be filled by the user
}

# Save to Excel function (for saving to Hydrology_Shared)
def save_to_excel_with_headers(dataframe, file_path_or_buffer, header_data):
    """Save DataFrame to Excel with header fields above it."""
    with pd.ExcelWriter(file_path_or_buffer, engine="xlsxwriter") as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet("Sheet1")
        writer.sheets["Sheet1"] = worksheet

        # Formatting options
        right_align_format = workbook.add_format({'align': 'right'})
        bold_right_align_format = workbook.add_format({'bold': True, 'align': 'right'})

        # Write the header data at the top
        row = 0
        for key, value in header_data.items():
            worksheet.write(row, 0, key, bold_right_align_format)  # Right-align and bold the header field name
            worksheet.write(row, 1, value, right_align_format)  # Right-align the header field value
            row += 1

        # Leave one empty row between headers and DataFrame
        start_row = row + 1

        # Write the DataFrame below the header
        dataframe.to_excel(writer, sheet_name="Sheet1", startrow=start_row, index=False)

        # Resize columns based on max length of both header data and dataframe content
        for col_num, col in enumerate(dataframe.columns):
            # For the DataFrame columns, just consider the content length in the dataframe
            data_length = max(dataframe[col].apply(lambda x: len(str(x))))

            # Determine the header data length for the first two columns (the header information)
            if col_num == 0:  # For column 0 (header field names)
                header_length = max(len(str(key)) for key in header_data.keys())  # Longest header key
            elif col_num == 1:  # For column 1 (header field values)
                header_length = max(len(str(value)) for value in header_data.values())  # Longest header value
            else:
                header_length = 0  # No header data for the DataFrame columns

            # Consider the column name (DataFrame column name itself)
            column_name_length = len(str(col))  # The length of the DataFrame column name

            # Determine the max length for this column (header + data + column name)
            max_length = max(header_length, data_length, column_name_length)

            # Set the column width
            worksheet.set_column(col_num, col_num, max_length)  # Resize based on column data

def main():
    st.title("CHRL Tire Toxin CF Processing")

    # Field inputs
    field_sampling_date = st.date_input("Field Sampling Date", value=None)
    calibration_date = st.date_input("Calibration Date", value=None)
    site = st.selectbox("Site", ["chase_bridge", "cat_beacons", "northfield", "Other"], index=None)
    if site == "Other":
        site = st.text_input("Enter custom site name", value=None)
    sensor = st.selectbox("Sensor", ["AT200", "AT201", "AT202", "AT203", "TM7.537", "TM7.538"], index=None)
    lab_or_field = st.selectbox("Lab/Field", ["Field", "Lab"])
    primary_solution = st.number_input("Primary solution [g/m3]", value=30000)    

    # Initialize df_cf with default values
    df_cf = pd.DataFrame(default_data)

    # File upload for Excel data
    st.write("### Upload CF Timeseries File")
    uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])

    # If a file is uploaded, process it
    if uploaded_file is not None:
        # First try reading just the headers
        df_preview = pd.read_excel(uploaded_file, nrows=0)
        
        if 'EC.T' in df_preview.columns:
            # Format 1: Headers in first row
            uploaded_file.seek(0)  # Reset file pointer
            df = pd.read_excel(uploaded_file)
            ec_column = 'EC.T'
            st.write('TYPE1!')
        else:
            # Try format 2: Headers in row 4
            uploaded_file.seek(0)  # Reset file pointer
            df_preview = pd.read_excel(uploaded_file, header=3, nrows=0)
            
            if 'EC.T(uS/cm)' in df_preview.columns:
                uploaded_file.seek(0)  # Reset file pointer
                df = pd.read_excel(uploaded_file, header=3)
                ec_column = 'EC.T(uS/cm)'
                st.write('TYPE2!')

            else:
                st.error("The uploaded file doesn't match any expected format. Please ensure it contains either 'EC.T' or 'EC.T(uS/cm)' columns.")
                st.stop()

        # Create the plot using the detected column
        fig = px.line(df, x=df.index, y=ec_column, 
                      title=f"{ec_column} Plot", 
                      labels={"x": "Index", ec_column: "EC.T [uS/cm]"})

        # Create a list to store selected points' indices
        selected_points = []

        # Create columns for input boxes for point selection (below the plot)
        st.write("### Select Points on the Plot")
        st.write("<p style='color: grey; font-style: italic;'>hint: hover cursor on plot to display index</p>", unsafe_allow_html=True)
        # Create columns for input fields to select points, placed below the plot
        cols = st.columns(6)

        # For each column, create a text input for the user to specify the index
        for i, col in enumerate(cols):
            label = f"Point {i + 1}"
            index = col.text_input(f"Index for {label}", value=str(i), key=f"input_{i}")
            try:
                index = int(index)
                if 0 <= index < len(df):
                    selected_points.append(index)
                    fig.add_trace(go.Scatter(
                        x=[index], 
                        y=[df.loc[index, ec_column]], 
                        mode='markers+text',
                        name=label,
                        text=[f"{label}"],
                        textposition='top center',
                        showlegend=False
                    ))
                else:
                    st.warning(f"Index {index} for {label} is out of range. Please enter a valid index.")
            except ValueError:
                st.warning(f"Invalid index entered for {label}. Please enter a valid integer.")

        # Display the updated plot with points selected
        st.plotly_chart(fig, use_container_width=True)

        # Display the EC.T values corresponding to the selected indices
        y_values = [df.loc[index, ec_column] for index in selected_points]
        df_cf['EC [uS/cm]'][:len(y_values)] = y_values

    # Show the CF DataFrame
    st.write("### CF DataFrame")
    df_cf = st.data_editor(df_cf, num_rows="dynamic", hide_index=True)

    # "Save to Hydrology Shared" Button
    st.write("### Save CF File to \Hydrology_Shared")
    if field_sampling_date and sensor and site:
        if st.button("Save CF File to \Hydrology_Shared"):
            formatted_date = field_sampling_date.strftime("%Y%m%d")
            file_name = rf"H:\tire-toxin\data\EC\CF\{site}\{site}_{formatted_date}_{sensor}_CFvals.xlsx"
            os.makedirs(os.path.dirname(file_name), exist_ok=True)

            header_data = {
                "Field Sampling Date": field_sampling_date.strftime("%Y-%m-%d"),
                "Calibration Date": calibration_date.strftime("%Y-%m-%d") if calibration_date else "N/A",
                "Site": site,
                "Sensor": sensor,
                "Lab/Field": lab_or_field,
                "Primary solution [g/m3]": primary_solution,
            }

            with open(file_name, "wb") as file:
                save_to_excel_with_headers(df_cf, file, header_data)

            st.success(f"File saved successfully at: {file_name}")
    else:
        st.warning("Please complete all required fields before saving the file.")

    # Download CF Excel File
    st.write("### Download CF File")
    
    if field_sampling_date and sensor and site:
        # Prepare the header data
        formatted_date = field_sampling_date.strftime("%Y%m%d")
        header_data = {
            "Field Sampling Date": field_sampling_date.strftime("%Y-%m-%d"),
            "Calibration Date": calibration_date.strftime("%Y-%m-%d") if calibration_date else "N/A",
            "Site": site,
            "Sensor": sensor,
            "Lab/Field": lab_or_field,
            "Primary solution [g/m3]": primary_solution,
        }

        # Create a buffer to hold the Excel file in memory
        buffer = io.BytesIO()
        save_to_excel_with_headers(df_cf, buffer, header_data)
        buffer.seek(0)

        # Immediately trigger the download without any extra button
        st.download_button(
            label="Download CF Excel File",
            data=buffer,
            file_name=f"{site}_{formatted_date}_{sensor}_CFvals.xlsx",
            mime="application/vnd.ms-excel"
        )
    else:
        st.warning("Please complete all required fields before downloading.")

if __name__ == "__main__":
    main()