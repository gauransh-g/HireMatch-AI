from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

def generate_candidate_pdf(candidate: dict, job: dict, match_res: dict) -> bytes:
    """Generate a clean, professional candidate evaluation report in PDF format."""
    buffer = BytesIO()
    
    # Page setup - 0.75 in (54pt) margins
    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
        title=f"Evaluation Report - {candidate['name']}",
        author="HireMatch AI"
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Palette
    c_primary = colors.HexColor("#312e81")  # Deep Indigo
    c_secondary = colors.HexColor("#4f46e5")  # Indigo accent
    c_text_dark = colors.HexColor("#1f2937")  # Charcoal
    c_text_muted = colors.HexColor("#6b7280")  # Slate Gray
    c_border = colors.HexColor("#e5e7eb")  # Light gray
    c_green = colors.HexColor("#047857")  # Forest Green
    c_red = colors.HexColor("#b91c1c")  # Crimson
    
    # Custom Typography Styles
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        textColor=c_primary,
        alignment=0,  # Left align
        spaceAfter=5
    )
    
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=c_text_muted,
        spaceAfter=15
    )
    
    h1_style = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        textColor=c_primary,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        textColor=c_text_dark,
        leading=14,
        spaceAfter=4
    )
    
    bullet_style = ParagraphStyle(
        "Bullet_Custom",
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=3
    )
    
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8,
        textColor=c_text_muted,
        leading=11,
        alignment=1  # Centered
    )

    story = []
    
    # Header Section
    story.append(Paragraph("HireMatch AI — Evaluation Report", title_style))
    story.append(Paragraph(f"Generated on behalf of hiring teams • System: HireMatch AI v1.0", subtitle_style))
    story.append(Spacer(1, 5))
    
    # Candidate & Job Metadata Table
    meta_data = [
        [
            Paragraph("<b>Candidate Name:</b>", body_style),
            Paragraph(candidate["name"], body_style),
            Paragraph("<b>Target Role:</b>", body_style),
            Paragraph(job["title"], body_style)
        ],
        [
            Paragraph("<b>Experience:</b>", body_style),
            Paragraph(f"{candidate['experience_years']:.1f} years", body_style),
            Paragraph("<b>Role Family:</b>", body_style),
            Paragraph(job["role_family"].replace("_", " ").title(), body_style)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[110, 140, 90, 160])
    meta_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, c_border),
        ("GRID", (0, 0), (-1, -1), 0.5, c_border),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f9fafb")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))
    
    # Score Breakdown Section
    story.append(Paragraph("Overall Match Score", h1_style))
    
    # Overall Score block
    score_style_big = ParagraphStyle(
        "ScoreBig",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=32,
        textColor=c_secondary,
        alignment=1  # Centered
    )
    score_lbl_style = ParagraphStyle(
        "ScoreLbl",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=c_text_dark,
        alignment=1
    )
    
    # Layout with score circle/block on left, progress bars on right
    score_val = match_res["overall_score"]
    score_table_data = [
        [
            [
                Spacer(1, 8),
                Paragraph(f"{score_val:.1f}%", score_style_big),
                Paragraph("MATCH SCORE", score_lbl_style),
                Spacer(1, 8)
            ],
            [
                Paragraph(f"<b>Skill Match (35%):</b> {match_res['skill_score']}%", body_style),
                Paragraph(f"<b>Experience Match (25%):</b> {match_res['experience_score']}%", body_style),
                Paragraph(f"<b>Responsibility Match (20%):</b> {match_res['responsibility_score']}%", body_style),
                Paragraph(f"<b>Education Match (10%):</b> {match_res['education_score']}%", body_style),
                Paragraph(f"<b>Semantic Similarity (10%):</b> {match_res['semantic_score']}%", body_style),
            ]
        ]
    ]
    
    score_table = Table(score_table_data, colWidths=[150, 350])
    score_table.setStyle(TableStyle([
        ("BOX", (0, 0), (0, 0), 1.5, c_secondary),
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#e0e7ff")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (0, 0), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 1), (-1, -1), 15),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 15))
    
    # Summary Recommendation
    story.append(Paragraph("Executive Summary", h1_style))
    story.append(Paragraph(match_res["summary"], body_style))
    story.append(Spacer(1, 12))
    
    # Skills Analysis
    story.append(Paragraph("Technical Skills Inventory", h1_style))
    
    # Split skills into paragraphs
    matched_p = Paragraph(
        f"<b>Matched Skills:</b> " +
        ", ".join([f"<font color='{c_green.hexval()}'>✓ {s}</font>" for s in match_res["matched_skills"]]) if match_res["matched_skills"] else "None detected",
        body_style
    )
    
    missing_p = Paragraph(
        f"<b>Missing/Unmatched Skills:</b> " +
        ", ".join([f"<font color='{c_red.hexval()}'>⚠ {s}</font>" for s in match_res["missing_skills"]]) if match_res["missing_skills"] else "None",
        body_style
    )
    
    skills_data = [[matched_p], [Spacer(1, 4)], [missing_p]]
    skills_table = Table(skills_data, colWidths=[500])
    skills_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, c_border),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fafafa")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(skills_table)
    story.append(Spacer(1, 15))
    
    # Strengths and Concerns
    story.append(Paragraph("Explainable Findings", h1_style))
    
    findings_data = []
    
    # Strengths (Indigo bullet)
    findings_data.append([Paragraph("<b>Key Strengths</b>", body_style), Paragraph("<b>Areas of Concern / Gaps</b>", body_style)])
    
    strength_bullets = []
    for s in match_res["strengths"]:
        strength_bullets.append(Paragraph(f"<font color='{c_green.hexval()}'>•</font> {s}", bullet_style))
    if not strength_bullets:
        strength_bullets.append(Paragraph("No critical strengths highlighted", bullet_style))
        
    concern_bullets = []
    for c in match_res["concerns"]:
        concern_bullets.append(Paragraph(f"<font color='{c_red.hexval()}'>•</font> {c}", bullet_style))
    if not concern_bullets:
        concern_bullets.append(Paragraph("No critical areas of concern highlighted", bullet_style))
        
    findings_data.append([strength_bullets, concern_bullets])
    
    findings_table = Table(findings_data, colWidths=[250, 250])
    findings_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (1, 0), 1, c_secondary),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 1), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(findings_table)
    story.append(Spacer(1, 20))
    
    # Responsible AI Notice at bottom
    story.append(Spacer(1, 10))
    story.append(Table([
        [
            Paragraph(
                "<b>Responsible AI Notice:</b> This evaluation report is generated to assist recruiters and HR teams. "
                "It evaluates job-relevant skills, experience, education, and semantic similarity. "
                "It does not evaluate personal demographic factors and should not independently determine employment decisions. "
                "Human review is required for final screening and hiring decisions.",
                disclaimer_style
            )
        ]
    ], colWidths=[500], style=[
        ("BOX", (0, 0), (-1, -1), 0.5, c_border),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fef2f2")),  # Light red warning background
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    
    doc.build(story)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
