from functools import cached_property
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qsl, urlparse

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
        # Código para buscar libros en Redis según el término de búsqueda 'query'
        # Debes implementar esta función para buscar en Redis y devolver los resultados
        pass
    
    def generate_search_results_html(self, matching_books):
        # Genera el HTML de los resultados de búsqueda
        # Puedes utilizar BeautifulSoup para construir la estructura HTML
        # Debes implementar esta función para generar la respuesta HTML
        pass
    
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
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(self.get_response().encode("utf-8"))

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
