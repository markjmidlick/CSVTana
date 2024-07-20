import streamlit as st
import pandas as pd
from io import BytesIO
import zipfile

def csv_to_tana_paste(df, delimiter):
    tana_paste = ""
    tag_column = df.columns[0]  # Use the first column's title as the tag name

    for index, row in df.iterrows():
        tag = row[0]
        tana_paste += f"- {tag} #{tag_column}\n"  # Create a Tana Paste node with the tag
        for col_name, value in row.items():
            if col_name != tag_column:  # Skip the tag column
                if delimiter and delimiter in str(value):
                    items = str(value).split(delimiter)
                    tana_paste += f"  - {col_name}::\n"
                    for item in items:
                        tana_paste += f"    - {item.strip()}\n"
                else:
                    tana_paste += f"  - {col_name}:: {value}\n"
        tana_paste += "\n"
    
    return tana_paste

def split_tana_paste(tana_paste, max_chars=100000):
    conversations = tana_paste.strip().split("\n- ")  # Split by conversation
    files = []
    current_file = ""
    current_length = 0

    for i, conversation in enumerate(conversations):
        conversation = conversation.strip()
        if i > 0:
            conversation = "- " + conversation  # Re-add the leading '- ' removed by split
        
        if not conversation:
            continue
        
        conversation_length = len(conversation) + len("\n\n")
        
        if current_length + conversation_length > max_chars:
            files.append(current_file.strip())
            current_file = ""
            current_length = 0
        
        current_file += conversation + "\n\n"
        current_length += conversation_length
    
    if current_file.strip():
        files.append(current_file.strip())
    
    # Prepend '%%tana%%\n\n' to each file content
    files = [f"%%tana%%\n\n{file_content}" for file_content in files]
    
    return files

st.title("CSV to Tana Paste Converter")
st.write("Upload a CSV file and convert it to Tana Paste format. The converted file will be split into multiple files if it exceeds 100k characters.")

uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
delimiter = st.text_input("Enter a delimiter to split multiple items in fields (optional)")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    if st.button("Convert"):
        tana_paste = csv_to_tana_paste(df, delimiter)
        files = split_tana_paste(tana_paste)
        
        if len(files) == 1:
            st.download_button(
                label="Download Tana Paste",
                data=files[0],
                file_name="converted_tana_paste.txt",
                mime="text/plain"
            )
        else:
            # Create a ZIP file to store all split files
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for i, file_content in enumerate(files):
                    zip_file.writestr(f"converted_tana_paste_part_{i+1}.txt", file_content)
            
            st.write("Conversion Successful! Download the Tana Paste files below:")
            
            st.download_button(
                label="Download Tana Paste ZIP",
                data=zip_buffer.getvalue(),
                file_name="converted_tana_paste.zip",
                mime="application/zip"
            )
