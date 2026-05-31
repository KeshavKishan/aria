import streamlit as st
from dotenv import load_dotenv
from fpdf import FPDF
import tempfile
import os
import re
from jd_analyser import analyse_job_description, analyse_skill_gap, generate_resume_bullets

load_dotenv(r"C:\Dev\.env")

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="ARIA — Career Module",
    page_icon="🤖",
    layout="wide"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .skill-tag {
        display: inline-block;
        padding: 3px 10px;
        margin: 3px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 500;
    }
    .skill-match {
        background-color: #d4edda;
        color: #155724;
    }
    .skill-missing {
        background-color: #f8d7da;
        color: #721c24;
    }
    .bullet-box {
        background-color: #e8f4f8;
        border-left: 4px solid #0077b6;
        padding: 10px 15px;
        border-radius: 5px;
        margin: 5px 0;
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)


def clean(text):
    """Replace special unicode chars with plain ASCII for PDF compatibility"""
    return (text
        .replace("\u2014", "-")
        .replace("\u2013", "-")
        .replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2022", "-")
        .replace("\u00e9", "e")
        .replace("\u00e8", "e")
    )


def parse_jd_result(jd_result):
    """Parse the JD analysis text into a dictionary for better display"""
    lines = jd_result.strip().split('\n')
    parsed = {
        "title": "", "company": "", "location": "",
        "experience": "", "level": "",
        "skills": [], "responsibilities": [],
        "summary": "", "match_tips": ""
    }
    current_section = None

    for line in lines:
        line = line.strip()
        if line.startswith("JOB TITLE:"):
            parsed["title"] = line.replace("JOB TITLE:", "").strip()
        elif line.startswith("COMPANY:"):
            parsed["company"] = line.replace("COMPANY:", "").strip()
        elif line.startswith("LOCATION:"):
            parsed["location"] = line.replace("LOCATION:", "").strip()
        elif line.startswith("EXPERIENCE REQUIRED:"):
            parsed["experience"] = line.replace("EXPERIENCE REQUIRED:", "").strip()
        elif line.startswith("LEVEL:"):
            parsed["level"] = line.replace("LEVEL:", "").strip()
        elif line.startswith("REQUIRED SKILLS:"):
            current_section = "skills"
        elif line.startswith("KEY RESPONSIBILITIES:"):
            current_section = "responsibilities"
        elif line.startswith("SUMMARY:"):
            current_section = "summary"
            inline = line.replace("SUMMARY:", "").strip()
            if inline:
                parsed["summary"] += inline + " "
        elif line.startswith("MATCH TIPS:"):
            current_section = "match_tips"
            inline = line.replace("MATCH TIPS:", "").strip()
            if inline:
                parsed["match_tips"] += inline + " "
        elif line.startswith("- ") and current_section == "skills":
            parsed["skills"].append(line[2:])
        elif line.startswith("- ") and current_section == "responsibilities":
            parsed["responsibilities"].append(line[2:])
        elif current_section == "summary" and line and not line.startswith("MATCH TIPS:"):
            parsed["summary"] += line + " "
        elif current_section == "match_tips" and line:
            parsed["match_tips"] += line + " "

    return parsed


def parse_gap_result(gap_result):
    """Parse skill gap text into structured data"""
    lines = gap_result.strip().split('\n')
    parsed = {
        "matching": [], "missing": [],
        "priority": [], "score": "",
        "assessment": ""
    }
    current_section = None

    for line in lines:
        line = line.strip()
        if line.startswith("MATCHING SKILLS:"):
            current_section = "matching"
        elif line.startswith("MISSING SKILLS:"):
            current_section = "missing"
        elif line.startswith("PRIORITY LEARNING ORDER:"):
            current_section = "priority"
        elif line.startswith("OVERALL MATCH SCORE:"):
            parsed["score"] = line.replace("OVERALL MATCH SCORE:", "").strip()
            current_section = None
        elif line.startswith("HONEST ASSESSMENT:"):
            current_section = "assessment"
        elif line.startswith("- ") and current_section == "matching":
            parsed["matching"].append(line[2:])
        elif line.startswith("- ") and current_section == "missing":
            parsed["missing"].append(line[2:])
        elif line and current_section == "priority" and line[0].isdigit():
            parsed["priority"].append(line)
        elif current_section == "assessment" and line:
            parsed["assessment"] += line + " "

    return parsed


