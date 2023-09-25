from functools import cached_property
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qsl, urlparse
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

# Código basado en:
# https://realpython.com/python-http-server/
# https://docs.python.org/3/library/http.server.html
# https://docs.python.org/3/library/http.cookies.html


class WebRequestHandler(BaseHTTPRequestHandler):
############################################################################################
		
	def search_books(self):
		query = self.query_data.get("q", "")  # Obtiene el parámetro 'q' del QueryString
		session_id = self.get_book_session()
		
		# Realiza la búsqueda en los libros y devuelve resultados coincidentes
		matching_books = self.search_books_in_redis(query)
		
		# Genera la respuesta HTML con los resultados
		response = self.generate_search_results_html(matching_books)
		
		self.send_response(200)
		self.send_header("Content-Type", "text/html")
		self.set_book_cookie(session_id)
		self.end_headers()
		self.wfile.write(response.encode("utf-8"))
	
	def search_books_in_redis(self, query):
        	# Conecta a Redis
        	r = redis.Redis(host='localhost', port=6379, db=0)
        
        	# Obtén todas las claves de libros almacenados en Redis
        	all_book_keys = r.keys('*')
        
        	# Inicializa una lista para almacenar los libros coincidentes
        	matching_books = []
        
        	# Itera sobre las claves de libros y busca si el término de búsqueda está en el contenido del libro
        	for book_key in all_book_keys:
        		book_content = r.get(book_key).decode('utf-8')
        		if query.lower() in book_content.lower():
        			matching_books.append((book_key, book_content))
        
        	# Devuelve la lista de libros coincidentes
        	return matching_books
        
        		class WebRequestHandler(BaseHTTPRequestHandler):
        	# ...

	def do_GET(self):
		# ...

		if self.path.startswith("/search"):
			# Si la solicitud es para la ruta /search, manéjala para buscar libros
			query = parse_qs(urlparse(self.path).query).get('q', [''])[0]
			matching_books = self.search_books(query)
			self.send_response(200)
			self.send_header("Content-Type", "text/html")
			self.end_headers()
			self.wfile.write(self.generate_search_results_html(matching_books).encode("utf-8"))
			return

	def search_books(self, query):
		# Implementa la lógica para buscar libros según el término de búsqueda
		# Devuelve una lista de libros que coinciden con la búsqueda
		matching_books = []

		# Lógica de búsqueda aquí

		return matching_books

	def generate_search_results_html(self, matching_books):
		# Genera el HTML de los resultados de búsqueda
		# Utiliza BeautifulSoup o construye el HTML manualmente
		# Devuelve una cadena HTML

		# Generación de HTML aquí
		search_results_html = """
		<!DOCTYPE html>
		<html>
		<head>
			<title>Resultados de búsqueda</title>
		</head>
		<body>
			<h2>Resultados de búsqueda:</h2>
			<ul>
		"""

		for book in matching_books:
			search_results_html += f"<li>{book}</li>"

		search_results_html += """
			</ul>
		</body>
		</html>
		"""

		return search_results_html
	
	def generate_search_results_html(self, matching_books):
        	# Crea una estructura HTML para mostrar los resultados
        	html = '<h1>Resultados de búsqueda:</h1>'
        	
        	if not matching_books:
        		html += '<p>No se encontraron resultados.</p>'
        	else:
                        # Itera sobre los libros coincidentes y muestra sus contenidos
                        for book_key, book_content in matching_books:
                                # Puedes usar BeautifulSoup para formatear mejor los resultados
                                soup = BeautifulSoup(book_content, 'html.parser')
                                book_title = soup.find('h1').text  # Supongamos que el título del libro está en un encabezado h1
                
                                # Agrega el título y el contenido del libro a la respuesta HTML
                                html += f'<h2>{book_title}</h2>'
                                html += str(soup)  # Agrega el contenido HTML del libro
        
        	# Devuelve la respuesta HTML completa
        	return html
        	
        	# Agrega el nuevo patrón de ruta para la búsqueda
        	mapping.append((r'^/search$', 'search_books'))
###################################################################################
    @cached_property
    def url(self):
        return urlparse(self.path)

    @cached_property
    def query_data(self):
        return dict(parse_qsl(self.url.query))

    @cached_property
    def post_data(self):
        content_length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(content_length)

    @cached_property
    def form_data(self):
        return dict(parse_qsl(self.post_data.decode("utf-8")))

    @cached_property
    def cookies(self):
        return SimpleCookie(self.headers.get("Cookie"))

    def do_GET(self):
        if self.url.path == '/search':
                self.search_books()
                return
            method = self.get_method(self.url.path)
        if method:
                method_name, dict_params = method
                method = getattr(self, method_name)
                method(**dict_params)
                return
        else:
                self.send_error(404, "Not Found")

    def get_response(self):
        return f"""
    <h1> Hola Web </h1>
    <p>  {self.path}         </p>
    <p>  {self.headers}      </p>
    <p>  {self.cookies}      </p>
    <p>  {self.query_data}   </p>
"""


if __name__ == "__main__":
    print("Server starting...")
    server = HTTPServer(("0.0.0.0", 8000), WebRequestHandler)
    server.serve_forever()
