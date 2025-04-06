from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from config import Config
from flasgger import Swagger
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token, get_jwt_identity
)

app= Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
jwt =JWTManager(app)

swagger = Swagger(app, template={
    "swagger": "2.0",
    "info": {
        "title": "Catálogo de Receitas Gourmet",
        "description": "API para gerenciar receitas com autenticação JWT",
        "version": "1.0.0"
    },
    "securityDefinitions": {
        "BearerAuth": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "Adicione o token JWT no formato: Bearer <seu_token>"
        }
    },
    "security": [
        {
            "BearerAuth": []
        }
    ]
})


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), unique=True, nullable=False)

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    time_minutes = db.Column(db.Integer, nullable=False)

@app.route('/register', methods=['POST'])
def register_user():
    '''
    Registra um novo usuário.
    ---
    parameters:
      - in: body
        name: body
        description: Dados do usuário
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
            email:
              type: string
    responses:
        201:
            description: Usuário registrado com sucesso.
        400:
            description: Erro ao registrar usuário.
    '''
    data = request.get_json()
    if User.query.filter_by(username=data['username']).first():
        return {'message': 'Usuário já existe'}, 400
    new_user = User(username=data['username'], password=data['password'])
    db.session.add(new_user)
    db.session.commit()
    return {'message': 'Usuário registrado com sucesso'}, 201

@app.route('/login', methods=['POST'])
def login():
    '''
    Faz login do usuário.
    ---
    parameters:
      - in: body
        name: body
        description: Dados do usuário
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
            password:
              type: string
    responses:
        200:
            description: Login bem-sucedido.
        401:
            description: Credenciais inválidas.
    '''
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if user and user.password == data['password']:
        access_token = create_access_token(identity=user.username)
        return {'access_token': access_token}, 200
    return {'message': 'Credenciais inválidas'}, 401

app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    '''
    Endpoint protegido que requer autenticação JWT.
    ---
    security:
      - BearerAuth: []
    responses:
        200:
            description: Acesso permitido.
        401:
            description: Token inválido ou ausente.
    '''
    current_user = get_jwt_identity()
    return {'message': f'Bem-vindo {current_user}'}, 200

@app.route('/recipes', methods=['POST'])
@jwt_required()
def create_recipe():
    '''
    Adiciona uma nova receita.
    ---
    security:
      - BearerAuth: []
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required: true
          properties:
            title:
              type: string
            ingredients:
              type: string
            time_minutes:
              type: integer
    responses:
        201:
            description: Receita adicionada com sucesso.
        401:
            description: Erro ao adicionar receita.
    '''
    data = request.get_json()
    new_recipe = Recipe(title=data['title'], ingredients=data['ingredients'], time_minutes=data['time_minutes'])
    db.session.add(new_recipe)
    db.session.commit()
    return {'message': 'Receita adicionada com sucesso'}, 201

@app.route('/recipes', methods=['GET'])
@jwt_required()
def get_recipes():
    '''
    Obtém todas as receitas.
    ---
    security:
      - BearerAuth: []    
    parameters:
      - in: query
        name: title
        type: string
        required: false
        description: Filtra receitas por ingredientes.
      - in: query
        name: imax time
        type: integer
        required: false
        description: Tempo máxcimo
    responses:
        200:
            description: Lista de receitas.
            schema:
                type: array
                items:
                    type: object
                    properties:
                        title:
                            type: string
                        ingredients:
                            type: string
                        time_minutes:
                            type: integer
    '''
    ingredient = request.args.get('ingredient')
    max_time = request.args.get('max_time', type=int)
    query = Recipe.query
    if ingredient:
        query = query.filter(Recipe.ingredients.ilike(f'%{ingredient}%'))
    if max_time is not None:
        query = query.filter(Recipe.time_minutes <= max_time)
    recipes = query.all()
    return jsonify([
        {
            'title': recipe.title,
            'ingredients': recipe.ingredients,
            'time_minutes': recipe.time_minutes
        } for recipe in recipes
    ])

@app.route('/recipes/<int:recipe_id>', methods=['PUT'])
@jwt_required()
def update_recipe(recipe_id):
    '''
    Atualiza uma receita existente.
    ---
    security:
      - BearerAuth: []
    parameters: 
      - in: path
        name: recipe_id
        type: integer
        required: true
        description: ID da receita a ser atualizada.
      - in: body
        name: body
        schema:
          type: object
          required: true
          properties:
            title:
              type: string
            ingredients:
              type: string
            time_minutes:
              type: integer
    responses:
        200:
            description: Receita atualizada com sucesso.
        404:
            description: Receita não encontrada.
    '''
    data = request.get_json()
    recipe = Recipe.query.get_or_404(recipe_id)
    if 'title' in data:
        recipe.title = data['title']
    if 'ingredients' in data:
        recipe.ingredients = data['ingredients']
    if 'time_minutes' in data:
        recipe.time_minutes = data['time_minutes']
    
    db.session.commit()
    return {'message': 'Receita atualizada com sucesso'}, 200


@app.route('/recipes/<int:recipe_id>', methods=['DELETE'])
@jwt_required()

def delete_recipe(recipe_id):
    '''
    Deleta uma receita existente.
    ---
    security:
      - BearerAuth: []
    parameters: 
      - in: path
        name: recipe_id
        type: integer
        required: true
        description: ID da receita a ser deletada.
    responses:
        200:
            description: Receita deletada com sucesso.
        404:
            description: Receita não encontrada.
    '''
    recipe = Recipe.query.get_or_404(recipe_id)
    db.session.delete(recipe)
    db.session.commit()
    return {'message': 'Receita deletada com sucesso'}, 200

@app.route('/')
def home():
    return 'Pagina Inicial'

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Banco de dados criado com sucesso!")
    app.run(debug=True)  # Adiciona o app.run() para iniciar o servidor