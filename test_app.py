import streamlit as st

st.markdown("### How would you like to describe your issue?")

input_tab1, input_tab2 = st.tabs(["✍️ Type Complaint", "🗣️ Speak Complaint (Voice)"])

with input_tab2:
    audio_bytes = st.audio_input("Click the microphone to start recording")

if "complaint_input" not in st.session_state:
    st.session_state.complaint_input = ""

if "last_audio" not in st.session_state:
    st.session_state.last_audio = None

if audio_bytes is not None and audio_bytes != st.session_state.last_audio:
    st.session_state.last_audio = audio_bytes
    # simulate transcription
    st.session_state.complaint_input = "Simulated Transcription!"
    st.success("Transcribed!")

with input_tab1:
    complaint = st.text_area("Complaint details", 
                             key="complaint_input",
                             height=150, label_visibility="collapsed")

if st.button("Find My Rights"):
    if not complaint.strip():
        st.warning("Please enter or record a complaint before continuing.")
    else:
        st.write("Processing:", complaint)
