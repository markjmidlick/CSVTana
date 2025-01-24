import streamlit as st
import pandas as pd
from io import BytesIO
import zipfile
import requests
import json
import time

##############################
# 1. EXISTING TANA PASTE CODE
##############################
# Inject custom CSS to style all hyperlinks consistently

def csv_to_tana_paste(df, delimiter):
    tana_paste = ""
    tag_column = df.columns[0]  # Use the first column's title as the tag name

    # Format tag: wrap multi-word tags in [[ ]]
    formatted_tag_column = f"#[[{tag_column}]]" if " " in tag_column else f"#{tag_column}"

    for index, row in df.iterrows():
        # Handle blank values in the first column
        tag = row[0] if not pd.isna(row[0]) else ""  # Use blank node if value is missing
        tana_paste += f"- {tag} {formatted_tag_column}\n"  # Create a Tana Paste node with the tag

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
st.markdown(
    """
    <style>
        /* Target all links in the Streamlit app */
        div.stMarkdown a {
            color: #ffffff;  /* Army Green */
            text-decoration: none;  /* No underline */
            background-color: #2D3E26;  /* Permanent white background */
            padding: 0.2px 2px;  /* Padding for spacing around text */
            border-radius: 2px;  /* Smooth rounded corners */
            font-weight: bold;  /* Make the text stand out more */
            transition: background-color 0.1s ease, color 0.1s ease;  /* Smooth transitions */
        }
        div.stMarkdown a:hover {
            background-color: #1E4D2B;  /* Slightly darker white on hover */
            color: #f0f0f0;  /* Slightly darker green for hover */
        }
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("CSV to Tana Paste Converter")
st.write("Created by [Mark J. Midlick](https://markjmidlick.com/)")
st.markdown(
    """
    <iframe width="560" height="315" 
    src="https://www.youtube.com/embed/1UwUOTZiOuk?si=h7Wvnc-RIiOeupkA"
    title="YouTube video player" 
    frameborder="0" 
    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
    allowfullscreen>
    </iframe>
    """,
    unsafe_allow_html=True,
)
st.write("---")
st.markdown(
    """
    <div style="font-size:20px; font-weight:normal;">
        Upload a CSV file and convert it to Tana Paste format.<br>
        <br>
        Manually copy-paste the results or automatically import them to your inbox with an API key.
    </div>
    """,
    unsafe_allow_html=True,
)

# 2) Donation link
st.write("---")
# First text
st.markdown(
    """
    <div style="font-size:14px; font-style:italic; color: #FFFFFF; margin-top: 10px;">
        I believe this basic tool should be free and accessible to all (and ideally built into Tana), 
        but will happily accept coffee donations if you desire:
    </div>
    """,
    unsafe_allow_html=True,
)

stripe_donation_url = "https://buy.stripe.com/00g29qfwNajy6fSfYY"  # Replace with your actual Stripe link
st.markdown(
    f"""
    <div style="margin: 20px 0;">  <!-- Add spacing above and below the button -->
        <a href="{stripe_donation_url}" target="_blank" style="text-decoration: none; background: none; padding: 0;">
            <button style="
                background-color: #2D3E26;  /* Army green background */
                color: white; 
                padding: 10px 20px; 
                text-align: center; 
                text-decoration: none; 
                display: inline-block; 
                font-size: 16px; 
                border: none;  /* Remove any border */
                border-radius: 5px; 
                cursor: pointer;">
                Donate via Stripe
            </button>
        </a>
    </div>
    """,
    unsafe_allow_html=True,
)
# Second text
st.markdown(
    """
    <div style="font-size:14px; font-style:italic; color: #FFFFFF; margin-top: 10px;">
        If you need a more customized or automated solution, reach out to me on the 
        <a href="https://tanainc.slack.com" target="_blank" style="color: #FFFFFF;">Tana Slack</a>
    </div>
    """,
    unsafe_allow_html=True,
)
st.write("---")
st.write("## Upload CSV")
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
delimiter = st.text_input("Enter a delimiter to split multiple items in fields (optional)")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # 1) CSV Preview
    st.write("---")
    st.write("## CSV Preview")
    st.write("Below are the first 10 rows of your CSV:")
    st.dataframe(df.head(10))
    st.write("---")
    st.header("CSV to Tana Paste")
    if st.button("Convert to Tana Paste"):
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

##############################
# PASTE THIS AFTER YOUR EXISTING CODE
##############################


import requests
import json
import time

TANA_API_ENDPOINT = "https://europe-west1-tagr-prod.cloudfunctions.net/addToNodeV2"

st.write("---")
st.header("CSV to Tana Inbox")
st.write(
    "Insert an API key from one of your workspaces to send a CSV directly to your Tana Inbox. "
)


# Tana token
tana_token = st.text_input("Tana API Token (Bearer)", type="password")

def parse_tana_children_for_ids(resp_json):
    return [
        child["nodeId"]
        for child in resp_json.get("children", [])
        if "nodeId" in child
    ]

def create_fields(token, field_names):
    if not field_names:
        return {}
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "targetNodeId": "SCHEMA",
        "nodes": []
    }
    for fn in field_names:
        payload["nodes"].append({
            "name": fn,
            "supertags": [{"id": "SYS_T02"}]
            # "description": f"Field named '{fn}'"  # removed per your preference
        })
    resp = requests.post(TANA_API_ENDPOINT, headers=headers, json=payload)
    if resp.status_code != 200:
        st.error(f"Error creating fields: {resp.status_code} - {resp.text}")
        return None

    data = resp.json()
    new_ids = parse_tana_children_for_ids(data)
    if len(new_ids) < len(field_names):
        st.error(f"Tana returned fewer IDs than expected: {data}")
        return None

    time.sleep(1)  # Rate limit
    field_map = {}
    for i, fn in enumerate(field_names):
        field_map[fn] = new_ids[i]
    return field_map

def create_supertag(token, supertag_name):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "targetNodeId": "SCHEMA",
        "nodes": [
            {
                "name": supertag_name,
                "supertags": [{"id": "SYS_T01"}]
                # "description": f"Supertag created from CSV header: '{supertag_name}'"
            }
        ]
    }
    resp = requests.post(TANA_API_ENDPOINT, headers=headers, json=payload)
    if resp.status_code != 200:
        st.error(f"Error creating supertag '{supertag_name}': {resp.status_code} - {resp.text}")
        return None

    data = resp.json()
    new_ids = parse_tana_children_for_ids(data)
    if not new_ids:
        st.error(f"No nodeId returned for supertag '{supertag_name}' in {data}")
        return None

    time.sleep(1)
    return new_ids[0]

def build_nodes_from_df(df, supertag_id, field_map, delimiter=None):
    """
    Converts the DataFrame into Tana-compatible nodes.
    Each row becomes a parent node with fields as children.
    Delimiter-split fields are turned into multiple child nodes.
    """
    supertag_name = df.columns[0]  # First column as supertag
    field_names = df.columns[1:]  # Remaining columns as fields

    nodes = []
    for _, row in df.iterrows():
        # Parent node name: Use blank node "" for empty values
        parent_name = str(row[supertag_name]).strip() if not pd.isna(row[supertag_name]) else ""

        children = []
        for field_name in field_names:
            if field_name in field_map:
                value = str(row[field_name]).strip() if not pd.isna(row[field_name]) else ""
                if delimiter and delimiter in value:
                    # Split the value into multiple child nodes
                    child_items = [item.strip() for item in value.split(delimiter) if item.strip()]
                    if child_items:
                        children.append({
                            "type": "field",
                            "attributeId": field_map[field_name],
                            "children": [{"name": item} for item in child_items],
                        })
                elif value:
                    # Single value as a field child
                    children.append({
                        "type": "field",
                        "attributeId": field_map[field_name],
                        "children": [{"name": value}],
                    })

        # Append the node with a blank parent name if applicable
        nodes.append({
            "name": parent_name,  # Use blank "" for empty parent names
            "supertags": [{"id": supertag_id}],
            "children": children,
        })

    return nodes

def chunk_nodes(nodes, max_nodes=100, max_chars=5000):
    """
    Yields sub-lists so each request has ≤100 nodes & ≤5000 JSON chars.
    """
    batch = []
    for node in nodes:
        test_batch = batch + [node]
        test_json = json.dumps({"targetNodeId": "INBOX", "nodes": test_batch})
        if len(test_json) > max_chars:
            if not batch:
                st.error("A single node alone exceeds 5k. Skipping it.")
                continue
            else:
                yield batch
                batch = [node]
        else:
            batch = test_batch
        if len(json.loads(test_json)["nodes"]) >= max_nodes:
            yield json.loads(test_json)["nodes"]
            batch = []
    if batch:
        yield json.loads(json.dumps({"nodes": batch}))["nodes"]

def estimate_chunk_count(nodes, max_nodes=100, max_chars=5000):
    """
    A quick pass to guess how many chunks we'll produce, so we can estimate time.
    We'll do a dry-run of chunk_nodes without actually sending them.
    """
    count = 0
    batch = []
    for node in nodes:
        test_batch = batch + [node]
        test_json = json.dumps({"targetNodeId": "INBOX", "nodes": test_batch})
        if len(test_json) > max_chars:
            if batch:
                count += 1
                batch = [node]
            else:
                # skip the huge node
                pass
        else:
            batch = test_batch
        parsed = json.loads(test_json)
        if len(parsed["nodes"]) >= max_nodes:
            count += 1
            batch = []
    if batch:
        count += 1
    return count

def send_nodes_in_batches(nodes, token, progress_bar):
    if not token:
        st.error("No Tana API token provided.")
        return
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # We'll do the real chunking pass, updating the progress bar each time
    total_chunks = estimate_chunk_count(nodes)
    st.info(f"Estimated {total_chunks} chunks to send, ~{total_chunks} seconds (min).")
    chunk_counter = 0

    for chunk in chunk_nodes(nodes):
        payload = {"targetNodeId": "INBOX", "nodes": chunk}
        payload_str = json.dumps(payload)
        time.sleep(1)  # Tana limit
        chunk_counter += 1
        resp = requests.post(TANA_API_ENDPOINT, headers=headers, data=payload_str)
        if resp.status_code == 200:
            st.success(f"Batch {chunk_counter} with {len(chunk)} nodes uploaded.")
        else:
            st.error(f"Batch {chunk_counter} failed: {resp.status_code} - {resp.text}")
            break

        # Update the progress bar
        if total_chunks > 0:
            progress_bar.progress(chunk_counter / total_chunks)

    # If chunk_counter == total_chunks, we've successfully completed
    if chunk_counter == total_chunks:
        progress_bar.progress(1.0)

if st.button("Send CSV to Tana"):
    if not tana_token:
        st.warning("Please enter your Tana API token.")
        st.stop()

    # Step 1: Extract supertag and field names
    all_cols = list(df.columns)
    if len(all_cols) < 1:
        st.error("No columns found in CSV? Check your file.")
        st.stop()
    supertag_name = all_cols[0]
    field_names = all_cols[1:]

    # Step 2: Create fields
    field_map = create_fields(tana_token, field_names)
    if field_map is None:
        st.stop()

    # Step 3: Create supertag
    supertag_id = create_supertag(tana_token, supertag_name)
    if supertag_id is None:
        st.stop()

    # Step 4: Build nodes
    final_nodes = build_nodes_from_df(df, supertag_id, field_map, delimiter=delimiter)

    # Step 5: Send nodes with progress bar
    progress_bar = st.progress(0.0)
    send_nodes_in_batches(final_nodes, tana_token, progress_bar)
    st.success("All done! Check Tana's INBOX.")
