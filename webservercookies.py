from functools import cached_property
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qsl, urlparse
import re
import redis
import uuid

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
		<p>  URL: {self.url}	  </p>
		<p>  HEADERS: {self.headers}  </p>
		<p>  SESSION: {session_id}	  </p>
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

	def get_method(self, path):
		for pattern, method in mapping:
			match = re.match(pattern, path)
			if match:
				return (method, match.groupdict())

	def search_books_in_redis(self, query):
    	# Realiza la búsqueda de libros en Redis según el término de búsqueda 'query'
    	# Devuelve una lista de libros que coincidan con la búsqueda
    	matching_books = []
    	all_books = r.keys("book*")  # Obtiene todas las claves de libros en Redis
    	for book_key in all_books:
    		book_page = r.get(book_key)
    		if book_page:
    			# Convierte la página del libro en una cadena de texto
    			book_text = book_page.decode("utf-8")
    			# Verifica si el término de búsqueda aparece en la página del libro
    			if query.lower() in book_text.lower():
    				matching_books.append(book_text)
    	return matching_books

	def generate_search_results_html(self, matching_books):
    	# Genera el HTML de los resultados de búsqueda a partir de la lista de libros coincidentes
    	# Puedes utilizar BeautifulSoup para construir la estructura HTML
    	from bs4 import BeautifulSoup
    
    	# Crea un documento HTML en blanco
    	doc = BeautifulSoup("<html><body></body></html>", "html.parser")
    	body = doc.body
    	h1 = doc.new_tag("h1")
    	h1.string = "Resultados de búsqueda"
    	body.append(h1)
    
    	if matching_books:
    		# Si se encontraron libros coincidentes, agrégalos a la lista
    		ul = doc.new_tag("ul")
    		for book in matching_books:
    			li = doc.new_tag("li")
    			li.string = book
    			ul.append(li)
    		body.append(ul)
    	else:
    		# Si no se encontraron libros coincidentes, muestra un mensaje
    		p = doc.new_tag("p")
    		p.string = "No se encontraron resultados para la búsqueda."
    		body.append(p)
    
    	# Convierte el documento HTML a una cadena de texto
    	result_html = doc.prettify()
    	return result_html

mapping = [
	(r'^/books/(?P<book_id>\d+)$', 'get_book'),
	(r'^/$', 'get_index'),
	(r'^/search\?q=(?P<query>[^&]+)', 'get_search'),  # Ruta de búsqueda
]

if __name__ == "__main__":
	print("Server starting...")
	server = HTTPServer(("0.0.0.0", 8000), WebRequestHandler)
	server.serve_forever()
