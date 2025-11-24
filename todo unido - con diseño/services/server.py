import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request
from persistence import PlayerRepository
from services.player_service import PlayerService
from services.email_sender import EmailSender  

app = Flask(__name__)

# Inicializar dependencias
repo = PlayerRepository("data/players.json")
email_sender = EmailSender(
    api_key=os.getenv("BREVO_API_KEY"), 
    remitente={"email": os.getenv("EMAIL_REMITENTE", "melmontoya245@gmail.com"), "name": "Battle for Saturn"}
    )

player_service = PlayerService(repo, email_sender)

@app.route('/')
def home():
    return "Servidor Flask funcionando"

@app.route("/confirmar")
def confirmar():
    token = request.args.get("token")
    if not token:
        return "Token no proporcionado", 400
    try:
        jugador = player_service.confirmar_jugador(token)
        return f"Correo de {jugador.email} confirmado correctamente"
    except ValueError as e:
        return str(e), 400
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)