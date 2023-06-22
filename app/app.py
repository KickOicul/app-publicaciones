from flask import Flask, render_template, request, redirect, url_for
import os
import psycopg2
from werkzeug.utils import secure_filename

conn = psycopg2.connect(
    host=os.environ.get('POSTGRES_HOST'),
    port=os.environ.get('POSTGRES_PORT'),
    database=os.environ.get('POSTGRES_DB'),
    user=os.environ.get('POSTGRES_USER'),
    password=os.environ.get('POSTGRES_PASSWORD')
)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'  # Carpeta de destino para las imágenes subidas
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}  # Extensiones de archivo permitidas

def allowed_file(filename):
    """Verifica si la extensión del archivo es permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM articles')
    articles = cursor.fetchall()
    return render_template('index.html', articles=articles)

@app.route('/upload', methods=['POST'])
def upload():
    title = request.form['title']
    price = request.form['price']
    image = request.files['image']

    if not title:
        return 'ingrese un nombre para el articulo'

    if image.filename == '':
        return 'No se seleccionó ningún archivo'

    if not price.isnumeric() or float(price) < 0 or len(price) > 10:
        return 'Debes ingresar un precio válido'

    if image and allowed_file(image.filename):
        filename = secure_filename(image.filename)
        destination = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])

        image.save(destination)

        cursor = conn.cursor()
        cursor.execute('INSERT INTO articles (title, price, image) VALUES (%s, %s, %s)', (title, price, filename))
        conn.commit()

        return redirect(url_for('index'))

    return 'Archivo no válido. Se permiten solo archivos con las siguientes extensiones: png, jpg, jpeg, gif'

@app.route('/delete/<int:article_id>', methods=['GET'])
def delete(article_id):
    cursor = conn.cursor()
    cursor.execute('SELECT image FROM articles WHERE id=%s', (article_id,))
    article = cursor.fetchone()

    if article:
        filename = article[0]
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Confirmación antes de eliminar
        confirm_message = "¿Estás seguro que deseas eliminar este artículo?"

        return render_template('delete.html', article_id=article_id, confirm_message=confirm_message)

    return redirect(url_for('index'))

@app.route('/delete/<int:article_id>', methods=['POST'])
def delete_confirm(article_id):
    cursor = conn.cursor()
    cursor.execute('SELECT image FROM articles WHERE id=%s', (article_id,))
    article = cursor.fetchone()

    if article:
        filename = article[0]
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        os.remove(filepath)

        cursor.execute('DELETE FROM articles WHERE id=%s', (article_id,))
        conn.commit()

    return redirect(url_for('index'))

@app.route('/update/<int:article_id>', methods=['GET', 'POST'])
def update(article_id):
    if request.method == 'POST':
        title = request.form['title']
        price = request.form['price']
        image = request.files['image']

        cursor = conn.cursor()
        cursor.execute('SELECT image FROM articles WHERE id=%s', (article_id,))
        article = cursor.fetchone()

        if article:
            if image.filename != '':
                filename = secure_filename(image.filename)
                destination = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                if not os.path.exists(app.config['UPLOAD_FOLDER']):
                    os.makedirs(app.config['UPLOAD_FOLDER'])

                image.save(destination)

                # Eliminar la imagen anterior
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], article[0])
                os.remove(filepath)

                cursor.execute('UPDATE articles SET title=%s, price=%s, image=%s WHERE id=%s',
                               (title, price, filename, article_id))
            else:
                cursor.execute('UPDATE articles SET title=%s, price=%s WHERE id=%s',
                               (title, price, article_id))

            conn.commit()

        return redirect(url_for('index'))

    else:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM articles WHERE id=%s', (article_id,))
        article = cursor.fetchone()

        if article:
            return render_template('update.html', article=article)
        else:
            return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
