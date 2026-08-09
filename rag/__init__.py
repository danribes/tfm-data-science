"""RAG sobre la biblioteca de economía y el corpus crack23.

Tres colecciones que nunca se mezclan en la recuperación (`rag.config.COLLECTIONS`):
`libros` (manuales con copyright, siempre locales), `metodo` (la documentación
del propio modelo) y `crack23` (transcripciones del canal, marcadas como
opinión). Un manual y un vídeo de YouTube no pueden competir en la misma lista
de resultados: citar el canal con la autoridad de Mankiw invalidaría la
respuesta entera.

Almacén: un único fichero SQLite con FTS5 (léxico) y sqlite-vec (denso). La
recuperación es híbrida con fusión RRF. Los embeddings se calculan en local
sobre la GPU — el corpus con copyright no sale de la máquina.
"""
