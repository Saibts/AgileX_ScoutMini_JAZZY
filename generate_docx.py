import os
import zipfile
import xml.sax.saxutils as saxutils

def escape(text):
    return saxutils.escape(str(text))

class DocxBuilder:
    def __init__(self):
        self.body_xml = []
        
    def add_title(self, text, subtitle=None):
        self.body_xml.append(f"""
        <w:p>
            <w:pPr>
                <w:pStyle w:val="Title"/>
                <w:jc w:val="center"/>
                <w:spacing w:before="240" w:after="120"/>
            </w:pPr>
            <w:r>
                <w:rPr>
                    <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
                    <w:b/>
                    <w:sz w:val="48"/>
                    <w:szCs w:val="48"/>
                    <w:color w:val="003366"/>
                </w:rPr>
                <w:t>{escape(text)}</w:t>
            </w:r>
        </w:p>
        """)
        if subtitle:
            self.body_xml.append(f"""
            <w:p>
                <w:pPr>
                    <w:pStyle w:val="Subtitle"/>
                    <w:jc w:val="center"/>
                    <w:spacing w:before="0" w:after="360"/>
                </w:pPr>
                <w:r>
                    <w:rPr>
                        <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
                        <w:i/>
                        <w:sz w:val="28"/>
                        <w:szCs w:val="28"/>
                        <w:color w:val="4682B4"/>
                    </w:rPr>
                    <w:t>{escape(subtitle)}</w:t>
                </w:r>
            </w:p>
            """)

    def add_heading1(self, text):
        self.body_xml.append(f"""
        <w:p>
            <w:pPr>
                <w:pStyle w:val="Heading1"/>
                <w:spacing w:before="360" w:after="120"/>
                <w:pBdr>
                    <w:bottom w:val="single" w:sz="12" w:space="4" w:color="003366"/>
                </w:pBdr>
            </w:pPr>
            <w:r>
                <w:rPr>
                    <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
                    <w:b/>
                    <w:sz w:val="32"/>
                    <w:szCs w:val="32"/>
                    <w:color w:val="003366"/>
                </w:rPr>
                <w:t>{escape(text)}</w:t>
            </w:r>
        </w:p>
        """)

    def add_heading2(self, text):
        self.body_xml.append(f"""
        <w:p>
            <w:pPr>
                <w:pStyle w:val="Heading2"/>
                <w:spacing w:before="240" w:after="80"/>
            </w:pPr>
            <w:r>
                <w:rPr>
                    <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
                    <w:b/>
                    <w:sz w:val="26"/>
                    <w:szCs w:val="26"/>
                    <w:color w:val="2B579A"/>
                </w:rPr>
                <w:t>{escape(text)}</w:t>
            </w:r>
        </w:p>
        """)

    def add_heading3(self, text):
        self.body_xml.append(f"""
        <w:p>
            <w:pPr>
                <w:pStyle w:val="Heading3"/>
                <w:spacing w:before="160" w:after="60"/>
            </w:pPr>
            <w:r>
                <w:rPr>
                    <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
                    <w:b/>
                    <w:sz w:val="22"/>
                    <w:szCs w:val="22"/>
                    <w:color w:val="1E395B"/>
                </w:rPr>
                <w:t>{escape(text)}</w:t>
            </w:r>
        </w:p>
        """)

    def add_paragraph(self, text, bold_prefix=None, italic=False):
        runs = []
        if bold_prefix:
            runs.append(f"""
            <w:r>
                <w:rPr>
                    <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
                    <w:b/>
                    <w:sz w:val="22"/>
                    <w:szCs w:val="22"/>
                    <w:color w:val="222222"/>
                </w:rPr>
                <w:t xml:space="preserve">{escape(bold_prefix)} </w:t>
            </w:r>
            """)
        runs.append(f"""
        <w:r>
            <w:rPr>
                <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
                {"<w:i/>" if italic else ""}
                <w:sz w:val="22"/>
                <w:szCs w:val="22"/>
                <w:color w:val="333333"/>
            </w:rPr>
            <w:t xml:space="preserve">{escape(text)}</w:t>
        </w:r>
        """)
        self.body_xml.append(f"""
        <w:p>
            <w:pPr>
                <w:spacing w:before="60" w:after="100" w:line="276" w:lineRule="auto"/>
                <w:jc w:val="both"/>
            </w:pPr>
            {''.join(runs)}
        </w:p>
        """)

    def add_bullet(self, text, bold_prefix=None):
        runs = []
        if bold_prefix:
            runs.append(f"""
            <w:r>
                <w:rPr>
                    <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
                    <w:b/>
                    <w:sz w:val="22"/>
                    <w:szCs w:val="22"/>
                    <w:color w:val="111111"/>
                </w:rPr>
                <w:t xml:space="preserve">{escape(bold_prefix)} </w:t>
            </w:r>
            """)
        runs.append(f"""
        <w:r>
            <w:rPr>
                <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
                <w:sz w:val="22"/>
                <w:szCs w:val="22"/>
                <w:color w:val="333333"/>
            </w:rPr>
            <w:t xml:space="preserve">{escape(text)}</w:t>
        </w:r>
        """)
        self.body_xml.append(f"""
        <w:p>
            <w:pPr>
                <w:pStyle w:val="ListParagraph"/>
                <w:numPr>
                    <w:ilvl w:val="0"/>
                    <w:numId w:val="1"/>
                </w:numPr>
                <w:spacing w:before="40" w:after="60" w:line="260" w:lineRule="auto"/>
                <w:ind w:left="400" w:hanging="240"/>
            </w:pPr>
            <w:r>
                <w:rPr><w:rFonts w:ascii="Symbol" w:hAnsi="Symbol"/><w:sz w:val="20"/></w:rPr>
                <w:t>• </w:t>
            </w:r>
            {''.join(runs)}
        </w:p>
        """)

    def add_code_block(self, code_text):
        lines = code_text.strip().split('\n')
        runs = []
        for line in lines:
            runs.append(f"""
            <w:r>
                <w:rPr>
                    <w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/>
                    <w:sz w:val="19"/>
                    <w:szCs w:val="19"/>
                    <w:color w:val="1A365D"/>
                </w:rPr>
                <w:t xml:space="preserve">{escape(line)}</w:t>
                <w:br/>
            </w:r>
            """)
        self.body_xml.append(f"""
        <w:p>
            <w:pPr>
                <w:spacing w:before="100" w:after="100"/>
                <w:shd w:val="clear" w:color="auto" w:fill="F3F4F6"/>
                <w:pBdr>
                    <w:top w:val="single" w:sz="6" w:space="6" w:color="CBD5E1"/>
                    <w:left w:val="single" w:sz="24" w:space="8" w:color="2563EB"/>
                    <w:bottom w:val="single" w:sz="6" w:space="6" w:color="CBD5E1"/>
                    <w:right w:val="single" w:sz="6" w:space="6" w:color="CBD5E1"/>
                </w:pBdr>
                <w:ind w:left="200" w:right="200"/>
            </w:pPr>
            {''.join(runs)}
        </w:p>
        """)

    def add_placeholder_box(self, title, filename, timestamp, description, height_pt=180):
        self.body_xml.append(f"""
        <w:p>
            <w:pPr>
                <w:spacing w:before="160" w:after="80"/>
                <w:shd w:val="clear" w:color="auto" w:fill="F8FAFC"/>
                <w:pBdr>
                    <w:top w:val="single" w:sz="12" w:space="10" w:color="3B82F6"/>
                    <w:left w:val="single" w:sz="12" w:space="10" w:color="3B82F6"/>
                    <w:bottom w:val="single" w:sz="12" w:space="10" w:color="3B82F6"/>
                    <w:right w:val="single" w:sz="12" w:space="10" w:color="3B82F6"/>
                </w:pBdr>
                <w:ind w:left="240" w:right="240"/>
            </w:pPr>
            <w:r>
                <w:rPr>
                    <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
                    <w:b/>
                    <w:sz w:val="22"/>
                    <w:szCs w:val="22"/>
                    <w:color w:val="1E40AF"/>
                </w:rPr>
                <w:t>📷 {escape(title)}</w:t>
                <w:br/>
            </w:r>
            <w:r>
                <w:rPr>
                    <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
                    <w:b/>
                    <w:sz w:val="20"/>
                    <w:color w:val="475569"/>
                </w:rPr>
                <w:t xml:space="preserve">Target File: </w:t>
            </w:r>
            <w:r>
                <w:rPr>
                    <w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/>
                    <w:sz w:val="20"/>
                    <w:color w:val="0F172A"/>
                </w:rPr>
                <w:t>{escape(filename)}</w:t>
                <w:br/>
            </w:r>
            {"<w:r><w:rPr><w:rFonts w:ascii='Calibri'/><w:b/><w:sz w:val='20'/><w:color w:val='475569'/></w:rPr><w:t>Timestamp: </w:t></w:r><w:r><w:rPr><w:rFonts w:ascii='Consolas'/><w:sz w:val='20'/><w:color w:val='047857'/></w:rPr><w:t>" + escape(timestamp) + "</w:t><w:br/></w:r>" if timestamp else ""}
            <w:r>
                <w:rPr>
                    <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
                    <w:i/>
                    <w:sz w:val="20"/>
                    <w:color w:val="334155"/>
                </w:rPr>
                <w:t>Description: {escape(description)}</w:t>
                <w:br/><w:br/>
            </w:r>
            <w:r>
                <w:rPr>
                    <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
                    <w:b/>
                    <w:sz w:val="20"/>
                    <w:color w:val="64748B"/>
                </w:rPr>
                <w:t>================ [ PASTE / INSERT SCREENSHOT HERE ] ================</w:t>
                <w:br/><w:br/>
            </w:r>
        </w:p>
        """)

    def add_table(self, headers, rows, col_widths=None):
        table_xml = ['<w:tbl>', """
        <w:tblPr>
            <w:tblStyle w:val="TableGrid"/>
            <w:tblW w:w="9200" w:type="dxa"/>
            <w:tblBorders>
                <w:top w:val="single" w:sz="8" w:space="0" w:color="CBD5E1"/>
                <w:left w:val="single" w:sz="8" w:space="0" w:color="CBD5E1"/>
                <w:bottom w:val="single" w:sz="8" w:space="0" w:color="CBD5E1"/>
                <w:right w:val="single" w:sz="8" w:space="0" w:color="CBD5E1"/>
                <w:insideH w:val="single" w:sz="6" w:space="0" w:color="E2E8F0"/>
                <w:insideV w:val="single" w:sz="6" w:space="0" w:color="E2E8F0"/>
            </w:tblBorders>
            <w:tblLook w:val="04A0"/>
        </w:tblPr>
        """]
        
        # Header row
        table_xml.append('<w:tr><w:trPr><w:tblHeader/></w:trPr>')
        for idx, h in enumerate(headers):
            w_xml = f'<w:tcW w:w="{col_widths[idx]}" w:type="dxa"/>' if col_widths else '<w:tcW w:w="2300" w:type="dxa"/>'
            table_xml.append(f"""
            <w:tc>
                <w:tcPr>
                    {w_xml}
                    <w:shd w:val="clear" w:color="auto" w:fill="003366"/>
                    <w:tcMar><w:top w:w="120"/><w:bottom w:w="120"/><w:left w:w="140"/><w:right w:w="140"/></w:tcMar>
                </w:tcPr>
                <w:p>
                    <w:pPr><w:spacing w:before="60" w:after="60"/></w:pPr>
                    <w:r>
                        <w:rPr>
                            <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
                            <w:b/>
                            <w:sz w:val="21"/>
                            <w:color w:val="FFFFFF"/>
                        </w:rPr>
                        <w:t>{escape(h)}</w:t>
                    </w:r>
                </w:p>
            </w:tc>
            """)
        table_xml.append('</w:tr>')
        
        # Data rows
        for r_idx, row in enumerate(rows):
            bg = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
            table_xml.append('<w:tr>')
            for c_idx, cell in enumerate(row):
                w_xml = f'<w:tcW w:w="{col_widths[c_idx]}" w:type="dxa"/>' if col_widths else '<w:tcW w:w="2300" w:type="dxa"/>'
                table_xml.append(f"""
                <w:tc>
                    <w:tcPr>
                        {w_xml}
                        <w:shd w:val="clear" w:color="auto" w:fill="{bg}"/>
                        <w:tcMar><w:top w:w="100"/><w:bottom w:w="100"/><w:left w:w="140"/><w:right w:w="140"/></w:tcMar>
                    </w:tcPr>
                    <w:p>
                        <w:pPr><w:spacing w:before="40" w:after="40"/></w:pPr>
                        <w:r>
                            <w:rPr>
                                <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
                                <w:sz w:val="20"/>
                                <w:color w:val="1E293B"/>
                            </w:rPr>
                            <w:t>{escape(cell)}</w:t>
                        </w:r>
                    </w:p>
                </w:tc>
                """)
            table_xml.append('</w:tr>')
            
        table_xml.append('</w:tbl>')
        self.body_xml.append(''.join(table_xml))

    def add_page_break(self):
        self.body_xml.append("""
        <w:p>
            <w:r>
                <w:br w:type="page"/>
            </w:r>
        </w:p>
        """)

    def build_docx(self, output_path):
        doc_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
                    xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
            <w:body>
                {''.join(self.body_xml)}
                <w:sectPr>
                    <w:pgSz w:w="12240" w:h="15840"/>
                    <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/>
                    <w:cols w:space="720"/>
                    <w:docGrid w:linePitch="360"/>
                </w:sectPr>
            </w:body>
        </w:document>
        """

        content_types_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
            <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
            <Default Extension="xml" ContentType="application/xml"/>
            <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
            <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
        </Types>
        """

        rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
            <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
        </Relationships>
        """

        doc_rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
            <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
        </Relationships>
        """

        styles_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
            <w:docDefaults>
                <w:rPrDefault>
                    <w:rPr>
                        <w:rFonts w:ascii="Calibri" w:eastAsia="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/>
                        <w:sz w:val="22"/>
                        <w:szCs w:val="22"/>
                        <w:lang w:val="en-US"/>
                    </w:rPr>
                </w:rPrDefault>
            </w:docDefaults>
        </w:styles>
        """

        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('[Content_Types].xml', content_types_xml)
            z.writestr('_rels/.rels', rels_xml)
            z.writestr('word/_rels/document.xml.rels', doc_rels_xml)
            z.writestr('word/styles.xml', styles_xml)
            z.writestr('word/document.xml', doc_xml)

print("DocxBuilder initialized.")
