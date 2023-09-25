from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import re

# Una lista de libros (en este caso, simplemente una lista de diccionarios)
libros = [
    {"titulo": "Rebelión en la Granja", "autor": "George Orwell"},
    {"titulo": "Metro 2033 (NE)", "autor": "Dmitry Glukhovsky"},
    {"titulo": "El Manifiesto Comunista", "autor": "Karl Marx, Friedrich Engels"},
    {"titulo": "Fahrenheit 451", "autor": "Ray Bradbury"},
    {"titulo": "Hitman: Damnation", "autor": "Raymond Benson"}
]

class WebRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        if parsed_url.path == '/search':
            # Procesar la búsqueda
            query = parse_qs(parsed_url.query)
            if 'q' in query:
                term = query['q'][0]
                resultados = self.buscar_libros(term)
                self.enviar_respuesta(resultados)
            else:
                self.send_response(400)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write("Parámetro de búsqueda 'q' faltante en la URL".encode("utf-8"))
        else:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write("Página no encontrada".encode("utf-8"))

    def buscar_libros(self, termino):
        coincidencias = []
        for libro in libros:
            if re.search(termino, libro["titulo"], re.IGNORECASE) or re.search(termino, libro["autor"], re.IGNORECASE):
                coincidencias.append(libro)
        return coincidencias

    def enviar_respuesta(self, resultados):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        response = "<html><body>"
        response += "<h1>Resultados de la búsqueda:</h1>"
        if resultados:
            for libro in resultados:
                response += f"<h2>{libro['titulo']}</h2>"
                response += f"<p>Autor: {libro['autor']}</p>"
        else:
            response += "<p>No se encontraron resultados.</p>"
        response += "</body></html>"
        self.wfile.write(response.encode("utf-8"))

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8000), WebRequestHandler)
    print("Server starting...")
    server.serve_forever()
