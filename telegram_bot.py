import telebot
from pymongo import MongoClient
import openai

# Configura la API de Telegram y OpenAI
TELEGRAM_BOT_TOKEN = ""
OPENAI_API_KEY = ""
openai.api_key = OPENAI_API_KEY

# Configura la conexión a MongoDB
client = MongoClient("mongodb+srv://Drew:1234@aracne.lsjzd.mongodb.net/empresa?retryWrites=true&w=majority&appName=Aracne")
db = client["guia_app"]
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Función para generar un resumen con OpenAI
def generar_resumen(tema):
    respuesta = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"Genera un resumen sobre el tema: {tema}",
        max_tokens=200
    )
    return respuesta.choices[0].text.strip()

@bot.message_handler(commands=["start", "help"])
def enviar_bienvenida(message):
    bot.reply_to(message, "Bienvenido al bot de guías de estudio. Envía un tema para generar un resumen.")

@bot.message_handler(func=lambda message: True)
def manejar_mensajes(message):
    tema = message.text
    resumen = generar_resumen(tema)
    bot.reply_to(message, resumen)
    # Guardar en MongoDB
    db.historial.insert_one({"usuario": message.chat.id, "tema": tema, "resumen": resumen})

if __name__ == "__main__":
    bot.polling()
