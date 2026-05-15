import streamlit as st
from dotenv import load_dotenv
from jd_analyser import analyse_job_description, analyse_skill_gap, generate_resume_bullets

load_dotenv(r"C:\Dev\.env")

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="ARIA — Career Module",
    page_icon="🤖",
    layout="wide"
)

# --- HEADER ---
st.title("🤖 ARIA — Career Module")
st.caption("AI-powered job description analyser, skill gap checker, and resume builder")
st.divider()

# --- STEP 1: UPLOAD JD ---
st.subheader("Step 1 — Upload Job Description")
uploaded_file = st.file_uploader(
    "Upload a .txt file containing the job description",
    type=["txt"]
)

if uploaded_file is not None:
    # read the uploaded file content
    jd_text = uploaded_file.read().decode("utf-8")

    st.success("Job description uploaded successfully")

    # show a preview of the uploaded text
    with st.expander("Preview uploaded JD"):
        st.text(jd_text)

    # --- STEP 2: ANALYSE JD ---
    st.divider()
    st.subheader("Step 2 — Analyse Job Description")

    if st.button("Analyse JD", type="primary"):
        with st.spinner("ARIA is analysing the job description..."):
            jd_result = analyse_job_description(jd_text)
            st.session_state["jd_result"] = jd_result

    if "jd_result" in st.session_state:
        st.markdown("**Analysis Result:**")
        st.text(st.session_state["jd_result"])

        # --- STEP 3: SKILL GAP ---
        st.divider()
        st.subheader("Step 3 — Skill Gap Analysis")

        candidate_skills = st.text_input(
            "Enter your current skills (comma separated)",
            placeholder="Python, Docker, REST APIs, Git"
        )

        if st.button("Check Skill Gap", type="primary"):
            if candidate_skills.strip() == "":
                st.warning("Please enter your skills first")
            else:
                with st.spinner("ARIA is analysing your skill gap..."):
                    gap_result = analyse_skill_gap(
                        st.session_state["jd_result"],
                        candidate_skills
                    )
                    st.session_state["gap_result"] = gap_result

        if "gap_result" in st.session_state:
            st.markdown("**Skill Gap Report:**")
            st.text(st.session_state["gap_result"])

            # --- STEP 4: RESUME BULLETS ---
            st.divider()
            st.subheader("Step 4 — Resume Bullet Generator")

            raw_experience = st.text_area(
                "Describe your experience in plain words",
                placeholder="I built REST APIs using Python and Flask. I worked on data pipelines using pandas...",
                height=150
            )

            if st.button("Generate Resume Bullets", type="primary"):
                if raw_experience.strip() == "":
                    st.warning("Please describe your experience first")
                else:
                    with st.spinner("ARIA is writing your resume bullets..."):
                        bullets = generate_resume_bullets(
                            raw_experience,
                            st.session_state["jd_result"]
                        )
                        st.session_state["bullets"] = bullets

            if "bullets" in st.session_state:
                st.markdown("**Your Resume Bullets:**")
                st.text(st.session_state["bullets"])
                st.success("Copy these bullets into your resume")