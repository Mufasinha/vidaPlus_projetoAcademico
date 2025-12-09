from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from functools import wraps
import datetime
import jwt
import os

app = Flask(__name__)

# =======================
# CONFIGURAÇÕES BÁSICAS
# =======================
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "sghss_minimo.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# IMPORTANTE:
# Em produção, troque esta chave por uma mais forte e use variável de ambiente.
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "chave-secreta-dev-mude-isto")

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)


# =======================
# MODELOS (tabelas)
# =======================
class User(db.Model):
    """
    Usuário do sistema.
    Representa autenticação e perfil de acesso (ADMIN, PROFISSIONAL, PACIENTE).
    """
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # ADMIN, PROFISSIONAL, PACIENTE

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role,
        }


class Patient(db.Model):
    """
    Paciente do sistema: dados básicos necessários para atendimento.
    """
    __tablename__ = "pacientes"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    data_nascimento = db.Column(db.String(10), nullable=True)
    telefone = db.Column(db.String(20), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "cpf": self.cpf,
            "data_nascimento": self.data_nascimento,
            "telefone": self.telefone,
        }


class Professional(db.Model):
    """
    Profissional de saúde: médico, enfermeiro, etc.
    """
    __tablename__ = "profissionais"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    especialidade = db.Column(db.String(80), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "especialidade": self.especialidade,
        }


class Consultation(db.Model):
    """
    Consulta entre paciente e profissional.
    Pode ser presencial ou teleconsulta.
    """
    __tablename__ = "consultas"

    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey("pacientes.id"), nullable=False)
    profissional_id = db.Column(db.Integer, db.ForeignKey("profissionais.id"), nullable=False)
    data_hora = db.Column(db.String(25), nullable=False)  # formato ISO string, exemplo: 2025-01-25T14:00:00
    via = db.Column(db.String(20), nullable=False)  # presencial ou teleconsulta
    status = db.Column(db.String(20), nullable=False, default="agendada")
    motivo = db.Column(db.String(255), nullable=True)

    paciente = db.relationship("Patient", backref="consultas")
    profissional = db.relationship("Professional", backref="consultas")

    def to_dict(self):
        return {
            "id": self.id,
            "paciente_id": self.paciente_id,
            "profissional_id": self.profissional_id,
            "data_hora": self.data_hora,
            "via": self.via,
            "status": self.status,
            "motivo": self.motivo,
        }


# =======================
# AUTENTICAÇÃO (JWT)
# =======================
def create_token(user: User) -> str:
    """
    Gera um token JWT com expiração de 2 horas.
    """
    payload = {
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    }
    token = jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")
    if isinstance(token, bytes):  # compatibilidade com versões do PyJWT
        token = token.decode("utf-8")
    return token