def parse_bullets(bullets_text):
    """Parse resume bullets into a list"""
    lines = bullets_text.strip().split('\n')
    bullets = []
    keywords = ""
    ats_score = ""
    tips = []
    current_section = None

    for line in lines:
        line = line.strip()
        if line.startswith("REWRITTEN RESUME BULLETS:"):
            current_section = "bullets"
        elif line.startswith("KEYWORDS USED FROM JD:"):
            current_section = "keywords"
        elif line.startswith("ATS SCORE ESTIMATE:"):
            ats_score = line.replace("ATS SCORE ESTIMATE:", "").strip()
            current_section = None
        elif line.startswith("IMPROVEMENT TIPS:"):
            current_section = "tips"
        elif line.startswith("- ") and current_section == "bullets":
            bullets.append(line[2:])
        elif current_section == "keywords" and line:
            keywords = line
        elif line.startswith("- ") and current_section == "tips":
            tips.append(line[2:])

    return {"bullets": bullets, "keywords": keywords,
            "ats_score": ats_score, "tips": tips}


def format_priority_item(item):
    """Extract skill name and weeks from priority item for PDF display"""
    item_clean = clean(item)
    # get number and skill name at the start before any dash
    match = re.match(r'^(\d+\.\s*[^-–—(]+)', item_clean)
    skill_part = match.group(1).strip() if match else item_clean[:40]
    # get weeks at the end
    weeks_match = re.search(r'(\d+\s*weeks?)\s*$', item_clean, re.IGNORECASE)
    weeks_part = weeks_match.group(1) if weeks_match else ""
    result = f"{skill_part} ({weeks_part})" if weeks_part else skill_part
    return result[:80]  # hard cap to prevent overflow


