from flask import Flask, render_template
from DCRE.DCRE_routes import dcre_bp
from NCM_Finder.NCM_routes import ncm_bp  
from EasyCKD.EasyCKD_routes import easyckd_bp
from DataSheetos.DataSheetos_routes import datasheetos_bp
from Manuel_dex.ManuelDex_routes import manueldex_bp

app = Flask(__name__)

app.register_blueprint(dcre_bp, url_prefix='/dcre')
app.register_blueprint(ncm_bp, url_prefix='/ncm')   
app.register_blueprint(easyckd_bp, url_prefix='/easyckd') 
app.register_blueprint(datasheetos_bp, url_prefix='/datasheetos')   
app.register_blueprint(manueldex_bp, url_prefix='/manueldex')   

app.secret_key = 'Somos_uma_empresa_de_tecnologia_pensada_para_aprimorar_o_seu_negócio_e_a_sua_casa.'

@app.route("/")
def home():
    return render_template("portal/index.html")  

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port="8080")