def token_required(f):
    """
    Decorator para proteger rotas que exigem autenticação.
    Usa cabeçalho: Authorization: Bearer <token>.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", None)
        if not auth_header:
            return jsonify({"message": "Token não enviado"}), 401

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({"message": "Cabeçalho Authorization inválido. Use: Bearer <token>"}), 401

        token = parts[1]

        try:
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            current_user = User.query.get(data["user_id"])
            if not current_user:
                return jsonify({"message": "Usuário não encontrado"}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token expirado"}), 401
        except Exception as e:
            return jsonify({"message": "Token inválido", "error": str(e)}), 401

        return f(current_user, *args, **kwargs)
    return decorated


# =======================
# ROTAS DE AUTENTICAÇÃO
# =======================
@app.route("/auth/signup", methods=["POST"])
def signup():
    """
    Cria um novo usuário do sistema.
    Campos: email, password, role (opcional, padrão PACIENTE).
    """
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "PACIENTE")

    if not email or not password:
        return jsonify({"message": "email e password são obrigatórios"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"message": "E-mail já cadastrado"}), 400

    pw_hash = bcrypt.generate_password_hash(password).decode("utf-8")
    user = User(email=email, password_hash=pw_hash, role=role)
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Usuário criado com sucesso", "user": user.to_dict()}), 201


@app.route("/auth/login", methods=["POST"])
def login():
    """
    Realiza login de um usuário e devolve um token JWT.
    """
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"message": "email e password são obrigatórios"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return jsonify({"message": "Credenciais inválidas"}), 401

    token = create_token(user)
    return jsonify({"access_token": token, "user": user.to_dict()})


# =======================
# ROTAS DE PACIENTES
# =======================
@app.route("/pacientes", methods=["POST"])
@token_required
def criar_paciente(current_user: User):
    """
    Cria um novo paciente.
    """
    data = request.get_json() or {}
    nome = data.get("nome")
    cpf = data.get("cpf")

    if not nome or not cpf:
        return jsonify({"message": "nome e cpf são obrigatórios"}), 400

    if Patient.query.filter_by(cpf=cpf).first():
        return jsonify({"message": "CPF já cadastrado"}), 400

    paciente = Patient(
        nome=nome,
        cpf=cpf,
        data_nascimento=data.get("data_nascimento"),
        telefone=data.get("telefone"),
    )
    db.session.add(paciente)
    db.session.commit()
    return jsonify(paciente.to_dict()), 201


@app.route("/pacientes", methods=["GET"])
@token_required
def listar_pacientes(current_user: User):
    """
    Lista todos os pacientes cadastrados.
    """
    pacientes = Patient.query.all()
    return jsonify([p.to_dict() for p in pacientes])


@app.route("/pacientes/<int:paciente_id>", methods=["GET"])
@token_required
def obter_paciente(current_user: User, paciente_id: int):
    """
    Retorna os dados de um paciente específico.
    """
    paciente = Patient.query.get_or_404(paciente_id)
    return jsonify(paciente.to_dict())


# =======================
# ROTAS DE PROFISSIONAIS
# =======================
@app.route("/profissionais", methods=["POST"])
@token_required
def criar_profissional(current_user: User):
    """
    Cria um profissional de saúde.
    """
    data = request.get_json() or {}
    nome = data.get("nome")
    if not nome:
        return jsonify({"message": "nome é obrigatório"}), 400

    profissional = Professional(
        nome=nome,
        especialidade=data.get("especialidade"),
    )
    db.session.add(profissional)
    db.session.commit()
    return jsonify(profissional.to_dict()), 201


@app.route("/profissionais", methods=["GET"])
@token_required
def listar_profissionais(current_user: User):
    """
    Lista todos os profissionais de saúde.
    """
    profissionais = Professional.query.all()
    return jsonify([p.to_dict() for p in profissionais])


# =======================
# ROTAS DE CONSULTAS
# =======================
@app.route("/consultas", methods=["POST"])
@token_required
def criar_consulta(current_user: User):
    """
    Cria uma consulta (presencial ou teleconsulta) entre paciente e profissional.
    """
    data = request.get_json() or {}
    paciente_id = data.get("paciente_id")
    profissional_id = data.get("profissional_id")
    data_hora = data.get("data_hora")
    via = data.get("via")  # "presencial" ou "teleconsulta"

    if not (paciente_id and profissional_id and data_hora and via):
        return jsonify({"message": "paciente_id, profissional_id, data_hora e via são obrigatórios"}), 400

    if via not in ["presencial", "teleconsulta"]:
        return jsonify({"message": "via deve ser 'presencial' ou 'teleconsulta'"}), 400

    if not Patient.query.get(paciente_id):
        return jsonify({"message": "Paciente não encontrado"}), 404
    if not Professional.query.get(profissional_id):
        return jsonify({"message": "Profissional não encontrado"}), 404

    consulta = Consultation(
        paciente_id=paciente_id,
        profissional_id=profissional_id,
        data_hora=data_hora,
        via=via,
        status=data.get("status", "agendada"),
        motivo=data.get("motivo"),
    )
    db.session.add(consulta)
    db.session.commit()
    return jsonify(consulta.to_dict()), 201


@app.route("/consultas", methods=["GET"])
@token_required
def listar_consultas(current_user: User):
    """
    Lista consultas; pode filtrar por paciente_id e profissional_id.
    """
    paciente_id = request.args.get("paciente_id")
    profissional_id = request.args.get("profissional_id")

    query = Consultation.query
    if paciente_id:
        query = query.filter_by(paciente_id=paciente_id)
    if profissional_id:
        query = query.filter_by(profissional_id=profissional_id)

    consultas = query.all()
    return jsonify([c.to_dict() for c in consultas])


# =======================
# ROTA DE HEALTHCHECK
# =======================
@app.route("/health", methods=["GET"])
def health():
    """
    Verifica se a API está respondendo.
    """
    return jsonify({"status": "ok", "message": "SGHSS mínimo rodando"}), 200


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    # debug=True apenas em desenvolvimento; em produção use False.
    app.run(debug=True)
