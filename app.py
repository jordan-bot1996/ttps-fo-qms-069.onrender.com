import io, json
from flask import Flask, request, send_file, jsonify
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib import colors
from reportlab.lib.units import mm
from pypdf import PdfWriter, PdfReader
from pypdf.generic import (
    NameObject, ArrayObject, NumberObject,
    TextStringObject, DictionaryObject, BooleanObject
)

app = Flask(__name__)

W, H = A4
ML = 12*mm; PW = W - 2*ML

BLUE   = colors.HexColor("#1B4F8A")
BLUE2  = colors.HexColor("#2E7BC4")
BLUE_L = colors.HexColor("#E8F0FA")
BLUE_LL= colors.HexColor("#F5F8FD")
GREEN  = colors.HexColor("#28A745")
RED    = colors.HexColor("#DC3545")
RED_L  = colors.HexColor("#FFF0F0")
WARN_L = colors.HexColor("#FFF8E1")
WARN_S = colors.HexColor("#FFB300")
GREY_L = colors.HexColor("#F0F4F9")
STROKE = colors.HexColor("#DADADA")
WHITE  = colors.white
BLACK  = colors.black

def gen_pdf(data):
    ref   = data.get('ref', 'REF')
    plan  = data.get('plan', {})
    op    = data.get('op', {})
    mal   = op.get('mal', False)
    lngRH = op.get('lngRH', '')
    lngLH = op.get('lngLH', '')
    buf  = io.BytesIO()
    fields = []
    c = rl_canvas.Canvas(buf, pagesize=A4)

    def box(x,y,w,h,fill,stroke=None,lw=0.5,radius=0):
        c.setFillColor(fill)
        c.setStrokeColor(stroke or fill); c.setLineWidth(lw if stroke else 0)
        if radius: c.roundRect(x,y,w,h,radius,fill=1,stroke=1 if stroke else 0)
        else:      c.rect(x,y,w,h,fill=1,stroke=1 if stroke else 0)

    def txt(x,y,s,size=8,bold=False,col=BLACK,align="left",maxw=0):
        c.setFillColor(col)
        fn="Helvetica-Bold" if bold else "Helvetica"
        c.setFont(fn,size)
        if align=="center" and maxw: x+=(maxw-c.stringWidth(s,fn,size))/2
        elif align=="right" and maxw: x+=maxw-c.stringWidth(s,fn,size)
        c.drawString(x,y,s)

    def field_plan(x,y,w,h,value,name):
        box(x+1*mm,y+1.5*mm,w-2*mm,h-3*mm,BLUE_L,stroke=BLUE2,lw=1,radius=2)
        if value:
            c.setFillColor(BLUE); c.setFont("Helvetica-Bold",9)
            tw=c.stringWidth(str(value),"Helvetica-Bold",9)
            c.drawString(x+1*mm+(w-2*mm-tw)/2,y+h/2-1.5*mm,str(value))
        fields.append((name,x+1*mm,y+1.5*mm,w-2*mm,h-3*mm,True,str(value or '')))

    def field_mes(x,y,w,h,name):
        box(x+1*mm,y+1.5*mm,w-2*mm,h-3*mm,WHITE,stroke=GREEN,lw=1.8,radius=2)
        fields.append((name,x+1*mm,y+1.5*mm,w-2*mm,h-3*mm,False,''))

    def cell_lbl(x,y,w,h,lines,bg):
        box(x,y,w,h,bg,stroke=STROKE,lw=0.3)
        c.setFillColor(BLACK); c.setFont("Helvetica",8.5)
        total=len(lines)*4*mm; sy=y+h/2+total/2-3.5*mm
        for i,ln in enumerate(lines): c.drawString(x+2*mm,sy-i*4*mm,ln)

    def hdr_cell(x,y,w,h,s):
        box(x,y,w,h,BLUE2,stroke=BLUE2,lw=0.3)
        c.setFillColor(WHITE); c.setFont("Helvetica-Bold",7.5)
        tw=c.stringWidth(s,"Helvetica-Bold",7.5)
        c.drawString(x+(w-tw)/2,y+h/2-2.5*mm,s)

    # EN-TÊTE
    y=H-12*mm; bh=18*mm
    box(0,y-bh,W,bh,BLUE); box(0,y-bh,4*mm,bh,BLUE2)
    txt(ML+3*mm,y-bh/2-4*mm,"TAC",20,True,WHITE)
    box(ML+3*mm,y-bh/2-7*mm,20*mm,1.5*mm,BLUE2)
    t="Formulaire de contrôle 1ère pièce — Rétreint"
    c.setFont("Helvetica-Bold",12); c.setFillColor(WHITE)
    c.drawString(W/2-c.stringWidth(t,"Helvetica-Bold",12)/2,y-bh/2-2*mm,t)
    box(W-ML-38*mm,y-bh+3*mm,36*mm,10*mm,BLUE2,radius=4)
    txt(W-ML-38*mm,y-bh+3*mm+3*mm,"FO-QMS-069",9,True,WHITE,"center",36*mm)
    c.setFont("Helvetica",6.5); c.setFillColor(colors.HexColor("#B0C8E8"))
    sub="Indice D  |  Page 1/1  |  21/12/2018"
    c.drawString(W-ML-c.stringWidth(sub,"Helvetica",6.5),y-5*mm,sub)
    y-=bh; box(0,y-2*mm,W,2*mm,BLUE2); y-=2*mm+4*mm

    # AVERTISSEMENT
    ah=10*mm
    box(ML,y-ah,PW,ah,WARN_L,stroke=WARN_S,lw=0.8,radius=3)
    box(ML,y-ah,3*mm,ah,WARN_S,radius=2)
    txt(ML+5*mm,y-4.5*mm,"⚠  Cette fiche est à intégrer à tous ordres de fabrication",7.5,True,colors.HexColor("#7A5500"))
    txt(ML+5*mm,y-9*mm,"ATTENTION : LE CONTRÔLE EST A EFFECTUER PAR UN OPERATEUR DU MEME FLUX OU UN CONTROLEUR QUALITE.",7,False,colors.HexColor("#7A5500"))
    y-=ah+4*mm

    # IDENTIFICATION
    id_h=12*mm; gap=3*mm; iw=(PW-3*gap)/4
    for i,(lbl,val) in enumerate([("Référence pièce",ref),("N° OF",None),("Machine utilisée",None),("Cachet RH / LH",None)]):
        cx=ML+i*(iw+gap)
        box(cx,y-id_h,iw,id_h,GREY_L,stroke=STROKE,lw=0.4,radius=3)
        box(cx,y-3.5*mm,iw,3.5*mm,BLUE2,radius=2)
        txt(cx+2*mm,y-2.8*mm,lbl,7,True,WHITE)
        if val: txt(cx+2*mm,y-id_h/2-1.5*mm,val,9,True,BLUE)
        else:   fields.append((f"id_{i}",cx+1*mm,y-id_h+1.5*mm,iw-2*mm,id_h-5*mm,False,''))
    y-=id_h+4*mm

    # MAL supprimé à la demande

    # LONGUEURS À REPRENDRE — champs interactifs remplissables
    lr_h=16*mm; half=(PW-gap)/2
    for i,(side,val) in enumerate([("RH", lngRH),("LH", lngLH)]):
        cx=ML+i*(half+gap)
        box(cx,y-lr_h,half,lr_h,RED_L,stroke=RED,lw=1,radius=3)
        txt(cx+4*mm,y-5.5*mm,f"Longueur à reprendre côté {side} :",7.5,True,RED)
        # Champ interactif remplissable (fond blanc, bordure rouge)
        box(cx+4*mm, y-lr_h+1.5*mm, half-6*mm, lr_h/2, WHITE, stroke=RED, lw=1.2, radius=2)
        if val:
            c.setFillColor(RED); c.setFont("Helvetica-Bold",13)
            c.drawString(cx+6*mm, y-lr_h+4*mm, str(val))
        fields.append((f"lng_{side.lower()}", cx+4*mm, y-lr_h+1.5*mm, half-6*mm, lr_h/2, False, str(val or '')))
    y-=lr_h+5*mm

    def section(y,side):
        s=side.lower()
        pm={k:plan.get(f'{s}_{k}','') for k in ['di_min','lpl','lt','de_min','ang1','ang2']}
        sh=10*mm
        box(ML,y-sh,PW,sh,BLUE,radius=4); box(ML+PW-11*mm,y-sh,9*mm,sh,BLUE2,radius=3)
        c.setFont("Helvetica-Bold",12); c.setFillColor(WHITE)
        t=f"Rétreint côté {side}"
        c.drawString(ML+(PW-c.stringWidth(t,"Helvetica-Bold",11))/2,y-sh/2-3*mm,t)
        y-=sh+1*mm

        cA=PW*0.27; cB=PW*0.11; cC=PW*0.12; sp=PW*0.02
        cD=PW*0.21; cE=PW*0.055; cF=PW*0.055; cG=PW*0.13
        xA=ML; xB=xA+cA; xC=xB+cB; xD=xC+cC+sp; xE=xD+cD; xF=xE+cE; xG=xF+cF

        # Colonnes : A=label | B=val.min | C=val.mes | SEP | D=label | E=cote plan | G=val.mes
        # Pour angle : E=ang1 | F=ang2 | G=val.mes
        hh=10*mm
        hdr_cell(xA,y-hh,cA,hh,"Type de contrôle")
        hdr_cell(xB,y-hh,cB,hh,"Val. min. (mm)")
        hdr_cell(xC,y-hh,cC,hh,"Val. mesurée (mm)")
        box(xC+cC,y-hh,sp,hh,WHITE)
        hdr_cell(xD,y-hh,cD,hh,"Type de contrôle")
        hdr_cell(xE,y-hh,cE+cF,hh,"Cote plan")
        hdr_cell(xG,y-hh,cG,hh,"Val. mesurée")
        y-=hh

        rh1=26*mm
        # Ø intérieur
        cell_lbl(xA,y-rh1,cA,rh1,["Ø intérieur (mm) svt OP-PRO-098","0,15 mm min. en dessous","du Ø d'alésage av. taraudage"],BLUE_L)
        field_plan(xB,y-rh1,cB,rh1,pm['di_min'],f"{s}_di_min_v")
        field_mes(xC,y-rh1,cC,rh1,f"{s}_di_mes")
        box(xC+cC,y-rh1,sp,rh1,WHITE)
        # Long. plat rétreint + Longueur totale — une seule case "Cote plan"
        rh2=rh1/2
        for i,(lab,kp,km) in enumerate([("Long. plat rétreint (mm)","lpl",f"{s}_lpl_mes"),("Longueur totale (mm)","lt",f"{s}_lt_mes")]):
            ry=y-i*rh2
            cell_lbl(xD,ry-rh2,cD,rh2,[lab],BLUE_L)
            field_plan(xE,ry-rh2,cE+cF,rh2,pm[kp],f"{s}_{kp}_v")
            field_mes(xG,ry-rh2,cG,rh2,km)
        y-=rh1

        rh3=16*mm
        # Ø extérieur
        cell_lbl(xA,y-rh3,cA,rh3,["Ø extérieur (mm)"],BLUE_LL)
        field_plan(xB,y-rh3,cB,rh3,pm['de_min'],f"{s}_de_min_v")
        field_mes(xC,y-rh3,cC,rh3,f"{s}_de_mes")
        box(xC+cC,y-rh3,sp,rh3,WHITE)
        # Angle : subdiviser "Cote plan" en 2 (ang1 | ang2)
        cell_lbl(xD,y-rh3,cD,rh3,["Angle de rétreint (°)"],BLUE_LL)
        ang_w=(cE+cF)/2
        field_plan(xE,        y-rh3,ang_w,rh3,pm['ang1'],f"{s}_ang1_v")
        field_plan(xE+ang_w,  y-rh3,ang_w,rh3,pm['ang2'],f"{s}_ang2_v")
        field_mes(xG,y-rh3,cG,rh3,f"{s}_ang_mes")
        # Labels Ang.1 / Ang.2 en petit
        c.setFillColor(colors.HexColor("#6C757D")); c.setFont("Helvetica",6)
        c.drawString(xE+1*mm,       y-rh3+2*mm, "Ang.1")
        c.drawString(xE+ang_w+1*mm, y-rh3+2*mm, "Ang.2")
        y-=rh3
        return y

    y=section(y,"RH"); y-=6*mm
    y=section(y,"LH"); y-=6*mm

    ph=9*mm
    box(ML,y-ph,PW,ph,RED_L,stroke=RED,lw=0.6,radius=3)
    box(ML,y-ph,3*mm,ph,RED,radius=2)
    msg="Attention – Contrôler votre fabrication en cours de production suivant IT-QMS-069"
    c.setFont("Helvetica-BoldOblique",7.5); c.setFillColor(RED)
    c.drawString(ML+(PW-c.stringWidth(msg,"Helvetica-BoldOblique",7.5))/2,y-ph/2-2*mm,msg)
    y-=ph+3*mm
    c.setFont("Helvetica",5.5); c.setFillColor(colors.HexColor("#AAAAAA"))
    c.drawCentredString(W/2,y-3*mm,"Ce document est la propriété de Technical Airborne Components Industries S.P.R.L. TAC. Il ne peut être utilisé ou communiqué sans autorisation préalable.")

    c.save(); buf.seek(0)

    reader=PdfReader(buf); writer=PdfWriter(); writer.append(reader)
    page=writer.pages[0]; annots=[]

    for (name,fx,fy,fw,fh,readonly,value) in fields:
        rect=[float(fx),float(fy),float(fx+fw),float(fy+fh)]
        if readonly=="checkbox":
            field=DictionaryObject({
                NameObject("/Type"):    NameObject("/Annot"),
                NameObject("/Subtype"): NameObject("/Widget"),
                NameObject("/FT"):      NameObject("/Btn"),
                NameObject("/T"):       TextStringObject(name),
                NameObject("/V"):       NameObject("/Off"),
                NameObject("/AS"):      NameObject("/Off"),
                NameObject("/DV"):      NameObject("/Off"),
                NameObject("/Ff"):      NumberObject(0),
                NameObject("/Rect"):    ArrayObject([NumberObject(r) for r in rect]),
                NameObject("/DA"):      TextStringObject("/ZaDb 10 Tf 0 0 1 rg"),
                NameObject("/F"):       NumberObject(4),
                NameObject("/H"):       NameObject("/T"),
                NameObject("/MK"):      DictionaryObject({
                    NameObject("/CA"): TextStringObject("4"),
                    NameObject("/BG"): ArrayObject([NumberObject(1),NumberObject(1),NumberObject(1)]),
                    NameObject("/BC"): ArrayObject([NumberObject(0.18),NumberObject(0.31),NumberObject(0.54)]),
                }),
            })
        else:
            flags=1 if readonly else 0
            field=DictionaryObject({
                NameObject("/Type"):    NameObject("/Annot"),
                NameObject("/Subtype"): NameObject("/Widget"),
                NameObject("/FT"):      NameObject("/Tx"),
                NameObject("/T"):       TextStringObject(name),
                NameObject("/V"):       TextStringObject(value),
                NameObject("/DV"):      TextStringObject(value),
                NameObject("/Ff"):      NumberObject(flags),
                NameObject("/Rect"):    ArrayObject([NumberObject(r) for r in rect]),
                NameObject("/DA"):      TextStringObject("/Helvetica 9 Tf 0 0 0 rg"),
                NameObject("/Q"):       NumberObject(1),
                NameObject("/F"):       NumberObject(4),
                NameObject("/BS"):      DictionaryObject({NameObject("/W"):NumberObject(0)}),
                NameObject("/MK"):      DictionaryObject({
                    NameObject("/BG"): ArrayObject([NumberObject(1),NumberObject(1),NumberObject(1)]),
                }),
            })
        ref_=writer._add_object(field); annots.append(ref_)

    if "/Annots" not in page: page[NameObject("/Annots")]=ArrayObject(annots)
    else: page[NameObject("/Annots")].extend(annots)
    acroform=DictionaryObject({
        NameObject("/Fields"):          ArrayObject(annots),
        NameObject("/DA"):              TextStringObject("/Helvetica 9 Tf 0 0 0 rg"),
        NameObject("/NeedAppearances"): BooleanObject(True),
    })
    writer._root_object[NameObject("/AcroForm")]=writer._add_object(acroform)

    # Protection PDF : remplissage autorisé, mais pas modification ni écrasement
    # Permissions : bit 3 (print) + bit 10 (fill forms) actifs
    # On encode en permissions PDF standard
    writer.encrypt(
        user_password="",       # Pas de mot de passe pour ouvrir/remplir
        owner_password="ADMIN_TAC_2024",  # Mot de passe admin pour modifier
        use_128bit=True,
        permissions_flag=0b100000100100  # Print + FillForms uniquement
    )

    out=io.BytesIO(); writer.write(out); out.seek(0)
    return out.read()


@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/gen_pdf', methods=['POST'])
def gen_pdf_route():
    data = request.get_json()
    try:
        pdf_bytes = gen_pdf(data)
        ref = data.get('ref','fiche').replace(' ','_')
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"FO-QMS-069_{ref}.pdf"
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, port=5000)
