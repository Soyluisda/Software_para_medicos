  ![image alt](https://github.com/Soyluisda/Software_para_medicos/blob/751c46764f05d5decff0a06ce6aba9ea8c53aa76/1.jpg)
# generador-historias-clinicas
Proyecto de ejemplo mínimo para generar historias clínicas sin internet.

## Archivos
- `main.py` : script principal. Rellena la plantilla y genera HTML (intenta generar PDF si está disponible).
- `formato.html` : plantilla de la historia clínica (Jinja2).
- `diagnosticos.json` : lista de diagnósticos de ejemplo.
- `requirements.txt` : dependencias Python (Jinja2 y pdfkit).

## Uso
1. Crear y activar un entorno virtual (recomendado).
2. `pip install -r requirements.txt`
3. Asegurarse de tener `wkhtmltopdf` instalado si se desea la generación de PDF.
4. Ejecutar: `python main.py`
5. agregas tus propias imagenes remplazando las que estan aqui
6. asegurate de poner el nombre del medico y su repectico registro medico en cada pante del codigo donde lo piden
7. se puede convertir en un archivo .exe y ejecutarse edesde cualquien pc
8. si neceistas ayuda, me puedes escribir a mi instagram Soyluis_david


