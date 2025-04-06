class Config:
    SECRET_KEY = 'mysecretkey'
    CACHE_TYPE = 'simple'
    SWAGGER = {
        'title': 'Catalogo de Receitas Gourmet',
        'uiversion': 3
    }
    SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'  # Caminho para o banco de dados SQLite
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = 'sua_chave_jwt_secreta'