def generate_pdf(jd_parsed, gap_parsed, bullets_parsed):
    """Generate a clean PDF report with all results"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # --- TITLE ---
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(0, 119, 182)
    pdf.cell(0, 12, "ARIA - Career Analysis Report", ln=True, align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    # --- SECTION 1: JD ANALYSIS ---
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_fill_color(230, 240, 255)
    pdf.cell(0, 9, "Job Description Analysis", ln=True, fill=True)
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, clean(f"Role: {jd_parsed['title']} at {jd_parsed['company']}"), ln=True)
    pdf.cell(0, 7, clean(f"Location: {jd_parsed['location']}"), ln=True)
    pdf.cell(0, 7, clean(f"Experience: {jd_parsed['experience']} years | Level: {jd_parsed['level']}"), ln=True)
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Required Skills:", ln=True)
    pdf.set_font("Helvetica", "", 11)
    for skill in jd_parsed["skills"]:
        pdf.cell(0, 6, clean(f"  - {skill}"), ln=True)
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Summary:", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(180, 6, clean(jd_parsed["summary"].strip()))
    pdf.ln(4)

    # --- SECTION 2: SKILL GAP ---
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_fill_color(230, 240, 255)
    pdf.cell(0, 9, "Skill Gap Analysis", ln=True, fill=True)
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, clean(f"Match Score: {gap_parsed['score']}"), ln=True)
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Matching Skills:", ln=True)
    pdf.set_font("Helvetica", "", 11)
    for skill in gap_parsed["matching"]:
        pdf.cell(0, 6, clean(f"  + {skill}"), ln=True)
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Missing Skills (Priority Order):", ln=True)
    pdf.set_font("Helvetica", "", 10)
    for item in gap_parsed["priority"]:
        short = format_priority_item(item)
        pdf.cell(0, 6, short, ln=True)
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Assessment:", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(180, 6, clean(gap_parsed["assessment"].strip()))
    pdf.ln(4)

    # --- SECTION 3: RESUME BULLETS ---
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_fill_color(230, 240, 255)
    pdf.cell(0, 9, "Resume Bullets", ln=True, fill=True)
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 11)
    for bullet in bullets_parsed["bullets"]:
        pdf.multi_cell(180, 6, clean(f"- {bullet}"))
        pdf.ln(1)
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, clean(f"ATS Score: {bullets_parsed['ats_score']}"), ln=True)
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Improvement Tips:", ln=True)
    pdf.set_font("Helvetica", "", 10)
    for tip in bullets_parsed["tips"]:
        tip_clean = clean(tip)
        tip_short = tip_clean[:100] + "..." if len(tip_clean) > 100 else tip_clean
        pdf.cell(0, 6, f"- {tip_short}", ln=True)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp.name)
    return tmp.name


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
    jd_text = uploaded_file.read().decode("utf-8")
    st.success("Job description uploaded successfully")

    with st.expander("Preview uploaded JD"):
        st.text(jd_text)

    # --- STEP 2: ANALYSE JD ---
    st.divider()
    st.subheader("Step 2 — Analyse Job Description")

    if st.button("Analyse JD", type="primary"):
        with st.spinner("ARIA is analysing the job description..."):
            jd_result = analyse_job_description(jd_text)
            st.session_state["jd_result"] = jd_result
            st.session_state["jd_parsed"] = parse_jd_result(jd_result)

    if "jd_parsed" in st.session_state:
        p = st.session_state["jd_parsed"]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Role", p["title"])
        col2.metric("Company", p["company"])
        col3.metric("Experience", p["experience"] + " yrs")
        col4.metric("Level", p["level"])

        st.markdown(f"📍 **Location:** {p['location']}")
        st.markdown(f"📝 **Summary:** {p['summary']}")

        col_s, col_r = st.columns(2)

        with col_s:
            st.markdown("**Required Skills:**")
            tags = ""
            for skill in p["skills"]:
                tags += f'<span class="skill-tag skill-missing">{skill}</span> '
            st.markdown(tags, unsafe_allow_html=True)

        with col_r:
            st.markdown("**Key Responsibilities:**")
            for r in p["responsibilities"]:
                st.markdown(f"• {r}")

        st.info(f"💡 **Match Tips:** {p['match_tips']}")

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
                    st.session_state["gap_parsed"] = parse_gap_result(gap_result)

        if "gap_parsed" in st.session_state:
            g = st.session_state["gap_parsed"]

            score_text = g["score"]
            try:
                score_num = int(score_text.split()[0])
                if score_num >= 7:
                    score_color = "normal"
                elif score_num >= 4:
                    score_color = "off"
                else:
                    score_color = "inverse"
            except:
                score_color = "off"

            st.metric("Overall Match Score", score_text, delta_color=score_color)

            col_m, col_x = st.columns(2)

            with col_m:
                st.markdown("**✅ Matching Skills:**")
                tags = ""
                for skill in g["matching"]:
                    tags += f'<span class="skill-tag skill-match">{skill}</span> '
                st.markdown(tags if tags else "None found", unsafe_allow_html=True)

            with col_x:
                st.markdown("**❌ Missing Skills:**")
                tags = ""
                for skill in g["missing"]:
                    tags += f'<span class="skill-tag skill-missing">{skill}</span> '
                st.markdown(tags if tags else "None — great match!", unsafe_allow_html=True)

            st.markdown("**📚 Priority Learning Order:**")
            for item in g["priority"]:
                st.markdown(f"• {item}")

            st.warning(f"💬 **Honest Assessment:** {g['assessment']}")

            # --- STEP 4: RESUME BULLETS ---
            st.divider()
            st.subheader("Step 4 — Resume Bullet Generator")

            raw_experience = st.text_area(
                "Describe your experience in plain words",
                placeholder="I built REST APIs using Python and Flask...",
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
                        st.session_state["bullets_parsed"] = parse_bullets(bullets)

            if "bullets_parsed" in st.session_state:
                b = st.session_state["bullets_parsed"]

                st.markdown("**Your Resume Bullets:**")
                for bullet in b["bullets"]:
                    st.markdown(
                        f'<div class="bullet-box">• {bullet}</div>',
                        unsafe_allow_html=True
                    )

                col_k, col_a = st.columns(2)
                col_k.info(f"🔑 **Keywords used:** {b['keywords']}")
                col_a.metric("ATS Score", b["ats_score"])

                st.markdown("**💡 Improvement Tips:**")
                for tip in b["tips"]:
                    st.markdown(f"• {tip}")

                # --- PDF DOWNLOAD ---
                st.divider()
                st.subheader("Download Full Report")

                if st.button("Generate PDF Report", type="primary"):
                    with st.spinner("Generating your PDF report..."):
                        pdf_path = generate_pdf(
                            st.session_state["jd_parsed"],
                            st.session_state["gap_parsed"],
                            st.session_state["bullets_parsed"]
                        )
                        with open(pdf_path, "rb") as f:
                            pdf_bytes = f.read()
                        os.unlink(pdf_path)

                    st.download_button(
                        label="⬇️ Download ARIA Career Report PDF",
                        data=pdf_bytes,
                        file_name="aria_career_report.pdf",
                        mime="application/pdf"
                    )
                    st.success("PDF ready — click the button above to download")
