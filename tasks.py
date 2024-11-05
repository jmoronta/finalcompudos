from celery_config import celery_app
import getGP as gp
from fast_plate_ocr import ONNXPlateRecognizer
import conexion

@celery_app.task
def process_image(image_path):
    try:
        # Procesar la imagen
        m = ONNXPlateRecognizer('argentinian-plates-cnn-model')
        nropatente = m.run(image_path)
        
        with open(image_path, 'rb') as image_file:
            image_data = image_file.read()
        
        link = gp.convert_to_gplink(image_path)
        
        # Insertar en la base de datos
        conexion.insert_en_tabla(image_path, nropatente, link)
        
        # Generar la ruta de la imagen validada
        asignada_image_path = os.path.join('./Validada', 'validada_' + os.path.basename(image_path))
        
        return {'status': 'success', 'path': asignada_image_path}
    
    except Exception as e:
        return {'status': 'error', 'message': str(e)}
