from flask import Blueprint

operator_bp = Blueprint('operator', __name__)

from app.operator import routes
