# Importar las bibliotecas necesarias
from functools import cached_property
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qsl, urlparse
from bs4 import BeautifulSoup as BS
import re
import redis
import uuid

# Configurar la conexión con Redis
r = redis.Redis(host='localhost', port=6379, db=0)

# Definir la clase manejadora de solicitudes web
class WebRequestHandler(BaseHTTPRequestHandler):
	# Propiedad calculada para obtener la URL
	@cached_property
	def url(self):
		return urlparse(self.path)

	# Método para configurar una cookie (ya no se usa)
	def set_book_cookie(self, session_id, max_age=10):
		# Aquí ya no necesitamos cookies
		pass

	# Método para obtener el identificador de sesión
	def get_book_session(self):
		# Obtener el identificador de sesión de la URL si está presente
		query_params = dict(parse_qsl(self.url.query))
		session_id = query_params.get('session_id')

		if not session_id:
			# Si no hay un identificador de sesión en la URL, generar uno nuevo
			session_id = str(uuid.uuid4())

		return session_id

	# Método para manejar solicitudes GET
	def do_GET(self):
		method = self.get_method(self.url.path)
		print("Method", method)
		if method:
			method_name, dict_params = method
			method = getattr(self, method_name)
			method(**dict_params)
			return
		else:
			self.send_error(404, "Not Found")

	# Método para obtener una recomendación de libro
	def get_book_recomendation(self, session_id, book_id):
		r.rpush(session_id, book_id)
		books = r.lrange(session_id, 0, 5)
		print(session_id, books)
		all_books = [str(i + 1) for i in range(4)]
		new = [b for b in all_books if b not in
			   [vb.decode() for vb in books]]
		if new:
			return new[0]

	# Método para obtener y mostrar información de un libro
	def get_book(self, book_id):
		session_id = self.get_book_session()
		book_recomendation = self.get_book_recomendation(session_id, book_id)
		book_page = r.get(book_id)
		print(book_id)
		if book_page:
			self.send_response(200)
			self.send_header("Content-Type", "text/html")
			self.end_headers()
			response = f"""
			{book_page.decode()}
			<p>  Ruta: {self.path}			</p>
			<p>  SESSION: {session_id}	  </p>
			<p>  Recomendación: {book_recomendation}	  </p>
			"""
			self.wfile.write(response.encode("utf-8"))
		else:
			self.send_error(404, "Not Found")

	# Método para obtener y mostrar la página de inicio
	def get_index(self):
		session_id = self.get_book_session()
		self.send_response(200)
		self.send_header("Content-Type", "text/html")
		self.end_headers()
		with open('html/index.html') as f:
			response = f.read()
		self.wfile.write(response.encode("utf-8"))

	# Método para determinar la acción de acuerdo a la URL
	def get_method(self, path):
		print(path)
		for pattern, method in mapping:
			match = re.match(pattern, path)
			if match:
				return (method, match.groupdict())

	# Método para realizar una búsqueda y mostrar resultados
	def get_search(self):
		# Obtener el contenido de la página de búsqueda almacenada en Redis
		searchpage = r.get("search")
	
		# Obtener la cadena de consulta (query) de la URL, excluyendo los primeros 5 caracteres (query = "book=")
		searchquery = self.url.query[5:]
	
		# Convertir la cadena de búsqueda a minúsculas y eliminar comillas
		searchquery = searchquery.lower().replace('"', '')
	
		# Inicializar una variable para almacenar los resultados de la búsqueda
		lastadd = ""
	
		# Iterar a través de los primeros 5 libros (identificados por 'id')
		for id in range(5):
			# Obtener el contenido HTML del libro desde Redis y decodificarlo
			html = r.get(id + 1).decode()
	
			# Utilizar BeautifulSoup para extraer el texto del contenido HTML
			text = BS(html, 'html.parser').get_text()
	
			# Convertir el texto del libro a minúsculas para realizar una búsqueda insensible a mayúsculas
			text = text.lower()
	
			# Tokeniza la cadena de búsqueda en palabras individuales
			search_words = searchquery.split()
	
			# Tokeniza el texto del libro en palabras individuales
			book_words = re.findall(r'\b\w+\b', text)
	
			# Verifica si todas las palabras clave de búsqueda están en el texto del libro
			if all(word in book_words for word in search_words):
				# Si se encuentra la búsqueda, agregar un elemento HTML con un enlace al libro
				# También se incluye un identificador de sesión en forma de QueryString
				lastadd = lastadd + f"""
					<div class="header">
						<h1><a href="\\books\\{id + 1}?session_id={self.get_book_session()}"> Libro {id + 1} contiene búsqueda</a></h1>
					</div>
					<br>
				"""
	
		# Si no se encontraron resultados, se muestra un mensaje indicando que no se encontró la búsqueda
		if lastadd == "":
			lastadd = f"""<h4>No se ha encontrado tu búsqueda</h4>"""
	
		# Configurar la respuesta HTTP con el código 200 (OK) y el tipo de contenido HTML
		self.send_response(200)
		self.send_header("Content-Type", "text/html")
		self.end_headers()
	
		# Combinar el contenido de la página de búsqueda con los resultados y escribir la respuesta
		response = f"""
			{searchpage.decode()}
			""" + lastadd
		self.wfile.write(response.encode("utf-8"))


# Definir las rutas y sus correspondientes métodos
mapping = [
	(r'^/books/(?P<book_id>\d+)$', 'get_book'),
	(r'^/$', 'get_index'),
	(r'^/search', 'get_search')
]

# Iniciar el servidor web
if __name__ == "__main__":
	print("Server starting...")
	server = HTTPServer(("0.0.0.0", 80), WebRequestHandler)
	print("Up")
	server.serve_forever()
