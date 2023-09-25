from functools import cached_property
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qsl, urlparse, parse_qs
import re
import redis
import uuid

# Conéctate a Redis
r = redis.Redis(host='localhost', port=6379, db=0)

class WebRequestHandler(BaseHTTPRequestHandler):
	@cached_property
	def url(self):
		return urlparse(self.path)

	@cached_property
	def cookies(self):
		return SimpleCookie(self.headers.get("Cookie"))

	def set_book_cookie(self, session_id, max_age=10):
		c = SimpleCookie()
		c["session"] = session_id
		c["session"]["max-age"] = max_age
		self.send_header('Set-Cookie', c.output(header=''))

	def get_book_session(self):
		c = self.cookies
		if not c:
			print("No cookie")
			c = SimpleCookie()
			c["session"] = uuid.uuid4()
		else:
			print("Cookie found")
		return c.get("session").value

	def do_GET(self):
		method = self.get_method(self.url.path)
		if method:
			method_name, dict_params = method
			method = getattr(self, method_name)
			method(**dict_params)
			return
		else:
			self.send_error(404, "Not Found")
		if self.url.path == '/search':
			query = self.query_data.get('q', '')
			self.send_response(200)
			self.send_header("Content-Type", "text/html")
			self.end_headers()
			response = self.search_books_in_redis(query)
			self.wfile.write(response.encode("utf-8"))
		return
		else:
			self.send_error(404, "Not Found")

	def search_books_in_redis(self, query):
		# Realiza la búsqueda en Redis y devuelve los resultados en formato HTML
		# En este ejemplo, se busca en todas las claves almacenadas en Redis si el término de búsqueda está contenido en ellas.
	
		# Obtén todas las claves de Redis
		keys = r.keys()
	
		# Filtra las claves que contienen el término de búsqueda (ignorando mayúsculas y minúsculas)
		matching_books = [key for key in keys if query.lower() in key.decode().lower()]
	
		# Luego, genera una respuesta HTML con los resultados encontrados.
		html_response = self.generate_search_results_html(matching_books)
	
		return html_response

	def generate_search_results_html(self, matching_books):
	        # Genera el HTML para mostrar los resultados de búsqueda
	        # En este ejemplo, se crea una lista ordenada de libros que coinciden con la búsqueda.
	
	        # Comienza la construcción del HTML
	        html = "<html><head><title>Resultados de búsqueda</title></head><body>"
	        html += "<h1>Resultados de búsqueda</h1>"
	
	        # Verifica si se encontraron libros que coinciden con la búsqueda
	        if matching_books:
	            html += "<ul>"
	            for book_key in matching_books:
	                book_id = book_key.decode()
	                # Puedes obtener más información sobre el libro desde Redis aquí
	                # Por ejemplo: book_data = r.get(book_id)
	                html += f"<li><a href='/books/{book_id}'>Libro {book_id}</a></li>"
	            html += "</ul>"
	        else:
	            html += "<p>No se encontraron resultados para esta búsqueda.</p>"
	
	        # Finaliza el HTML
	        html += "</body></html>"
	
	        return html

	def get_book_recomendation(self, session_id, book_id):
		r.rpush(session_id, book_id)
		books = r.lrange(session_id, 0, 5)
		print(session_id, books)
		all_books = [str(i+1) for i in range(4)]
		new = [b for b in all_books if b not in
			   [vb.decode() for vb in books]]
		if new:
			return new[0]

	def get_book(self, book_id):
		session_id = self.get_book_session()
		book_recomendation = self.get_book_recomendation(session_id, book_id)
		book_page = r.get(book_id)
		if book_page:
			self.send_response(200)
			self.send_header("Content-Type", "text/html")
			self.set_book_cookie(session_id)
			self.end_headers()
			response = f"""
			{book_page.decode()}
		<p>  Ruta: {self.path}	</p>
		<p>  URL: {self.url}  </p>
		<p>  HEADERS: {self.headers}  </p>
		<p>  SESSION: {session_id} </p>
		<p>  Recomendación: {book_recomendation}  </p>
"""
			self.wfile.write(response.encode("utf-8"))
		else:
			self.send_error(404, "Not Found")

	def get_index(self):
		session_id = self.get_book_session()
		self.send_response(200)
		self.send_header("Content-Type", "text/html")
		self.set_book_cookie(session_id)
		self.end_headers()
		with open('html/index.html') as f:
			response = f.read()
		self.wfile.write(response.encode("utf-8"))

	def search_books(self):
		session_id = self.get_book_session()
		self.send_response(200)
		self.send_header("Content-Type", "text/html")
		self.set_book_cookie(session_id)
		self.end_headers()
		
		# Obtener los términos de búsqueda del QueryString
		query = parse_qs(self.url.query)
		search_terms = query.get('q', [])
		
		# Aquí puedes realizar la búsqueda en tus libros en Redis y generar la página de resultados
		
		# En este ejemplo, simplemente mostraremos los términos de búsqueda
		response = "<h1>Resultados de búsqueda</h1>"
		response += "<ul>"
		for term in search_terms:
			response += f"<li>{term}</li>"
		response += "</ul>"
		
		self.wfile.write(response.encode("utf-8"))

	def get_method(self, path):
		for pattern, method in mapping:
			match = re.match(pattern, path)
			if match:
				return (method, match.groupdict())

		mapping = [
			(r'^/books/(?P<book_id>\d+)$', 'get_book'),
			(r'^/$', 'get_index'),
			(r'^/search$', 'search_books')  # Agregamos una nueva ruta para la búsqueda
		]
	
	if __name__ == "__main__":
		print("Server starting...")
		server = HTTPServer(("0.0.0.0", 8000), WebRequestHandler)
		server.serve_forever()
