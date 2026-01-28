"""
PDF generation service for medical records.

Uses ReportLab for PDF generation.
"""
import io
from datetime import datetime
from django.conf import settings
from django.utils import timezone

# Try importing reportlab, provide fallback if not installed
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        PageBreak,
        Image,
        HRFlowable
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class MedicalRecordPDFService:
    """Service for generating PDF versions of medical records."""
    
    # Page settings
    PAGE_SIZE = A4 if REPORTLAB_AVAILABLE else None
    MARGIN = 0.75 * inch if REPORTLAB_AVAILABLE else None
    
    # Colors
    PRIMARY_COLOR = colors.HexColor('#4A90A4') if REPORTLAB_AVAILABLE else None
    SECONDARY_COLOR = colors.HexColor('#6c757d') if REPORTLAB_AVAILABLE else None
    HEADER_BG = colors.HexColor('#f8f9fa') if REPORTLAB_AVAILABLE else None
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if PDF generation is available."""
        return REPORTLAB_AVAILABLE
    
    @classmethod
    def generate_single_record_pdf(cls, medical_record, include_attachments=False) -> io.BytesIO:
        """
        Generate a PDF for a single medical record.
        
        Args:
            medical_record: MedicalRecord instance
            include_attachments: Whether to list attachments
        
        Returns:
            BytesIO buffer containing the PDF
        """
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError(
                'ReportLab is not installed. Install it with: pip install reportlab'
            )
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=cls.PAGE_SIZE,
            rightMargin=cls.MARGIN,
            leftMargin=cls.MARGIN,
            topMargin=cls.MARGIN,
            bottomMargin=cls.MARGIN
        )
        
        elements = []
        styles = cls._get_styles()
        
        # Header
        elements.extend(cls._build_header(medical_record.patient, styles))
        elements.append(Spacer(1, 0.3 * inch))
        
        # Record details
        elements.extend(cls._build_record_section(medical_record, styles))
        
        # Prescription if exists
        if hasattr(medical_record, 'prescription'):
            elements.append(Spacer(1, 0.3 * inch))
            elements.extend(cls._build_prescription_section(medical_record.prescription, styles))
        
        # Allergy if exists
        if hasattr(medical_record, 'allergy'):
            elements.append(Spacer(1, 0.3 * inch))
            elements.extend(cls._build_allergy_section(medical_record.allergy, styles))
        
        # Attachments list
        if include_attachments and medical_record.attachments.exists():
            elements.append(Spacer(1, 0.3 * inch))
            elements.extend(cls._build_attachments_section(medical_record, styles))
        
        # Notes
        visible_notes = medical_record.notes.filter(is_locked=False)
        if visible_notes.exists():
            elements.append(Spacer(1, 0.3 * inch))
            elements.extend(cls._build_notes_section(visible_notes, styles))
        
        # Footer
        elements.append(Spacer(1, 0.5 * inch))
        elements.extend(cls._build_footer(styles))
        
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    @classmethod
    def generate_patient_summary_pdf(cls, patient, records=None) -> io.BytesIO:
        """
        Generate a PDF summary of all medical records for a patient.
        
        Args:
            patient: User instance (patient)
            records: Optional QuerySet of records to include
        
        Returns:
            BytesIO buffer containing the PDF
        """
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError(
                'ReportLab is not installed. Install it with: pip install reportlab'
            )
        
        from medical_record.models import MedicalRecord
        
        if records is None:
            records = MedicalRecord.objects.filter(
                patient=patient,
                is_active=True
            ).select_related('created_by').prefetch_related(
                'prescription', 'allergy'
            ).order_by('-record_date')
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=cls.PAGE_SIZE,
            rightMargin=cls.MARGIN,
            leftMargin=cls.MARGIN,
            topMargin=cls.MARGIN,
            bottomMargin=cls.MARGIN
        )
        
        elements = []
        styles = cls._get_styles()
        
        # Header
        elements.extend(cls._build_header(patient, styles, title='Medical Records Summary'))
        elements.append(Spacer(1, 0.3 * inch))
        
        # Summary statistics
        elements.extend(cls._build_summary_stats(records, styles))
        elements.append(Spacer(1, 0.3 * inch))
        
        # Records table
        elements.extend(cls._build_records_table(records, styles))
        
        # Individual record details
        for i, record in enumerate(records[:20]):  # Limit to 20 records
            elements.append(PageBreak())
            elements.extend(cls._build_record_section(record, styles))
            
            if hasattr(record, 'prescription'):
                elements.append(Spacer(1, 0.2 * inch))
                elements.extend(cls._build_prescription_section(record.prescription, styles))
        
        # Footer
        elements.append(Spacer(1, 0.5 * inch))
        elements.extend(cls._build_footer(styles))
        
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    @classmethod
    def _get_styles(cls):
        """Get custom paragraph styles."""
        styles = getSampleStyleSheet()
        
        # Title style
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=cls.PRIMARY_COLOR,
            spaceAfter=12,
            alignment=TA_CENTER
        ))
        
        # Section header
        styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=cls.PRIMARY_COLOR,
            spaceBefore=12,
            spaceAfter=6,
            borderColor=cls.PRIMARY_COLOR,
            borderWidth=1,
            borderPadding=3
        ))
        
        # Label style
        styles.add(ParagraphStyle(
            name='FieldLabel',
            parent=styles['Normal'],
            fontSize=9,
            textColor=cls.SECONDARY_COLOR,
            spaceAfter=2
        ))
        
        # Value style
        styles.add(ParagraphStyle(
            name='FieldValue',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6
        ))
        
        # Footer style
        styles.add(ParagraphStyle(
            name='Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=cls.SECONDARY_COLOR,
            alignment=TA_CENTER
        ))
        
        return styles
    
    @classmethod
    def _build_header(cls, patient, styles, title='Medical Record'):
        """Build the PDF header section."""
        elements = []
        
        # Title
        elements.append(Paragraph(title, styles['CustomTitle']))
        
        # Horizontal rule
        elements.append(HRFlowable(
            width='100%',
            thickness=1,
            color=cls.PRIMARY_COLOR,
            spaceAfter=12
        ))
        
        # Patient info table
        patient_name = f"{patient.first_name} {patient.last_name}" if patient.first_name else patient.email
        
        patient_data = [
            ['Patient Name:', patient_name],
            ['Email:', patient.email],
            ['Generated:', timezone.now().strftime('%B %d, %Y at %I:%M %p')],
        ]
        
        if hasattr(patient, 'phone_number') and patient.phone_number:
            patient_data.insert(2, ['Phone:', str(patient.phone_number)])
        
        patient_table = Table(patient_data, colWidths=[1.5 * inch, 4 * inch])
        patient_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (0, -1), cls.SECONDARY_COLOR),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        elements.append(patient_table)
        
        return elements
    
    @classmethod
    def _build_record_section(cls, record, styles):
        """Build the record details section."""
        elements = []
        
        elements.append(Paragraph(f'📋 {record.title}', styles['SectionHeader']))
        
        # Record info table
        record_data = [
            ['Type:', record.get_record_type_display()],
            ['Date:', record.record_date.strftime('%B %d, %Y') if record.record_date else 'N/A'],
            ['Status:', 'Active' if record.is_active else 'Archived'],
        ]
        
        if record.diagnosis_code:
            record_data.append(['Diagnosis Code:', record.diagnosis_code])
        
        if record.created_by:
            provider_name = f"{record.created_by.first_name} {record.created_by.last_name}".strip()
            record_data.append(['Provider:', provider_name or record.created_by.email])
        
        record_table = Table(record_data, colWidths=[1.5 * inch, 4.5 * inch])
        record_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), cls.SECONDARY_COLOR),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('BACKGROUND', (0, 0), (-1, -1), cls.HEADER_BG),
            ('BOX', (0, 0), (-1, -1), 0.5, cls.SECONDARY_COLOR),
        ]))
        
        elements.append(record_table)
        elements.append(Spacer(1, 0.15 * inch))
        
        # Description
        if record.description:
            elements.append(Paragraph('Description:', styles['FieldLabel']))
            elements.append(Paragraph(record.description, styles['FieldValue']))
        
        # Symptoms
        if record.symptoms:
            elements.append(Paragraph('Symptoms:', styles['FieldLabel']))
            elements.append(Paragraph(record.symptoms, styles['FieldValue']))
        
        # Follow-up
        if record.requires_followup:
            followup_text = f"Follow-up required"
            if record.followup_date:
                followup_text += f" on {record.followup_date.strftime('%B %d, %Y')}"
            elements.append(Paragraph(f'⚠️ {followup_text}', styles['FieldValue']))
        
        return elements
    
    @classmethod
    def _build_prescription_section(cls, prescription, styles):
        """Build the prescription section."""
        elements = []
        
        elements.append(Paragraph('💊 Prescription', styles['SectionHeader']))
        
        rx_data = [
            ['Medication:', prescription.medication_name],
            ['Dosage:', prescription.dosage],
            ['Frequency:', prescription.frequency],
        ]
        
        if prescription.duration:
            rx_data.append(['Duration:', prescription.duration])
        
        if prescription.quantity:
            rx_data.append(['Quantity:', str(prescription.quantity)])
        
        if prescription.refills:
            rx_data.append(['Refills:', str(prescription.refills)])
        
        rx_table = Table(rx_data, colWidths=[1.5 * inch, 4.5 * inch])
        rx_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), cls.SECONDARY_COLOR),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fff3cd')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#ffc107')),
        ]))
        
        elements.append(rx_table)
        
        if prescription.instructions:
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph('Instructions:', styles['FieldLabel']))
            elements.append(Paragraph(prescription.instructions, styles['FieldValue']))
        
        return elements
    
    @classmethod
    def _build_allergy_section(cls, allergy, styles):
        """Build the allergy section."""
        elements = []
        
        elements.append(Paragraph('⚠️ Allergy Information', styles['SectionHeader']))
        
        allergy_data = [
            ['Allergen:', allergy.allergen],
            ['Severity:', allergy.get_severity_display()],
        ]
        
        if allergy.first_observed:
            allergy_data.append(['First Observed:', allergy.first_observed.strftime('%B %d, %Y')])
        
        allergy_table = Table(allergy_data, colWidths=[1.5 * inch, 4.5 * inch])
        allergy_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), cls.SECONDARY_COLOR),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8d7da')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#dc3545')),
        ]))
        
        elements.append(allergy_table)
        
        if allergy.reaction:
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph('Reaction:', styles['FieldLabel']))
            elements.append(Paragraph(allergy.reaction, styles['FieldValue']))
        
        return elements
    
    @classmethod
    def _build_attachments_section(cls, record, styles):
        """Build the attachments list section."""
        elements = []
        
        elements.append(Paragraph('📎 Attachments', styles['SectionHeader']))
        
        attach_data = [['#', 'File Name', 'Type', 'Uploaded']]
        
        for i, attachment in enumerate(record.attachments.all(), 1):
            attach_data.append([
                str(i),
                attachment.file_name[:40] + '...' if len(attachment.file_name) > 40 else attachment.file_name,
                attachment.file_type or 'Unknown',
                attachment.uploaded_at.strftime('%Y-%m-%d') if attachment.uploaded_at else 'N/A'
            ])
        
        attach_table = Table(attach_data, colWidths=[0.4 * inch, 3 * inch, 1.2 * inch, 1.2 * inch])
        attach_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), cls.HEADER_BG),
            ('GRID', (0, 0), (-1, -1), 0.5, cls.SECONDARY_COLOR),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        elements.append(attach_table)
        
        return elements
    
    @classmethod
    def _build_notes_section(cls, notes, styles):
        """Build the notes section."""
        elements = []
        
        elements.append(Paragraph('📝 Notes', styles['SectionHeader']))
        
        for note in notes:
            note_header = f"{note.get_note_type_display()} - {note.created_at.strftime('%Y-%m-%d %H:%M')}"
            elements.append(Paragraph(note_header, styles['FieldLabel']))
            elements.append(Paragraph(note.content, styles['FieldValue']))
            elements.append(Spacer(1, 0.1 * inch))
        
        return elements
    
    @classmethod
    def _build_summary_stats(cls, records, styles):
        """Build summary statistics section."""
        elements = []
        
        elements.append(Paragraph('📊 Summary', styles['SectionHeader']))
        
        # Count by type
        from collections import Counter
        type_counts = Counter(r.record_type for r in records)
        
        stats_data = [
            ['Total Records:', str(records.count())],
            ['Active Records:', str(sum(1 for r in records if r.is_active))],
            ['Requiring Follow-up:', str(sum(1 for r in records if r.requires_followup))],
        ]
        
        stats_table = Table(stats_data, colWidths=[2 * inch, 2 * inch])
        stats_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), cls.SECONDARY_COLOR),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        elements.append(stats_table)
        
        return elements
    
    @classmethod
    def _build_records_table(cls, records, styles):
        """Build a table of all records."""
        elements = []
        
        elements.append(Paragraph('📋 Records List', styles['SectionHeader']))
        
        table_data = [['#', 'Date', 'Title', 'Type', 'Status']]
        
        for i, record in enumerate(records, 1):
            table_data.append([
                str(i),
                record.record_date.strftime('%Y-%m-%d') if record.record_date else 'N/A',
                record.title[:30] + '...' if len(record.title) > 30 else record.title,
                record.get_record_type_display(),
                'Active' if record.is_active else 'Archived'
            ])
        
        records_table = Table(table_data, colWidths=[0.4 * inch, 1 * inch, 2.5 * inch, 1.3 * inch, 0.8 * inch])
        records_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), cls.HEADER_BG),
            ('GRID', (0, 0), (-1, -1), 0.5, cls.SECONDARY_COLOR),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ]))
        
        elements.append(records_table)
        
        return elements
    
    @classmethod
    def _build_footer(cls, styles):
        """Build the PDF footer."""
        elements = []
        
        elements.append(HRFlowable(
            width='100%',
            thickness=0.5,
            color=cls.SECONDARY_COLOR,
            spaceBefore=12
        ))
        
        footer_text = (
            f"This document was generated by Medilink on {timezone.now().strftime('%B %d, %Y at %I:%M %p')}. "
            "This is an official medical record document. Please keep it confidential."
        )
        elements.append(Paragraph(footer_text, styles['Footer']))
        
        return elements
